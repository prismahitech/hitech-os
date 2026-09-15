# PRISMA Live Phase Truth Reducer and Drift Sentinel Specification

Status: `FOUNDATION_V1_CANONICAL_CONTRACT`

## 1. Purpose

The reducer computes an effective process view without confusing canonical truth with temporal coordination.

It reads canonical `main` plus regenerable live observations and returns both layers separately.

## 2. Canonical inputs

Canonical-state inputs may include:

- Factory Ledger and Evidence Index;
- canonical phase outputs on `main`;
- current Target Index / Identity / RIFAT / NDC authorities;
- versioned promotion Current Truth / Surface Readiness / Promotion Readiness;
- canonical status-channel contract/index;
- canonical Git commit/PR provenance.

## 3. Live overlay inputs

Live overlay may include:

- status branch/mailbox heads;
- worker branches/heads;
- unintegrated receipts;
- open PR state;
- CI queued/in-progress/completed state;
- observation timestamps/freshness.

Live overlay is not committed as historical truth by the reducer.

## 4. Effective-state algorithm

1. Resolve `currentCanonicalMain`.
2. Validate the canonical source-set lock.
3. Build canonical process facts only from sources on that main.
4. Read live sources as a separate overlay.
5. Bind every live fact to its observed head and timestamp.
6. Compare live facts against canonical receipts/phase state.
7. classify drift;
8. emit canonical state, live overlay, disagreements and evidence obligations separately.

Missing live evidence remains missing.

## 5. Drift Sentinel classes

The sentinel distinguishes:

- `CANONICAL_AUTHORITY_DRIFT`: a locked canonical authority changed.
- `RELEVANT_DRIFT`: changed source affects the current graph/query/phase.
- `NON_RELEVANT_DRIFT`: main moved but relevant locked sources are unchanged.
- `STALE_DERIVED_ARTIFACT`: generated map/lock no longer matches its inputs.
- `LIVE_OVERLAY_DRIFT`: live status/worker/receipt disagreement.
- `TEMPORAL_STALENESS`: live observation exceeds freshness policy.
- `WRITER_DRIFT`: unexpected writer modified a governed/generated artifact.

Minimum detections:

- generated Master Map stale;
- source lock mismatch;
- main moved;
- worker head mismatch;
- stale status mailbox;
- status-vs-receipt disagreement;
- Target Index changed;
- Work Entry contract changed;
- surface registry changed;
- promotion vocabulary changed;
- Factory Ledger maturity changed;
- graph generated from obsolete sources.

## 6. Example disagreement

If a worker mailbox says a receipt is missing while the canonical composer already contains an accepted receipt, the reducer reports:

- canonical receipt: present;
- live mailbox: stale/disagreeing;
- classification: `LIVE_OVERLAY_DRIFT`;
- authority effect: none unless a canonical source is also affected.

It never rewrites canonical truth from the stale mailbox.

## 7. Output contract

Reducer output must expose:

- observed canonical main;
- source-set status;
- canonical phase;
- canonical facts;
- live overlay;
- drift findings;
- stale sources;
- unresolved conflicts;
- provenance;
- `productionCertified=false` unless a separate authority proves otherwise.

## 8. Mutation boundary

The reducer and sentinel are read-only.

They may recommend evidence acquisition. They may not mutate authority, status branches, product/runtime, Work Entry or GVAE state.
