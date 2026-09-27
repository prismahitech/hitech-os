# Tablet /inventory — Visual Reconciliation Roadmap

Status: `CANDIDATE / PRESERVATION RECORD — NO RUNTIME MUTATION AUTHORIZED`

Date: 2026-09-26

## Purpose

Preserve the already-established visual diagnosis and solution path for Tablet `/inventory` so the visual work is not lost while semantic promotion/governance is resolved.

This file is not canonical visual authority, does not mint IDs, and does not authorize a CSS/runtime change.

## Current surface

- Surface: `tablet`
- Route: `/inventory`
- Functional module: Catalog → Stock → Selling Assist
- Canonical RIFAT source: `prisma-html/authority/rifat/tablet/runtime-sources/modules/catalog-stock-selling-assist/catalog-stock-selling-assist.module.css`
- Generated product projection: `apps/terminal-de-venta-system/products/tablet/app/components/catalog-stock-selling-assist/catalog-stock-selling-assist.module.css`
- Current Visual Control authority confirms the `/inventory` route and multiple governed layers owned by the same CSS source.

## Visual problem already established

The current implementation reads as overly blue and utility-driven. The owner-supplied reference establishes a different visual target:

- dark atmospheric photographic environment remains visible behind the UI;
- large translucent glass surfaces carry the information hierarchy;
- panels have depth, reflection and subtle specular treatment instead of reading as opaque blue rectangles;
- color is distributed by semantic role, not concentrated into one blue/cyan family;
- the page reads as one composed operational surface, not a pile of unrelated cards;
- primary actions may use controlled glow, but the glow must not turn the whole page blue;
- functional behavior, catalog data, inventory controls and selling flow remain unchanged.

## Reference-to-solution translation

### 1. Preserve the atmosphere

The background is part of the visual composition. Do not solve the problem with a flat dark/blue page background.

Target treatment:
- retain the governed atmospheric background mechanism;
- allow localized translucent surfaces to reveal it;
- use restrained localized Gaussian/radial light fields where needed;
- use a restrained vignette/depth layer;
- avoid a global cyan wash.

### 2. Rebuild surfaces as glass, not blue cards

For the governed `/inventory` selectors, the intended direction is:
- translucent dark glass;
- soft blur/saturation;
- thin low-contrast borders;
- restrained inner highlight;
- soft elevation shadow;
- enough transparency to preserve background continuity.

Priority surface families:
- `.heroCard`
- `.metricCard`
- `.operationsSurface`
- `.mainPanel`
- `.detailPanel`
- `.searchInputWrap`
- operation inputs/selects
- filter controls
- product rows
- selected product row
- detail cells

Do not flatten the entire surface into one giant panel.

### 3. Break the blue monoculture

Use accents by semantic role:
- cyan/ice: informational identity and active operational focus;
- violet: secondary analytical/structural emphasis;
- green: healthy/available/success state;
- amber/gold: attention, cart, caution or inventory-watch state;
- red/pink only for genuine danger/error emphasis.

Accents should appear as restrained borders, text highlights, glyphs, radial illumination and selected states. They should not become full opaque fills across the page.

### 4. Restore editorial hierarchy

The reference establishes:
1. atmosphere;
2. hero/title;
3. high-level metrics;
4. operational control surface;
5. searchable catalog;
6. selected-item detail.

The existing functional structure already supports this hierarchy. Refine it instead of rebuilding the information architecture.

### 5. Buttons and actions

The agreed direction is to make actionable controls unmistakable without turning every control into a neon billboard.

Primary selling/operation actions:
- controlled blue → violet gradient;
- subtle Gaussian glow;
- thin light edge;
- small specular highlight;
- stronger hover/focus glow;
- no layout shift.

Secondary/filter controls:
- mostly glass;
- accent only on active/hover/focus;
- different semantic accents may be used so every action does not read as blue.

### 6. Product rows

Rows remain compact and operational:
- translucent dark row surface;
- subtle border;
- selected row gets localized cyan/ice emphasis;
- product glyphs may use restrained cyan/violet/green/amber accents;
- price, stock and status stay subordinate to product identity;
- `Agregar` remains clear, with localized glow.

## What must NOT happen

- Do not replace the reference with a generic blue SaaS dashboard.
- Do not introduce opaque white panels.
- Do not make every border cyan.
- Do not make every button blue.
- Do not add giant vertical sections or nested card pyramids.
- Do not alter catalog/inventory/sale behavior to obtain the visual result.
- Do not hand-edit the generated product projection.
- Do not mutate RIFAT until the exact target passes Work Entry/GVAE authorization.
- Do not treat Atlasfin recipe similarity as semantic authorization.
- Do not declare visual green without runtime evidence.

