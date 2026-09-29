# Tablet /inventory — Canonical Composer Reconciliation Checkpoint

Status: `BLOCKED_MISSING_CANONICAL_AUTHORITY`

Date: 2026-09-27

## Target

- targetId: `TGT.CENSUS.TABLET.00EE5391791EB685F977.V1`
- proposalKey: `proposal.tablet.00ee5391791eb685f977.meaning.table`
- route: `tablet.inventory.route`
- routePath: `/inventory`
- implementationLayerId: `products.tablet.app.components.catalog.stock.selling.assist.catalog.stock.selling.assist.module.css.data.prisma.route.inventory.stockcell`
- selector: `[data-prisma-route="/inventory"] .stockCell`
- visualRegion: `table`
- projectionMode: `existing-rifat-tablet-generator`

Source evidence packet:
`prisma-html/governance/visual-promotion/candidates/tablet/inventory-reference-reconciliation/TARGET_REGISTRATION_EVIDENCE_PACKET.json`

## Composer finding

The proposal key is a valid **local proposal key**, not a canonical Identity ID. It is therefore eligible to enter canonical-composer consideration only after the exact registration evidence required by the promotion contract is complete.

Current canonical promotion-readiness machinery is proposal-only/readiness-only. Its registration decision requires, for the exact target:

1. resolved semantic meaning or an explicit `PROPOSE_NEW` proposal;
2. canonical Identity recipe;
3. canonical Identity adapter;
4. existing canonical binding or a binding proposal key;
5. exact route, region, slot, component, owner and implementation-layer evidence;
6. canonical application-layer authority;
7. projection/application policy.

The current inventory evidence packet does **not** satisfy items 2, 4, 5 (region/slot remain unresolved for the exact `.stockCell` target), or 6. Its `exactTargetRegistrationReady` remains `false`.

## Existing-authority checks

Current main `0626c72e325660435683d178d7e04395ec66306a` was inspected against the existing Identity authority:

- Identity recipe registry: `prisma-html/authority/rifat/identity/registries/recipe.registry.json`
  - current recipe count: 1
  - registered recipe: `REC.button.primary`
  - no canonical table recipe is registered.
- Identity element-binding registry:
  `prisma-html/authority/rifat/identity/registries/element-bindings.registry.json`
  - exact resolved binding present for Tablet POS Cobrar only;
  - no exact binding for the inventory `.stockCell` target;
  - surface adapter `prisma.adapter.tablet.v1` is explicitly not a concrete element binding.
- Atlasfin:
  - `REC.table.governed.v2`
  - `ADP.TB.TOUCH.V2`
  remain reference/support evidence only and cannot substitute for Identity authority.

The canonical visual authority registry further confirms the authority split:
- `AUTH.PRISMA.VISUAL.IDENTITY` owns neutral visual meaning, identity profiles, recipes, assets and surface adapters;
- `AUTH.PRISMA.UI.BINDINGS` owns surface/route/owner/region/slot/layer location truth;
- Atlasfin is explicitly a non-authoritative cockpit.

## Follow-up RIFAT authority refinement

A second exact lookup was performed against current canonical RIFAT/prisma-ui authority, without changing any registry.

Proven:

- `routeId = tablet.inventory.route` is directly present in route authority.
- `componentId = products.tablet.app.components.catalog.stock.selling.assist.catalog.stock.selling.assist.screen.tsx` is directly present in the canonical component/owner authority and points to the exact render component.
- The same component is associated with the governed CSS owner:
  `products/tablet/app/components/catalog-stock-selling-assist/catalog-stock-selling-assist.module.css`.
- The route page itself mounts that exact screen beneath:
  `[data-prisma-route="/inventory"]`.

Still **not proven** for the exact `.stockCell` target:

- exact `regionId`;
- exact `slotId`;
- canonical `applicationLayerId`;
- canonical Identity recipe;
- exact canonical binding.

The presence of other regions/slots owned by the same CSS/component is not sufficient to assign them to `.stockCell`. In particular, existing `unknown.buttons` slot evidence belongs to the button/action zone and cannot be generalized to the table cell.

The exact source also proves that `.stockCell` is a span inside `ProductRow`, while the row's actual action controls are separate buttons. This reinforces that the existing button binding/slot cannot be reused for the table-cell target.

This refinement therefore narrows the physical-location uncertainty but does not open registration.

## Layer-index audit

The canonical Tablet Visual Control `layers.json` was searched directly for the exact implementation-layer string:

`products.tablet.app.components.catalog.stock.selling.assist.catalog.stock.selling.assist.module.css.data.prisma.route.inventory.stockcell`

No canonical `layer_id` record was found for that exact target string.

