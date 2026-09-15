# Chat 3 — MOBILE_PROMOTION status log

No updates published yet.

## 2026-09-04T19:50:47-06:00 — START / PROGRESS / FINDING / DECISION / VALIDATION / HANDOFF

- Published first Chat 3 status report under the canonical shared status channel.
- Work base: `57b01ad8bda043ec25763203354b686341bace09`.
- Work branch/head: `visual-promotion-chat3-mobile-20260904` @ `7f32ce6f1b602a14781fa2f4f3f323035f8029ec`.
- Current main observed: `d08013db42c34ccafb80075392ec6d7a289cf7b5`; work branch is 1 commit ahead and 3 commits behind.
- Candidate shard is complete and isolated to five files under `prisma-html/governance/visual-promotion/candidates/mobile/`.
- Zero-loss accounting PASS: 271 input targets, 271 unique outcomes, 0 missing, 0 extra, 0 duplicate.
- Projection partition PASS: 133 CURRENT, 138 DRIFT.
- Material finding: governed Mobile cleanup commit `731574f97dba0ec46420369b777071500ce2f833` removed retired `.multiContextRoot` from the product dashboard rule while current RIFAT source still carries it. The lane records both a legitimate newer runtime/product candidate and stale canonical-authority candidate without choosing a repair direction.
- Decision: no broad rediscovery, no canonical ID minting, no Materiality fallback, no product/RIFAT/projection repair. All outcomes remain `REGISTER_TARGET_FIRST`.
- Current lane state: `READY_FOR_INTEGRATION`.
- No user action requested at this time.
- Next: inspect the three commits by which `main` advanced and record whether that drift is relevant to Chat 3 evidence before integration.

## 2026-09-04T19:52:07-06:00 — FINDING / DECISION / BLOCKER_CLEARED / VALIDATION / HANDOFF

- Completed explicit drift review from work base `57b01ad8bda043ec25763203354b686341bace09` to current `main` `d08013db42c34ccafb80075392ec6d7a289cf7b5`.
- The three intervening commits changed status-channel/governance coordination only: shared status mailboxes/index, status-channel contract/docs, AGENTS wiring, interoperability/status vocabulary additions, and the corresponding `prisma-html/FILES_MANIFEST.json` refresh.
- No Chat 3 Mobile authority/readset or projection evidence path changed: no Mobile Target Index/expanded authority, RIFAT Mobile canonical source, Mobile product projection, visual-source-manifest, Identity registry, NDC registry or Atlasfin registry mutation was present in the delta.
- Validation result: `PASS_NON_RELEVANT_DRIFT` for the completed candidate shard.
- Current Chat 3 prompt/write ownership/output contract remains unchanged; the new status-channel reporting requirement is now satisfied on `status/vp-chat-03-mobile`.
- Decision: do not rewrite/rebase candidate data merely because `main` moved. Preserve original `baseHead` and evidence provenance.
- Handoff remains `READY_FOR_INTEGRATION`. Preferred integration is the single isolated candidate commit `7f32ce6f1b602a14781fa2f4f3f323035f8029ec` applied onto the coordinator's current integration base.
- No user action required. No new blocker.

## 2026-09-04T19:52:46-06:00 — VALIDATION / COMPLETE

- Status-branch isolation validation PASS against current `main` `d08013db42c34ccafb80075392ec6d7a289cf7b5`.
- Exactly two paths differ on `status/vp-chat-03-mobile`: this Chat's `STATUS.json` and append-only `LOG.md`.
- No code, candidate shard, product/runtime, visual authority, global manifest or another Chat mailbox is present in the status-branch delta.
- Chat 3 lane work remains `READY_FOR_INTEGRATION`; no additional candidate mutation is justified by current evidence.

## 2026-09-04T20:14:00-06:00 — PROGRESS / FINDING / DECISION / VALIDATION / HANDOFF

- Re-read the canonical prompt at current `main` `66fa02147f0cf31529c090a47f376026b406875a` and located assigned **Chat 3 — Mobile Promotion**.
- Current phase is `INTEGRATION_HANDOFF_AND_PLANNING`; normative continuation places Chat 3 in **HOLD**.
- Re-read this Chat's current mailbox and confirmed preserved provenance: work branch `visual-promotion-chat3-mobile-20260904`, work head `7f32ce6f1b602a14781fa2f4f3f323035f8029ec`, base `57b01ad8bda043ec25763203354b686341bace09`, accounting `271 = 133 CURRENT + 138 DRIFT`.
- Re-read current interoperability contract, vocabulary registry and status-channel contract. Atlasfin remains priority reference; Materiality Catalog remains `STANDBY_USER_INVOKED_ONLY`.
- Latest drift review from prior observed `main` `d08013db42c34ccafb80075392ec6d7a289cf7b5` to current `main` found only two changed paths: the canonical parallel prompt and `prisma-html/FILES_MANIFEST.json`. Result: `PASS_NON_RELEVANT_DRIFT` for Chat 3 evidence.
- Decision: no shard regeneration, no rebase, no RIFAT-vs-product repair choice, no change to the 138 DRIFT classifications, and no change to `REGISTER_TARGET_FIRST` outcomes.
- No candidate/runtime/authority/product mutation performed in this continuation step.
- Chat 3 remains `READY_FOR_INTEGRATION` in HOLD, pending only an explicit bounded correction request from Chat 6/integration if deterministic validation finds one.
- No user action required.

