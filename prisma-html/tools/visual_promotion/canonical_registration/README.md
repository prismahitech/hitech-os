# Canonical Registration Foundation V1

Capability: `visual.canonical_promotion_integration_v1`

This capability is the bounded transaction boundary between promotion resolution and existing visual authorities. It is independent of GVAE and never performs browser/runtime mutation.

## Authority boundaries

- Workers remain proposal-only.
- NDC Curation remains the semantic canonical writer.
- Identity remains visual-meaning, recipe and adapter authority.
- RIFAT remains exact visual location/layer authority.
- Target Index remains a generated derived view.
- GVAE remains the exact visual application/control engine.
- Atlasfin remains reference/evidence only.

## Target identity

A registration request distinguishes:

- `censusTargetId`: immutable physical evidence from the all-surface census.
- `targetId`: canonical exact application identity.

New canonical target IDs are allocated only by this canonical-registration policy, from a deterministic semantic/census key. Census IDs are never created or rewritten by the capability.

## Transaction

Before mutation the engine requires:

1. exact census evidence pinned in a current-truth snapshot;
2. expected current HEAD;
3. source digest and path;
4. explicit NDC semantic adjudication reference;
5. exact RIFAT binding;
6. explicit application-layer policy;
7. explicit Work Entry handoff;
8. mutation authorization.

The engine builds a complete mutation plan before writing. It uses a transaction lock, current-head check, per-registry preconditions, atomic writes, persisted journal, postcondition verification and transaction-scoped compensating rollback.

Idempotent replay is fail-closed: request identity, expected HEAD and recorded post-state must still match before a prior result can be reused. Rollback is transaction-scoped and refuses to overwrite newer work.

## ID policy

Existing IDs are immutable. Workers cannot mint canonical IDs outside the canonical-registration policy. Automatic semantic inference is forbidden. CREATE_NEW cannot silently reuse an existing ID.

Target and application-layer identifiers are not derived from selectors, filenames, routes, implementation-layer strings or visual similarity.

## Authority integration

The hardening now present on canonical main includes explicit read/validation adapters for the existing authority chain, exact current-truth verification, collision classification, application-policy validation, Work Entry handoff requirements and exact postcondition verification.

This does not create replacement NDC, Identity, RIFAT, Target Index or GVAE authorities.

## Derived outputs

Canonical registration does not hand-edit the Target Index manifest or compiled Identity outputs. `derivation.py` produces an explicit derived-only regeneration plan and verification set using the existing repository generators.

## Current status

The canonical-registration hardening is integrated on `main` after PR #599. Exact-head CI, VISCORE1, ForgeOS, Sync Sentinel and repository-navigation gates passed before merge.

This is **not** G-01 closure. The remaining gate is a fresh exact-main authority/reconciliation pass that proves the concrete canonical registration scope for any target, including owning-authority evidence, Work Entry/GVAE handoff, derived regeneration and end-to-end postconditions. Runtime visual certification remains a separate later gate.

The Tablet `/inventory` target remains blocked until its missing canonical Identity/Binding/Application authority is explicitly proven. No product/runtime visual mutation is authorized by this capability alone.
