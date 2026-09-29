#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const terminalRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const workerModule = await import(pathToFileURL(path.join(terminalRoot, "infra/cloudflare/licflow3-worker/src/worker.js")).href);
const worker = workerModule.default;
const ADMIN_TOKEN = "PRISMA_TEST_ADMIN_TOKEN";

const PYTHON_SERVER = String.raw`
import json, sqlite3, sys

db_path = sys.argv[1]
conn = sqlite3.connect(db_path, timeout=30, isolation_level=None, check_same_thread=False)
conn.execute("PRAGMA foreign_keys=ON")
failure_pattern = None

def reply(req_id, payload):
    print(json.dumps({"id": req_id, **payload}, separators=(",", ":")), flush=True)

while True:
    line = sys.stdin.readline()
    if not line:
        break
    try:
        req = json.loads(line)
        req_id = req.get("id")
        kind = req.get("kind")
        if kind == "init":
            conn.executescript(req.get("sql", ""))
            reply(req_id, {"ok": True})
            continue
        if kind == "set_failure":
            failure_pattern = req.get("pattern")
            reply(req_id, {"ok": True, "pattern": failure_pattern})
            continue
        if kind == "query" or kind == "run":
            sql = req.get("sql", "")
            params = req.get("params", [])
            if failure_pattern and failure_pattern in sql:
                raise RuntimeError("Injected failure for test atomicity")
            cur = conn.execute(sql, params)
            if kind == "run":
                reply(req_id, {"ok": True, "changes": cur.rowcount})
            else:
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description] if cur.description else []
                mapped = [dict(zip(cols, row)) for row in rows]
                reply(req_id, {"ok": True, "rows": mapped})
            continue
        if kind == "first":
            sql = req.get("sql", "")
            params = req.get("params", [])
            if failure_pattern and failure_pattern in sql:
                raise RuntimeError("Injected failure for test atomicity")
            cur = conn.execute(sql, params)
            row = cur.fetchone()
            cols = [d[0] for d in cur.description] if cur.description else []
            reply(req_id, {"ok": True, "row": dict(zip(cols, row)) if row else None})
            continue
        if kind == "batch":
            statements = req.get("statements", [])
            conn.execute("BEGIN IMMEDIATE")
            try:
                if failure_pattern:
                    for stmt in statements:
                        if failure_pattern in stmt.get("sql", ""):
                            raise RuntimeError("Injected failure for test atomicity")
                results = []
                for index, stmt in enumerate(statements):
                    try:
                        cur = conn.execute(stmt.get("sql", ""), stmt.get("params", []))
                        results.append({"changes": cur.rowcount})
                    except Exception as exc:
                        raise RuntimeError(f"statement_index={index}; sql={stmt.get('sql', '')[:500]}; error={exc}") from exc
                conn.execute("COMMIT")
                reply(req_id, {"ok": True, "results": results})
            except Exception:
                conn.execute("ROLLBACK")
                raise
            continue
        raise RuntimeError("Unsupported test command")
    except Exception as e:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        reply(req.get("id"), {"ok": False, "error": str(e)})
`;

