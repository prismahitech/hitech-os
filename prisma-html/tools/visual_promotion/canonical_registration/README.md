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
7. mutation authorization.

The engine builds a complete mutation plan before writing. It uses a request lock, current-head check, per-registry preconditions, atomic writes, persisted journal, postcondition verification and transaction-scoped compensating rollback.

## ID policy

Existing IDs are immutable. Workers cannot mint canonical IDs. Automatic semantic inference is forbidden. CREATE_NEW cannot silently reuse an existing ID.

Target and application-layer identifiers are not derived from selectors, filenames, routes, implementation-layer strings or visual similarity.

## Derived outputs

Canonical registration does not hand-edit the Target Index manifest or compiled Identity outputs. `derivation.py` produces an explicit derived-only regeneration plan and verification set using the existing repository generators.

## Current status

This branch hardens the transaction boundary but does **not** claim G-01 fully closed yet. Existing-authority integration for all canonical write dimensions, final derived regeneration commit handling, Work Entry/GVAE handoff and runtime certification remain separate gates.
