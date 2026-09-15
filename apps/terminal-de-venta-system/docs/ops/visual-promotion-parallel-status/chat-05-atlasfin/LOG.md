# Chat 5 — ATLASFIN_BRIDGE status log

No updates published yet.


## 2026-09-04T19:50:29-06:00 — START
- Began using the canonical visual-promotion status channel for Chat 5 / ATLASFIN_BRIDGE.
- Read the complete status-channel README and STATUS_CHANNEL_CONTRACT.json.
- Confirmed status branch: `status/vp-chat-05-atlasfin`.
- Confirmed mailbox: `apps/terminal-de-venta-system/docs/ops/visual-promotion-parallel-status/chat-05-atlasfin/`.

## 2026-09-04T19:50:29-06:00 — PROGRESS
- Current work branch is `chat5-atlasfin-bridge-20260904`.
- Current work HEAD is `c5ef78edcc1bcb50ca7b108e316cdc0dbe1034d0`.
- Work base is `57b01ad8bda043ec25763203354b686341bace09`.
- PR #540 contains the bounded read-only Atlasfin promotion bridge under `prisma-html/extras/atlasfin/bridge/**`.
- Reused the existing 418-element Atlasfin catalog and current structured registries. No Atlasfin rebuild, product/runtime mutation, Identity/RIFAT mutation, Target Index mutation or Factory Ledger mutation was performed.
- Materiality Catalog remained `STANDBY_USER_INVOKED_ONLY` and was not inspected.

## 2026-09-04T19:50:29-06:00 — FINDING
- The bridge preserves separate authority domains for Atlasfin, Identity, RIFAT and NDC references.
- Missing worker candidate shards are represented as `PENDING_NOT_PRESENT`; partial or malformed shards are represented as `INVALID`.
- Current Cobrar exact-target evidence remains usable as a read-only reference, while Identity recipe IDs are not collapsed into Atlasfin recipe IDs.
- Optional VISCORE feed absence is kept explicit rather than converted into a synthetic status.

## 2026-09-04T19:50:29-06:00 — DECISION
- Chat 5 will not write `prisma-html/FILES_MANIFEST.json` because that file is outside the lane's allowed write ownership.
- Chat 5 will not merge PR #540 itself.
- Integration/composer ownership will handle global manifest parity and cohort integration.

## 2026-09-04T19:50:29-06:00 — VALIDATION
- CI: PASS.
- PRISMA Sync Sentinel Watch: PASS.
- ForgeOS Quality Gate: PASS.
- GVAE deterministic source/static suite: PASS, 134 tests, zero skips.
- GVAE mandatory registered-target mutation gate: PASS.
- Universal Visual Work Entry Gate: PASS.
- Fresh task-scoped Authority Mesh with native Layer Map: PASS.
- PRISMA HTML source validator: PASS.
- VISCORE architecture check: PASS.
- Identity Dictionary gate: PASS.
- RIFAT authority no-regression gate: PASS with no new regression.
- Atlasfin static gate: PASS, 27/27 pages, 20/20 tasks, zero issues.
- No-fake-READY gate: PASS.

## 2026-09-04T19:50:29-06:00 — BLOCKER
- PRISMA VISCORE1 Certification remains red only at the final committed `FILES_MANIFEST.json` parity step.
- Cause: five new Chat 5 bridge files are absent from the committed global manifest.
- This is an integration-only blocker, not a Chat 5 source/bridge failure.
- Generated manifest candidate artifact: workflow run `33936224670`, artifact `9960264654`, digest `sha256:54f10cb8d7d04b10de3af4feb58a25b1791f0758fab2552de020184dd78e7cdc`.

## 2026-09-04T19:50:29-06:00 — HANDOFF
- Lane state: `READY_FOR_INTEGRATION`.
- PR: https://github.com/prismahitech/hitech-os/pull/540
- Integration must preserve Chat 5 invariants: no automatic Materiality Catalog use, no second editable Atlasfin authority, no authority-domain ID collapse, no candidate-to-authority promotion, and no product/runtime writes from the bridge.
- No user action is currently required.


