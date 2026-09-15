# PRISMA Next Safe Action and What-if Digital Twin Specification

Status: `FOUNDATION_V1_CANONICAL_CONTRACT`

## 1. Purpose

This contract defines two read-only consumers of Operating Graph state:

- **Next Safe Action Engine**: explain the next evidence/gate that may be pursued.
- **What-if Digital Twin**: simulate hypothetical authority resolutions without mutating any authority.

Neither system grants authorization.

## 2. Required queries

The Next Safe Action Engine must support at least:

`WHAT_CAN_I_DO_NEXT?`

`WHY_NOT_APPLY_READY(targetId)?`

Expected output fields:

- subject/target;
- current decision;
- preserved source blockers;
- blocker families;
- missing authorities;
- owning authority;
- recommended next safe action;
- allowed tools;
- forbidden actions;
- evidence required;
- possible next gates after resolution;
- provenance;
- stale/unknown flags;
- `authorizationGranted=false`.

## 3. Decision precedence

1. Factory Ledger controls capability-level next gate.
2. Current task-exact Authority Mesh controls task authorization/protected scope.
3. Domain authorities control semantic/location/binding/projection truth.
4. Promotion Readiness explains promotion blockers.
5. Work Entry controls entry into governed visual mutation.
6. GVAE can apply only after its own exact requirements.
7. Runtime QA controls rendered proof.

The engine never skips a layer because a later layer appears technically available.

## 4. Fail-closed actions

If authority is missing, stale, conflicted or unmapped, the default action is one of:

- `ACQUIRE_EVIDENCE`
- `RESOLVE_AUTHORITY_CONFLICT`
- `RESOLVE_SEMANTIC_AUTHORITY`
- `RESOLVE_BINDING`
- `RECONCILE_PROJECTION`
- `REVALIDATE_AUTHORITY`
- `STOP_BLOCKED`

No numerical score may convert these into APPLY.

## 5. What-if simulation

A simulation operates on a copy of canonical graph state.

Hypotheses are tagged:

- `hypothetical=true`;
- `nonAuthoritative=true`;
- `simulationOnly=true`.

Examples:

- resolve NDC primary meaning for a set of targets;
- add a valid binding;
- mark a projection as reconciled;
- update a stale worker receipt.

The simulator recomputes only derived blockers and possible subsequent gates.

It must report:

- blockers removed;
- blockers remaining;
- newly reachable **candidate** gates;
- unresolved authorities;
- assumptions used;
- provenance of the original state;
- `authorizationGranted=false`.

## 6. Critical rule

`possible next gate` is not `authorized next action`.

A simulation that removes the last modeled blocker still cannot mint the real authority/evidence that the production gate requires.

## 7. No writer privileges

The Next Safe Action Engine and What-if Digital Twin are planners/explainers only.

They do not write NDC, Identity, RIFAT, Target Index, Visual Promotion, Work Entry, GVAE, runtime or Factory Ledger.