## 2026-09-04T23:44:00-06:00 — START / PROGRESS / DECISION

- Re-read the canonical prompt at `main` `8cc1918c5e015d1408335c15313e7364e04859c2`.
- Current phase is now `CANDIDATE_CORPUS_CERTIFICATION_PARALLEL`; the previous HOLD is superseded.
- Assigned lane is **Chat 3 — Mobile Corpus Certification**.
- Immutable source provenance remains `visual-promotion-chat3-mobile-20260904` @ `7f32ce6f1b602a14781fa2f4f3f323035f8029ec`, source base `57b01ad8bda043ec25763203354b686341bace09`, input `271`.
- Planned certification branch: `chat3/mobile-corpus-cert-20260904` from current canonical main.
- Scope is syntactic/reference normalization only. No semantic upgrade, no projection repair, no RIFAT-vs-product choice, no Materiality use, no product/runtime mutation.
- Lane state changed to `IN_PROGRESS`.

## 2026-09-04T23:59:00-06:00 — FINDING / DECISION / VALIDATION / HANDOFF / COMPLETE

- Created certification branch `chat3/mobile-corpus-cert-20260904` from canonical `main` `8cc1918c5e015d1408335c15313e7364e04859c2`.
- Certification commit: `664035e83943ae48c923585765d3c505b1bd8c53`.
- Wrote exactly five owned outputs under `prisma-html/governance/visual-promotion/candidates/mobile/certification/`: `MANIFEST.json`, `NORMALIZED.jsonl`, `CERTIFICATION.jsonl`, `INVALID.jsonl`, `SUMMARY.md`.
- Strict representation normalization completed for the known Mobile mismatches only: projection flattening, raw domain-scoped NDC refs, strict evidence-ref qualification, and raw Atlasfin adapter ID.
- Original worker bytes remain immutable at `7f32ce6f1b602a14781fa2f4f3f323035f8029ec`; every normalized row pins source file, line and SHA-256 of the original JSONL record.
- Validation PASS: `271/271` normalized, `271/271` certification, unique targets `271`, missing `0`, extra `0`, duplicates `0`, invalid `0`.
- Certification status: `271 VALID_REGISTER_TARGET_FIRST`.
- Semantic invariants PASS: `semanticMutationCount=0`; all promotion and Work Entry decisions remain `REGISTER_TARGET_FIRST`.
- Projection partition unchanged: `133 CURRENT + 138 DRIFT`.
- Read-back provenance validation PASS: source-record hash mismatches `0`; normalized-record hash mismatches `0`.
- Reference validation PASS for NDC `SURF.mb.owner_home`, Atlasfin `ADP.MB.TOUCH.V2`, Identity `prisma.adapter.mobile.v1`; strict evidence refs invalid count `0`.
- File digests: `NORMALIZED.jsonl = bfec6c59764f92ed54edd63dd1df4273165044ade95839a92d08930e93703ee1`; `CERTIFICATION.jsonl = 81eb0afbf8c7fa54833ed09f503d2ccf2ee5407c5aed089dcda6bbd75219a287`.
- Branch-scope validation PASS: exactly five changed paths, all inside the Mobile certification root.
- No RIFAT-vs-product repair direction chosen. No broad rediscovery. No Materiality Catalog. No product/runtime/global-authority mutation. No `FILES_MANIFEST.json` refresh. No Chat 3 PR.
- Chat 3 state: `READY_FOR_INTEGRATION` with result `PASS_MOBILE_CANDIDATE_CORPUS_CERTIFIED`.
- Handoff to Chat 6: consume `chat3/mobile-corpus-cert-20260904` @ `664035e83943ae48c923585765d3c505b1bd8c53` as the certified Mobile derivative while preserving raw source provenance `7f32ce6f1b602a14781fa2f4f3f323035f8029ec`.

## 2026-09-11T22:45:00-06:00 — START / PROGRESS

- Re-read current canonical phase from main `7c5b8d477a9006c5184ddbc806874b6e7c02571c`: `CORPUS_FINAL_PARALLEL_VERIFICATION`.
- Resolved Chat 3 lane from STATUS_INDEX: `MOBILE_PROMOTION`, status branch `status/vp-chat-03-mobile`, phase role `MOBILE_FINAL_WITNESS`, expected result `PASS_MOBILE_CORPUS_WITNESS`.
- Final witness source is immutable certification head `664035e83943ae48c923585765d3c505b1bd8c53` on `chat3/mobile-corpus-cert-20260904`.
- Verification starts read-only from exact Git head-tree bytes. No certification/source/product/runtime/global-authority mutation is authorized or planned.
- Materiality Catalog remains uninspected and forbidden for this task.

## 2026-09-11T22:53:00-06:00 — FINDING / VALIDATION / DECISION

