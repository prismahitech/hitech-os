# PRISMA Visual Promotion — Six Parallel Chat Prompts

Status: `CANONICAL_PARALLEL_CHAT_PROMPTS`

Current phase: `CORPUS_FINAL_PARALLEL_VERIFICATION`

## How the user should invoke a chat

For a new chat, the user may give only the folder path and say:

> Go to this folder, read the mandatory startup documents, and execute **Chat N** from `PRISMA_VISUAL_PROMOTION_PARALLEL_CHAT_PROMPTS.md`.

For an existing Chat 1–6 that already completed its first lane phase, the user may now say only:

> Continue with your work. The canonical prompt in `prisma-html/docs/ops/visual-promotion-parallel/PRISMA_VISUAL_PROMOTION_PARALLEL_CHAT_PROMPTS.md` was updated. Re-read it, locate your assigned Chat number, read your current status mailbox, and follow the current continuation instructions exactly.

The chat must read the interoperability contract, vocabulary registry, current prompt and its own status mailbox before doing any lane work.

### Mailbox-driven continuation rule

For the current cohort the owner does **not** need to paste per-Chat instructions, witness results or cross-chat handoffs.

The only continuation message required in an existing Chat is:

> Continue with your work. Re-read the canonical prompt and your own mailbox, then execute your current Chat assignment.

On receipt, every Chat must:

1. resolve its own Chat number, status branch and mailbox from `STATUS_CHANNEL_CONTRACT.json` / `STATUS_INDEX.json`;
2. read its own current `STATUS.json` and append-only `LOG.md`;
3. re-read the current phase and its exact Chat section in this canonical prompt;
4. execute only that assignment;
5. publish start/progress/blocker/completion back to the **same mailbox branch**;
6. place the phase result/receipt under `handoff` as required by the current phase;
7. never ask the repository owner to carry a receipt from one Chat to another when the status branch is readable.

Chat 6 must discover Chats 1–5 progress and receipts by reading their deterministic status branches directly. A missing receipt remains missing; do not infer it and do not request a copy/paste relay from the owner.

## Rules shared by all six chats

These rules are inherited by every chat below:

- Work from repository truth, not conversational memory.
- Read root `AGENTS.md`, Field Manual, Factory Ledger Agent Gate, Visual Change Master Map, Visual Core Contract, this folder's interoperability contract and vocabulary registry.
- Record exact `baseHead`.
- Use a fresh task-exact Authority Mesh/Layer Map when the lane intends repository mutation beyond its candidate/bridge/control-plane ownership.
- Reuse current Visual Control/Target Index census. Never treat `DISCOVERY_ONLY` as undiscovered.
- Atlasfin is the priority visual reference.
- The Surface Visual Governor Materiality Catalog is `STANDBY_USER_INVOKED_ONLY`. Do not inspect or consume it unless the repository owner explicitly invokes it for this named task.
- Do not mutate product runtime, product visual source, generated product projections, DB, Prisma, dev servers, ports or unrelated surfaces.
- Do not write global Identity recipe/binding registries, generated Target Index, visual-source-manifest, Factory Ledger/Evidence Index or `FILES_MANIFEST.json` in a worker lane.
- Do not invent canonical IDs. Existing IDs are immutable. Candidate keys are local; canonical composer assigns new global IDs.
- Do not merge into protected branches. Finish on the lane branch with exact changed paths, validation and commit SHA.
- No fake green. Unknown/ambiguous stays blocked or unresolved.
- Web, Chart Lab and Control Center are out of scope and protected.
- Read `status-channel/README.md` and `status-channel/STATUS_CHANNEL_CONTRACT.json`; publish status to the mailbox mapped to your assigned Chat number.
- Status reporting is separate from lane work: update only your dedicated `STATUS.json` and `LOG.md` on the mapped `status/vp-chat-XX-...` branch. Never put lane source/candidate changes on the status branch.
- Publish immediately when this instruction is received, whenever a blocker appears/clears, after a material finding/decision/milestone, and at completion. Include work branch/head, blockers, findings, validations and next action.


