# Tablet /inventory — Canonical Composer Reconciliation Checkpoint

Status: `BLOCKED_MISSING_CANONICAL_AUTHORITY`

Date: 2026-09-27

## Target

- targetId: `TGT.CENSUS.TABLET.00EE5391791EB685F977.V1`
- proposalKey: `proposal.tablet.00ee5391791EB685f977.meaning.table`
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

## Follow-up RIFAT authority refinement

A second exact lookup was performed against current canonical RIFAT/prisma-ui authority, without changing any registry.

Proven:

- `routeId = tablet.inventory.route` is directly present in route authority.
- `componentId = products.tablet.app.components.catalog.stock.selling.assist.catalog.stock.selling.assist.screen.tsx` is directly present in the canonical component/owner authority and points to the exact render component.
- The same component is associated with the governed CSS owner:
  `products/tablet/app/components/catalog-stock-selling-assist/catalog-stock-selling-assist.module.css`.

Still **not proven** for the exact `.stockCell` target:

- exact `regionId`;
- exact `slotId`;
- canonical `applicationLayerId`;
- canonical Identity recipe;
- exact canonical binding.

The presence of other regions/slots owned by the same CSS/component is not sufficient to assign them to `.stockCell`. In particular, existing `unknown.buttons` slot evidence belongs to the button/action zone and cannot be generalized to the table cell.

This refinement therefore narrows the physical-location uncertainty but does not open registration.

## Canonical registration integration-path audit

The repository was searched for an explicit canonical-registration writer capable of taking this proposal through:

`visual meaning -> Identity recipe -> exact binding/slot/component -> application layer/policy -> target registration`.

Findings:

- `prisma-html/tools/visual_promotion/promotion_readiness.py` composes readiness and explicitly emits `canonicalMutationAuthorized=false`; it does not register canonical Identity/RIFAT authority.
- `prisma-html/tools/identity_binding_resolver.py` / `identity_binding_resolver_core.py` resolve existing binding evidence and can refresh an authority snapshot, but the resolver does not create a new canonical binding from a promotion proposal. Its application gate remains false.
- The Atlasfin generator `prisma-html/extras/atlasfin/generator/build_canonical_visual_control.py` is tied to the already-certified Cobrar authority path and explicitly keeps product application disabled. It is not a generic table-registration composer.
- The interoperability contract states that workers may emit candidate keys but may not create canonical `BND.*`, `LYR.*`, Identity `REC.*`, or new exact targets; canonical IDs are assigned only by the deterministic canonical composer after evidence review.
- The promotion contracts state that if canonical registration is not explicitly machine-authorized, the phase stops at `READY_FOR_CANONICAL_PROMOTION_INTEGRATION`.

Therefore no repository-local, machine-authorized generic registration path was proven for this target. No registry writer was invoked.

## Result

No existing canonical table Identity recipe or exact table binding was proven.

The proposal therefore cannot be converted to canonical authority merely by changing `proposalKey` into a `VIS.*` string, nor by copying the Atlasfin recipe into `identityRecipeId`.

No canonical VIS/BND/LYR/recipe/adapter ID is assigned by this checkpoint.

## Next governed subphase

A separately authorized canonical-registration integration must resolve, in order:

`visual meaning -> Identity recipe -> exact binding/slot/component -> application layer/policy -> exact target registration -> Work Entry -> GVAE`

The existing proposal key, proven route, proven component, owner and physical-layer evidence are reusable inputs. The missing authority must be created or reused only by the canonical authority path after its required anti-rework, Authority Mesh + Layer Map, collision/dedupe and Work Entry gates pass.

Product/runtime mutation, generated-projection edits and GVAE APPLY remain out of scope.

## Explicit negative shortcuts

- Do not mint a canonical `VIS.*` from the proposal key by string transformation.
- Do not use `REC.table.governed.v2` as an Identity recipe.
- Do not invent a slot or application-layer ID from the physical selector/layer string.
- Do not generalize the existing Cobrar binding.
- Do not generalize the `unknown.buttons` slot to `.stockCell`.
- Do not edit RIFAT or generated product CSS.
- Do not claim APPLY_READY or visual green.