- Independent exact-head readback of certification `664035e83943ae48c923585765d3c505b1bd8c53` reproduced `271` NORMALIZED rows, `271` CERTIFICATION rows and an empty INVALID file.
- Target accounting PASS: `271` unique target IDs; duplicate/missing/extra counts all `0`.
- Certification labels PASS: `271 VALID_REGISTER_TARGET_FIRST`.
- Projection partition PASS: exactly `133 CURRENT + 138 DRIFT`.
- Semantic preservation PASS: `semanticMutationCount=0`, independently reconstructed source-to-normalized semantic diff count `0`, representation error count `0`.
- Provenance hashes PASS: `271/271` original source-record hashes and `271/271` normalized-record hashes reproduced with zero mismatches.
- Exact file SHA-256 PASS: NORMALIZED `bfec6c59764f92ed54edd63dd1df4273165044ade95839a92d08930e93703ee1`; CERTIFICATION `81eb0afbf8c7fa54833ed09f503d2ccf2ee5407c5aed089dcda6bbd75219a287`.
- Representation-only provenance PASS: all NDC/Atlasfin normalization records reproduce source and normalized values; `1,493` evidence-reference conversions reconstruct the normalized evidence lists exactly.
- Drift policy PASS so far: all `138/138` DRIFT rows explicitly say no repair direction is selected, retain `projection-hash-drift`, remain `REGISTER_TARGET_FIRST`, and have no application layer. No RIFAT-vs-product repair choice was found.
- The first string probe counted `137` because one note begins with capital `No`; a case-insensitive exact invariant check confirms `138/138`. This was a verifier wording issue, not a corpus defect.
- No repair or certification mutation performed. Final witness remains read-only.

## 2026-09-11T22:54:00-06:00 — VALIDATION / HANDOFF / COMPLETE

- Final strict reference verification PASS: all `271/271` certification rows report strict candidate validation PASS, reference validation PASS, provenance pinned, zero-loss membership and `semanticMutation=false`.
- Normalized Mobile reference set is deterministic across all 271 rows: NDC `SURF.mb.owner_home`, Atlasfin `ADP.MB.TOUCH.V2`, Identity `identity::prisma.adapter.mobile.v1`.
- Current canonical `main` remained `7c5b8d477a9006c5184ddbc806874b6e7c02571c` through closure.
- Current-main registry blobs are byte-identical to the certification-head registry blobs: NDC `44c29f0333144501b0bef2e36c0aed0d3865ef2f`, Atlasfin `f6eb2a32ff7a18ec80c6917654fc6d63c9024319`, Identity `b284f0300ae5cd6d88a5d6cd252c11858ab7376d`.
- Final witness result: `PASS_MOBILE_CORPUS_WITNESS`.
- Receipt published at `handoff.parallelWitness` with exact certification head, Git blob SHAs, SHA-256 digests, accounting, drift invariants, provenance/hash verification, reference validation and prohibited-action flags.
- Materiality Catalog was not inspected. Broad rediscovery was not performed. Product/runtime mutation = false. Canonical promotion = false. No certification/source bytes were changed.
- Chat 3 enters `CERTIFIED_HOLD` represented by status-channel state `READY_FOR_INTEGRATION`. Chat 6 can read the witness receipt directly from `status/vp-chat-03-mobile`; no owner relay is required.

## 2026-09-12T16:07:00-06:00 — START / PROGRESS / DECISION

- Re-read the canonical prompt and own deterministic mailbox after the owner continuation message.
- Canonical `main` is `d4b451cc92c597d02cfc65094922bd2c5dd17c12`; current phase is `CANONICAL_PROMOTION_READINESS_RESOLUTION`.
- `STATUS_INDEX.json` assigns Chat 3 lane `MOBILE_PROMOTION`, role `MOBILE_PROMOTION_READINESS_RESOLVER`, expected result `PASS_MOBILE_PROMOTION_READINESS`, receipt field `handoff.promotionReadiness`.
- Opened/confirmed owned work branch `chat3/canonical-promotion-readiness-mobile-20260912` from the exact current `main`.
- Required scope is exactly the 271 certified Mobile corpus records. Prior corpus certification and final witness remain closed evidence and will not be rebuilt.
- Owned output root is `prisma-html/governance/visual-promotion/promotion-readiness/mobile/**`; no other Chat ownership or global authority is writable in this lane.
- Decision: resolve semantic/binding/application-layer readiness and projection debt only from current canonical authority; preserve unknowns; no broad rediscovery, no canonical ID minting, no RIFAT/product overwrite, no projection repair.
- Materiality Catalog remains `STANDBY_USER_INVOKED_ONLY` and is not being inspected.

## 2026-09-13T01:20:00-06:00 — FINDING / VALIDATION / BLOCKER / HANDOFF

