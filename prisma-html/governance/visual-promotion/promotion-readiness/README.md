# PRISMA Canonical Promotion Readiness

Status: `CANONICAL_PROMOTION_READINESS_RESOLUTION`

This tree is a governed derivative of the immutable certified corpus under `../contracts/corpus-certification/`. It never replaces or rewrites that corpus.

## Purpose

Resolve how far each of the 2,097 certified visual census targets can advance toward exact canonical registration using existing NDC, Identity, RIFAT, Visual Control, Target Index, projection and Atlasfin reference evidence.

Candidate is not authority. Promotion readiness is not registration. Registration is not Work Entry authorization. Work Entry authorization is not GVAE APPLY. Source/static evidence is not runtime visual green.

## Ownership

| Writer | Exclusive phase output |
|---|---|
| Chat 1 | `tablet/**` |
| Chat 2 | `pc/**` |
| Chat 3 | `mobile/**` |
| Chat 4 | `shared-ui/**` |
| Chat 5 | `atlasfin-evidence/**` |
| Chat 6 | `README.md`, `contracts/**`, `composed/**` |

No cross-lane writes.

## Surface output set

Each of Tablet, PC, Mobile and Shared UI must produce:

- `RESOLUTION.jsonl` — exactly one row per certified target;
- `REUSE.jsonl` — exact subset whose decision is `READY_REUSE_EXISTING_AUTHORITY`;
- `REGISTRATION_PROPOSALS.jsonl` — exact subset whose decision is `READY_FOR_CANONICAL_REGISTRATION`;
- `BLOCKED.jsonl` — exact subset whose decision starts with `BLOCKED_`;
- `PROJECTION_DEBT.jsonl` — exact rows where projection debt/direction needs classification; may be empty when not applicable;
- `MANIFEST.json` — input/output counts, source corpus pins and validation;
- `SUMMARY.md` — human-readable findings without inventing authority.

The union of reuse + registration proposals + blocked + not-applicable must equal the exact surface input count.

## Chat 5 evidence output

`atlasfin-evidence/` contains only reference evidence:

- `REFERENCE_ANALYSIS.jsonl`
- `IDENTITY_RECIPE_REUSE_CANDIDATES.jsonl`
- `CROSS_SURFACE_EQUIVALENCE_EVIDENCE.jsonl`
- `VISUAL_ONLY_EQUIVALENCE.jsonl`
- `MANIFEST.json`
- `SUMMARY.md`

Atlasfin evidence never mints or resolves NDC/Identity authority by itself.

## Chat 6 composed output

After accepted handoffs exist, Chat 6 may deterministically produce:

- `composed/RESOLUTION_CORPUS.jsonl`
- `composed/CROSS_SURFACE_SEMANTIC_GROUPS.json`
- `composed/COLLISIONS.json`
- `composed/ZERO_LOSS.json`
- `composed/CANONICAL_PROMOTION_PLAN.json`
- `composed/CANONICAL_PROMOTION_PLAN.md`
- `composed/SUMMARY.md`

The composer must fail closed on missing lane bytes, stale source hashes, duplicate target IDs, unknown enum values, invented canonical IDs, semantic mutation, or accounting other than exactly 2,097 input records.

## Hard boundaries

- no recensus or broad rediscovery;
- no Materiality Catalog;
- no GVAE/Atlasfin rebuild;
- no CSS/SCSS/TSX/JSX/product/runtime mutation;
- no generated projection repair;
- no GVAE APPLY;
- no canonical NDC/VIS/BND/TGT/LYR/adapter minting in worker lanes;
- no global Identity/RIFAT/NDC/Target Index registration before the final plan and gates;
- recipe equality alone is visual similarity, never semantic identity.
