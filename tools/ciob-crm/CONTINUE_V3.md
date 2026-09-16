# CIOB CRM V3 — continuation contract

V3 está terminada y verificada. Para V4 o un patch futuro, partir del V3 canónico; no volver a inventar V3 desde memoria del chat.

## Autoridades

1. `tools/ciob-crm/AGENTS.md`
2. `tools/ciob-crm/README.md`
3. `tools/ciob-crm/spec/CRM_V3_PLAN.md`
4. `tools/ciob-crm/config/crm_rules.json`
5. `tools/ciob-crm/build/build_crm_v3.py`
6. `tools/ciob-crm/tests/verify_xlsx.py`
7. `tools/ciob-crm/tests/verify_v3_semantics.py`
8. `tools/ciob-crm/evidence/CRM_V3_VERIFICATION.json`
9. `tools/ciob-crm/releases/CRM_V3_RELEASE_MANIFEST.json`

## Workbook canónico V3

ChatGPT Library:

`/CIOB CRM/CIOB_CRM_V3_FINAL.xlsx`

Verificar antes de cualquier mutación:

- bytes: `220348`
- SHA-256: `f5a39cf8be5f62e402dde98d201410df9830cfab81cc886bcf7315c08250ce9f`

Si la identidad difiere, detenerse y reconciliar. No usar otro archivo silenciosamente.

## Baseline V2 inmutable

`/CIOB CRM/CIOB_CRM_V2_FINAL.xlsx`

- bytes: `159678`
- SHA-256: `e8eb06bcf05b88500c4733a9b54b11f355ce3a7c51773b062fefafab86b27bf9`

V2 queda como baseline histórico y fuente de reconstrucción determinista. Nunca sobrescribirlo.

## Reconstrucción de emergencia

Si V3 se pierde o se corrompe, `build/build_crm_v3.py` reconstruye V3 incrementalmente desde una copia del V2 exacto y genera cinco checkpoints. Un rebuild correcto debe terminar en `220348` bytes y SHA-256 `f5a39cf8be5f62e402dde98d201410df9830cfab81cc886bcf7315c08250ce9f`, además de pasar ambos verificadores.

## Regla futura

Toda V4 o corrección parte del V3 verificado, preserva Seguimiento comercial como fuente de verdad y se mantiene dentro de `tools/ciob-crm/**` salvo autoridad separada. No tocar Tablet, PC, Mobile, POS, Chart Lab, Shared UI, Prisma DB, licensing, deployment, prisma-html ni runtime PRISMA.