- Re-read current main, canonical phase contract, own mailbox, schema and `promotion_readiness.py`; assignment remains Chat 3 `MOBILE_PROMOTION_READINESS_RESOLVER` with expected receipt `PASS_MOBILE_PROMOTION_READINESS`.
- Current work head is `eb7440288b791560b0ca3a2e1fd3d8529ce9a0ef`, exactly 5 commits ahead of phase base `d4b451cc92c597d02cfc65094922bd2c5dd17c12` and 0 behind.
- Branch-scope validation PASS: only five owned Mobile readiness paths differ from base. No product/runtime/global-authority/status-crosswrite occurred.
- Certified Mobile accounting is deterministically confirmed as `271 = 133 CURRENT + 138 DRIFT`; target IDs and exact certified `recordSha256` values are visible in repository evidence.
- Material classification remains bounded: all targets still lack target-level neutral meaning, recipe, binding and application-layer authority. For DRIFT, `TGT.CENSUS.MOBILE.C30F6FBF52AEFF7B5E02.V1` has evidence for `PRODUCT_CANDIDATE_AUTHORITY_RECONCILIATION_REQUIRED`; the remaining DRIFT rows stay ambiguous without stronger target-local direction evidence.
- The canonical seven-output contract is not complete: `RESOLUTION.jsonl` and `SUMMARY.md` are missing. Existing `BLOCKED.jsonl` has 271 target-id-only rows and `PROJECTION_DEBT.jsonl` has 138 target-id-only rows, so they are not valid full-row subsets yet.
- Demonstrable execution hard stop: the canonical `CANDIDATE_CORPUS.jsonl` is 2,876,194 bytes. In the available GitHub connector, `fetch_file` returns empty content for this large file even with line-range arguments; raw/blob retrieval is truncated or rejected. The session has no executable repo checkout/runner and no connector-to-Python raw-byte bridge.
- Because `promotion_readiness.py` requires exact 271-row source-hash pins, target uniqueness, exact subsets and manifest parity, hand-transcribing from truncated excerpts would be non-reproducible and risks fake green. That route is rejected.
- Result published as `BLOCKED_EXECUTION_ENVIRONMENT_NO_CANONICAL_RUNNER`, not `PASS_MOBILE_PROMOTION_READINESS`.
- Required continuation: resume from the same work head in an executable checkout/runner, deterministically generate the 271 full rows from the immutable corpus, derive subsets, run `promotion_readiness.py`, then publish PASS only if every zero-loss/source-hash/vocabulary/subset/manifest check passes.
- Materiality Catalog remains uninspected. Product/runtime mutation = false. Projection repair = false. Global authority mutation = false. GVAE APPLY = false.

## 2026-09-14T13:45:00-06:00 — BLOCKER_CLEARED / VALIDATION / HANDOFF / COMPLETE

- Resumed from the real Mobile work head and did not reset to the stale mailbox head.
- Materialized the complete `RESOLUTION.jsonl` at exactly `271` rows. A read-back audit then found a materialization-only SHA-256 defect in 137 DRIFT rows; those 137 `sourceRecordSha256` values were corrected without changing target IDs, semantic decisions, projection classifications, authority gaps or any canonical meaning.
- Final work head: `bf99bf782c7b295ee8badd936a4b9078e751ecdf`. Current canonical main remained `d4b451cc92c597d02cfc65094922bd2c5dd17c12`.
- Final branch scope PASS: `17 ahead / 0 behind`; exactly seven changed files, all under `prisma-html/governance/visual-promotion/promotion-readiness/mobile/**`.
- Final zero-loss accounting PASS: `271` resolution rows, `271` unique targets, missing `0`, extra `0`, duplicates `0`.
- Certified source-hash validation PASS: `271/271` `sourceRecordSha256` values reproduce the immutable Mobile certified NORMALIZED records; mismatches `0`. Certified Mobile NORMALIZED blob: `cc474d39d2027371921d8aba19ee02911c96b0f2`.
- Projection accounting PASS: `133 CURRENT + 138 DRIFT`; DRIFT remains `137 AMBIGUOUS + 1 PRODUCT_CANDIDATE_AUTHORITY_RECONCILIATION_REQUIRED` for `TGT.CENSUS.MOBILE.C30F6FBF52AEFF7B5E02.V1`.
- Readiness decisions remain intentionally conservative: `271 BLOCKED_MISSING_SEMANTIC_AUTHORITY`, `0 READY_REUSE_EXISTING_AUTHORITY`, `0 READY_FOR_CANONICAL_REGISTRATION`. No semantic authority, Identity recipe, binding, application layer or repair direction was invented.
- Exact current `promotion_readiness.py::validate_surface` rule set replay against the final branch bytes PASS: `surfaceKey=mobile`, `inputCount=271`, `legitimatelyBlocked=271`, `projectionDebtCount=138`, resolution digest `f3cd9b87583b0a2a65a9c530b52ee6f7c39b198ff685309e929ab97ea2154f8a`.
- Derived subset validation PASS: `REUSE=0`, `REGISTRATION_PROPOSALS=0`, `BLOCKED=271`, `PROJECTION_DEBT=138`; target sets exactly match the canonical derivation from RESOLUTION.
- Manifest accounting PASS for all fields enforced by the canonical readiness validator.
- Output Git blob SHAs: RESOLUTION `3ab06c9bca25301dd292463ac3185386f968ef3e`; REUSE `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`; REGISTRATION_PROPOSALS `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`; BLOCKED `9550610e2e8586869fa1082e24d8cb2679e8c2a5`; PROJECTION_DEBT `3d6d42d468419e2e3fa1381845a9f19178633e29`; MANIFEST `c06af09636e95b4e7eeba0916bd60d7135150cfc`; SUMMARY `51c072d5c95d544cdcf46a903df168d3575a15f2`.
- PR #553 executable-checkout evidence at the final head: CI PASS, ForgeOS Quality Gate PASS, Sync Sentinel PASS. VISCORE1 fails only at its final deterministic `prisma-html/FILES_MANIFEST.json` equality gate because the seven new Mobile outputs are intentionally absent from that global manifest; Chat 3 is explicitly forbidden to mutate that global path, so this is not converted into a lane defect.
- Prohibited-action guard PASS: Materiality Catalog uninspected; product/runtime mutation=false; canonical authority mutation=false; projection repair=false; GVAE APPLY=false.
- Final lane result: `PASS_MOBILE_PROMOTION_READINESS`.
- Receipt published in `handoff.promotionReadiness`; state is `READY_FOR_INTEGRATION`. Chat 6 may consume the receipt directly. No owner relay or user action is required.

