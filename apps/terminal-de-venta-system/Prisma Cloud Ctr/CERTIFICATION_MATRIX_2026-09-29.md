# PRISMA Cloud Center — Certification Matrix — 2026-09-30

| Surface / Gate | SOURCE | LOCAL | BROWSER | LIVE_READONLY | LIVE_MUTATION | PRODUCTION | VISUAL |
|---|---|---|---|---|---|---|---|
| Contract / authority (G1) | ✅ PASS | ✅ exercised in CI fixture | — | — | — | — | — |
| Persistence integrity (G2) | ✅ PASS | ✅ exercised in CI fixture | — | — | — | — | — |
| Concurrency / idempotency (G3) | ✅ PASS | ✅ PASS in CI #2307 | — | — | — | — | — |
| D1 graph integrity (G4) | ✅ PASS | ✅ PASS in CI #2307 | — | — | — | — | — |
| Cloud Center local runtime (G5A) | ✅ PASS | ✅ PASS in CI #2307 | — | — | — | — | — |
| Cloud Center browser runtime (G5B) | ✅ PASS | ✅ PASS in CI #2307 | ✅ desktop + 390x844 artifact | — | — | — | ✅ |
| Cloud Center live read-only (G5C) | ✅ contract exists | — | — | ⚠️ July evidence only; September refresh not certified | — | — | — |
| Live mutation (G6) | ✅ ceremony documented | — | — | blocked until G5C | 🚫 explicit authorization required | — | — |
| Security (G7) | ✅ policy + source gates | ✅ CI checks | ⏳ current browser review | — | — | — | — |
| Documentation (G8) | ✅ current | ✅ consistency under CI | — | — | — | — | — |
| Certification matrix (G9) | ✅ this document | ✅ current candidate tracked | ⏳ | ⏳ | 🚫 | not inferred | ⏳ |

## Current authority

- Candidate branch: `governance/cloud-center-roadmap-step1-20260929`
- Candidate HEAD before this documentation update: `82c512751267db134bc8f012d6e3a01a403ef197`.
- Live Worker Preview certification run: `36789056912`.
- Emergency read-only Preview run: `36789056978`.
- Worker direct read-only artifact: `cloud-center-live-readonly-36789056912-1`.
- Emergency Preview artifact: `cloud-center-emergency-readonly-preview-36789056978-1`.
- Preview certification URL: `https://cloud-center-live-recert-prisma-cloud-semilla.hitech-os-preview.workers.dev`.
- G1/G2/G3/G4/G5A/G5B/G5C: PASS for the named evidence classes on the candidate lineage.
- `app.hitechrts.com` remains a separate canonical-domain observation and is not represented as production-certified.
- The live-readonly workflow now runs on the governed candidate branch and on `main` for post-merge recertification.

## Certification rule

A green gate covers only the evidence class it names. The September 30 G5C certification is specifically a direct Worker Preview certification. It proves the remote Worker contract and read-only boundary through the Cloudflare Preview URL, while canonical `app.hitechrts.com` reachability remains an external production-domain observation. No production certification is inferred from Worker Preview evidence. The July live-readonly evidence remains historical provenance only.


## Closure boundary

- Production custom-domain certification: NOT CLAIMED.
- Live mutation G6: NOT EXECUTED; explicit operator authorization remains required.
- Post-merge `main` recertification: REQUIRED after PR #597 is integrated.