## CURRENT CONTINUATION PHASE — NORMATIVE OVERRIDE

Phase: `CANONICAL_PROMOTION_READINESS_RESOLUTION`

This phase begins only after `CORPUS_FINAL_PARALLEL_VERIFICATION` is merged and verified. The certified corpus under `prisma-html/governance/visual-promotion/contracts/corpus-certification/` is immutable input evidence for this phase. Do not rebuild, recensus, broad-discover or silently reinterpret it.

### Canonical phase-start truth

Resolve current `main` directly before work. At phase bootstrap on `3eb092fad5e746a7ceeb9fdba079671934ae9b6d`, repository evidence revalidated:

- total certified input: 2,097;
- `VALID_ELIGIBLE_CANDIDATE`: 139;
- `VALID_REGISTER_TARGET_FIRST`: 1,926;
- `VALID_BLOCKED`: 32;
- Work Entry: 2,065 `REGISTER_TARGET_FIRST` + 32 `BLOCKED`;
- `GVAE_EXACT_APPLY=0`;
- currently authorized canonical promotions: 0;
- `runtimeVisualGreen=false`;
- whole-surface APPLY_READY count: 0;
- semantic review groups: 10;
- cross-surface canonical groups: 0;
- Atlasfin references: 2,421/2,421 valid;
- Materiality Catalog: `STANDBY_USER_INVOKED_ONLY`, uninspected.

Surface truth is reused exactly: Tablet 929, PC 827, Mobile 271, Shared UI 70. Existing DRIFT/MISSING/BLOCKED evidence remains evidence, not a repair request.

### Phase objective

Convert the maximum **demonstrably resolvable** portion of the 2,097 certified records into machine-verifiable canonical-promotion readiness without changing product/runtime and without inventing meaning.

For every input target, determine from existing authority and exact evidence:

1. neutral/canonical meaning when provable;
2. existing NDC / existing Identity meaning reuse or proposal-needed state;
3. existing Identity recipe reuse when provable;
4. Atlasfin reference evidence without granting Atlasfin semantic authority;
5. canonical adapter;
6. exact physical target;
7. route/region/slot/component/owner/layer applicability;
8. projection policy/debt classification;
9. exact existing binding or proposal-needed state;
10. deterministic registration readiness;
11. exact missing authority when blocked;
12. whether Work Entry could be rerun after registration;
13. primary block reason and all authority gaps;
14. strong cross-surface semantic equivalence evidence;
15. visual-only equivalence that must **not** coalesce meaning.

Workers do not mint canonical NDC, VIS, BND, TGT, LYR or adapter IDs. Proposal keys are local evidence keys only. Unknown remains unknown.

### Common machine output contract

Chats 1–4 write exactly one `RESOLUTION.jsonl` row per certified target in their surface and derive subset files from that exact row set:

- `RESOLUTION.jsonl`
- `REUSE.jsonl`
- `REGISTRATION_PROPOSALS.jsonl`
- `BLOCKED.jsonl`
- `PROJECTION_DEBT.jsonl`
- `MANIFEST.json`
- `SUMMARY.md`

Every resolution row must preserve `surfaceKey`, `targetId` and the certified corpus `recordSha256` as `sourceRecordSha256`; must use the vocabulary registry's `promotionReadinessDecision`, `authorityReuseDisposition` and `projectionDebtClassification`; must list `evidenceRefs` and exact `blockingAuthorityGaps`; and must not silently fill absent semantic/physical fields.

Each surface must prove:

`inputCount = resolutionCount = uniqueTargetCount`

and:

`resolutionCount = readyExistingAuthorityReuse + readyCanonicalRegistration + legitimatelyBlocked + notApplicable`.

No missing, extra or duplicate target IDs.

### Parallel architecture and disjoint write ownership

