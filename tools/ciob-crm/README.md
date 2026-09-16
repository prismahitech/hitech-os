# CIOB CRM Builder

Herramientas canónicas para evolucionar, generar y verificar el CRM comercial XLSX de CIOB sin acoplarlo al runtime de PRISMA.

## Estado actual

**CIOB CRM V3 está terminado y verificado.** El artefacto canónico persistente es:

`/CIOB CRM/CIOB_CRM_V3_FINAL.xlsx`

Identidad exacta V3:

- SHA-256: `054be2704261e44c93d548b84eaf56ca7a491a15591d527eb07c0d8577251b8e`
- Tamaño: `221187` bytes
- Prospectos preservados desde V2: `27`
- Fuente de verdad: `Seguimiento comercial`

El baseline V2 permanece inmutable en Library:

`/CIOB CRM/CIOB_CRM_V2_FINAL.xlsx`

- SHA-256: `e8eb06bcf05b88500c4733a9b54b11f355ce3a7c51773b062fefafab86b27bf9`
- Tamaño: `159678` bytes

## Scope

Todo el trabajo vive en `tools/ciob-crm/**`. No toca Tablet, PC, Mobile, POS, Chart Lab, Shared UI, Prisma DB, licensing, deployment, prisma-html ni runtime PRISMA.

## Layout

```text
tools/ciob-crm/
  AGENTS.md
  README.md
  CONTINUE_V3.md
  build/
    build_crm_v3.py
  config/
    crm_rules.json
  spec/
    CRM_V3_PLAN.md
  tests/
    verify_xlsx.py
    verify_v3_semantics.py
  evidence/
    CRM_V3_VERIFICATION.json
    CRM_V3_VERIFICATION.md
    render_ooxml_preview.py
  releases/
    CRM_V3_RELEASE_MANIFEST.json
  baseline/
    BASELINE_MANIFEST.json
```

## Cómo regenerar V3

1. Recuperar el baseline exacto de Library y comprobar tamaño + SHA-256.
2. Ejecutar `build/build_crm_v3.py` contra una copia del baseline, nunca contra el baseline original.
3. Conservar los cinco checkpoints: guardrails, intelligence, productivity, visual/dashboard y final candidate.
4. Ejecutar `tests/verify_xlsx.py` y `tests/verify_v3_semantics.py`.
5. Revisar Mi día, Dashboard, Base de contactos y Seguimiento comercial con el renderer de evidencia o con Excel.
6. Promover sólo un candidato que conserve los datos V2 y produzca la identidad de release esperada.

El builder trabaja incrementalmente sobre el OOXML de V2. `artifact_tool` fue intentado primero, pero el importador cerró el RPC/BrokenPipe con este baseline concreto; por contrato se detuvo el reintento repetitivo y se continuó con mutación OOXML conservadora usando sólo Python stdlib.

## V3 implementado

- Catálogos dinámicos autoexpandibles mediante nombres definidos.
- Dropdowns y validaciones suaves/cruzadas.
- Normalización de correo, teléfono y WhatsApp para duplicados.
- Protección de campos automáticos preservando captura y filtros.
- Motivo de pérdida/cierre, días en etapa e intentos consecutivos sin respuesta.
- Completitud contextual por etapa.
- Fecha, canal y acción siguiente sugeridos.
- Idioma y canal preferidos.
- Mi día priorizado por urgencia, temperatura, score y valor, con filtro por responsable.
- Acciones rápidas: WhatsApp, correo, web y registrar actividad.
- Base compacta mediante grupos/columnas colapsables.
- Paleta premium y badges discretos.
- Dashboard ejecutivo con cinco gráficos nativos.
- Seguimiento comercial conserva la autoridad de estatus, contacto, próxima fecha, próxima acción, motivo de cierre y días en etapa.

## Verificación final

- ZIP/OOXML íntegro y reabierto.
- 6 hojas requeridas.
- 2 tablas estructuradas principales.
- `tblProspectos = A6:AX506`.
- `tblSeguimiento = A6:P1006`.
- 27 nombres definidos; catálogos dinámicos incluidos.
- 37 reglas de validación.
- 19,258 fórmulas de hoja.
- 5 gráficos.
- 0 fórmulas con tokens `#REF!`, `#VALUE!`, `#NAME?`, `#DIV/0!`.
- Verificador oficial: PASS.
- Verificador semántico V3: PASS.
- Segundo build desde el mismo baseline: byte-identical.

## Principio

Más inteligencia debajo, menos fricción arriba. El operador captura lo mínimo y recibe prioridad, alertas, score, temperatura, siguiente acción y contexto comercial sin convertir el libro en una cabina de avión.

## Limpieza visual post-QA

- Filas vacías ya no muestran `0`, `31-dic-1899` ni otros cachés de fórmula.
- Los IDs de prospecto y actividad aparecen sólo cuando la fila tiene un registro real.
- `Actividad ID` y `Cambio etapa?` quedan ocultos en Seguimiento.
- Alturas de filas de tablas normalizadas para evitar geometría irregular.
- La limpieza forma parte del builder determinista; no es un parche manual al XLSX.
