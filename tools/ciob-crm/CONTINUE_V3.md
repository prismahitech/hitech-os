# CIOB CRM — continuation contract

V3 está terminada y verificada. **No reconstruir V3 desde V2** en futuras sesiones salvo que exista evidencia de corrupción.

## Canonical sources

1. `tools/ciob-crm/AGENTS.md`
2. `tools/ciob-crm/README.md`
3. `tools/ciob-crm/config/crm_rules.json`
4. `tools/ciob-crm/spec/CRM_V3_PLAN.md`
5. `tools/ciob-crm/evidence/CRM_V3_VERIFICATION.json`
6. `tools/ciob-crm/releases/CRM_V3_RELEASE_MANIFEST.json`
7. `tools/ciob-crm/tests/verify_xlsx.py`

## Current workbook

Retrieve from ChatGPT Library:

`/CIOB CRM/CIOB_CRM_V3_FINAL.xlsx`

Verify before mutation:

- bytes: `95134`
- SHA-256: `3df440dafe2ed9e4f1c29220dbedb9627ec79553beb8226ba685dfe2981f01f0`

If identity differs, stop and reconcile rather than silently using another workbook.

## Baseline V2

`/CIOB CRM/CIOB_CRM_V2_FINAL.xlsx`

- bytes: `159678`
- SHA-256: `e8eb06bcf05b88500c4733a9b54b11f355ce3a7c51773b062fefafab86b27bf9`

V2 is historical baseline only.

## Future work rule

Any V4 or patch starts from verified V3, uses checkpoints, runs structural/error/visual QA, and stays inside `tools/ciob-crm` unless separate PRISMA authority explicitly expands scope.

Do not touch Tablet, PC, Mobile, Chart Lab, Shared UI, Prisma DB, licensing, deployment, terminal runtime or prisma-html for ordinary CIOB CRM changes.