## 2026-09-04T20:16:00-06:00 — PROGRESS
- Re-read the updated canonical `PRISMA_VISUAL_PROMOTION_PARALLEL_CHAT_PROMPTS.md` and current Chat 5 mailbox.
- Confirmed current phase `INTEGRATION_HANDOFF_AND_PLANNING`.
- Confirmed Chat 5 is explicitly in HOLD and must preserve work branch `chat5-atlasfin-bridge-20260904`, work head `c5ef78edcc1bcb50ca7b108e316cdc0dbe1034d0`, PR #540 and base `57b01ad8bda043ec25763203354b686341bace09`.
- Re-read the updated interoperability contract, vocabulary registry and root AGENTS status-channel additions.

## 2026-09-04T20:16:00-06:00 — FINDING
- Canonical main is now `66fa02147f0cf31529c090a47f376026b406875a`.
- Bounded diff from the Chat 5 base shows only coordination/governance changes relevant to the cohort: status-channel plumbing, continuation prompt, status vocabulary/interoperability additions, AGENTS coordination instructions and corresponding FILES_MANIFEST bookkeeping.
- No Atlasfin catalog/registry input, Cobrar bridge evidence, Identity/RIFAT bridge contract, or Chat 5-owned bridge source changed on main.
- Therefore current main movement is `NON_RELEVANT_COORDINATION_ONLY` drift for Chat 5 and does not require bridge recomputation.

## 2026-09-04T20:16:00-06:00 — DECISION
- Stay `READY_FOR_INTEGRATION` in HOLD.
- Do not rebase, regenerate, or mutate the Chat 5 work branch merely because main moved.
- Do not touch `prisma-html/FILES_MANIFEST.json`; final parity remains integration/composer-owned.
- Do not merge PR #540.
- Do not inspect or use Materiality Catalog.
- Only an explicit, bounded, evidence-backed integration correction request may reopen Chat 5 bridge mutation.

## 2026-09-04T20:16:00-06:00 — VALIDATION
- Continuation bounded drift revalidation: `PASS_NON_RELEVANT_COORDINATION_ONLY_DRIFT`.
- Compared base `57b01ad8bda043ec25763203354b686341bace09` to current main `66fa02147f0cf31529c090a47f376026b406875a`.
- Existing Chat 5 validation evidence at work head remains preserved; no new lane mutation was performed.

## 2026-09-04T20:16:00-06:00 — HANDOFF
- Chat 5 remains ready for deterministic integration with exact frozen work head `c5ef78edcc1bcb50ca7b108e316cdc0dbe1034d0`.
- No user action is required.
- Waiting only for a bounded bridge correction request from the integration lane, if one is produced.


## 2026-09-04T23:44:00-06:00 — START
- Re-read the canonical continuation prompt and current Chat 5 mailbox.
- Current phase is `CANDIDATE_CORPUS_CERTIFICATION_PARALLEL`.
- Chat 5 assignment is `ATLASFIN CORPUS REFERENCE CERTIFICATION`.
- Current canonical main/base for the certification branch is `8cc1918c5e015d1408335c15313e7364e04859c2`.
- New authorized work branch: `chat5/atlasfin-corpus-cert-20260904`.
- Write scope is only `prisma-html/extras/atlasfin/bridge/certification/**`.
- Exact raw surface worker heads will be consumed independently; no wait on Chats 1-4 certification branches.
- No PR is allowed for Chat 5 certification, no `FILES_MANIFEST.json` update is allowed, PR #540 remains unmerged, and Materiality Catalog remains entirely uninspected.


## 2026-09-04T23:51:17-06:00 — FINDING
- Exact raw source accounting was re-derived from the recorded worker heads: Tablet 929, PC 827, Mobile 271, Shared UI 70, total 2,097.
- The raw corpus contains 2,421 non-null Atlasfin refs: 2,097 adapter refs plus 324 recipe refs.
- All 2,421 normalized non-null refs validate against current structured Atlasfin authority. Hard invalid refs: 0.
- 341 representation-only normalizations are required, exactly Mobile 271 + Shared UI 70 qualified `atlasfin::` adapter values.
- Every normalized reference row preserves source head, source file, source line and deterministic source-record SHA-256.
- Re-derived review groups: table 66 Tablet + 105 PC, card 41 + 54, panel 20 + 27, overlay 11 Tablet only.
- Recipe equality remains review-only evidence and never authorizes semantic coalescing.

