# Prisma Cloud Center Changelog

## 2026-09-30 — G5C live-readonly recertification

- Fixed the live-readonly workflow diagnostics command and removed the redundant pnpm argument delimiter from the verifier invocation.
- Corrected verifier argument handling so network failures are preserved as structured evidence rather than aborting before the report is written.
- CI workflow #5 (`36670756664`) executed the corrected diagnostic and verifier against `https://app.hitechrts.com`.
- Public reachability failed at DNS: HTTP preflight `000`, curl exit `6`; Node fetch reported `ENOTFOUND app.hitechrts.com`. No authentication, admin mutation, D1 mutation, or secret exposure occurred.
- Evidence artifact: `cloud-center-live-readonly-36670756664-1`.
- G5C remains OPEN. No production deployment or live mutation was performed.

## 2026-09-29 — G5 runtime recertification

- CI #2307 passed on candidate `63c70f0…` for Cloud Center customer runtime, G1 contract authority, G2 persistence integrity, G3 concurrency/idempotency, G4 D1 graph integrity, G5A local runtime, and G5B browser runtime.
- G3 current verifier covers blocked-license, expired/revoked setup and refresh/revoke/renew conflict behavior; G4 graph corruption drills pass.
- Browser certification produced desktop and 390x844 evidence in CI artifact `cloud-center-browser-runtime-36644998368-1`.
- G5C remains intentionally open because the repository's last live-readonly evidence is dated July 7, 2026; no September 29 live recertification is claimed.
- No production deployment, D1 live write, or live mutation was performed.

## 2026-09-29 — Cloud Center certification hardening

- Completed and CI-certified Cloud Center gates G1 (contract authority), G2 (persistence integrity), G3 (concurrency/idempotency), and G4 (D1 graph integrity) on candidate `e92feb8…`.
- Separated Customer Setup provisioning IDs from canonical commercial SKUs; `TABLET_PC_MOBILE_MANAGED` maps to `TABLET_PC_MANAGED` for underlying license/tenant commercial state.
- Hardened Customer Setup, device claim, replacement, audit, and license mutation flows with atomic D1 batches and read-after-write verification.
- Added replacement-safe claim-slot uniqueness migration and idempotent setup retry behavior.
- Added current certification matrix and retained the July live-readonly evidence as historical rather than current.
- No production deployment or live D1 mutation was performed in this work.



## 2026-07-04

- Canonized visible license terminology for Prisma Cloud Center.
- Promoted `Cloud License Gateway`, `License Admin Bridge`, `Simulation (Dry Run)`, `Confirmed License Operation`, `License Operation Audit`, `License Diagnostics`, and `License Route Map` as operator-facing names.
- Added bridge status fields for `tokenMode`, `mutationMode`, last simulation/confirmed-operation timestamps, last result, upstream reachability, operator checklist, conservative `safeToMutate`, and `secretsExposed: false`.
- Implemented Simulation policy so dry-run validates fields without admin token or confirmed-operation confirmation; confirmed revoke still requires `REVOKE_LICENSE`.
- Added Prisma Customer Setup source readiness with Setup Link, Setup Code, Setup QR, Device Slots, Tablet POS Slot, PC Admin Slot, and Mobile Companion Slot.
- Preserved legacy/internal identifiers `LICFLOW3`, `LICFLOW4`, `/api/licflow4/bridge/*`, `/api/licenses/*`, `prisma-cloud-semilla`, and `prisma_cloud_semilla` for compatibility and verifiers.
- No Cloudflare deploy, DNS/Tunnel change, D1 operation, secret exposure, or real license operation.

## 2026-07-03

- Historical/legacy note: promoted the folder-era product name `Prisma Cloud Ctr` and added LICFLOW4 route compatibility.
- Added server-side-only admin token handling for confirmed bridge actions.
- Added bridge UI status, dry-run controls, explicit confirmations, revoke phrase, and sanitized result display.
- Added sanitized in-memory audit records and diagnostics bridge summary.
- Added safe LICFLOW4 verifiers for bridge routes, frontend token absence, confirmations, sanitized diagnostics, and no auto-run mutations.
- No Cloudflare deploy, DNS/Tunnel change, D1 export/copy, or real license mutation was part of that milestone.
- Documented live Worker `prisma-cloud-semilla` and D1 `prisma_cloud_semilla`.
- Documented expected unauthenticated license route smoke: `401 ADMIN_TOKEN_REQUIRED`.
- Preserved the existing canonical folder instead of creating a duplicate root.

## 2026-07-04 - Final operator readiness closure

- `safeToMutate` is now an explicitly calculated conservative readiness field, not a magic permission and not decorative copy.
- The calculation requires admin-token presence, configured Cloud License Gateway routes, a prior Simulation, and confirmed upstream reachability.
- When reachability is `unknown`, Prisma Cloud Center must keep `safeToMutate: false` and explain the missing gate through `safeToMutateReason` and `safeToMutateChecks`.
- Prisma Customer Setup remains source-ready until Cloud License Gateway deploy and D1 migration are explicitly authorized. Setup Link, Setup Code, Setup QR and Device Claim must not be sold as live customer onboarding until then.
- No Cloudflare deploy, no D1 operation, no secret exposure, no process/port change, and no commit were performed by this closure package.