class D1Harness {
  constructor(dbPath) {
    this.dbPath = dbPath;
    this.proc = spawn("python3", ["-u", "-c", PYTHON_SERVER, dbPath], { stdio: ["pipe", "pipe", "pipe"] });
    this.seq = 0;
    this.pending = new Map();
    this.buffer = "";
    this.proc.stdout.setEncoding("utf8");
    this.proc.stdout.on("data", (chunk) => {
      this.buffer += chunk;
      while (true) {
        const idx = this.buffer.indexOf("\n");
        if (idx < 0) break;
        const line = this.buffer.slice(0, idx);
        this.buffer = this.buffer.slice(idx + 1);
        if (!line.trim()) continue;
        const msg = JSON.parse(line);
        const resolver = this.pending.get(msg.id);
        if (resolver) {
          this.pending.delete(msg.id);
          resolver(msg);
        }
      }
    });
    this.proc.stderr.setEncoding("utf8");
    this.proc.stderr.on("data", () => {});
  }
  command(kind, extra = {}) {
    const id = ++this.seq;
    const payload = JSON.stringify({ id, kind, ...extra }) + "\n";
    return new Promise((resolve, reject) => {
      this.pending.set(id, resolve);
      this.proc.stdin.write(payload, (err) => {
        if (err) {
          this.pending.delete(id);
          reject(err);
        }
      });
    });
  }
  async init(sql) {
    const r = await this.command("init", { sql });
    if (!r.ok) throw new Error(r.error || "D1_INIT_FAILED");
  }
  async setFailure(pattern) {
    const r = await this.command("set_failure", { pattern });
    if (!r.ok) throw new Error(r.error || "SET_FAILURE_FAILED");
    if (r.pattern !== pattern) throw new Error("SET_FAILURE_PATTERN_NOT_ACCEPTED");
  }
  async query(sql, params = []) {
    const r = await this.command("query", { sql, params });
    if (!r.ok) throw new Error(r.error || "D1_QUERY_FAILED");
    return r.rows;
  }
  async first(sql, params = []) {
    const r = await this.command("first", { sql, params });
    if (!r.ok) throw new Error(r.error || "D1_FIRST_FAILED");
    return r.row;
  }
  async all(sql, params = []) {
    const r = await this.command("query", { sql, params });
    if (!r.ok) throw new Error(r.error || "D1_ALL_FAILED");
    return r.rows;
  }
  async run(sql, params = []) {
    const r = await this.command("run", { sql, params });
    if (!r.ok) throw new Error(r.error || "D1_RUN_FAILED");
    return r;
  }
  async batch(prepared) {
    const statements = prepared.map((stmt) => ({ sql: stmt.sql, params: stmt.params }));
    const r = await this.command("batch", { statements });
    if (!r.ok) {
      const error = new Error(r.error || "D1_BATCH_FAILED");
      error.message = r.error || "D1_BATCH_FAILED";
      throw error;
    }
    return r.results.map((result) => ({ success: true, meta: { changes: result.changes } }));
  }
  prepare(sql) {
    const harness = this;
    return {
      sql,
      params: [],
      bind: (...params) => ({
        sql,
        params,
        run: () => harness.run(sql, params),
        first: () => harness.first(sql, params),
        all: async () => ({ results: await harness.all(sql, params) })
      })
    };
  }
  close() {
    try { this.proc.stdin.end(); } catch {}
    try { this.proc.kill(); } catch {}
  }
}

function makeEnv(harness) {
  return {
    PRISMA_LICFLOW3_D1: harness,
    PRISMA_ADMIN_TOKEN: ADMIN_TOKEN,
    PRISMA_LICFLOW3_MODE: "test"
  };
}

async function call(harness, urlPath, method = "GET", body = null, admin = false) {
  const headers = { "content-type": "application/json" };
  if (admin) headers["x-prisma-admin-token"] = ADMIN_TOKEN;
  const request = new Request(`https://test.invalid${urlPath}`, {
    method,
    headers,
    body: body === null ? undefined : JSON.stringify(body)
  });
  const response = await worker.fetch(request, makeEnv(harness));
  let payload = null;
  try { payload = await response.json(); } catch {}
  return { status: response.status, payload };
}

function assert(condition, code, details = {}) {
  if (!condition) {
    const error = new Error(code);
    error.details = details;
    throw error;
  }
}
function unique(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}
function migrationSql() {
  const paths = [
    "infra/cloudflare/licflow3-worker/migrations/0001_licflow3_core.sql",
    "infra/cloudflare/licflow3-worker/migrations/0002_customer_setup.sql",
    "infra/cloudflare/licflow3-worker/migrations/0003_plan_based_provisioning.sql",
    "infra/cloudflare/licflow3-worker/migrations/0004_customer_device_claim_integrity.sql",
    "infra/cloudflare/licflow3-worker/migrations/0005_replacement_slot_reuse.sql"
  ];
  return paths.map((p) => fs.readFileSync(path.join(terminalRoot, p), "utf8")).join("\n");
}