## 2026-09-04T23:51:17-06:00 — DECISION
- Certified strict representation for values inside `atlasfin.*` fields is the raw Atlasfin ID.
- A source value `atlasfin::<id>` may normalize to `<id>` only as representation, with the original serialized value retained in certification evidence.
- Authority-qualified evidence refs remain qualified.
- All-null and `NO_MATCH` records are excluded from semantic recipe coalescing.
- Materiality Catalog remains entirely uninspected.
- No certification PR, no `FILES_MANIFEST.json` update, no canonical promotion and no product/runtime mutation.

## 2026-09-04T23:51:17-06:00 — VALIDATION
- Certification work branch: `chat5/atlasfin-corpus-cert-20260904`.
- Certification base: `8cc1918c5e015d1408335c15313e7364e04859c2`.
- Certification head: `6c7743f55434eb8d3429f286e2f9eae275d93d87`.
- Branch is exactly one commit ahead of base, zero commits behind at certification creation, and changes exactly six required files under `prisma-html/extras/atlasfin/bridge/certification/**`.
- `ATLASFIN_REFERENCE_CERTIFICATION.jsonl`: 2,421 rows, all `VALID_REFERENCE`.
- `INVALID_REFS.jsonl`: 0 rows.
- Representation normalizations: 341.
- Semantic mutations: 0.
- Source-record hashes: all valid 64-hex SHA-256 values.
- Materiality inspected: false.
- No PR exists for the certification branch.

## 2026-09-04T23:51:17-06:00 — COMPLETE
- Chat 5 Atlasfin corpus reference certification is complete and `READY_FOR_INTEGRATION`.
- Required outputs created:
  - `MANIFEST.json`
  - `NORMALIZATION_POLICY.json`
  - `ATLASFIN_REFERENCE_CERTIFICATION.jsonl`
  - `RECIPE_REVIEW_GROUPS.json`
  - `INVALID_REFS.jsonl`
  - `SUMMARY.md`
- No user action is required.

## 2026-09-04T23:51:17-06:00 — HANDOFF
- Chat 6 should consume `chat5/atlasfin-corpus-cert-20260904@6c7743f55434eb8d3429f286e2f9eae275d93d87` together with immutable raw worker heads and source bridge `chat5-atlasfin-bridge-20260904@c5ef78edcc1bcb50ca7b108e316cdc0dbe1034d0`.
- Final `prisma-html/FILES_MANIFEST.json` refresh remains Chat 6/integration-owned and must happen exactly once after accepted corpus bytes are assembled.

## 2026-09-11T22:45:00-06:00 — START
- Re-read current canonical main instructions and resolved the normative phase as `CORPUS_FINAL_PARALLEL_VERIFICATION`.
- Exact Chat 5 role is `ATLASFIN FINAL WITNESS`; expected result is `PASS_ATLASFIN_CORPUS_WITNESS` only if every immutable-head invariant reproduces.
- Read current Chat 5 mailbox before work and published `IN_PROGRESS` on the dedicated status branch.
- Immutable witness input is `chat5/atlasfin-corpus-cert-20260904@6c7743f55434eb8d3429f286e2f9eae275d93d87`.
- Current canonical main is `7c5b8d477a9006c5184ddbc806874b6e7c02571c`.
- Bounded comparison from certification base to current main shows coordination/governance movement without structured Atlasfin authority drift, so the immutable certification remains eligible for read-only revalidation.
- Materiality Catalog remains completely uninspected; product/runtime mutation and canonical promotion remain forbidden.