| Chat | Phase role | Work branch | Exclusive phase output |
|---|---|---|---|
| 1 | `TABLET_PROMOTION_READINESS_RESOLVER` | `chat1/canonical-promotion-readiness-tablet-20260912` | `prisma-html/governance/visual-promotion/promotion-readiness/tablet/**` |
| 2 | `PC_PROMOTION_READINESS_RESOLVER` | `chat2/canonical-promotion-readiness-pc-20260912` | `prisma-html/governance/visual-promotion/promotion-readiness/pc/**` |
| 3 | `MOBILE_PROMOTION_READINESS_RESOLVER` | `chat3/canonical-promotion-readiness-mobile-20260912` | `prisma-html/governance/visual-promotion/promotion-readiness/mobile/**` |
| 4 | `SHARED_UI_PROMOTION_READINESS_RESOLVER` | `chat4/canonical-promotion-readiness-shared-ui-20260912` | `prisma-html/governance/visual-promotion/promotion-readiness/shared-ui/**` |
| 5 | `ATLASFIN_SEMANTIC_REFERENCE_ANALYST` | `chat5/canonical-promotion-readiness-atlasfin-20260912` | `prisma-html/governance/visual-promotion/promotion-readiness/atlasfin-evidence/**` |
| 6 | `CANONICAL_PROMOTION_READINESS_COMPOSER` | `chat6/canonical-promotion-readiness-control-plane-20260912` | contracts/composed/control-plane paths defined below |

Chat 6 exclusively owns:

- `prisma-html/governance/visual-promotion/promotion-readiness/README.md`;
- `prisma-html/governance/visual-promotion/promotion-readiness/contracts/**`;
- `prisma-html/governance/visual-promotion/promotion-readiness/composed/**`;
- `prisma-html/tools/visual_promotion/promotion_readiness.py` and its focused tests;
- phase coordination documents explicitly assigned by the repository owner.

No Chat writes another Chat's phase output or mailbox. Status branches remain coordination-only.

### Common hard stops

All Chats:

- reuse the certified corpus; no recensus or broad rediscovery;
- do not rebuild GVAE or Atlasfin;
- do not inspect/use Materiality Catalog;
- do not mutate CSS/SCSS/TSX/JSX/product runtime;
- do not repair generated product projections;
- do not run GVAE APPLY or wildcard/batch mutation;
- do not mutate global Identity/RIFAT/NDC/Target Index/Factory Ledger authority;
- do not interpret Atlasfin recipe equality as semantic identity;
- do not invent canonical IDs;
- preserve unknown/ambiguous evidence as unknown/ambiguous;
- revalidate Authority Mesh if relevant `main` drift occurs before governed mutation;
- publish START, blockers/clears, material findings, handoff and completion to the same deterministic mailbox branch;
- place this phase receipt under `handoff.promotionReadiness`.

### CHAT 1 — TABLET PROMOTION READINESS

Role: `TABLET_PROMOTION_READINESS_RESOLVER`.

Read the common startup set, your own mailbox, the complete certified Tablet subset and current canonical NDC/Identity/RIFAT/Visual Control/Target Index authority. Use Atlasfin only as priority reference.

Primary work:

1. Resolve all 929 Tablet targets exactly once.
2. Prioritize the 139 current `ELIGIBLE_CANDIDATE` rows.
3. Prove existing neutral meaning/Identity meaning reuse where authority exists.
4. Reuse existing recipes/adapters/bindings only by exact registry evidence.
5. Prove route/region/slot/component/owner/layer only from existing governed authority; do not infer missing coordinates from CSS selectors.
6. Preserve the 2 physical DRIFT rows as blocked unless current authority truly resolves them.
7. Treat the known Cobrar binding `BND.ACT.PRIMARY.TABLET.POS.COBRAR.V1` as reuse evidence only; do not generalize it to neighboring targets.
8. Produce exact registration proposals only when semantic + recipe + adapter + physical/application evidence is sufficient.
9. Classify all remaining authority gaps explicitly.

Expected receipt: `PASS_TABLET_PROMOTION_READINESS`.