async function createSetup(harness, prefix, extra = {}) {
  const setupId = unique(`setup_${prefix}`);
  const setupBundleId = unique(`bundle_${prefix}`);
  const setupCode = unique(`G3-${prefix}`).toUpperCase().replace(/[^A-Z0-9_-]/g, "-");
  const tenantSlug = unique(`tenant-${prefix}`).toLowerCase();
  const body = {
    setupId,
    setupBundleId,
    setupCode,
    tenantSlug,
    businessName: `PRISMA G3 ${prefix}`,
    planId: "TABLET_PC_MANAGED",
    customerId: unique(`cust_${prefix}`),
    tenantId: unique(`tenant_${prefix}`),
    businessId: unique(`biz_${prefix}`),
    licenseId: unique(`lic_${prefix}`),
    licenseAssignmentId: unique(`assign_${prefix}`),
    ...extra
  };
  const result = await call(harness, "/api/admin/customer-setups/create", "POST", body, true);
  assert(result.status === 200 && result.payload?.resultCode === "PLAN_BASED_CUSTOMER_ONBOARDING_READY", "SETUP_CREATE_FAILED", { result });
  return body;
}

async function directCount(harness, table, where, params) {
  const row = await harness.first(`select count(*) as count from ${table} where ${where}`, params);
  return Number(row?.count || 0);
}