## 2026-09-11T23:02:00-06:00 — FINDING
- Immutable certification branch still resolves exactly to `6c7743f55434eb8d3429f286e2f9eae275d93d87`, with parent/base `8cc1918c5e015d1408335c15313e7364e04859c2`.
- Source accounting reproduces 929 Tablet + 827 PC + 271 Mobile + 70 Shared UI = 2,097 source surface outcomes.
- Certification evidence reproduces 2,421 non-null Atlasfin reference rows: 2,097 adapter + 324 recipe references. `INVALID_REFS.jsonl` is the empty Git blob `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`.
- Current structured Atlasfin recipe and adapter authority blobs remain exactly `af8dbff2cf22e0cb77163128af0358cd0a9d3762` and `f6eb2a32ff7a18ec80c6917654fc6d63c9024319`, matching certification provenance.
- Qualified Mobile and Shared UI adapter rows retain original `atlasfin::` serialization, normalized raw adapter IDs, source head/file/line/hash, `VALID_REFERENCE`, and `semanticMutation=false`.
- Recipe review groups reproduce card=95, table=171, panel=47, overlay=11 and declare `semanticCoalescingAllowed=false`; `ALL_NULL_ATLASFIN_REFS` and `NO_MATCH` stay excluded from automatic semantic coalescing.

## 2026-09-11T23:02:00-06:00 — VALIDATION
- Final witness result: `PASS_ATLASFIN_CORPUS_WITNESS`.
- Valid normalized Atlasfin references: 2,421/2,421.
- Hard invalid references: 0.
- Representation-only adapter normalizations: 341.
- Semantic mutations: 0.
- Provenance required fields are present in the certification evidence: `sourceHead`, `sourceFile`, `sourceLine`, `sourceRecordSha256`.
- Current main was rechecked at completion and remains `7c5b8d477a9006c5184ddbc806874b6e7c02571c`; no relevant structured Atlasfin authority drift was found.
- Materiality Catalog inspected: false.
- Product/runtime mutation: false.
- Canonical promotion: false.
- Global snapshot written by Chat 5: false.

## 2026-09-11T23:02:00-06:00 — DECISION
- Publish the deterministic witness receipt under `handoff.parallelWitness` in the Chat 5 mailbox.
- Snapshot acceptance criteria require Chat 6's read-only snapshot to reproduce the same 2,097 outcomes, 2,421 references, 341 representation-only normalizations, 0 semantic mutations, recipe-group partition and complete provenance, while failing closed on head/hash/shape mismatch.
- Any witness/snapshot mismatch is a hard stop for Chat 6, not a warning.
- Chat 5 now remains in `CERTIFIED_HOLD`; no source/certification/runtime/global-authority mutation is permitted by this phase.

## 2026-09-11T23:02:00-06:00 — COMPLETE
- Chat 5 current canonical assignment is complete.
- Status mailbox state is `DONE` with `handoff.parallelWitness.result = PASS_ATLASFIN_CORPUS_WITNESS`.
- No blocker and no user action remain for Chat 5.
- Chat 6 can read this deterministic mailbox directly; no owner relay is required.

## 2026-09-12T16:07:00-06:00 — START
- Re-read the canonical continuation prompt and current Chat 5 mailbox.
- Resolved current phase `CANONICAL_PROMOTION_READINESS_RESOLUTION` from repository truth.
- Resolved role `ATLASFIN_SEMANTIC_REFERENCE_ANALYST`, work branch `chat5/canonical-promotion-readiness-atlasfin-20260912`, exclusive output `prisma-html/governance/visual-promotion/promotion-readiness/atlasfin-evidence/**`, expected result `PASS_ATLASFIN_PROMOTION_READINESS_EVIDENCE`, receipt field `handoff.promotionReadiness`.
- Current canonical main and initial work head were both `d4b451cc92c597d02cfc65094922bd2c5dd17c12`.
- Reused the immutable certified corpus and prior certified Atlasfin reference evidence; no broad rediscovery or recensus was performed.

## 2026-09-12T16:11:00-06:00 — FINDING
- Current canonical Identity recipe registry contains exactly one recipe: `REC.button.primary`.
- The certified Atlasfin recipe groups are `REC.table.governed.v2`, `REC.card.governed.v2`, `REC.panel.governed.v2`, and `REC.overlay.governed.v2`; none has an exact Identity recipe-ID match.
- Certified `SEMANTIC_REVIEW_GROUPS.json` reports 10 groups and `crossSurfaceGroupCount=0`; there is no independent cross-surface semantic authority in the immutable certified evidence that permits canonical coalescing.
- The three Tablet+PC Atlasfin recipe convergences remain visual-only evidence: table 171, card 95, panel 47. Overlay 11 is Tablet-only.
- `IDENTITY_RECIPE_REUSE_CANDIDATES.jsonl` and `CROSS_SURFACE_EQUIVALENCE_EVIDENCE.jsonl` are intentionally zero-row files. Unknown is preserved instead of manufactured.