### CHAT 2 — PC PROMOTION READINESS

Role: `PC_PROMOTION_READINESS_RESOLVER`.

Resolve all 827 PC targets exactly once. Preserve the known physical selector DRIFT unless authority resolves it.

For the 139 `projectionStatus=MISSING` rows, classify each exactly as one of the canonical `projectionDebtClassification` values. At minimum distinguish:

- canonical projection required and missing;
- intentionally non-projected;
- reference/governor-only;
- stale authority;
- unresolved/ambiguous.

Do not repair projection files. Do not choose a projection owner without evidence.

Resolve semantic/Identity/recipe/adapter/binding/application readiness from current authority only. Recipe similarity with Tablet is review evidence, never semantic proof.

Expected receipt: `PASS_PC_PROMOTION_READINESS`.

### CHAT 3 — MOBILE PROMOTION READINESS

Role: `MOBILE_PROMOTION_READINESS_RESOLVER`.

Resolve all 271 Mobile targets exactly once.

For the 138 current projection DRIFT rows, classify authority direction without mutating RIFAT or product. Each must be evidence-backed as one of:

- RIFAT authoritative / product stale;
- product likely newer candidate / authority reconciliation required;
- intentional divergence;
- ambiguous.

The existing `SURF.mb.owner_home` supporting surface reference does not by itself resolve target-level neutral meaning. Existing adapter evidence is reusable only where the canonical Identity adapter registry proves it. Do not manufacture recipes/bindings.

Expected receipt: `PASS_MOBILE_PROMOTION_READINESS`.

### CHAT 4 — SHARED UI PROMOTION READINESS

Role: `SHARED_UI_PROMOTION_READINESS_RESOLVER`.

Resolve all 70 Shared UI targets exactly once.

Focus on current authority only:

- 19 no-region unresolved targets;
- 11 multi-region conflicts;
- 40 remaining register-first rows;
- NDC unresolved across current corpus;
- Atlasfin `NO_MATCH` across current Shared UI corpus.

Resolve no-region or multi-region only when existing RIFAT/Visual Control/owner authority proves the exact answer. Otherwise remain blocked. Shared ownership may prove a shared semantic source, but visual reuse alone does not.

Expected receipt: `PASS_SHARED_UI_PROMOTION_READINESS`.

### CHAT 5 — ATLASFIN CROSS-SURFACE EVIDENCE

Role: `ATLASFIN_SEMANTIC_REFERENCE_ANALYST`.

This lane is read-only with respect to canonical authority and does not write per-surface resolution rows.

Write only:

`prisma-html/governance/visual-promotion/promotion-readiness/atlasfin-evidence/**`

Produce:

- `REFERENCE_ANALYSIS.jsonl`;
- `IDENTITY_RECIPE_REUSE_CANDIDATES.jsonl`;
- `CROSS_SURFACE_EQUIVALENCE_EVIDENCE.jsonl`;
- `VISUAL_ONLY_EQUIVALENCE.jsonl`;
- `MANIFEST.json`;
- `SUMMARY.md`.

Investigate strong cross-surface equivalence only when independent semantic evidence accompanies Atlasfin reference evidence. Strong evidence may include same existing NDC concept, same existing canonical Identity meaning, same established business action/state, or shared ownership proving one semantic source.

Atlasfin recipe/family/preset equality alone must be recorded as `VISUAL_SIMILARITY_ONLY`, never canonical semantic coalescing.

Expected receipt: `PASS_ATLASFIN_PROMOTION_READINESS_EVIDENCE`.

### CHAT 6 — CANONICAL PROMOTION READINESS COMPOSER

Role: `CANONICAL_PROMOTION_READINESS_COMPOSER`.

Chat 6 owns phase contracts, validator/composer tooling and final integration. It never repairs another lane's evidence by inference.

Immediate work:

1. Publish this phase and machine contracts.
2. Keep the original certified corpus immutable.
3. Validate every worker handoff directly from its mailbox and exact work head.
4. Validate per-surface zero-loss and source-record hash pins.
5. Validate vocabulary, authority-qualified refs, proposal-key rules and no canonical-ID minting.
6. Cross-check Chat 5 evidence without granting Atlasfin authority.
7. Compute duplicate/collision analysis separately from semantic equivalence.
8. Build `composed/RESOLUTION_CORPUS.jsonl`, `CROSS_SURFACE_SEMANTIC_GROUPS.json`, `COLLISIONS.json`, `ZERO_LOSS.json`, `CANONICAL_PROMOTION_PLAN.json`, `CANONICAL_PROMOTION_PLAN.md` and `SUMMARY.md` only after accepted lane inputs exist.
9. Separate plan output into safe exact authority reuse, safe exact canonical registration proposals, blocked and not-applicable.
10. Require total accounting = 2,097 exactly.
11. Run universal Factory Ledger anti-rework, current task-exact Authority Mesh + Layer Map and Work Entry on exact planned registration scope before any global authority mutation.
12. If canonical registration is not explicitly machine-authorized, stop at `READY_FOR_CANONICAL_PROMOTION_INTEGRATION`.
13. If a later exact plan and gates authorize registration in this phase, perform it as a separate deterministic integration subphase. Product/runtime remains forbidden.

Before final planning, read Chats 1–5 receipts directly from their status branches. Do not ask the owner to relay messages.

Expected initial hard-stop result: `READY_FOR_CANONICAL_PROMOTION_INTEGRATION`.

### Deterministic close order

`phase bootstrap -> six lanes start -> surface/Atlasfin receipts -> zero-loss + authority/collision checks -> CANONICAL_PROMOTION_PLAN -> anti-rework -> current-head Authority Mesh + Layer Map -> Work Entry exact scope -> READY_FOR_CANONICAL_PROMOTION_INTEGRATION or separately authorized canonical-registration subphase`

This phase does **not** authorize product/runtime visual mutation, projection repair, GVAE APPLY, Materiality Catalog use, wildcard surface mutation or runtime visual-green claims.

# CHAT 1 — TABLET PROMOTION

## Mission

Promote the **existing Tablet census evidence** toward semantic/binding/application candidates without broad rediscovery and without visual/runtime mutation.

Tablet owns its current Target Index census records. The lane must account for every Tablet census input exactly once.

## Read authority

In addition to the shared startup set, read:

- `prisma-html/authority/rifat/prisma-ui/visual-control/target-index/tablet.json`
- Tablet rows in `prisma-html/authority/rifat/prisma-ui/visual-control/expanded/tablet/**`
- `prisma-html/authority/rifat/identity/registries/element-bindings.registry.json`
- `prisma-html/authority/rifat/identity/registries/recipe.registry.json`
- `prisma-html/authority/rifat/identity/registries/surface-adapters.registry.json`
- `prisma-html/authority/rifat/visual-source-manifest.json`
- NDC canon and ID grammar under `apps/terminal-de-venta-system/docs/ndc/`
- Atlasfin registries listed by the interoperability contract.

## Write ownership

Write only:

`prisma-html/governance/visual-promotion/candidates/tablet/**`

Do not modify Tablet product files, RIFAT authority, global Identity registries, Target Index, manifest or global repository manifests.

## Required analysis per target

For every Tablet census target:

1. preserve exact `targetId`;
2. determine whether physical evidence is current;
3. resolve existing route/region/slot/component/owner/layer evidence by reading current RIFAT/Visual Control, without recensus;
4. find existing NDC meaning when directly supported;
5. find the strongest supported Atlasfin match: exact, family, preset, recipe, ambiguous or none;
6. distinguish Atlasfin IDs from canonical Identity IDs;
7. reuse an existing Identity recipe/binding only if current registry authority proves it;
8. create candidate meaning/binding data when appropriate, never a new canonical ID;
9. classify projection status;
10. emit blockers and evidence refs.

