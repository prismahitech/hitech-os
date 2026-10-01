# Prisma Cloud Center — Plan Authority Semantics

**Status:** G1 authority reconciliation target  
**Effective:** 2026-09-29

## Canonical ownership

Prisma has two related but different concepts:

1. **Commercial SKU / license plan**
   - Canonical owner: `apps/terminal-de-venta-system/shared/licensing/plan-catalog.canonical.json`
   - Controls vendibility, commercial list price, commercial limits, and the commercial plan vocabulary.
   - Current vendible plans: `TABLET_SOLO`, `TABLET_PRO`, `TABLET_PC_MANAGED`.

2. **Customer Setup provisioning plan**
   - Canonical source owner: `apps/terminal-de-venta-system/shared/licensing/customer-setup-contract.ts`
   - Controls device surfaces, slot generation, provisioning behavior, setup mode, claim mode, and onboarding policies.
   - It may contain commercial plan IDs plus provisioning-only package IDs.

## Provisioning-only package

`TABLET_PC_MOBILE_MANAGED` is classified as:

```text
PROVISIONING_ONLY_PLAN
commercialSku: TABLET_PC_MANAGED
standalonePrice: NONE
canonicalCommercialCatalog: ABSENT_BY_DESIGN
```

The provisioning identifier remains `TABLET_PC_MOBILE_MANAGED`, while the underlying customer license/tenant commercial plan is `TABLET_PC_MANAGED`.

It represents the `PRISMA_TRIPLE_DEVICE_STARTER` Customer Setup package with:

- Tablet: 1
- PC: 1
- Mobile: 1
- auto-generated claim slots
- one-shot operator provisioning

It must not be added to commercial UI selectors, commercial pricing, or commercial entitlement resolution merely because Customer Setup uses it as a provisioning plan.

## Cross-surface rule

A consumer may use `TABLET_PC_MOBILE_MANAGED` as a Customer Setup provisioning identifier only when it is operating inside the provisioning contract.

A consumer that needs a **vendible commercial SKU** must derive from `plan-catalog.canonical.json` and filter to `vendible=true`.

The Cloud Center customer-registration selector already follows this rule through `_canonical_license_plan_options()`, which reads the canonical commercial catalog and only emits vendible plans.

## LICFLOW3 persistence semantics

The `license_plans` table introduced by migration `0003_plan_based_provisioning.sql` is an operational provisioning registry. Its legacy name must not be interpreted as a second commercial catalog.

Future work must not introduce commercial pricing or commercial SKU ownership into `license_plans`.

## Required invariants

- Commercial vendible set is exactly the canonical catalog's `vendible=true` set.
- `TABLET_PC_MOBILE_MANAGED` is absent from that commercial vendible set.
- Every provisioning plan has an explicit `commercialPlanId`; the starter maps to `TABLET_PC_MANAGED`.
- `licenses.plan` and `tenants.plan` must always be a commercial SKU.
- Customer Setup provisioning may support `TABLET_PC_MOBILE_MANAGED`.
- Worker and shared provisioning definitions must agree on the provisioning plan set.
- Commercial UI selectors must derive from the commercial catalog, never from Customer Setup provisioning definitions.
- No second commercial plan/price authority may be introduced.

## Certification consequence

This semantic separation closes the previously ambiguous interpretation of `TABLET_PC_MOBILE_MANAGED` without changing commercial pricing or creating a new product SKU.

G1 passes only when the permanent verifier proves these invariants against the current repository state.
