# PRISMA Cloud Center — Master Roadmap & Certification Checklist

**Status:** G0 PASSED — STEP 1 BASELINE CLOSED  
**Baseline date:** 2026-09-29  
**Target repository:** `prismahitech/hitech-os`  
**Canonical component:** `apps/terminal-de-venta-system/Prisma Cloud Ctr`

## Mission

Take Prisma Cloud Center from "implemented / historically verified" to a **current, reproducible, evidence-backed certification state** without rebuilding certified components, creating duplicate authorities, or conflating local, browser, live read-only, live mutation, and production certification.

The operating rule is:

> **No evidence. No green. No duplicate authority. No rebuild of certified work.**

## Scope boundaries

This roadmap governs three related but distinct surfaces:

1. **Prisma Cloud Center Core**
   - local control center
   - local API / bridge
   - browser runtime
   - cloud metadata/read-only integration
   - operator diagnostics and supporting views

2. **Cloud License Gateway / LICFLOW3**
   - Cloudflare Worker
   - D1
   - licensing routes
   - Customer Setup
   - device claims and replacement
   - licensing audit/state transitions

3. **PRISMA Change Assurance**
   - isolated Cloud Center vertical
   - Code Atlas projections
   - Authority Pack / Evidence references
   - entitlements projection
   - ROI projection
   - explicit `productionCertified=false` boundary unless independently proven

These surfaces may share contracts, but they do not inherit certification from each other automatically.

---

# MASTER CHECKLIST

## G0 — Baseline freeze

- [ ] Record exact `main` HEAD.
- [ ] Record repository/default branch state.
- [ ] Record source file SHAs for all Cloud Center / LICFLOW3 / shared licensing owners.
- [ ] Record existing evidence artifacts and generation timestamps.
- [ ] Record current Factory Ledger classifications/statuses and `doNotRebuild`.
- [ ] Search open PRs and issues for Cloud Center / LICFLOW3 / Customer Setup overlap.
- [ ] Record current CI/status visibility; never assume green when status is unavailable.
- [ ] Generate machine-readable baseline.
- [ ] Mark stale evidence as historical rather than current.
- [ ] Freeze the baseline reference before source changes begin.

**Gate G0:** `PASS_CLOUD_CENTER_BASELINE_CAPTURED`

---

## G1 — Contract / authority reconciliation

- [x] Define the canonical plan taxonomy.
- [x] Reconcile commercial plans with Customer Setup plans/packages.
- [x] Resolve `TABLET_PC_MOBILE_MANAGED` semantic status explicitly.
- [x] Make `commercialPlanId` explicit and enforce provisioning→commercial SKU mapping at persistence boundaries.
- [x] Build cross-contract matrix: plan, entitlement, surfaces, route, persistence, UI, owner.
- [x] Detect duplicate/competing owners.
- [x] Detect orphan terminology and undocumented aliases.
- [x] Detect routes documented but not implemented and implemented but undocumented.
- [x] Detect incompatible result codes/status vocabulary.
- [x] Register terminology authority.

 **Gate G1:** `PASS_CLOUD_CENTER_CONTRACT_AUTHORITY_RECONCILED` — source/invariant gate revalidated after commercial/provisioning split; CI status remains separately observable.
**G1 revalidation note:** `TABLET_PC_MOBILE_MANAGED` remains provisioning-only and maps to commercial SKU `TABLET_PC_MANAGED`; worker persistence now enforces that boundary.

---

## G2 — Persistence integrity

### Device Claim

- [x] Audit all writes in `claimCustomerDevice()`. Source-hardened.
- [x] Make claim provisioning transactional. D1 batch + claim-slot linkage.
- [x] Ensure slot consumption cannot succeed independently of the claim graph.
- [x] Ensure audit persistence is part of the success contract.
- [x] Add read-after-write verification.
- [x] Forbid `DEVICE_CLAIM_ACCEPTED` on partial state.

### Device Replacement

- [x] Check every write result in `approveDeviceReplacement()`.
- [x] Add fail-closed behavior.
- [x] Add read-after-write verification for claim + slot + audit.
- [x] Forbid `DEVICE_REPLACEMENT_APPROVED` on uncertain state.

### Customer Setup

- [x] Audit provisioning sequence.
- [x] Introduce transaction strategy with explicit schema preflight.
- [x] Ensure no half-created tenant/license/setup graph is reported as success.
- [x] Add full graph verification.

### Audit

- [x] Make `recordAudit()` return verified persistence success/failure.
- [x] Make critical mutations fail closed when audit cannot be verified.
- [x] Preserve sanitized diagnostic behavior.

