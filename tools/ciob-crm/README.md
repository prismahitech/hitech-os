# CIOB CRM Builder

Repositorio fuente para evolucionar y verificar el CRM comercial XLSX de CIOB sin acoplarlo al runtime de PRISMA.

## Scope

- Ruta canónica: `tools/ciob-crm/`
- No modifica Tablet, PC, Mobile, Chart Lab, Shared UI, Prisma DB, licenciamiento ni runtime de `terminal-de-venta-system`.
- El XLSX es un artefacto generado/versionado, no la única fuente de verdad.
- Las reglas comerciales, validaciones y criterios de QA viven como texto/configuración revisable en Git.

## Layout

```text
tools/ciob-crm/
  README.md
  AGENTS.md
  config/
    crm_rules.json
  spec/
    CRM_V3_PLAN.md
  tests/
    verify_xlsx.py
  baseline/
    CIOB_CRM_V2_FINAL.xlsx     # se incorpora después del gate
  output/
    CIOB_CRM_V3.xlsx           # generado, no fuente canónica
```

## Workflow

1. Preservar un baseline V2 inmutable.
2. Cambiar reglas/spec en commits pequeños.
3. Generar un XLSX candidato.
4. Ejecutar `tests/verify_xlsx.py`.
5. Verificar visualmente Mi día, Dashboard, Base y Seguimiento.
6. Sólo entonces promover el XLSX como versión entregable.

## Design principle

Más inteligencia debajo, menos fricción arriba. El operador debe capturar lo mínimo y recibir automáticamente prioridades, alertas, score, temperatura, siguiente acción y contexto comercial.
