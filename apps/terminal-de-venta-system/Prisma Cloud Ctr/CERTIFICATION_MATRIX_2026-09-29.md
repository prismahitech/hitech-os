# PRISMA Cloud Center — Certification Matrix — 2026-09-29

| Surface / Gate | SOURCE | LOCAL | BROWSER | LIVE_READONLY | LIVE_MUTATION | PRODUCTION | VISUAL |
|---|---|---|---|---|---|---|---|
| Contract / authority (G1) | ✅ PASS | ✅ exercised in CI fixture | — | — | — | — | — |
| Persistence integrity (G2) | ✅ PASS | ✅ exercised in CI fixture | — | — | — | — | — |
| Concurrency / idempotency (G3) | ✅ PASS | ✅ PASS in CI #2238 | — | — | — | — | — |
| D1 graph integrity (G4) | ✅ PASS | ✅ PASS in CI #2238 | — | — | — | — | — |
| Cloud Center local runtime (G5A) | ✅ verifier exists | ⏳ current run required | — | — | — | — | ⏳ |
| Cloud Center browser runtime (G5B) | ✅ tooling exists | ⏳ current run required | ⏳ current desktop/mobile evidence required | — | — | — | ⏳ |
| Cloud Center live read-only (G5C) | ✅ contract exists | — | — | ⚠️ July evidence only; September refresh not certified | — | — | — |
| Live mutation (G6) | ✅ ceremony documented | — | — | blocked until G5C | 🚫 explicit authorization required | — | — |
| Security (G7) | ✅ policy + source gates | ✅ CI checks | ⏳ current browser review | — | — | — | — |
| Documentation (G8) | ✅ current | ✅ consistency under CI | — | — | — | — | — |
| Certification matrix (G9) | ✅ this document | ✅ current candidate tracked | ⏳ | ⏳ | 🚫 | not inferred | ⏳ |

## Current authority

- Candidate branch: `governance/cloud-center-roadmap-step1-20260929`
- Candidate HEAD: `e92feb8220a6899b4a06f9082a02f56da615435e`
- CI run: `#2238`
- G1/G2/G3/G4: PASS in that same CI run.
- `main` baseline remains the historical reference captured separately.

## Certification rule

A green gate covers only the evidence class it names. In particular, the July live-readonly evidence is historical and does not certify September 29 live health. No production certification is inferred from repository or fixture evidence.