## 2026-09-14T23:30:00Z — OWNER_ASSIGNMENT

# OWNER ASSIGNMENT — AUTHORITY_RECONCILIATION_ANTI_REWORK

**Chat:** 3
**Lane:** MOBILE_AUTHORITY_RECONCILIATION
**Assignment basis main:** `46c9032d8734bcb5d13242b8ccd7b7cb3c8274e0`
**Work branch to use/create:** `chat3/authority-reconciliation-mobile-20260914`
**Exclusive output root:** `prisma-html/governance/visual-promotion/authority-reconciliation/mobile/**`

Esta asignación viene directamente del dueño del repositorio. La fase previa `CANONICAL_PROMOTION_READINESS_RESOLUTION` ya cerró mediante PR #554. **No la repitas.**

## Objetivo

Reconciliar autoridad ya existente alrededor del corpus certificado de **2,097** targets sin recensus, sin broad rediscovery y sin reconstruir GVAE/RIFAT/Identity/NDC.

El resultado que buscamos no es “resolver 2,097 cosas nuevas”. Buscamos demostrar el delta verdadero entre:
- autoridad que ya existe y puede reutilizarse;
- concepto existente al que sólo le falta el enlace machine-readable target↔significado;
- semántica existente a la que le falta binding/aplicación/proyección;
- conflicto real que requiere curación;
- drift/projection reconciliation;
- autoridad genuinamente nueva.

## Verdad anti-retrabajo que debes preservar

PR #529 y Factory Ledger ya certificaron el all-surface physical mapping:
- 7 surfaces
- 96 routes
- 1,978 visual regions
- 10,575 editable slots
- 215 component owners
- 89 CSS owners
- 4,453 layers
- 0 blockers / 0 warnings

GVAE Target Index ya contiene 3,915 registros:
- 4 EXACT_APPLICATION_TARGET / GVAE_ENFORCED
- 3,911 VISUAL_CONTROL_CENSUS_TARGET / DISCOVERY_ONLY

Nuestros 2,097 son:
- Tablet 929
- PC 827
- Mobile 271
- Shared UI 70

`DISCOVERY_ONLY` **NO significa undiscovered**.

Factory Ledger: `visual.generic_application_engine_v1 = DONE / SOURCE_READY / doNotRebuild=true`.
Acción permitida: REUSE / VERIFY / ADVANCE. Nunca BUILD/REBUILD.

## Lecturas obligatorias antes de trabajar

Lee desde GitHub, no desde memoria conversacional:
1. root `AGENTS.md`
2. `apps/terminal-de-venta-system/docs/ops/PRISMA_FIELD_MANUAL_APRENDIZAJE_OPERATIVO.md`
3. `PRISMA Factory Ledger/PRISMA_FACTORY_LEDGER_AGENT_GATE.md`
4. `PRISMA Factory Ledger/PRISMA_FACTORY_LEDGER.json`
5. `PRISMA Factory Ledger/PRISMA_EVIDENCE_INDEX.json`
6. `prisma-html/docs/ops/PRISMA_VISUAL_CHANGE_MASTER_MAP.md`
7. parallel interoperability contract + vocabulary
8. PR #529 evidence and current all-surface authority
9. PR #554 `promotion-readiness/composed/**`
10. `apps/terminal-de-venta-system/docs/ndc/**`
11. `prisma-html/authority/rifat/identity/**`
12. `prisma-html/authority/rifat/prisma-ui/visual-control/**`
13. Code Atlas UIMAP/UI Bridge authority/evidence
14. Atlasfin structured registries only as support/reference
15. exact history/PRs/commits when necessary to decide existing intent

**Materiality Catalog remains `STANDBY_USER_INVOKED_ONLY`. The owner has NOT authorized it in this assignment. Do not inspect it, consume it, or use it as fallback.**

## GitHub-only operating mode

El dueño no tiene computadora. Todo debe ocurrir directamente en GitHub:
- no pedir PowerShell;
- no pedir archivos locales;
- no pedir localhost;
- no pedir que levante servidores;
- no pedir comandos manuales;
- no tocar puertos/dev servers;
- no depender de una carpeta local.