## Governance route

The target that blocked the prior direct mutation attempt is:

`TGT.CENSUS.TABLET.00EE5391791EB685F977.V1`

Certified evidence identifies:
- owner/style source: `catalog-stock-selling-assist.module.css`;
- selector: `[data-prisma-route="/inventory"] .stockCell`;
- projection mode: existing RIFAT Tablet generator;
- Atlasfin recipe evidence: `REC.table.governed.v2`;
- Atlasfin adapter evidence: `ADP.TB.TOUCH.V2`;
- existing Tablet adapter evidence: `prisma.adapter.tablet.v1`;
- promotion decision: `REGISTER_TARGET_FIRST`.

The target was blocked because its certified record lacks sufficient canonical meaning/binding/application evidence. Current Visual Control expanded authority independently confirms exact `/inventory` route and governed layers owned by the same CSS source. Those facts are evidence for resolution, not permission to mutate.

## Execution roadmap

```
PRESERVE THIS ROADMAP
        ↓
resolve exact Tablet target against current Target Index + RIFAT route/region/layer authority
        ↓
resolve neutral meaning / Identity / adapter / binding without invention
        ↓
Work Entry exact target
        ↓
GVAE exact authorization
        ↓
edit ONLY canonical RIFAT source
        ↓
deterministic projection
        ↓
runtime screenshot/evidence
        ↓
compare against owner-supplied reference
        ↓
verify atmosphere + glass + hierarchy + multi-accent balance
        ↓
certify or rollback
```

The visual solution described here must survive the governance work unchanged unless new repository evidence disproves a specific detail.

## 2026-09-27 resolution checkpoint

A bounded reconciliation against current machine-readable authority was performed before any mutation.

### Newly proven authority

- `/inventory` is explicitly registered in the current Tablet route authority as `tablet.inventory.route`.
- Its canonical route regions include `tablet.inventory.route.main-content` and `tablet.inventory.route.shell`.
- The exact physical layer remains the governed `table` layer:
  - implementation layer: `products.tablet.app.components.catalog.stock.selling.assist.catalog.stock.selling.assist.module.css.data.prisma.route.inventory.stockcell`
  - selector: `[data-prisma-route="/inventory"] .stockCell`
  - visual region: `table`
  - safety classification: `safeVisualOnly`
  - current projection hashes remain consistent with the visual-source manifest.
- The Tablet route budget explicitly permits background visibility and zero full-viewport opaque panels on `/inventory`.
- The governed Tablet light-shell route-combo catalog classifies inventory/audit as `route_combo.table_heavy_operations`, with medium glass density, signature-only rims, a semantic glow budget of one strong plus three medium accents, and reduced-motion compliance.

### Still missing, deliberately unresolved

The current authority does **not** prove an exact region/slot/component binding for `.stockCell`, nor an existing Identity visual meaning or Identity recipe for the generic table role. The existing Atlasfin `REC.table.governed.v2` match remains reference evidence only.

Therefore this target remains:

`REGISTER_TARGET_FIRST`

No canonical ID was invented, no target-index record was edited, and no product/runtime mutation was performed.

### Immediate next governed step

Use the newly proven route/layer evidence to resolve whether an existing canonical neutral table meaning/recipe/binding can be reused. If no existing authority exists, the canonical composer must be allowed to register the missing semantic/application authority. Only after that may Work Entry/GVAE be reconsidered.

## Historical note

A prior direct visual patch attempt was intentionally abandoned after the Universal Visual Work Entry Gate returned `REGISTER_TARGET_FIRST`. The attempted patch was reverted and its PR closed.

That was a governance stop, not a rejection of the visual diagnosis.

Therefore:

> The next authorized visual change resumes from this roadmap, not from the current blue-heavy styling as though the reference analysis never happened.

## Evidence sources

- Current RIFAT source and generated projection declaration.
- Tablet Visual Control expanded component/region authority.
- Certified Visual Control Target Index record for the target above.
- Canonical visual-promotion phase contract.
- Owner-supplied `Inventario general` reference screenshot.

## Non-authority note

This candidate document records the intended solution path. It does not become visual authority merely by existing. Canonical meaning, exact location and authorization remain owned by the machine-readable authorities described in the Visual Change Master Map.