**Gate G2:** `PASS_CLOUD_CENTER_PERSISTENCE_INTEGRITY` — **PASS in CI #2238** on candidate `e92feb8…`

---

## G3 — Concurrency / idempotency

- [x] Same-slot simultaneous claims.
- [x] Same-device simultaneous claims.
- [x] Simultaneous replacement approvals.
- [x] Repeated identical requests.
- [x] Retry after injected intermediate failure.
- [x] Setup creation retries.
- [ ] Refresh/revoke/renew conflict cases.
- [x] Prove device counters never exceed plan limits.
- [x] Prove no duplicate claims or double slot release.
- [x] Prove no orphan rows.

**G3 status note:** The repository now contains a same-DB multi-connection D1-compatible runtime harness covering concurrency, failure injection, retry preservation and graph integrity. **CI execution is the runtime gate.**

**Gate G3:** `PASS_CLOUD_CENTER_CONCURRENCY_IDEMPOTENCY` — CI-certified on candidate `94c184f…`; refresh/revoke/renew conflict matrix remains open.

---

## G4 — D1 graph and invariant verification

- [x] Validate license -> assignment -> setup -> bundle graph.
- [x] Validate setup -> slot -> claim -> device graph.
- [x] Validate tenant ownership across all related rows.
- [x] Validate audit linkage.
- [x] Validate claimed counters against actual claim state.
- [ ] Validate blocked license states cannot perform customer actions.
- [x] Validate replaced devices cannot remain active.
- [ ] Validate expired/revoked setups fail closed.
- [x] Validate zero orphan/dangling/contradictory state.

**Gate G4:** `PASS_CLOUD_CENTER_D1_GRAPH_INTEGRITY` — CI-certified on candidate `94c184f…`; blocked-license and expired/revoked behavioral fail-closed checks remain open.

---

## G5 — Runtime verification

### Local

- [x] Local server bootstrap (verifier/tooling integrated; runtime execution pending CI/operator environment).
- [x] Port/bind safety.
- [x] Route map.
- [x] Health.
- [x] Cloud adapter.
- [x] License Admin Bridge.
- [x] Diagnostics.
- [x] Secret boundary.
- [x] No destructive process/port behavior.

### Browser

- [x] Desktop runtime verifier implemented; CI evidence pending.
- [x] Mobile runtime verifier implemented; CI evidence pending.
- [x] All 13 Cloud Center core surfaces are covered by browser verifier.
- [x] Hash/surface navigation covered by browser verifier.
- [x] Console error capture/fail-closed assertion covered by browser verifier.
- [x] Page error capture/fail-closed assertion covered by browser verifier.
- [x] HTTP contract checks included in browser verifier via isolated test stub.
- [ ] Expected disconnected probes classified correctly.
- [ ] Screenshot evidence (CI artifact capture for core verifier can be added once G5B baseline is green).

### Live read-only

- [ ] `/health`.
- [ ] public capabilities.
- [ ] tenant status.
- [ ] safe customer setup resolution where available.
- [ ] unauthorized admin boundary.
- [ ] sanitized diagnostics.
- [ ] D1/OAuth/read-only health.
- [x] Current evidence timestamp (historical live evidence explicitly marked stale).

**Gate G5A:** `PASS_CLOUD_CENTER_LOCAL_RUNTIME`  
**Gate G5B:** `PASS_CLOUD_CENTER_BROWSER_RUNTIME` — verifier implemented; current candidate awaits CI execution.  
**Gate G5C:** `PASS_CLOUD_CENTER_LIVE_READONLY_CERTIFIED`

---

## G6 — Live mutation ceremony (separate gate)

This gate is **not implied** by OAuth/D1 or read-only certification.

- [ ] Explicit operator authorization.
- [ ] Token remains presence-only outside backend.
- [ ] Dry run first.
- [ ] Synthetic isolated customer/setup.
- [ ] Create setup.
- [ ] Claim Tablet/PC/Mobile as applicable.
- [ ] Negative claim cases.
- [ ] Refresh.
- [ ] Renewal/commercial transitions.
- [ ] Replacement request/approval/reclaim.
- [ ] Revoke.
- [ ] Audit read-back.
- [ ] Final state read-back.
- [ ] Cleanup/neutralization.
- [ ] Verify no production customer was touched.
- [ ] Verify no secret entered evidence.

**Gate G6:** `PASS_CLOUD_CENTER_LIVE_MUTATION_E2E_CERTIFIED`

---

## G7 — Security certification