## Required outputs

Under the owned directory produce deterministic:

- `MANIFEST.json`
- `CANDIDATES.jsonl`
- `UNRESOLVED.jsonl`
- `CONFLICTS.jsonl`
- `SUMMARY.md`

Accounting must reconcile exactly to Tablet census input count.

## Completion

Finish when every Tablet census target has exactly one outcome and there are zero writes outside the owned directory.

---

# CHAT 2 — PC PROMOTION

## Mission

Promote the **existing PC census evidence** toward semantic/binding/application candidates without broad rediscovery or product mutation.

Also classify the known class of PC census records that do not currently have a canonical projection/source match. Do not repair them in this lane.

## Read authority

Read the shared startup set plus:

- `prisma-html/authority/rifat/prisma-ui/visual-control/target-index/pc.json`
- PC rows in `prisma-html/authority/rifat/prisma-ui/visual-control/expanded/pc/**`
- canonical Identity binding/recipe/adapter registries;
- visual-source-manifest;
- NDC canon;
- Atlasfin registries.

## Write ownership

Write only:

`prisma-html/governance/visual-promotion/candidates/pc/**`

## Required analysis per target

Apply the same candidate logic as Chat 1.

For a PC record without proven canonical projection, use only:

- `MISSING` when evidence shows projection is required but absent;
- `NOT_REQUIRED` when evidence proves it is intentionally not a generated projection;
- `UNRESOLVED` when the lane cannot prove either.

Do not invent a canonical source and do not copy product bytes into RIFAT.

## Required outputs

Produce the five standard candidate files and reconcile every PC census input exactly once.

---

# CHAT 3 — MOBILE PROMOTION

## Mission

Promote existing Mobile census evidence and classify existing Mobile projection drift without broad rediscovery and without repairing runtime/source in this lane.

## Read authority

Read the shared startup set plus:

- `prisma-html/authority/rifat/prisma-ui/visual-control/target-index/mobile.json`
- Mobile rows in `prisma-html/authority/rifat/prisma-ui/visual-control/expanded/mobile/**`
- visual-source-manifest and current RIFAT Mobile canonical sources;
- current Mobile product projection files referenced by the manifest;
- Identity/NDC/Atlasfin registries.

## Write ownership

Write only:

`prisma-html/governance/visual-promotion/candidates/mobile/**`

## Drift policy

For every drifted Mobile target, classify evidence without choosing a repair direction merely to become green.

Use notes/blockers to distinguish, when provable:

- current canonical source vs changed product projection;
- legitimate newer runtime candidate requiring authority reconciliation;
- stale canonical authority candidate;
- ambiguous drift requiring review.

Do not overwrite Mobile product files. Do not overwrite RIFAT. Do not regenerate projections.

## Required outputs

Produce the five standard files, account for every Mobile census target and separately summarize projection-status counts.

---

# CHAT 4 — SHARED UI PROMOTION

## Mission

Promote existing Shared UI census evidence as neutral/shared visual-source candidates while preserving one source of semantic truth across consumers.

## Read authority

Read the shared startup set plus:

- `prisma-html/authority/rifat/prisma-ui/visual-control/target-index/shared-ui.json`
- Shared UI rows in `prisma-html/authority/rifat/prisma-ui/visual-control/expanded/shared-ui/**`
- Identity Shared UI adapter/binding sources;
- projection manifest;
- NDC canon;
- Atlasfin registries.

## Write ownership

Write only:

`prisma-html/governance/visual-promotion/candidates/shared-ui/**`

## Consumer policy

A Shared UI target may record that Tablet, PC, Mobile or an excluded surface consumes it, but this lane may not edit consumer shards or product surfaces.

Do not duplicate one Shared UI semantic source into separate canonical meanings solely because it has multiple consumers.

Out-of-scope consumer observations are evidence only.

## Required outputs

Produce the five standard files and zero-loss accounting for all Shared UI census targets.

---

# CHAT 5 — ATLASFIN BRIDGE