Resuelve `main` al inicio. `46c9032d8734bcb5d13242b8ccd7b7cb3c8274e0` es sólo el SHA de asignación. Si main avanzó:
- compara/revalida drift;
- reutiliza autoridad sólo si sigue válida;
- si hubo drift relevante, usa el flujo GitHub-only AutoMesh v2 / Authority Mesh correspondiente;
- jamás “arregles” historia restaurando snapshots viejos.

Antes de cualquier mutación de repo en tu work branch, respeta Factory Ledger anti-rework y la autoridad vigente. Si un gate no puede ejecutarse desde GitHub, sigue read-only, publica el blocker y no inventes PASS.

## Separación semántica obligatoria

Nunca confundas:
- NDC neutral/business meaning: `ENT.* / EVT.* / ACT.* / STA.* / MET.* / ALT.* / EVD.* / CAP.* / CAN.*`
- visual meaning/Identity: IDs históricos `identity::...` y futuros `VIS.*`
- physical location: surface/route/region/slot/component/owner/layer/selector
- binding/application authority: `BND.* / LYR.* / recipe / adapter`

Un target puede tener un `ACT.sale.checkout` operacional y a la vez un `identity::ACT.primary` visual. Relación no significa igualdad.

## Clasificación final permitida por target

Cada target de superficie debe terminar exactamente en una:
- `EXISTING_AUTHORITY_EXACT_REUSE`
- `EXISTING_CONCEPT_LINK_MISSING`
- `EXISTING_SEMANTIC_AUTHORITY_APPLICATION_GAP`
- `EXISTING_AUTHORITY_CONFLICT_CURATE`
- `PHYSICAL_OR_PROJECTION_RECONCILIATION_REQUIRED`
- `TRUE_NEW_AUTHORITY_REQUIRED`
- `NOT_APPLICABLE`

`TRUE_NEW_AUTHORITY_REQUIRED` es la clasificación más cara y exige **negative evidence completa**. No basta con que un registry no tenga un campo.

Antes de usar TRUE_NEW debes demostrar búsqueda/reconciliación contra:
- NDC canon + registries + seeds/examples relevantes;
- Identity registries + aliases + recipes + bindings + visual stacks;
- RIFAT/Visual Control/Target Index;
- Code Atlas/UIMAP/UI Bridge;
- Atlasfin structured evidence;
- Factory Ledger/Evidence Index;
- historia/PRs/commits/docs relevantes cuando exista pista;
- crosswalk de Chat 5 cuando esté disponible.

Una búsqueda vacía aislada NO prueba ausencia.

## Output contract y archivos grandes

No generes un JSONL monstruoso único.

Para outputs de muchos targets:
- orden determinista por `targetId`;
- shards de **máximo 250 filas** y preferentemente **<= 2 MiB** por archivo;
- nombre sugerido: `resolution/part-0001.jsonl`, `part-0002.jsonl`, etc.;
- `INDEX.json` pequeño con target ranges/partes;
- `MANIFEST.json` con inputCount, outputCount, uniqueTargetCount, source pins, blob/hash, shard counts y validaciones;
- `SUMMARY.md` humano;
- archivos de subsets/deuda también shardeados si crecen.

Cada row de superficie debe preservar como mínimo:
`surfaceKey`, `targetId`, `sourceRecordSha256`, autoridad física existente, neutral/business refs existentes, visual meaning refs existentes, Identity/recipe/binding/adapter/application refs existentes, evidenceRefs, negativeEvidenceRefs, classification, blockers, confidence y local proposal key sólo si hace falta.

**No mintas IDs canónicos nuevos.** Si hace falta proponer algo nuevo, usa un `proposal.*` local y no autoritativo.

### Si un archivo fuente es demasiado grande

No intentes traer varios MB enteros al contexto sólo “por si acaso”.

Orden de escape:
1. usa GitHub code search con `targetId`, ID semántico o path exacto;
2. usa `fetch_file` por rangos de líneas cuando el formato lo permita;
3. usa manifiestos/summaries/indexes pequeños para localizar el shard correcto;
4. consulta el raw exacto por commit SHA sólo del shard necesario;
5. para agregados, usa procesamiento **streaming línea por línea**, nunca `json.load()` de corpus multi-MB;
6. si necesitas código auxiliar, colócalo sólo dentro de tu output root y mantenlo determinista;
7. ejecútalo mediante infraestructura GitHub/CI ya existente cuando esté disponible; no modifiques workflows globales sólo para obtener comodidad;
8. si no existe una ruta de ejecución GitHub válida, publica `BLOCKED_EXECUTION_PATH` con evidencia. No le pidas al dueño una computadora.

## Playbook de errores inmediatos