- [ ] Secret scanning.
- [ ] Browser exposure review.
- [ ] Diagnostics review.
- [ ] Logs/reports/evidence review.
- [ ] Raw header leakage review.
- [ ] D1 error sanitization review.
- [ ] Tenant enumeration review.
- [ ] Setup-code exposure review.
- [ ] Magic-link scope review.
- [ ] Admin authentication boundary review.
- [ ] Customer authorization does not depend on tenant slug alone.

**Gate G7:** `PASS_CLOUD_CENTER_SECURITY_CERTIFIED`

---

## G8 — Documentation / terminology

- [ ] README.
- [ ] ARCHITECTURE.
- [ ] SECURITY.
- [ ] MANUAL / runbook.
- [ ] CHANGELOG.
- [ ] Current-state document.
- [ ] Certification status document.
- [ ] Canonical terminology registry.
- [ ] Cross-link all evidence and gates.
- [ ] Remove or formally mark stale claims.
- [ ] Homologate Cloud Center / Cloud License Gateway / LICFLOW3 / LICFLOW4 / Change Assurance vocabulary.

**Gate G8:** `PASS_CLOUD_CENTER_DOCUMENTATION_HOMOLOGATED`

---

## G9 — Certification matrix

Maintain one matrix with distinct columns for:

```
SOURCE
LOCAL
BROWSER
LIVE_READONLY
LIVE_MUTATION
PRODUCTION
VISUAL
```

No single `PASS` may imply all columns.

**Gate G9:** `PASS_CLOUD_CENTER_CERTIFICATION_MATRIX_CURRENT`

---

## G10 — Final closure

- [ ] Full lint/type/compile battery.
- [ ] Cloud Center source verifiers.
- [ ] Authority Mesh.
- [ ] anti-rework / Factory Ledger.
- [ ] route map.
- [ ] D1 graph verifier.
- [ ] negative tests.
- [ ] concurrency/idempotency.
- [ ] local runtime.
- [ ] browser desktop/mobile.
- [ ] security.
- [ ] documentation consistency.
- [ ] current live read-only.
- [ ] authorized live mutation if explicitly approved.
- [ ] evidence packaging and hashes.
- [ ] final HEAD revalidation.
- [ ] final tree revalidation.
- [ ] classify every final diff as AUTHORIZED / DERIVED / UNRELATED / ACCIDENTAL.

**Gate G10:** `PASS_CLOUD_CENTER_FINAL_CERTIFICATION`

---

## G11 — Freeze

- [ ] Record certified HEAD.
- [ ] Record source hashes.
- [ ] Record verifier versions.
- [ ] Record evidence hashes.
- [ ] Record D1 schema reference.
- [ ] Record terminology version.
- [ ] Register final Factory Ledger state.
- [ ] Mark certified capabilities `doNotRebuild=true`.
- [ ] Define drift-triggered recertification rules.

**Gate G11:** `CLOUD_CENTER_CERTIFIED_BASELINE_FROZEN`

---

# Non-negotiable operating rules

1. **No rebuild of certified capability without demonstrated drift.**
2. **No second owner for an existing contract or runtime capability.**
3. **No live mutation before live-read certification.**
4. **No critical mutation PASS without read-after-write verification.**
5. **No critical mutation PASS without verifiable audit.**
6. **No current certification from stale historical evidence.**
7. **No terminology drift without explicit canonical mapping.**
8. **No production certification claim from local/source evidence alone.**
9. **No token value in frontend, logs, diagnostics, screenshots, reports, or evidence.**
10. **The final certification must match the exact HEAD that remains governed.**

# Current execution pointer

**Current:** G4 CI-CERTIFIED — G1/G2/G3/G4 PASS on candidate `94c184f…`  
**Next:** G5 runtime/browser + live-readonly; then close G3 license-conflict and G4 blocked-state behavioral subgates.  
**Mutation policy:** live mutation remains prohibited until G5C is green and explicit operator authorization exists.

# Historical evidence rule

Evidence generated in July/August 2026 remains useful as historical baseline and provenance, but does not automatically certify the September 29, 2026 state.

# Stop conditions

Stop and classify instead of forcing green when:

- evidence is missing or stale;
- authority is ambiguous;
- a write result is unchecked;
- state cannot be read back;
- a secret boundary is uncertain;
- a live mutation lacks explicit authorization;
- a change conflicts with Factory Ledger `doNotRebuild`;
- a different component owns the capability;
- the final HEAD differs from the certified HEAD.



### G4 CI pass note
- G3 and G4 passed in the same CI authority cycle after the replacement-slot migration and idempotent Customer Setup hardening.
- No live production mutation was performed.
- G5A previously failed only because the verifier resolved the Worker syntax-check `cwd` one level above the repository; that path is now corrected.