The Target Registration Evidence Packet's `implementationLayerId` is therefore a Visual Control implementation-layer observation, not proof of a canonical `LYR.*` authority ID.

This is consistent with the binding registry policy:
- unknown bindings remain null;
- fully resolved bindings require all trace fields;
- required trace fields include owner, route, region, slot, componentUiId and layerId;
- a compact implementation-layer index cannot by itself prove a canonical layer ID.

No `LYR.*` ID was inferred.

## Canonical registration integration-path audit

The current main was re-audited after G-01 hardening and the canonical-registration integration is now present in:

- `prisma-html/tools/visual_promotion/canonical_registration/engine.py`
- `prisma-html/tools/visual_promotion/canonical_registration/request_builder.py`
- `prisma-html/tools/visual_promotion/canonical_registration/current_truth.py`
- `prisma-html/tools/visual_promotion/canonical_registration/authority_adapters.py`
- `prisma-html/tools/visual_promotion/canonical_registration/collision_classifier.py`
- `prisma-html/tools/visual_promotion/canonical_registration/application_policy.py`
- `prisma-html/tools/visual_promotion/canonical_registration/policy.py`

This is the governed capability `visual.canonical_promotion_integration_v1`. It is a bounded canonical-registration writer, not a replacement authority. Its documented/runtime-checked boundary requires, before mutation:

1. exact census evidence pinned in current truth;
2. expected current HEAD;
3. source digest/path;
4. explicit NDC semantic adjudication;
5. exact RIFAT binding;
6. explicit `LYR.*` application-layer authority and policy;
7. Work Entry `REGISTER_TARGET_FIRST` handoff;
8. explicit canonical-registration authorization.

The engine also performs transaction locking, current-head checks, registry preconditions, collision classification, atomic writes, persisted journal, postcondition verification, idempotent replay protection and transaction-scoped rollback.

### Target-specific result

The existence of this engine **does not unblock Tablet /inventory**. The target still cannot produce a valid registration request because the current target evidence lacks:

- canonical NDC meaning/adjudication;
- Identity recipe;
- exact binding;
- exact slot;
- canonical `LYR.*` application-layer authority/policy;
- exact target registration inputs.

The current Identity recipe registry still contains only `REC.button.primary`; the current binding registry still has no exact `.stockCell` binding; and no canonical layer record was proven for the target implementation-layer string.

Therefore **the canonical writer was not invoked**. This is now a real governed path waiting for missing authority, not a missing-engine problem.

## Why no registration was invoked

Invoking the writer with guessed semantic, binding, slot, recipe or application-layer inputs would fail the writer's own fail-closed contracts and would violate the authority split. In particular:

- Atlasfin `REC.table.governed.v2` remains support/reference evidence and is not an Identity recipe.
- The existing `unknown.buttons` slot is a button/action-zone authority and cannot be generalized to `.stockCell`.
- The implementation-layer observation cannot be transformed into a `LYR.*` ID.
- A canonical NDC meaning cannot be minted by this worker.
- The canonical-registration engine cannot manufacture missing RIFAT/Identity authority from physical similarity.

Accordingly, no registry mutation, target registration, product projection edit or GVAE APPLY is authorized by this checkpoint.

## Result

No existing canonical table Identity recipe, canonical layer ID or exact table binding was proven.

The proposal therefore cannot be converted to canonical authority merely by changing `proposalKey` into a `VIS.*` string, nor by copying the Atlasfin recipe into `identityRecipeId`, nor by transforming the implementation-layer string into a `LYR.*` ID.

No canonical VIS/BND/LYR/recipe/adapter ID is assigned by this checkpoint.

## Next governed subphase

A separately authorized canonical-registration integration must resolve, in order:

`visual meaning -> Identity recipe -> exact binding/slot/component -> application layer/policy -> exact target registration -> Work Entry -> GVAE`

The existing proposal key, proven route, proven component, owner, route anchor, source selector and physical-layer evidence are reusable inputs. The missing authority must be created or reused only by the canonical authority path after its required anti-rework, current-head Authority Mesh + Layer Map, collision/dedupe and Work Entry gates pass.

Product/runtime mutation, generated-projection edits and GVAE APPLY remain out of scope until those gates independently pass.

## Explicit negative shortcuts

- Do not mint a canonical `VIS.*` from the proposal key by string transformation.
- Do not use `REC.table.governed.v2` as an Identity recipe.
- Do not transform the implementation-layer string into a `LYR.*` ID.
- Do not invent a slot or application-layer ID from the physical selector/layer string.
- Do not generalize the existing Cobrar binding.
- Do not generalize the `unknown.buttons` slot to `.stockCell`.
- Do not edit RIFAT or generated product CSS.
- Do not add a new generic registration engine merely to unblock this target.
- Do not claim APPLY_READY or visual green.