## 2026-09-12T16:13:00-06:00 — VALIDATION
- Exact work head: `4ffbf95450de6f19adfa5ed2e5c084edd45ca36d`.
- Base/head comparison: 6 commits ahead, 0 behind, exactly six added files and all are inside Chat 5's exclusive `atlasfin-evidence/**` ownership.
- Required outputs all exist: `REFERENCE_ANALYSIS.jsonl`, `IDENTITY_RECIPE_REUSE_CANDIDATES.jsonl`, `CROSS_SURFACE_EQUIVALENCE_EVIDENCE.jsonl`, `VISUAL_ONLY_EQUIVALENCE.jsonl`, `MANIFEST.json`, `SUMMARY.md`.
- Exact branch bytes satisfy the published `validate_atlasfin_evidence` contract conditions by static parity inspection: required files present, Materiality false, canonical-authority mutation false, product/runtime mutation false, no semantic recipe-equality-only row, and all visual-only rows set `canonicalCoalescingAllowed=false`.
- Current main rechecked at completion and remains `d4b451cc92c597d02cfc65094922bd2c5dd17c12`; no post-start main drift occurred.
- Materiality Catalog inspected: false. Canonical IDs minted: false. Per-surface resolution writes: false. Product/runtime mutation: false. FILES_MANIFEST mutation: false.

## 2026-09-12T16:13:00-06:00 — DECISION
- Strong semantic coalescing is not asserted because independent canonical semantic evidence is absent.
- Atlasfin recipe equality is recorded strictly as `VISUAL_SIMILARITY_ONLY`, never semantic identity.
- No Identity recipe reuse candidate is emitted without exact canonical Identity evidence.
- Chat 5 remains support/reference-only and does not invade per-surface or composer ownership.

## 2026-09-12T16:13:00-06:00 — COMPLETE
- Result: `PASS_ATLASFIN_PROMOTION_READINESS_EVIDENCE`.
- Status: `READY_FOR_INTEGRATION`.
- Exact work head: `chat5/canonical-promotion-readiness-atlasfin-20260912@4ffbf95450de6f19adfa5ed2e5c084edd45ca36d`.
- No blocker and no user action remain for Chat 5.

## 2026-09-12T16:13:00-06:00 — HANDOFF
- Chat 6 can consume `handoff.promotionReadiness` directly from this mailbox and validate exact work head `4ffbf95450de6f19adfa5ed2e5c084edd45ca36d`.
- Handoff metrics: reference analysis 8 rows; Identity reuse candidates 0; strong cross-surface semantic evidence 0; visual-only equivalence 3; certified Atlasfin refs 2,421/2,421 valid; hard invalid 0; representation-only normalizations 341; semantic mutations 0.
- Any stronger cross-surface semantic group requires independent canonical semantic authority and must not be derived from Atlasfin recipe equality alone.

## 2026-09-14T23:30:00Z — OWNER_ASSIGNMENT

# OWNER ASSIGNMENT — AUTHORITY_RECONCILIATION_ANTI_REWORK

**Chat:** 5
**Lane:** CROSS_AUTHORITY_EVIDENCE_RECONCILIATION
**Assignment basis main:** `46c9032d8734bcb5d13242b8ccd7b7cb3c8274e0`
**Work branch to use/create:** `chat5/authority-reconciliation-cross-evidence-20260914`
**Exclusive output root:** `prisma-html/governance/visual-promotion/authority-reconciliation/cross-authority-evidence/**`

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


## CHAT 5 — ZONA TRANSVERSAL DE EVIDENCIA

No eres resolver de superficie. Eres el **analista transversal de autoridad existente** para los 2,097.

Tu misión es construir evidencia que impida a Chats 1–4 y 6 inventar conceptos que ya existen.

Debes inspeccionar y cruzar:
- NDC canon, grammar, schemas, seeds y registries;
- los catálogos NDC con estado `defined_for_doc1`;
- Identity registries, aliases, profiles, recipes, tokens, bindings, visual stacks y adapters;
- RIFAT/Visual Control/Target Index;
- Code Atlas/UIMAP/UI Bridge y sus fixtures/contratos;
- Atlasfin como referencia visual, nunca como autoridad semántica;
- Factory Ledger/Evidence Index;
- commits, PRs y docs/ops históricos relevantes.