async function main() {
  const dbPath = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "prisma-cloud-center-g3-")), "g3.sqlite");
  const harnesses = [];
  const seed = new D1Harness(dbPath);
  harnesses.push(seed);
  const migrations = migrationSql();
  await seed.init(migrations);

  const checks = [];

  // 1. Atomic create failure: no partial setup graph.
  const setupFailHarness = new D1Harness(dbPath);
  harnesses.push(setupFailHarness);
  await setupFailHarness.setFailure("insert into customer_setup_bundles");
  const failedSetupIds = unique("setup_atomic_fail");
  const failedSetup = {
    setupId: failedSetupIds,
    setupBundleId: unique("bundle_atomic_fail"),
    setupCode: unique("G3-ATOMIC-SETUP").toUpperCase(),
    tenantSlug: unique("tenant-g3-atomic-fail").toLowerCase(),
    businessName: "PRISMA G3 atomic setup failure",
    planId: "TABLET_PC_MANAGED",
    customerId: unique("cust_atomic_fail"),
    tenantId: unique("tenant_atomic_fail"),
    businessId: unique("biz_atomic_fail"),
    licenseId: unique("lic_atomic_fail"),
    licenseAssignmentId: unique("assign_atomic_fail")
  };
  const setupFailure = await call(setupFailHarness, "/api/admin/customer-setups/create", "POST", failedSetup, true);
  assert(setupFailure.status === 500 && setupFailure.payload?.resultCode === "CUSTOMER_SETUP_PROVISIONING_FAILED", "ATOMIC_SETUP_FAILURE_NOT_FAIL_CLOSED", { setupFailure });
  assert(await directCount(seed, "customer_setups", "setup_id = ?", [failedSetup.setupId]) === 0, "ATOMIC_SETUP_LEFT_CUSTOMER_SETUP");
  assert(await directCount(seed, "customer_setup_bundles", "setup_bundle_id = ?", [failedSetup.setupBundleId]) === 0, "ATOMIC_SETUP_LEFT_BUNDLE");
  assert(await directCount(seed, "license_assignments", "license_assignment_id = ?", [failedSetup.licenseAssignmentId]) === 0, "ATOMIC_SETUP_LEFT_ASSIGNMENT");
  assert(await directCount(seed, "licenses", "license_id = ?", [failedSetup.licenseId]) === 0, "ATOMIC_SETUP_LEFT_LICENSE");
  assert(await directCount(seed, "tenants", "slug = ?", [failedSetup.tenantSlug]) === 0, "ATOMIC_SETUP_LEFT_TENANT");
  checks.push("atomic_customer_setup_rollback");

  // 2. Provisioning-only package must persist the canonical commercial SKU separately.
  const starter = await createSetup(seed, "starter", { planId: "TABLET_PC_MOBILE_MANAGED" });
  const starterLicense = await seed.first("select plan, status from licenses where license_id = ?", [starter.licenseId]);
  const starterTenant = await seed.first("select plan, status from tenants where slug = ?", [starter.tenantSlug]);
  const starterSetupRow = await seed.first("select plan_code, package_code from customer_setups where setup_id = ?", [starter.setupId]);
  const starterSlots = await seed.query("select surface, allowed from customer_setup_slots where setup_id = ? order by surface", [starter.setupId]);
  assert(starterLicense?.plan === "TABLET_PC_MANAGED", "STARTER_LICENSE_PLAN_NOT_COMMERCIAL");
  assert(starterTenant?.plan === "TABLET_PC_MANAGED", "STARTER_TENANT_PLAN_NOT_COMMERCIAL");
  assert(starterSetupRow?.plan_code === "TABLET_PC_MOBILE_MANAGED" && starterSetupRow?.package_code === "PRISMA_TRIPLE_DEVICE_STARTER", "STARTER_PROVISIONING_ID_LOST");
  assert(JSON.stringify(starterSlots) === JSON.stringify([
    { surface: "mobile", allowed: 1 },
    { surface: "pc", allowed: 1 },
    { surface: "tablet", allowed: 1 }
  ]), "STARTER_SLOT_MATRIX_DRIFT", { starterSlots });
  checks.push("provisioning_only_starter_maps_to_commercial_sku");

  // 3. Real concurrent claims on the same DB with separate connections.
  const setup = await createSetup(seed, "concurrent");
  const claimHarnesses = [new D1Harness(dbPath), new D1Harness(dbPath), new D1Harness(dbPath)];
  harnesses.push(...claimHarnesses);
  const claimResponses = await Promise.all(claimHarnesses.map((h, i) =>
    call(h, "/api/customer/devices/claim", "POST", {
      setupCode: setup.setupCode,
      surface: "tablet",
      deviceId: `g3-concurrent-tablet-${i}`
    })
  ));
  const successes = claimResponses.filter((r) => r.status === 200 && r.payload?.resultCode === "DEVICE_CLAIM_ACCEPTED");
  assert(successes.length === 2, "CONCURRENT_CLAIM_SUCCESS_COUNT_DRIFT", { claimResponses });
  assert(await directCount(seed, "customer_device_claims", "setup_id = ? and surface = ? and status = 'claimed'", [setup.setupId, "tablet"]) === 2, "CONCURRENT_CLAIM_PERSISTENCE_COUNT_DRIFT");
  const claimedSlotCount = Number((await seed.first("select claimed from customer_setup_slots where setup_id = ? and surface = 'tablet'", [setup.setupId]))?.claimed || 0);
  assert(claimedSlotCount === 2, "CONCURRENT_CLAIM_AGGREGATE_COUNTER_DRIFT", { claimedSlotCount });
  checks.push("concurrent_claims_respect_two_tablet_slots");

  // 4. Idempotency / replay: same device cannot create a second claim.
  const successfulDevice = successes[0].payload.device.deviceId;
  const beforeReplay = await directCount(seed, "customer_device_claims", "setup_id = ? and device_id = ?", [setup.setupId, successfulDevice]);
  const replay = await call(seed, "/api/customer/devices/claim", "POST", {
    setupCode: setup.setupCode,
    surface: "tablet",
    deviceId: successfulDevice
  });
  const afterReplay = await directCount(seed, "customer_device_claims", "setup_id = ? and device_id = ?", [setup.setupId, successfulDevice]);
  assert(replay.status === 409 && replay.payload?.resultCode === "DEVICE_ALREADY_CLAIMED", "DEVICE_REPLAY_NOT_BLOCKED", { replay });
  assert(beforeReplay === afterReplay, "DEVICE_REPLAY_MUTATED_STATE");
  checks.push("device_claim_replay_is_idempotently_blocked");

  // 5. Replacement releases the exact physical claim slot, then new device can reclaim it.
  const oldDeviceId = successes[1].payload.device.deviceId;
  const replacement = await call(seed, "/api/admin/customer-devices/replacement/approve", "POST", {
    setupCode: setup.setupCode,
    surface: "tablet",
    oldDeviceId,
    reason: "G3 replacement slot release test",
    confirmAdminLicenseAction: true
  }, true);
  assert(replacement.status === 200 && replacement.payload?.resultCode === "DEVICE_REPLACEMENT_APPROVED" && replacement.payload?.slotReleased === true, "REPLACEMENT_SLOT_NOT_RELEASED", { replacement });
  const activeAfterReplacement = await directCount(seed, "customer_device_claims", "setup_id = ? and surface = 'tablet' and status = 'claimed'", [setup.setupId]);
  const availableSlotsAfterReplacement = await directCount(seed, "customer_device_claim_slots", "setup_bundle_id = ? and surface = 'tablet' and status = 'AVAILABLE'", [setup.setupBundleId]);
  assert(activeAfterReplacement === 1 && availableSlotsAfterReplacement >= 1, "REPLACEMENT_STATE_DRIFT", { activeAfterReplacement, availableSlotsAfterReplacement });
  const replacementEligibleSlot = await seed.first("select slot_id as slotId, status, expires_at as expiresAt from customer_device_claim_slots where setup_id = ? and surface = 'tablet' and status = 'AVAILABLE' and (expires_at is null or expires_at > ?) order by slot_index asc limit 1", [setup.setupId, new Date().toISOString()]);
  const replacementSetupSlot = await seed.first("select claimed, allowed from customer_setup_slots where setup_id = ? and surface = 'tablet' limit 1", [setup.setupId]);
  const replacementSetupRow = await seed.first("select plan_code as planCode, package_code as packageCode, status from customer_setups where setup_id = ? limit 1", [setup.setupId]);
  const replacementClaim = await call(seed, "/api/customer/devices/claim", "POST", {
    setupCode: setup.setupCode,
    surface: "tablet",
    deviceId: "g3-replacement-new-device"
  });
  assert(replacementClaim.status === 200 && replacementClaim.payload?.resultCode === "DEVICE_CLAIM_ACCEPTED", "REPLACEMENT_NEW_DEVICE_CLAIM_FAILED", { replacementClaim, replacementEligibleSlot, replacementSetupSlot, replacementSetupRow });
  checks.push("replacement_releases_and_reuses_exact_slot");

  // 6. Atomic claim failure: audit failure rolls back claim, device and slot.
  const failClaimSetup = await createSetup(seed, "claim-failure");
  const failClaimHarness = new D1Harness(dbPath);
  harnesses.push(failClaimHarness);
  await failClaimHarness.setFailure("audit_events (event_id");
  const failClaimBefore = await directCount(seed, "customer_device_claims", "setup_id = ? and device_id = ?", [failClaimSetup.setupId, "g3-atomic-claim-device"]);
  const failedClaim = await call(failClaimHarness, "/api/customer/devices/claim", "POST", {
    setupCode: failClaimSetup.setupCode,
    surface: "tablet",
    deviceId: "g3-atomic-claim-device"
  });
  assert(failClaimBefore === 0 && failedClaim.status === 500 && failedClaim.payload?.resultCode === "CUSTOMER_SETUP_UPSTREAM_FAILED", "ATOMIC_CLAIM_FAILURE_NOT_FAIL_CLOSED", { failedClaim });
  assert(await directCount(seed, "customer_device_claims", "setup_id = ? and device_id = ?", [failClaimSetup.setupId, "g3-atomic-claim-device"]) === 0, "ATOMIC_CLAIM_LEFT_CLAIM");
  assert(await directCount(seed, "devices", "tenant_slug = ? and device_id = ?", [failClaimSetup.tenantSlug, "g3-atomic-claim-device"]) === 0, "ATOMIC_CLAIM_LEFT_DEVICE");
  assert(await directCount(seed, "customer_device_claim_slots", "setup_bundle_id = ? and surface = 'tablet' and status = 'AVAILABLE'", [failClaimSetup.setupBundleId]) === 1 || await directCount(seed, "customer_device_claim_slots", "setup_bundle_id = ? and surface = 'tablet' and status = 'AVAILABLE'", [failClaimSetup.setupBundleId]) === 2, "ATOMIC_CLAIM_SLOT_NOT_ROLLED_BACK");
  checks.push("atomic_claim_failure_rolls_back_all_writes");

  // 7. Atomic replacement failure: audit failure leaves old claim and slot intact.
  const failReplacementSetup = await createSetup(seed, "replacement-failure");
  const successfulReplacementClaim = await call(seed, "/api/customer/devices/claim", "POST", {
    setupCode: failReplacementSetup.setupCode,
    surface: "tablet",
    deviceId: "g3-replacement-atomic-old"
  });
  assert(successfulReplacementClaim.status === 200, "PRECONDITION_REPLACEMENT_CLAIM_FAILED", { successfulReplacementClaim });
  const failReplacementHarness = new D1Harness(dbPath);
  harnesses.push(failReplacementHarness);
  await failReplacementHarness.setFailure("audit_events (event_id");
  const failedReplacement = await call(failReplacementHarness, "/api/admin/customer-devices/replacement/approve", "POST", {
    setupCode: failReplacementSetup.setupCode,
    surface: "tablet",
    oldDeviceId: "g3-replacement-atomic-old",
    reason: "G3 injected audit failure",
    confirmAdminLicenseAction: true
  }, true);
  assert(failedReplacement.status === 500, "ATOMIC_REPLACEMENT_FAILURE_NOT_FAIL_CLOSED", { failedReplacement });
  const replacementClaimState = await seed.first("select status, claim_slot_id from customer_device_claims where setup_id = ? and device_id = ?", [failReplacementSetup.setupId, "g3-replacement-atomic-old"]);
  assert(replacementClaimState?.status === "claimed", "ATOMIC_REPLACEMENT_LEFT_CLAIM_REPLACED");
  const replacementSlotState = await seed.first("select status, device_id from customer_device_claim_slots where setup_bundle_id = ? and device_id = ?", [failReplacementSetup.setupBundleId, "g3-replacement-atomic-old"]);
  assert(replacementSlotState?.status === "CLAIMED" && replacementSlotState?.device_id === "g3-replacement-atomic-old", "ATOMIC_REPLACEMENT_LEFT_SLOT_RELEASED", { replacementSlotState });
  checks.push("atomic_replacement_failure_rolls_back_all_writes");

  // 8. Retry createCustomerSetup with identical identifiers must preserve an already claimed slot.
  const retrySetup = await createSetup(seed, "setup-retry");
  const retryClaim = await call(seed, "/api/customer/devices/claim", "POST", {
    setupCode: retrySetup.setupCode,
    surface: "tablet",
    deviceId: "g3-retry-claimed-device"
  });
  assert(retryClaim.status === 200, "RETRY_PRECONDITION_CLAIM_FAILED", { retryClaim });
  const retryBefore = Number((await seed.first("select claimed from customer_setup_slots where setup_id = ? and surface = 'tablet'", [retrySetup.setupId]))?.claimed || 0);
  const retryReplay = await call(seed, "/api/admin/customer-setups/create", "POST", retrySetup, true);
  assert(retryReplay.status === 200 && retryReplay.payload?.resultCode === "PLAN_BASED_CUSTOMER_ONBOARDING_READY", "SETUP_RETRY_NOT_ACCEPTED", { retryReplay });
  const retryAfter = Number((await seed.first("select claimed from customer_setup_slots where setup_id = ? and surface = 'tablet'", [retrySetup.setupId]))?.claimed || 0);
  const retryClaimSlot = await seed.first("select status, device_id from customer_device_claim_slots where setup_bundle_id = ? and device_id = ?", [retrySetup.setupBundleId, "g3-retry-claimed-device"]);
  assert(retryBefore === 1 && retryAfter === 1 && retryClaimSlot?.status === "CLAIMED", "SETUP_RETRY_RESET_CLAIMED_SLOT", { retryBefore, retryAfter, retryClaimSlot });
  checks.push("setup_retry_preserves_claimed_state");

  // Read-only graph integrity over the same local D1-compatible database used by the race tests.
  const orphanClaims = await directCount(seed, "customer_device_claims", "claim_slot_id IS NULL", []);
  assert(orphanClaims === 0, "GRAPH_ORPHAN_CLAIMS_WITHOUT_SLOT", { orphanClaims });

  const danglingClaims = Number((await seed.first(
    "select count(*) as count from customer_device_claims c left join customer_setups s on s.setup_id = c.setup_id left join customer_device_claim_slots cs on cs.slot_id = c.claim_slot_id left join licenses l on l.license_id = cs.license_id left join license_plans p on p.plan_id = cs.plan_id where c.status = 'claimed' and (s.setup_id is null or cs.slot_id is null or l.license_id is null or p.plan_id is null)"
  ))?.count || 0);
  assert(danglingClaims === 0, "GRAPH_DANGLING_ACTIVE_CLAIMS", { danglingClaims });

  const danglingBundles = Number((await seed.first(
    "select count(*) as count from customer_setup_bundles b left join customer_setups s on s.setup_id = b.setup_id left join licenses l on l.license_id = b.license_id left join license_assignments a on a.license_assignment_id = b.license_assignment_id where s.setup_id is null or l.license_id is null or a.license_assignment_id is null"
  ))?.count || 0);
  assert(danglingBundles === 0, "GRAPH_DANGLING_SETUP_BUNDLES", { danglingBundles });

  const danglingClaimSlots = Number((await seed.first(
    "select count(*) as count from customer_device_claim_slots cs left join customer_setup_bundles b on b.setup_bundle_id = cs.setup_bundle_id left join licenses l on l.license_id = cs.license_id left join license_plans p on p.plan_id = cs.plan_id where b.setup_bundle_id is null or l.license_id is null or p.plan_id is null"
  ))?.count || 0);
  assert(danglingClaimSlots === 0, "GRAPH_DANGLING_CLAIM_SLOTS", { danglingClaimSlots });

  const counterMismatches = Number((await seed.first(
    "select count(*) as count from customer_setup_slots ss where ss.claimed != (select count(*) from customer_device_claims c where c.setup_id = ss.setup_id and c.surface = ss.surface and c.status = 'claimed') or ss.claimed > ss.allowed or ss.claimed < 0"
  ))?.count || 0);
  assert(counterMismatches === 0, "GRAPH_AGGREGATE_SLOT_COUNTER_MISMATCH", { counterMismatches });
  checks.push("setup_license_assignment_claim_slot_graph_integrity");
  checks.push("aggregate_slot_counter_integrity");

  console.log(JSON.stringify({
    ok: true,
    verifier: "verify-cloud-center-concurrency-idempotency-01",
    generatedAt: new Date().toISOString(),
    gate: "G3",
    resultCode: "PASS_CLOUD_CENTER_CONCURRENCY_IDEMPOTENCY_SOURCE_AND_LOCAL_RUNTIME",
    checks
  }, null, 2));

  harnesses.forEach((h) => h.close());
}

try {
  await main();
} catch (error) {
  console.error(JSON.stringify({
    ok: false,
    verifier: "verify-cloud-center-concurrency-idempotency-01",
    generatedAt: new Date().toISOString(),
    gate: "G3",
    resultCode: error.message || "CLOUD_CENTER_CONCURRENCY_IDEMPOTENCY_FAILED",
    details: error.details || {}
  }, null, 2));
  process.exit(1);
}
