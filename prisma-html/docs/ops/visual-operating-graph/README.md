# PRISMA Visual Operating Graph

Status: `FOUNDATION_V1`  
Capability: `visual.operating_graph_v1`

This directory is the operator entry point for the PRISMA Visual Operating Graph Foundation.

The Operating Graph does **not** create a new semantic authority, repository intelligence engine, mutation engine, status mailbox, database or runtime control plane. It composes current PRISMA authorities into a deterministic, provenance-preserving process model so agents can answer where the visual-governance process is, why something is blocked and what evidence is required next.

## Read order

1. `PRISMA_VISUAL_OPERATING_GRAPH_SPEC.md`
2. `PRISMA_VISUAL_CHANGE_DOCTRINE.md`
3. `PRISMA_PROCESS_PHASE_AND_BLOCKER_MODEL.md`
4. `PRISMA_MASTER_MAP_GENERATION_CONTRACT.md`
5. `PRISMA_LIVE_PHASE_TRUTH_REDUCER_SPEC.md`
6. `PRISMA_NEXT_SAFE_ACTION_AND_WHAT_IF_SPEC.md`

Machine-readable contracts live under:

`prisma-html/governance/visual-operating-graph/`

## Authority boundary

The graph is a composition layer. Domain authorities remain authoritative in their own domains:

- Factory Ledger: capability maturity, anti-rework, next gate and do-not-rebuild.
- Authority Mesh / Layer Map: task-exact authority and protected scope.
- Code Atlas / UIMAP: repository and physical UI evidence.
- NDC: neutral meaning, scope and provenance concepts.
- Identity: visual meaning, recipes and adapters.
- RIFAT / prisma-ui: exact visual location and projection authority.
- Target Index: generated persistent target addressing.
- Visual Promotion: candidate/current-truth/readiness evidence.
- Work Entry / GVAE: admission and governed visual mutation.
- Runtime QA: rendered proof.
- Change Assurance: evidence lifecycle from UNDERSTAND through PROVE.
- Atlasfin: visual cockpit/reference/evidence only.

A graph node or edge never becomes stronger authority than the source it references.

## Foundation outputs

Foundation defines the contracts for:

- canonical process graph;
- canonical versus live-overlay separation;
- phase/head semantics;
- blocker crosswalks without erasing source codes;
- surface cohort derivation;
- write ownership;
- generated Master Map;
- Live Phase Truth Reducer and Drift Sentinel;
- Next Safe Action explanation;
- non-mutating what-if simulation.

Foundation intentionally does not perform product/runtime mutation, canonical visual registration, GVAE APPLY, broad rediscovery, DB/Prisma work or production certification.

## NEXT ALLOWED GATE

After this Foundation is reviewed and source/static validated, the next allowed gate is a bounded implementation of the **read-only graph builder + source-set verifier + Live Phase Truth Reducer**, using these contracts.

Still forbidden until separately authorized: semantic minting, canonical visual registration, Work Entry mutation, GVAE APPLY and product/runtime mutation.
