#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const toolsDir = path.dirname(fileURLToPath(import.meta.url));
const terminalRoot = path.resolve(toolsDir, "..");

function read(relativePath) {
  return fs.readFileSync(path.join(terminalRoot, relativePath), "utf8");
}
function assert(condition, code, details = {}) {
  if (!condition) {
    const error = new Error(code);
    error.details = details;
    throw error;
  }
}
function sliceFunction(source, startMarker, endMarker) {
  const start = source.indexOf(startMarker);
  const end = source.indexOf(endMarker, start);
  assert(start >= 0 && end > start, "FUNCTION_BOUNDARY_NOT_FOUND", { startMarker, endMarker });
  return source.slice(start, end);
}

function main() {
  const worker = read("infra/cloudflare/licflow3-worker/src/worker.js");
  const migration0004 = read("infra/cloudflare/licflow3-worker/migrations/0004_customer_device_claim_integrity.sql");
  const migration0002 = read("infra/cloudflare/licflow3-worker/migrations/0002_customer_setup.sql");

  assert(worker.includes("const results = await db.batch(prepared);"), "RUNBATCH_RESULT_CAPTURE_MISSING");
  assert(worker.includes("results: Array.isArray(results) ? results : []"), "RUNBATCH_RESULTS_NOT_RETURNED");

  const claim = sliceFunction(worker, "async function claimCustomerDevice(request, env) {", "async function customerLicenseStatus");
  assert(claim.includes("claim_slot_id"), "CLAIM_SLOT_ID_LINK_MISSING");
  assert(claim.includes("runBatch(env, statements"), "CLAIM_NOT_TRANSACTIONAL");
  assert(claim.includes("customer_device_claim_slots"), "CLAIM_SLOT_PERSISTENCE_MISSING");
  assert(claim.includes("auditInsertStatement"), "CLAIM_AUDIT_NOT_IN_BATCH");
  assert(claim.includes("D1_CLAIM_PERSISTENCE_VERIFY_FAILED"), "CLAIM_READ_AFTER_WRITE_MISSING");
  assert(!claim.includes("await registerClaimedDevice(env, pass"), "CLAIM_DEVICE_WRITE_IS_OUTSIDE_TRANSACTION");
  assert(!claim.includes('await recordAudit(env, pass.tenantSlug, \\"customer_device.claim\\"'), "CLAIM_AUDIT_IS_OUTSIDE_TRANSACTION");
  checksPush("device_claim_atomic_batch_and_readback");

  const setup = sliceFunction(worker, "async function createCustomerSetup(request, env) {", "async function resolveCustomerSetup");
  assert(setup.includes("runBatch(env, statements"), "CUSTOMER_SETUP_NOT_TRANSACTIONAL");
  assert(setup.includes("D1_CUSTOMER_SETUP_PERSISTENCE_VERIFY_FAILED"), "CUSTOMER_SETUP_READ_AFTER_WRITE_MISSING");
  assert(!setup.includes("insert or replace into customer_setups"), "CUSTOMER_SETUP_REPLACE_CAN_RESET_PARENT_STATE");
  assert(!setup.includes("insert or replace into customer_setup_slots"), "CUSTOMER_SETUP_REPLACE_CAN_RESET_AGGREGATE");
  assert(!setup.includes("insert or replace into customer_device_claim_slots"), "CUSTOMER_SETUP_REPLACE_CAN_RESET_CLAIMS");
  assert(setup.includes("on conflict(setup_id, surface)"), "CUSTOMER_SETUP_SLOT_IDEMPOTENCY_GUARD_MISSING");
  assert(setup.includes("on conflict(slot_id)"), "CLAIM_SLOT_IDEMPOTENCY_GUARD_MISSING");
  checksPush("customer_setup_atomic_and_retry_safe");

  const activation = sliceFunction(worker, "async function activateLicense(request, env, mode) {", "async function registerDevice");
  assert(activation.includes("runBatch(env, [tenantStatement, licenseMutation.statement, auditStatement]"), "LICENSE_MUTATIONS_NOT_TRANSACTIONAL");
  assert(activation.includes("D1_LICENSE_OPERATION_PERSISTENCE_VERIFY_FAILED"), "LICENSE_MUTATION_READ_AFTER_WRITE_MISSING");
  assert(activation.includes("auditEventExists"), "LICENSE_MUTATION_AUDIT_READBACK_MISSING");
  checksPush("confirmed_license_mutations_atomic_and_verified");

  const refresh = sliceFunction(worker, "async function customerLicenseRefresh(request, env) {", "async function customerPortal");
  assert(refresh.includes("const refreshAudit = await recordAudit"), "CUSTOMER_LICENSE_REFRESH_AUDIT_NOT_CHECKED");
  assert(refresh.includes("AUDIT_PERSISTENCE_REQUIRED"), "CUSTOMER_LICENSE_REFRESH_AUDIT_FAILURE_NOT_FAIL_CLOSED");
  checksPush("customer_license_refresh_requires_verified_audit");

  const deviceRegister = sliceFunction(worker, "async function registerDevice(request, env) {", "async function integrationReceipt");
  assert(deviceRegister.includes("const audit = result.ok ? await recordAudit"), "DEVICE_REGISTER_AUDIT_NOT_CHECKED");
  assert(deviceRegister.includes("auditVerified: audit.ok === true"), "DEVICE_REGISTER_AUDIT_RESULT_NOT_EXPOSED");
  checksPush("device_register_requires_verified_audit");

  const receipt = sliceFunction(worker, "async function integrationReceipt(request, env) {", "async function createNote");
  assert(receipt.includes("const audit = result.ok ? await recordAudit"), "RECEIPT_AUDIT_NOT_CHECKED");
  assert(receipt.includes("auditVerified: audit.ok === true"), "RECEIPT_AUDIT_RESULT_NOT_EXPOSED");
  checksPush("integration_receipt_requires_verified_audit");

  const note = sliceFunction(worker, "async function createNote(request, env, slug) {", "async function route");
  assert(note.includes("const audit = result.ok ? await recordAudit"), "NOTE_AUDIT_NOT_CHECKED");
  assert(note.includes("auditVerified: audit.ok === true"), "NOTE_AUDIT_RESULT_NOT_EXPOSED");
  checksPush("tenant_note_requires_verified_audit");

  const replacement = sliceFunction(worker, "async function approveDeviceReplacement(request, env) {", "async function commercialSummary");
  assert(replacement.includes("runBatch(env, ["), "REPLACEMENT_NOT_TRANSACTIONAL");
  assert(replacement.includes("D1_REPLACEMENT_PERSISTENCE_VERIFY_FAILED"), "REPLACEMENT_READ_AFTER_WRITE_MISSING");
  assert(replacement.includes("select count(*) as count from customer_device_claims"), "REPLACEMENT_RECOMPUTES_ACTIVE_CLAIM_COUNT");
  assert(replacement.includes("set status = 'AVAILABLE', device_id = null"), "REPLACEMENT_DOES_NOT_RELEASE_EXACT_CLAIM_SLOT");
  assert(replacement.includes("D1_REPLACEMENT_PERSISTENCE_VERIFY_FAILED"), "REPLACEMENT_READ_AFTER_WRITE_MISSING");
  assert(replacement.includes("releasedClaimSlot"), "REPLACEMENT_SLOT_READBACK_MISSING");
  assert(replacement.includes("auditEventExists"), "REPLACEMENT_AUDIT_READBACK_MISSING");
  checksPush("replacement_atomic_and_readback");

  const auditStart = worker.indexOf("async function recordAudit(env, slug, eventType, payload) {");
  const auditEnd = worker.indexOf("async function activateLicense", auditStart);
  assert(auditStart >= 0 && auditEnd > auditStart, "AUDIT_FUNCTION_NOT_FOUND");
  const audit = worker.slice(auditStart, auditEnd);
  assert(audit.includes("AUDIT_TABLE_REQUIRED"), "AUDIT_SCHEMA_FAILURE_NOT_EXPLICIT");
  assert(audit.includes("AUDIT_WRITE_FAILED"), "AUDIT_WRITE_FAILURE_NOT_EXPLICIT");
  assert(audit.includes("AUDIT_PERSISTENCE_VERIFY_FAILED"), "AUDIT_READBACK_FAILURE_NOT_EXPLICIT");
  assert(audit.includes("verified: true"), "AUDIT_SUCCESS_NOT_VERIFIED");
  checksPush("audit_helper_fail_closed");

  assert(migration0004.includes("ALTER TABLE customer_device_claims ADD COLUMN claim_slot_id TEXT;"), "CLAIM_SLOT_COLUMN_MIGRATION_MISSING");
  assert(migration0004.includes("UPDATE customer_device_claims"), "CLAIM_SLOT_LEGACY_BACKFILL_MISSING");
  assert(migration0004.includes("customer_device_claim_slots.device_id = customer_device_claims.device_id"), "CLAIM_SLOT_BACKFILL_NOT_DEVICE_BOUND");
  assert(migration0004.includes("ux_customer_device_claims_setup_surface_slot"), "CLAIM_SLOT_UNIQUE_INDEX_MISSING");
  assert(migration0002.includes("UNIQUE (setup_id, device_id)"), "BASE_DEVICE_ID_IDEMPOTENCY_CONSTRAINT_MISSING");
  checksPush("schema_constraints_support_atomic_claim");

  console.log(JSON.stringify({
    ok: true,
    verifier: "verify-cloud-center-persistence-hardening-01",
    generatedAt: new Date().toISOString(),
    gate: "G2",
    resultCode: "PASS_CLOUD_CENTER_PERSISTENCE_INTEGRITY_SOURCE",
    checks
  }, null, 2));
}

const checks = [];
function checksPush(value) { checks.push(value); }

try {
  main();
} catch (error) {
  console.error(JSON.stringify({
    ok: false,
    verifier: "verify-cloud-center-persistence-hardening-01",
    generatedAt: new Date().toISOString(),
    gate: "G2",
    resultCode: error.message || "CLOUD_CENTER_PERSISTENCE_HARDENING_FAILED",
    details: error.details || {}
  }, null, 2));
  process.exit(1);
}
