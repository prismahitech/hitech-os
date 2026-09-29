# PRISMA Visual Operating Graph Wave 2 post-merge adversarial audit

Status: `FIX_REQUIRED`
Canonical base audited: `5ad615cd2264310a2e669adbf58ee4c12fd5c2ea`
Source PR: `#585`
Fresh task-exact Authority Mesh: run `36548016503`, artifact `11023820410`, digest `sha256:94ffc3ed4a97543022b21dbbe42e5d3a7989d5a3ee616620ac6066f293e76184`
Authority result: `PASS_COMPOSED_AUTHORITY_MESH`, 100% required authority coverage, zero blockers.

Evidence classification: source-static contract review only. This document does not certify browser rendering, runtime visuals, production, distribution or deployment.

## Decision

PR #585 established the read-only Next Safe Action Engine and What-if Digital Twin. A post-merge source-static contract review found one bounded defect in unmapped blocker handling. The canonical capability therefore moves from `DONE / LOCAL_VERIFIED` to `FIX / VERIFY_REQUIRED` while setting `doNotRebuild=true`. This is corrective hardening of the existing implementation, not a rebuild.

## Proven defect

The published blocker model requires that an unmapped source blocker be preserved as `UNCLASSIFIED_SOURCE_BLOCKER` **and** explicitly carry `requiresTaxonomyUpdate=true`, never a guessed category.

Current Wave 2 `classify_blockers()` preserves the source token and assigns `UNCLASSIFIED_SOURCE_BLOCKER`, but the returned row does not include `requiresTaxonomyUpdate=true`. The accompanying fail-closed action is correct, but the contract metadata is incomplete.

## Required corrective gate

Before touching Wave 2 source:
- keep `doNotRebuild=true`;
- obtain a fresh Factory Ledger MUTATION decision for requestedAction `FIX`;
- patch only the existing Wave 2 blocker-classification contract;
- add a native adversarial regression test;
- run deterministic CI and no-fake-green gates;
- return to `DONE / LOCAL_VERIFIED` only after exact-head evidence proves the corrected output.

## Boundaries preserved

No product/runtime mutation, semantic minting, canonical visual registration, NDC/Identity/RIFAT/Target Index/Visual Promotion/Work Entry/GVAE writes, database change, deployment or runtime certification is authorized by this audit.