- **301 / Moved Permanently:** usa el repo canónico `prismahitech/hitech-os`.
- **404 de branch/raw/path:** resuelve primero el ref/commit SHA exacto y vuelve a pedir el archivo por ese SHA; URL-encodea espacios cuando aplique.
- **Response too large / truncation / parse EOF:** no uses contenido parcial. Cambia a search, line ranges, shards o streaming.
- **403/rate limit:** deja de hacer búsquedas masivas; reduce queries a IDs/paths exactos y reutiliza manifests/hashes ya obtenidos.
- **409 SHA mismatch al escribir:** re-fetch del archivo y blob SHA actual; integra sólo tu cambio y reintenta. Nunca sobrescribas silenciosamente trabajo ajeno.
- **422 branch already exists:** inspecciona el branch existente; si parte del main/authority correcto, reutilízalo. No lo borres ni hagas force.
- **Main avanzó:** AutoMesh v2/revalidación. Drift ajeno puede reanclarse; drift relevante exige autoridad fresca.
- **Source hash mismatch:** no “corrijas” el hash. Marca drift, recupera la fuente actual, decide si afecta significado y fail closed si no puedes probar continuidad.
- **Duplicate targetId / missing / extra:** FAIL. Regenera desde input inmutable. Nunca parchees conteos a mano.
- **Schema/enum desconocido:** FAIL CLOSED. No inventes enum nuevo dentro de una lane.
- **Ambigüedad NDC/Identity:** conserva ambas hipótesis como evidencia y clasifica conflict/curation; no elijas por nombre de selector.
- **PR/check falla:** inspecciona job y logs; corrige causa. Re-run sólo si el fallo es realmente transitorio.
- **FILES_MANIFEST churn:** workers no lo tocan. La integración global es de Chat 6 y sólo cuando corresponda.
- **Merge conflict:** no fuerces merge ni reescribas otra lane. Rebase/reconcilia sólo después de comparar autoridad y scope.
- **Empty search:** no lo uses como prueba de inexistencia; completa la checklist negativa.
- **Generated projection diferente de producto:** no elijas dirección por antigüedad aparente. Revisa authority/history.
- **Tool no puede ejecutar mutación/gate:** mantén análisis read-only y publica blocker preciso.

## Límites duros

En esta fase NO:
- recensus;
- broad rediscovery;
- rebuild de GVAE/RIFAT/Identity/NDC;
- product/runtime/CSS/TSX/JSX mutation;
- generated projection repair;
- canonical registration;
- creación de NDC/VIS/BND/TGT/LYR/recipe/adapter canónicos;
- GVAE APPLY;
- wildcard mutation;
- Materiality fallback;
- `FILES_MANIFEST.json` desde worker lanes;
- fake green.

Sí puedes escribir únicamente evidencia/herramientas lane-local dentro de tu root exclusivo en la work branch asignada.

## Status/mailbox

Publica START, hallazgos materiales, blockers y HANDOFF en tu propia mailbox/status branch.
No escribas el mailbox de otro chat.
No le pidas al dueño copiar receipts: Chat 6 los leerá directamente.


## CHAT 3 — ZONA MOBILE

Tu universo exacto son **271 targets Mobile**. No recenses Mobile.

Punto de partida certificado:
- 271 BLOCKED_MISSING_SEMANTIC_AUTHORITY
- 133 projection CURRENT
- 138 projection debt
- de esas 138: 137 AMBIGUOUS + 1 PRODUCT_CANDIDATE_AUTHORITY_RECONCILIATION_REQUIRED

Trabajo especial:
1. No uses `SURF.mb.owner_home` ni el adapter Mobile como sustituto de significado target-level.
2. Para las 138 filas con deuda de proyección, determina sólo con evidencia si la dirección es autoridad RIFAT vigente, producto más nuevo que exige reconciliación, divergencia intencional o ambigua.
3. El caso retirado `.multiContextRoot` debe tratarse como historia/autoridad reconciliation, nunca restaurarse por hacer coincidir snapshots.
4. Busca significado existente en NDC, Identity, Code Atlas/UIMAP y commits/PRs históricos antes de clasificar TRUE_NEW_AUTHORITY_REQUIRED.
5. No fabriques recipes/bindings por analogía con Tablet o PC.

Objetivo de Mobile: separar “semántica faltante” de “proyección desalineada” y demostrar cuál es el delta semántico verdadero.

## Criterio de cierre

No cierres por “ya revisé bastante”. Cierra sólo cuando:
- todo tu input exacto está contabilizado;
- no hay target perdido/extra/duplicado;
- cada clasificación tiene evidencia;
- todo TRUE_NEW tiene negative-evidence completa;
- no hubo canonical minting ni runtime mutation;
- los outputs están shardeados y son consumibles sin archivos gigantes;
- publicaste work branch, exact head, counts, hashes/manifest, blockers y handoff.

**No abras ni merges a main por tu cuenta salvo instrucción explícita posterior del dueño.**

## 2026-09-15T00:14:00Z — START / FINDING / DECISION

- Auto-detected identity from the canonical status-channel contract and STATUS_INDEX: Chat 3. Latest OWNER_ASSIGNMENT changes the active lane to `MOBILE_AUTHORITY_RECONCILIATION` under phase `AUTHORITY_RECONCILIATION_ANTI_REWORK`.
- Exact assigned universe: `271` certified Mobile targets. No recensus or broad rediscovery is authorized.
- Assigned work branch: `chat3/authority-reconciliation-mobile-20260914`.
- Exclusive output root: `prisma-html/governance/visual-promotion/authority-reconciliation/mobile/**`.
- Assignment basis main was `46c9032d8734bcb5d13242b8ccd7b7cb3c8274e0`; current main is `70f381e9b3c0b63ee4c7e445c98e86b3e9211be9`.
- Drift classification: governance-sensitive / relevant. The intervening main changes modify only `PRISMA Factory Ledger/PRISMA_FACTORY_LEDGER.json` and `PRISMA Factory Ledger/PRISMA_EVIDENCE_INDEX.json`, which are explicit anti-rework authority inputs.
- Decision: do not reuse stale assignment-time authority blindly. Obtain current-head GitHub-only anti-rework / task-exact Authority Mesh evidence before any lane output write.
- Materiality Catalog remains uninspected and unauthorized. Product/runtime mutation, projection repair, canonical registration, GVAE APPLY, RIFAT/Identity/NDC/GVAE rebuild remain forbidden.
- No owner action required; GitHub-only preflight continues autonomously.

