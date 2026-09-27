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

The current inventory evidence packet does **not** satisfy items 2, 4, 5 (slot/component are unresolved), or 6. Its `exactTargetRegistrationReady` remains `false`.

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

## Result

No existing canonical table Identity recipe or exact table binding was proven.

The proposal therefore cannot be converted to canonical authority merely by changing `proposalKey` into a `VIS.*` string, nor by copying the Atlasfin recipe into `identityRecipeId`.

No canonical VIS/BND/LYR/recipe/adapter ID is assigned by this checkpoint.

## Next governed subphase

A separately authorized canonical-registration integration must resolve, in order:

`visual meaning -> Identity recipe -> exact binding/slot/component -> application layer/policy -> exact target registration -> Work Entry -> GVAE`

The existing proposal key and the newly proven route/layer evidence are reusable inputs. The missing authority must be created or reused only by the canonical authority path after its required anti-rework, Authority Mesh + Layer Map, collision/dedupe and Work Entry gates pass.

Product/runtime mutation, generated-projection edits and GVAE APPLY remain out of scope.

## Explicit negative shortcuts

- Do not mint a canonical `VIS.*` from the proposal key by string transformation.
- Do not use `REC.table.governed.v2` as an Identity recipe.
- Do not invent a slot or application-layer ID from the physical selector/layer string.
- Do not generalize the existing Cobrar binding.
- Do not edit RIFAT or generated product CSS.
- Do not claim APPLY_READY or visual green.
