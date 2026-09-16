# CIOB CRM Builder

Repositorio fuente para evolucionar y verificar el CRM comercial XLSX de CIOB sin acoplarlo al runtime de PRISMA.

## Estado actual

**CIOB CRM V3 está generado y verificado.**

Artefacto canónico persistente:

`/CIOB CRM/CIOB_CRM_V3_FINAL.xlsx`

Identidad V3:

- SHA-256: `3df440dafe2ed9e4f1c29220dbedb9627ec79553beb8226ba685dfe2981f01f0`
- Tamaño: `95134` bytes
- Prospectos preservados desde V2: `27`
- Actividades históricas preservadas desde V2: `0`
- Fuente de verdad: `Seguimiento comercial`

El XLSX binario se conserva persistentemente fuera del historial Git y Git conserva reglas, contratos y evidencia verificable. No se debe afirmar que el binario vive dentro del repo mientras el conector no permita materializarlo de forma segura.

## Scope

- Ruta canónica: `tools/ciob-crm/`
- No modifica Tablet, PC, Mobile, Chart Lab, Shared UI, Prisma DB, licenciamiento ni runtime de `terminal-de-venta-system`.
- Las reglas comerciales, validaciones y criterios de QA viven como texto/configuración revisable en Git.
- El workbook final es un artefacto generado y verificado.

## Baseline V2

Baseline persistente:

`/CIOB CRM/CIOB_CRM_V2_FINAL.xlsx`

- SHA-256: `e8eb06bcf05b88500c4733a9b54b11f355ce3a7c51773b062fefafab86b27bf9`
- Tamaño: `159678` bytes

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
  evidence/
    CRM_V3_VERIFICATION.json
  releases/
    CRM_V3_RELEASE_MANIFEST.json
```

## V3 implementado

- Seguimiento comercial como fuente de verdad.
- Estatus, último contacto, próxima fecha y próxima acción automáticos.
- Score, HOT/WARM/COLD, alertas y pipeline ponderado.
- Días en etapa e intentos sin respuesta.
- Completitud contextual y advertencias de coherencia.
- Motivo de cierre/pérdida.
- Fecha, canal y siguiente acción sugeridos.
- Mi día priorizado con filtro por responsable y accesos rápidos.
- Idioma y canal preferidos.
- Configuración ampliada mediante tablas de catálogos.
- Dashboard ejecutivo con funnel y temperatura.
- Detección de duplicados por correo, teléfono, WhatsApp y Empresa + Nombre.
- Validaciones cruzadas en Seguimiento.
- Diseño premium, campos automáticos visualmente separados y navegación rápida.

## Capacidad preparada

Para estabilidad del XLSX generado:

- `80` filas de prospectos presembradas.
- `60` filas de actividades presembradas.
- Ambas zonas son tablas estructuradas. El builder debe ampliarlas antes de llegar al límite, en lugar de copiar fórmulas manualmente.

## Verificación V3

- ZIP/OOXML íntegro.
- 6 hojas requeridas.
- 17 tablas estructuradas.
- 2723 fórmulas.
- 17 reglas de validación.
- 0 errores `#REF!`, `#VALUE!`, `#NAME?`, `#DIV/0!`, `#N/A` en el escaneo final.
- `tblProspectos = A6:AW86`.
- `tblSeguimiento = A6:Q66`.
- Seguimiento conserva 366 fórmulas y 6 dropdowns propios.
- Revisión visual de Mi día, Dashboard, Base de contactos y Seguimiento comercial completada.

## Principio de diseño

Más inteligencia debajo, menos fricción arriba. El operador debe capturar lo mínimo y recibir automáticamente prioridades, alertas, score, temperatura, siguiente acción y contexto comercial.
