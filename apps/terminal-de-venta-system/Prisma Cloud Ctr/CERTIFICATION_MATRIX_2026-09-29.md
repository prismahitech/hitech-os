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
- Candidate HEAD: `d1200ca3841d5a15d98152f024aaba1c5b1678e9` (documentation commit; runtime evidence remains CI #2314)
- CI run: `#2307`
- G1/G2/G3/G4/G5A/G5B: PASS in CI #2314 on the current candidate lineage.
- Browser evidence artifact: `cloud-center-browser-runtime-36644998368-1`.
- G5C remains OPEN: workflow #5 (`36670756664`) failed at public DNS resolution for `app.hitechrts.com`; evidence artifact `cloud-center-live-readonly-36670756664-1`.
- `main` baseline remains the historical reference captured separately.

## Certification rule

A green gate covers only the evidence class it names. The July live-readonly evidence remains historical and does not certify September 29 live health. The current CI run certifies G5A/G5B only. G5C still requires a fresh live-readonly execution. No production certification is inferred from repository, fixture, or browser evidence.