## 2026-09-14T18:27:00-06:00 — FINDING / VALIDATION / BLOCKER / HANDOFF

- Current main and assigned work branch are both pinned at `70f381e9b3c0b63ee4c7e445c98e86b3e9211be9`. The work branch exists but remains source/output-clean.
- Current-head capability-pinned GitHub AutoMesh v2 completed successfully: run `34912882027`, artifact `10375366759`, request `41680e216d10bdc6`.
- AutoMesh preflight PASS: both assigned lanes resolve `7/7` required authorities at `100%`, missing `0`, blockers `0`; `visual.generic_application_engine_v1` is FOUND from the canonical Factory Ledger. Composed status is `PASS_COMPOSED_AUTHORITY_MESH`.
- Authority evidence pins requestDigest `0674a60ec8e5edec7bcd854f6d4f8549cb299e2ccf1b080299fb244d4e885cd1`, composed SHA-256 `05c38359e5196f368599ee2c11c92f083e848d13499c7ebf11b67d9af32a1efe`, outer workflow-artifact SHA-256 `b6937753d5c7cb764c0aacf7ec94fb8e4a62e3778916cbf5cfb80d7800400b60`.
- Read-only exact-input accounting is complete: `271 = 133 CURRENT + 138 DRIFT`; target-level NDC meaning remains unresolved `271/271`, visual meaning unresolved `271/271`, exact binding blocked `271/271`.
- Bounded classification candidate from current authority: `133 EXISTING_CONCEPT_LINK_MISSING` and `138 PHYSICAL_OR_PROJECTION_RECONCILIATION_REQUIRED`; all other final classes currently `0`. This is not materialized as lane output because the canonical anti-rework request gate has not executed.
- Projection-debt reconciliation: all 138 DRIFT rows share `prisma-mobile-dashboard.module.css`. Governed commit `731574f97dba0ec46420369b777071500ce2f833` proves `TGT.CENSUS.MOBILE.C30F6FBF52AEFF7B5E02.V1` intersects a newer product cleanup removing retired `.multiContextRoot`; current RIFAT still contains that selector. The other 137 remain target-direction AMBIGUOUS because only file-level drift is proven. No repair is selected or performed.
- `TRUE_NEW_AUTHORITY_REQUIRED=0`. Existing Mobile NDC projection concepts, Identity adapter/binding source, RIFAT physical authority, Code Atlas/UIMAP evidence and Atlasfin reference evidence exist. The demonstrated delta is target-level concept linkage/application authority, not complete absence of authority.
- **BLOCKED_EXECUTION_PATH:** the OWNER_ASSIGNMENT requires the canonical task-specific Factory Ledger anti-rework gate before any work-branch mutation. Current GitHub tools can run/read AutoMesh and workflows but expose no `workflow_dispatch`, `repository_dispatch` or arbitrary GitHub runner for `PRISMA Factory Ledger/tools/verify_prisma_anti_rework_gate.py --request`. The existing Factory anti-rework workflow runs only `--validate` and `--self-test`, not the task-specific request.
- No global workflow is modified and no PR is opened merely to manufacture a runner. Per the owner contract, Chat 3 remains fail-closed and withholds all output-root writes.
- No owner/computer action is requested. To resume, the missing capability is specifically a GitHub-native execution path for the canonical PROPOSAL/MUTATION request gate. Once available, no rediscovery is needed: re-pin main if necessary, execute the gate, write deterministic <=250-row shards, validate 271/271, and publish the final handoff.
- Guardrails preserved: Materiality Catalog uninspected; no recensus; no broad rediscovery; no RIFAT/Identity/NDC/GVAE rebuild; no canonical minting; no product/runtime mutation; no projection repair; no GVAE APPLY; no `FILES_MANIFEST.json` write.

## 2026-09-15T00:38:00Z — ORCHESTRATOR ROUTING CLARIFICATION

- PR #555 registered `visual.operating_graph_v1` as a separate `BUILD / NOT_STARTED` capability for another Foundation task.
- **This authority-reconciliation phase does not switch to that capability.**
- Canonical affected capability remains `visual.generic_application_engine_v1` = `DONE / SOURCE_READY / doNotRebuild=true`.
- Requested action for governed phase work is `ADVANCE`; strictly read-only verification may use `VERIFY`.
- PR #555 still counts as governance-sensitive Ledger/Evidence drift and therefore current-head authority/gate evidence must be rebound before repository output mutation.
- Continue all safe read-only analysis/orchestration. Hold only governed output writes if the correct gate execution path is unavailable.