Entregables especiales:
1. `EXISTING_CONCEPT_INDEX`: conceptos NDC/Identity/VIS ya existentes y dónde viven.
2. `SEMANTIC_CROSSWALK_EVIDENCE`: relaciones demostrables entre significado operacional, significado visual y targets, sin afirmar equivalencia cuando sólo hay relación.
3. `NDC_MATERIALIZATION_AUDIT`: qué es canon/doctrina/schema/seed/ejemplo y qué está realmente poblado machine-readable. Debe confirmar o refutar con evidencia el hueco `defined_for_doc1`.
4. `HISTORICAL_AUTHORITY_EVIDENCE`: commits/PRs/docs que prueban intención o concepto previo.
5. `NEGATIVE_EVIDENCE_RULES`: qué fuentes mínimas deben haberse consultado antes de que Chat 6 acepte TRUE_NEW_AUTHORITY_REQUIRED.
6. Evidencia cross-surface fuerte sólo cuando hay autoridad semántica independiente. Recipe/family/preset equality sola = VISUAL_SIMILARITY_ONLY.

No decidas el resultado final de un target de otra lane; entrega evidencia indexada que Chat 6 pueda consumir.

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

## 2026-09-15T00:38:00Z — ORCHESTRATOR ROUTING CLARIFICATION

- PR #555 registered `visual.operating_graph_v1` as a separate `BUILD / NOT_STARTED` capability for another Foundation task.
- **This authority-reconciliation phase does not switch to that capability.**
- Canonical affected capability remains `visual.generic_application_engine_v1` = `DONE / SOURCE_READY / doNotRebuild=true`.
- Requested action for governed phase work is `ADVANCE`; strictly read-only verification may use `VERIFY`.
- PR #555 still counts as governance-sensitive Ledger/Evidence drift and therefore current-head authority/gate evidence must be rebound before repository output mutation.
- Continue all safe read-only analysis/orchestration. Hold only governed output writes if the correct gate execution path is unavailable.

## 2026-09-15T09:32:00-06:00 — OWNER/ORCHESTRATOR ASSIGNMENT: DYNAMIC_CROSS_AUTHORITY_SUPPORT

Chat 5 baseline work is accepted for read-only consumption:

- baseline receipt: `AUTHORITY_RECONCILIATION_READ_ONLY_RECEIPT.json`;
- result: `PASS_READ_ONLY_CROSS_AUTHORITY_EVIDENCE_WITH_WRITE_GATE_PENDING`;
- exact input accounting: 2,097 / missing 0 / extra 0 / duplicate 0;
- baseline MUST NOT be rebuilt.

### New operating role

From now on Chat 5 is the **dynamic cross-authority semantic support lane** for Chats 1-4 and Chat 6.

Do not sit idle waiting for the write gate.

Continuously inspect the current surface-worker mailboxes for concrete unresolved items, especially:
- target IDs awaiting semantic linkage;
- concept IDs with uncertain NDC vs Identity/VIS relationship;
- conflict/curation candidates;
- projection-vs-semantic ambiguity that needs authority/history evidence;
- any provisional `TRUE_NEW_AUTHORITY_REQUIRED`;
- any worker claim that depends on negative evidence.

For each concrete question:
1. narrow the scope to the exact target/concept;
2. search NDC canon/registries/schemas/seeds/examples;
3. search Identity registries/aliases/recipes/bindings/stacks/adapters;
4. inspect RIFAT/Visual Control/Target Index exact evidence;
5. inspect Code Atlas/UIMAP/UI Bridge;
6. use Atlasfin as structured reference only, never semantic authority by visual similarity;
7. inspect Factory Ledger/Evidence Index;
8. inspect relevant PR/commit/docs history when there is a clue;
9. publish a compact **delta receipt** in this mailbox with evidence, relation type, negative-evidence coverage, confidence and unresolved remainder.

### Semantic rules remain mandatory

