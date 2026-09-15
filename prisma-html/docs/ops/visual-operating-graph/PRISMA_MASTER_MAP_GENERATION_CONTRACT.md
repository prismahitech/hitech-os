# PRISMA Master Map Generation Contract

Status: `FOUNDATION_V1_CANONICAL_CONTRACT`

## 1. Problem

The current `PRISMA_VISUAL_CHANGE_MASTER_MAP.md` is useful as an operator/lifecycle contract, but mutable phase state, counts, heads and readiness snapshots age quickly when maintained manually.

Foundation preserves the existing manual Master Map as the current operator contract while introducing a generated operational companion.

A later explicit governance gate may reduce the manual file to stable doctrine after the generated view is proven. Foundation does not silently change that authority today.

## 2. Rule

`manual doctrine + locked machine truth = generated operational map`

Never:

`manual dated snapshot = current truth`

## 3. Source-set lock

`MASTER_MAP_SOURCESET.lock.json` declares the canonical inputs used for generation.

Each source may include:

- path;
- authority domain;
- role;
- schema/version;
- Git blob SHA;
- observed canonical main SHA;
- provenance note.

The lock is generated evidence and must be regenerated when a locked source changes.

## 4. Planned generated outputs

After the generator implementation gate, expected derived outputs are:

- `PRISMA_VISUAL_CHANGE_MASTER_MAP.generated.md`
- `PRISMA_VISUAL_CHANGE_MASTER_MAP.generated.json`
- `PRISMA_PROCESS_GRAPH.generated.json`
- optional `PRISMA_PROCESS_GRAPH.generated.dot`

Exact names/paths remain subject to the implementation gate and repository conventions.

Generated outputs must carry:

- generator/schema version;
- observed canonical main;
- source-set digest;
- generation time as metadata only;
- stale/fresh status;
- explicit non-authority boundary where applicable.

## 5. Precedence

The generator does not flatten authority precedence.

For each field it records the owning domain and source. Conflicting domain sources remain conflicts.

Canonical domain authority beats derived views. Live overlay is rendered separately.

## 6. Staleness

The generated map is stale if:

- current main moved and relevant locked blobs changed;
- source lock does not match source blobs;
- generator/schema version changed without regeneration;
- a required source disappeared;
- a generated file was manually edited;
- a canonical capability or vocabulary source changed.

Main movement with no relevant locked-source change is `NON_RELEVANT_DRIFT`, not automatic invalidation.

## 7. No manual repair

A generated map is never hand-corrected.

If it is wrong:

1. fix the owning canonical authority, curation record or generator;
2. regenerate;
3. verify source-set and output digests.

## 8. Foundation boundary

Foundation defines this contract and the source-set lock only. It does not yet claim that the full generated Master Map engine is implemented or certified.
