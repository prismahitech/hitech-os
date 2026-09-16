# CIOB CRM V3 — Final Evidence

**Status:** PASS  
**Branch:** `feat/ciob-crm-builder`  
**Final artifact:** `CIOB_CRM_V3_FINAL.xlsx`  
**SHA-256:** `f5a39cf8be5f62e402dde98d201410df9830cfab81cc886bcf7315c08250ce9f`  
**Size:** `220348` bytes

## Baseline immutability

- Library source: `/CIOB CRM/CIOB_CRM_V2_FINAL.xlsx`
- Size: `159678` bytes
- SHA-256: `e8eb06bcf05b88500c4733a9b54b11f355ce3a7c51773b062fefafab86b27bf9`
- Result: unchanged and identity-verified before and after V3.

## Final verification

- Official `tests/verify_xlsx.py`: **PASS**
- `tests/verify_v3_semantics.py`: **PASS**
- OOXML ZIP integrity: **PASS**
- XML parse: **PASS**
- Required sheets: **PASS**
- Tables: `2`
- Charts: `5`
- Data validations: `37`
- Defined names: `27`
- Worksheet formulas: `17758`
- Broken-reference formula count: `0`
- Existing literal data preserved: **PASS**
- Seguimiento comercial remains source of truth: **PASS**
- Second build byte-identical to final candidate: **PASS**

## Checkpoints

- `01_guardrails.xlsx` — `167620` bytes — `a49e0ae1f11313c1cb02aeee042f9867245e8f8c50941a94766b1a1b096646ae`
- `02_intelligence.xlsx` — `215585` bytes — `f8cf41d4f77d598fbd9de10b5eee7715c8e409cb1cb0d04b8eb48d15fc47994d`
- `03_productivity.xlsx` — `217192` bytes — `4c8473482f052718b484f1720799fbae318ddb22aa80e0012c5546e27886342e`
- `04_visual_dashboard.xlsx` — `220348` bytes — `f5a39cf8be5f62e402dde98d201410df9830cfab81cc886bcf7315c08250ce9f`
- `05_final_candidate.xlsx` — `220348` bytes — `f5a39cf8be5f62e402dde98d201410df9830cfab81cc886bcf7315c08250ce9f`

## Visual QA

- **Mi día:** PASS — prioritized queue, owner selector, KPIs and quick actions.
- **Dashboard:** PASS — executive KPI hierarchy and five native XLSX charts.
- **Base de contactos:** PASS — compact visible nucleus with grouped/collapsible secondary fields.
- **Seguimiento comercial:** PASS — linear activity log preserved; closure reason added without displacing source-of-truth behavior.

## Data preservation

- Existing contacts preserved: `27`.
- Literal V2 data preserved in the covered Base de contactos and Seguimiento ranges.
- V2 baseline file remains `159678` bytes with its original SHA-256.

## Tool continuity

`artifact_tool` was attempted first and failed with RPC closed/BrokenPipe while importing this V2 workbook. Per `CONTINUE_V3.md`, retries were stopped and the last good baseline was preserved. The successful path uses conservative OOXML ZIP/XML mutation with Python stdlib only. No `openpyxl`, pandas or LibreOffice was used.