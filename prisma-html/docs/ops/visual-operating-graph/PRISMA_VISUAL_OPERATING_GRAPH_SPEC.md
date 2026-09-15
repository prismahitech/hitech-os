# PRISMA Visual Operating Graph Specification

Status: `FOUNDATION_V1_CANONICAL_CONTRACT`  
Capability: `visual.operating_graph_v1`

## 1. Purpose

PRISMA already has extensive machine-readable truth. The missing layer is a deterministic operating model that can compose that truth without replacing it.

The Visual Operating Graph exists to answer, with provenance:

- where the governed visual process currently is;
- which capability, target, phase or worker is blocked;
- which authority is missing or stale;
- which evidence supports the current state;
- which writer owns a canonical or generated artifact;
- which action is safe to consider next;
- what would remain blocked under a hypothetical resolution.

It is a **process knowledge graph and derived operational view**, not a new source of truth.

## 2. Non-goals and collision barriers

The Operating Graph MUST NOT:

1. rebuild Code Atlas repository discovery, dependency/ownership/evidence graphs or snapshots;
2. duplicate NDC neutral records, edges, curation or canonical meaning;
3. mint semantic IDs from selectors, routes, filenames, CSS, visual similarity or Atlasfin recipes;
4. become a competing Identity, RIFAT, Target Index or Visual Promotion registry;
5. create a second Factory Ledger or second status mailbox;
6. turn PRISMO Learning patterns into authority;
7. issue Agent Authority Packs or replace Change Assurance;
8. convert recommendation, probability, similarity or score into authorization;
9. write product/runtime source;
10. run GVAE APPLY;
11. claim runtime or production green from static evidence.

When a source is absent, conflicting or stale, the graph represents the gap.

## 3. Authority precedence

For every fact, precedence is domain-scoped rather than globally flattened.

1. Canonical machine-readable authority in the fact's own domain.
2. Current task-exact Authority Mesh / Layer Map for authorization and protected scope.
3. Canonical manual contracts for interpretation and lifecycle.
4. Generated canonical evidence on `main`.
5. Reference-only evidence.
6. Live overlay and coordination status.

A lower layer may explain a higher layer but may not overwrite it.

## 4. Graph node types

Foundation node types are limited to operational queries that PRISMA already needs:

`REQUEST`, `CAPABILITY`, `AUTHORITY`, `SURFACE`, `SURFACE_COHORT`, `NEUTRAL_MEANING`, `VISUAL_MEANING`, `TARGET`, `RECIPE`, `ADAPTER`, `BINDING`, `APPLICATION_LAYER`, `PROJECTION`, `GATE`, `TOOL`, `EVIDENCE`, `BLOCKER`, `WRITER`, `OUTPUT`, `PHASE`, `WORKER`, `RECEIPT`, `PR`, `COMMIT`, `CI_RUN`, `RUNTIME_PROOF`, `LEDGER_STATE`, `DOCUMENT`.

No node type is authority merely because it exists in the graph.

## 5. Base edge types

Foundation relations are:

`requires`, `blocks`, `produces`, `validates`, `projects_to`, `represented_by`, `derived_from`, `evidenced_by`, `observed_by`, `owned_by`, `writes`, `reads`, `updates`, `conflicts_with`, `reconciles`, `supersedes`, `implements`, `belongs_to`, `authorizes`, `does_not_authorize`.

Every material edge carries source provenance. An unsupported relationship is omitted or represented as an explicit gap; it is never inferred into authority.

## 6. Canonical state

`CANONICAL_STATE` is deterministically derived from versioned authorities on the observed canonical `main` commit.

It may contain:

- capability maturity from Factory Ledger;
- neutral IDs from NDC;
- physical location from RIFAT / UIMAP / Target Index;
- Identity recipe and binding authority;
- promotion/current-truth/readiness outputs;
- canonical phase receipts that are committed to `main`;
- versioned contracts and generated evidence.

Canonical graph generation MUST be reproducible from the declared source-set lock.

## 7. Live overlay

`LIVE_OVERLAY` contains ephemeral information such as:

- status branches/mailboxes;
- worker heads not yet integrated;
- receipts not yet canonical;
- CI runs in progress;
- PR state;
- freshness observations;
- pending handoffs.

Live overlay is never allowed to replace canonical state. It is regenerated, time-bounded and clearly marked non-canonical.

## 8. Provenance contract

Every node and edge must identify:

- authority domain;
- source path or external evidence reference;
- source role;
- observed canonical main SHA when applicable;
- source blob or artifact digest when available;
- canonicality class;
- optional evidence refs;
- gaps or conflicts.

A derived graph assertion without provenance is `UNKNOWN`, not green.

## 9. Write ownership

The graph must model who can write what.

Writer roles:

- `CANONICAL_WRITER`: owns a domain authority.
- `GENERATED_WRITER`: deterministically regenerates a derived artifact.
- `RUNTIME_WRITER`: writes runtime/product state under separate authorization.
- `STATUS_WRITER`: writes coordination state only.
- `EVIDENCE_WRITER`: writes evidence/receipts without promoting authority.
- `PROTECTED_CONSUMER`: may read but not write the referenced authority.

Two canonical writers for the same artifact are a blocker. A manually edited generated artifact is drift.

The Operating Graph Foundation owns only its own contracts and future generated Operating Graph outputs.

## 10. Separation from existing graphs

### Code Atlas

Code Atlas remains the repository graph/evidence engine. Operating Graph nodes reference Code Atlas facts; they do not re-discover the repository.

### NDC

NDC remains neutral meaning and scope authority. Operating Graph may point to NDC IDs, but process-graph edges do not become NDC edges automatically.

### Change Assurance

Change Assurance remains the evidence lifecycle and authorization-oriented change-control product. The Operating Graph may consume its stage/evidence results, but cannot issue an Agent Authority Pack or convert its own recommendation into authorization.

### PRISMO Learning

PRISMO Learning remains a read-only pattern/evidence consumer. Its pattern recommendations are not source authority for Operating Graph state.

## 11. Regeneration

Canonical graph generation must be deterministic from:

`source-set lock + canonical main + machine-readable authorities + stable contracts`.

Generated operational views are disposable projections. Manual corrections belong in the owning canonical authority or curation source, never in generated output.

## 12. What the graph does not authorize

A graph result, generated Master Map, Next Safe Action result or what-if simulation does not by itself authorize:

- semantic promotion;
- canonical registration;
- Work Entry mutation;
- GVAE APPLY;
- product/runtime mutation;
- runtime visual certification;
- production certification.
