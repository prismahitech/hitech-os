# PRISMA Cloud Center — Certification Matrix — 2026-09-29

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
- Candidate HEAD: `63c70f0adf6f09de4a9214c3ccbb1ee29fc8fe00`
- CI run: `#2307`
- G1/G2/G3/G4/G5A/G5B: PASS in that same CI run.
- Browser evidence artifact: `cloud-center-browser-runtime-36644998368-1`.
- `main` baseline remains the historical reference captured separately.

## Certification rule

A green gate covers only the evidence class it names. The July live-readonly evidence remains historical and does not certify September 29 live health. The current CI run certifies G5A/G5B only. G5C still requires a fresh live-readonly execution. No production certification is inferred from repository, fixture, or browser evidence.

