# CIOB CRM V3 — continuation contract

Use this file when resuming in a new ChatGPT conversation.

## Canonical sources

1. `tools/ciob-crm/AGENTS.md`
2. `tools/ciob-crm/README.md`
3. `tools/ciob-crm/spec/CRM_V3_PLAN.md`
4. `tools/ciob-crm/config/crm_rules.json`
5. `tools/ciob-crm/baseline/BASELINE_MANIFEST.json`
6. `tools/ciob-crm/tests/verify_xlsx.py`

## Exact baseline

Retrieve from ChatGPT Library:

`/CIOB CRM/CIOB_CRM_V2_FINAL.xlsx`

Verify before use:

- bytes: `159678`
- SHA-256: `e8eb06bcf05b88500c4733a9b54b11f355ce3a7c51773b062fefafab86b27bf9`

If identity differs, stop rather than silently using another workbook.

## Mission

Finish V3 completely. Do not stop after scaffolding or partial implementation.

Implement all approved V3 improvements in `spec/CRM_V3_PLAN.md`, including:
- stronger validations and dynamic configuration,
- normalized duplicate detection,
- protected automatic fields,
- loss/closure reason,
- days in stage,
- no-response attempts,
- contextual completeness,
- suggested follow-up date/channel/action,
- prioritized Mi día,
- owner selector and quick actions,
- preferred language/channel,
- compact/collapsible Base layout,
- cleaner premium visual system,
- executive dashboard,
- final structural and visual QA.

## Execution safety

- Do not rebuild the workbook from scratch unless the existing file is provably unrecoverable.
- Work incrementally from V2.
- Create checkpoints after each major layer: guardrails, intelligence, productivity, visual/dashboard.
- If artifact_tool RPC/BrokenPipe fails, do not repeat it indefinitely; change execution strategy while preserving the last checkpoint.
- Keep the original V2 immutable.
- Do not touch PRISMA product/runtime surfaces outside `tools/ciob-crm`.
- Do not declare PASS until the final XLSX is exported, reopened/verified, structurally clean and visually reviewed.
