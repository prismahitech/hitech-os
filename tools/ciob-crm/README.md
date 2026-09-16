# CIOB CRM Builder

Repositorio fuente para evolucionar y verificar el CRM comercial XLSX de CIOB sin acoplarlo al runtime de PRISMA.

## Scope

- Ruta canónica: `tools/ciob-crm/`
- No modifica Tablet, PC, Mobile, Chart Lab, Shared UI, Prisma DB, licenciamiento ni runtime de `terminal-de-venta-system`.
- El XLSX es un artefacto generado/versionado, no la única fuente de verdad.
- Las reglas comerciales, validaciones y criterios de QA viven como texto/configuración revisable en Git.

## Baseline V2

El baseline exacto está preservado de forma persistente en ChatGPT Library:

`/CIOB CRM/CIOB_CRM_V2_FINAL.xlsx`

Identidad esperada:

- SHA-256: `e8eb06bcf05b88500c4733a9b54b11f355ce3a7c51773b062fefafab86b27bf9`
- Tamaño: `159678` bytes
- Nombre canónico futuro en repo: `baseline/CIOB_CRM_V2_FINAL.xlsx`

El conector GitHub usado en esta sesión no acepta una referencia de archivo binario local directamente para crear el blob. No se debe fingir que el binario ya está en Git. El manifiesto de baseline permite recuperar el archivo persistente y comprobar su identidad antes de construir V3.

## Layout

```text
tools/ciob-crm/
  README.md
  AGENTS.md
  CONTINUE_V3.md
  config/
    crm_rules.json
  spec/
    CRM_V3_PLAN.md
  tests/
    verify_xlsx.py
  baseline/
    BASELINE_MANIFEST.json
    CIOB_CRM_V2_FINAL.xlsx     # destino canónico cuando se materialice el binario
  output/
    CIOB_CRM_V3.xlsx           # generado, no fuente canónica
```

## Workflow

1. Recuperar el baseline V2 persistente y verificar SHA-256 + tamaño.
2. Preservarlo inmutable.
3. Cambiar reglas/spec en commits pequeños.
4. Generar un XLSX candidato por checkpoints.
5. Ejecutar `tests/verify_xlsx.py`.
6. Verificar visualmente Mi día, Dashboard, Base y Seguimiento.
7. Sólo entonces promover el XLSX como versión entregable.

## Design principle

Más inteligencia debajo, menos fricción arriba. El operador debe capturar lo mínimo y recibir automáticamente prioridades, alertas, score, temperatura, siguiente acción y contexto comercial.