## Mission

Make `prisma-html/extras/atlasfin` the clear priority human cockpit/reference for the promotion system without turning Atlasfin into a competing editable authority or direct product writer.

The bridge must use the existing 418-element catalog and structured Atlasfin registries. It must not rebuild the catalog.

## Read authority

Read the shared startup set plus all current Atlasfin manifests, registries, schemas, validators, VISREC2 code, current Cobrar pilot/visual application evidence, Visual Core status feed and Identity/RIFAT contracts.

## Write ownership

Write only newly assigned bridge implementation under:

`prisma-html/extras/atlasfin/bridge/**`

Do not rewrite existing Atlasfin source registries unless a later separately authorized task explicitly requires it.

## Required bridge capabilities

Design/implement a read-only bridge model that can represent:

- Atlasfin catalog element;
- property/family/preset/recipe/state/variant;
- Atlasfin adapter;
- authority-qualified IDs;
- NDC refs;
- canonical visual meaning when resolved;
- exact target/RIFAT coordinates when available;
- projection status;
- binding/promotion status;
- blockers/evidence;
- Work Entry decision when present.

The bridge must tolerate candidate directories that do not yet exist. Missing worker data renders as pending/unresolved, never as error-created fake data.

It must not require Chats 1–4 to finish before this bridge can be implemented or validated with fixtures/current Atlasfin data.

## Materiality restriction

Do not inspect, import or fallback to the Surface Visual Governor Materiality Catalog.

## Validation

Use existing Atlasfin validators plus narrow bridge tests/fixtures. No product runtime mutation.

---

# CHAT 6 — VISUAL PROMOTION CONTROL PLANE

## Mission

Build the deterministic machine layer that makes parallel candidate outputs interoperable and prevents future anti-rework mistakes.

This lane must be buildable and testable entirely from schemas/fixtures/current authority. It does not wait for surface workers.

## Read authority

Read the shared startup set plus:

- `prisma-html/tools/visual_application/**`
- current Work Entry Gate and tests;
- Target Index generator;
- Identity binding resolver;
- Visual Core;
- NDC ID and edge registries;
- current Atlasfin registries.

## Write ownership

Primary ownership:

`prisma-html/tools/visual_promotion/**`

`prisma-html/governance/visual-promotion/contracts/**`

When the exact task authority permits bounded gate hardening, this lane may also modify:

`prisma-html/tools/visual_application/visual_work_entry_gate.py`

`prisma-html/tools/visual_application/tests/test_visual_work_entry_gate.py`

Do not populate Tablet/PC/Mobile/Shared UI candidate shards.

## Required control-plane capabilities

Implement deterministic contracts/tools for:

- candidate schema validation;
- vocabulary/enumeration validation;
- authority-qualified ID validation;
- disjoint write-ownership validation;
- base-head/source-hash validation;
- zero-loss surface accounting;
- duplicate/collision detection;
- Atlasfin candidate normalization;
- NDC/visual-meaning reconciliation candidates;
- canonical-composer planning without direct mutation;
- `Visual Current Truth` generation;
- `Surface Readiness` generation;
- explicit distinction between current census and genuine discovery need.

## Work Entry hardening

Preserve exactly the four existing decisions.

Add/test machine-readable reasons so current census cannot be mistaken for discovery work, including:

`REUSE_EXISTING_CENSUS_SEMANTIC_PROMOTION_REQUIRED`

`BROAD_REDISCOVERY_FORBIDDEN_CURRENT_CENSUS`

Add strict request-contract validation if it can be done without weakening existing behavior.

## Integration mode

Initial Control Plane work must finish without worker outputs.

Later, if the user explicitly returns with worker branch/commit refs, the same lane may run deterministic integration/reconciliation. That later assembly is not a prerequisite for any worker to start.

## Completion

Finish with control-plane code/contracts/tests on its own branch, no product visual mutation, no surface candidate writes, and no global canonical registry promotion unless a later separately authorized integration task requests it.