- NDC operational meaning is not visual Identity meaning.
- `identity::ACT.primary RELATED_TO ndc::ACT.sale.checkout` does not mean equivalent.
- Existing concept without target link favors `EXISTING_CONCEPT_LINK_MISSING`.
- Existing semantic authority with missing binding/application favors `EXISTING_SEMANTIC_AUTHORITY_APPLICATION_GAP`.
- Contradictory authority remains `EXISTING_AUTHORITY_CONFLICT_CURATE`.
- Projection/product disagreement without proven direction remains `PHYSICAL_OR_PROJECTION_RECONCILIATION_REQUIRED`.
- `TRUE_NEW_AUTHORITY_REQUIRED` is allowed only after complete target-specific negative evidence across every required authority family.
- Empty search never proves absence.

### Output behavior

Publish bounded mailbox delta receipts. Suggested naming:
- `AUTHORITY_DELTA_<target-or-topic>.json` for small bounded investigations, or
- append structured DELTA/HANDOFF sections to `LOG.md`.

Do not create giant replacement corpora.
Do not rewrite the baseline receipt unless a factual correction is required and proven.
Do not write governed output-root files while `WRITE_GATE_PATH_PENDING` remains.
Do not ask the owner for a computer, PowerShell, localhost, manual workflow dispatch or file relay.
Do not open or merge PRs.
Do not inspect Materiality Catalog.
Do not mint canonical IDs.
Do not mutate product/runtime, projections, NDC, Identity, RIFAT or GVAE.

### Coordination contract

- Read Chats 1-4 directly; owner relay is not required.
- Chat 6 will read this mailbox directly.
- Publish findings as soon as they are useful; do not wait for all four workers to finish.
- If no concrete unresolved query exists, keep the lane ready and re-check worker receipts rather than recomputing the baseline.

## 2026-09-15T09:40:00-06:00 — START / DYNAMIC CROSS-AUTHORITY SUPPORT
- Re-read current STATUS mailboxes for Chats 1-4 directly from their status branches.
- Baseline `AUTHORITY_RECONCILIATION_READ_ONLY_RECEIPT.json` remains accepted and was not rebuilt.
- Current main remains `70f381e9b3c0b63ee4c7e445c98e86b3e9211be9`.
- `WRITE_GATE_PATH_PENDING` remains scoped only to governed output-root writes.

## 2026-09-15T09:40:00-06:00 — FINDING
- Chat 1 still has 924 Tablet semantic-link reviews pending. Chat 2 and Chat 3 have complete read-only classification with `TRUE_NEW_AUTHORITY_REQUIRED=0`. Chat 4 still has 40 target-specific Shared UI semantic joins pending.
- Identity has an existing Shared UI semantic binding authority: `BND.ACT.PRIMARY.SHAREDUI.V1` -> `ACT.primary` / `REC.button.primary`, status `BLOCKED_BY_MISSING_BINDING`, zero targets.
- This positive authority means bounded Shared UI primary-action targets must not default to TRUE_NEW merely because exact target linkage is missing.
- `identity::ACT.primary` remains visual meaning and is not equivalent to `ndc::ACT.sale.checkout`.

## 2026-09-15T09:40:00-06:00 — DELTA RECEIPTS
- Tablet `TGT.CENSUS.TABLET.0A305145467F0C5CF3E3.V1`: existing `TOK.color.accent` + `BND.TOK.COLOR.ACCENT.TABLET.MULTI.V1` one-to-many ambiguity. Suggested `EXISTING_AUTHORITY_CONFLICT_CURATE`, HIGH.
- Tablet `TGT.CENSUS.TABLET.2E41F7A945432E762571.V1`: same existing ambiguous accent authority. Suggested `EXISTING_AUTHORITY_CONFLICT_CURATE`, HIGH.
- Shared UI `TGT.CENSUS.SHARED_UI.09F96569FF3A6B805D9C.V1`: exact CURRENT physical target spans CheckoutButton + primary ScanButton; existing Shared UI `ACT.primary` semantic authority has no exact target binding. Suggested `EXISTING_SEMANTIC_AUTHORITY_APPLICATION_GAP`, MEDIUM_HIGH. Do not map the whole grouped target to NDC `ACT.sale.checkout`.
- Shared UI `TGT.CENSUS.SHARED_UI.BA2256417613E877ABEE.V1`: exact CURRENT `.actionButton:hover` target; existing Shared UI `ACT.primary` semantic authority remains unbound. Suggested `EXISTING_SEMANTIC_AUTHORITY_APPLICATION_GAP`, HIGH.
- PC `TGT.CENSUS.PC.6CC072FF944F55B85FE6.V1`: exact ProductMediaWorkspace `.workspace` target has projection MISSING and historical `VIS.SURFACE.CONTENT.PRIMARY` candidate intent. Suggested final `PHYSICAL_OR_PROJECTION_RECONCILIATION_REQUIRED`, HIGH; historical intent is anti-TRUE_NEW evidence, not canonical Identity authority.

## 2026-09-15T09:40:00-06:00 — VALIDATION
- Published five bounded JSON delta receipts in Chat 5's own mailbox.
- No foreign mailbox write.
- No recensus or baseline reconstruction.
- No Materiality Catalog access.
- No canonical registration/minting.
- No product/runtime mutation.
- No projection repair.
- No GVAE APPLY.
- No PR or merge.

## 2026-09-15T09:40:00-06:00 — HANDOFF
- Chat 6 and surface workers can consume the five new `AUTHORITY_DELTA_*.json` files directly.
- Continue dynamic target-specific support immediately; do not wait for the write gate.

## 2026-09-15T10:14:37-06:00 — PROGRESS / CURRENT-MAIN REVALIDATION
- Current main advanced to `8db4370d579014f8fed6e190ffce45e1589b33d9`.
- Exact compare from `70f381e9...` is 8 commits / 13 changed paths.
- Drift is limited to `prisma-html/FILES_MANIFEST.json`, `prisma-html/docs/ops/README.md`, and the separate visual-operating-graph Foundation docs/governance.
- No NDC, Identity, RIFAT/Visual Control/Target Index, visual-promotion candidate corpus, Atlasfin registry, Factory Ledger or Evidence Index path changed.
- Result: prior Chat 5 read-only semantic evidence remains consumable; baseline rebuild is not justified.

## 2026-09-15T10:14:37-06:00 — DELTA RECEIPTS ROUND 2
- Shared UI `TGT.CENSUS.SHARED_UI.C27228263069C7175BA1.V1` (exact CheckoutButton): existing `ACT.primary` / `REC.button.primary` authority, exact binding absent. Suggested `EXISTING_SEMANTIC_AUTHORITY_APPLICATION_GAP`, HIGH.
- Shared UI `TGT.CENSUS.SHARED_UI.718C4BEE50BF4F4078A8.V1` (`.actionButton`): existing `ACT.primary` authority, exact binding/application absent. Suggested `EXISTING_SEMANTIC_AUTHORITY_APPLICATION_GAP`, HIGH.
- Shared UI `TGT.CENSUS.SHARED_UI.3863084F2D7188E87D08.V1` (CheckoutButton + primary ScanButton reference-effects group): existing primary visual authority, grouped exact binding absent. Suggested `EXISTING_SEMANTIC_AUTHORITY_APPLICATION_GAP`, MEDIUM_HIGH; no NDC equivalence.
- Topic receipt `AUTHORITY_DELTA_MAIN_DRIFT_8DB4370D.json`: `READ_ONLY_EVIDENCE_REMAINS_CONSUMABLE`, HIGH.
- Shared UI `TGT.CENSUS.SHARED_UI.6A23B437B2D23C3D918D.V1`: `data-prisma-profile="perf"` is a performance/rendering profile, not Identity `VIS.identity.profile`. This receipt is a non-equivalence guard only and intentionally does not fabricate a final classification.

## 2026-09-15T10:14:37-06:00 — VALIDATION / HANDOFF
- Chat 5 mailbox now exposes 10 dynamic delta receipts total.
- Chat 1/2/3 are read-only structurally complete; Chat 4 remains the first-priority surface lane with 40 target-specific rows.
- Chat 6 may consume the current delta list directly from Chat 5 STATUS.
- `WRITE_GATE_PATH_PENDING` still blocks only governed output-root writes.
- Materiality uninspected; no canonical minting; no product/runtime mutation; no projection repair; no GVAE APPLY; no PR/merge.

