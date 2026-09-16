# CIOB CRM V3 — plan y cierre

Estado: **PASS_FINAL_VERIFIED**  
Base funcional: CIOB CRM V2 exacto  
Artefacto final: `/CIOB CRM/CIOB_CRM_V3_FINAL.xlsx`

## Decisión de implementación

V3 se construyó **incrementalmente sobre el OOXML del V2**, preservando el baseline original y los datos existentes. No se reconstruyó el workbook desde cero. `artifact_tool` se intentó primero; ante RPC cerrado/BrokenPipe repetitivo se cambió de estrategia, como exige el contrato de continuidad, usando mutación OOXML conservadora con Python stdlib.

## 1. Blindaje completado

- Catálogos de Configuración autoexpandibles mediante nombres definidos dinámicos.
- Dropdowns reforzados para las 500 filas de prospectos y 1000 filas de actividades.
- Validaciones de porcentaje 0–100, pesos/días y reglas comerciales configurables heredadas + V3.
- Validaciones cruzadas en Seguimiento:
  - una actividad exige Fecha + ID prospecto + Actividad;
  - próximo seguimiento no puede ser anterior a la actividad;
  - Perdido/No viable exige motivo de cierre;
  - Cliente y Ganado se mantienen coherentes;
  - estatus avanzados disparan controles de servicio/valor/siguiente paso.
- Validación suave de correo, teléfono, WhatsApp y web.
- Duplicados normalizados por correo, teléfono y WhatsApp, más Empresa + Nombre.
- Campos automáticos protegidos; captura, filtros y orden permanecen operables.

## 2. Inteligencia comercial completada

- Motivo de pérdida/cierre gobernado por Seguimiento.
- Días en etapa.
- Intentos consecutivos sin respuesta.
- Completitud contextual distinta por etapa comercial.
- Fecha de seguimiento sugerida según último resultado.
- Canal sugerido según preferencia e historial.
- Acción siguiente sugerida enriquecida.
- Idioma preferido y canal preferido.
- Score contextual y temperatura HOT/WARM/COLD conservados/mejorados.

## 3. Productividad completada

Mi día prioriza exactamente:

1. Vencido + HOT.
2. Vencido.
3. Hoy + HOT.
4. Hoy.
5. Próximo.
6. HOT sin fecha.
7. WARM sin fecha.
8. Datos incompletos.
9. Posibles duplicados.

Orden secundario: Score descendente y Valor potencial descendente.

Además:

- selector por Responsable;
- acciones rápidas de WhatsApp, correo, web y registrar actividad;
- cola compacta sin duplicar hojas por vendedor.

## 4. Visual premium completado

- Base de contactos con núcleo visible y grupos secundarios colapsables.
- Menor densidad visual.
- Paleta navy, blanco, azul grisáceo, dorado, rojo y verde.
- Temperatura/alertas tratadas como señales discretas.
- Mi día optimizado para operación diaria.
- Dashboard ejecutivo con KPIs y cinco gráficos nativos XLSX: pipeline/funnel, temperatura, salud de seguimiento, fuentes y motivos de pérdida.

## 5. Autoridad de datos

`Seguimiento comercial` sigue gobernando último contacto, próxima fecha, próxima acción, estatus, motivo de cierre, días en etapa e intentos sin respuesta. Base de contactos proyecta esa verdad, no la sustituye.

## 6. Checkpoints de construcción

1. `01_guardrails.xlsx`
2. `02_intelligence.xlsx`
3. `03_productivity.xlsx`
4. `04_visual_dashboard.xlsx`
5. `05_final_candidate.xlsx`

El candidato final y un segundo rebuild independiente resultaron byte-identical.

## Definition of done

- [x] Baseline V2 verificado: 159678 bytes + SHA-256 exacto.
- [x] Baseline V2 no alterado.
- [x] XLSX final exportado y reabierto.
- [x] Integridad ZIP/OOXML completa.
- [x] 6 hojas obligatorias.
- [x] 2 tablas estructuradas principales.
- [x] 27 nombres definidos.
- [x] 37 validaciones.
- [x] 17,758 fórmulas de hoja.
- [x] 5 gráficos.
- [x] Cero referencias rotas/tokens de error en fórmulas.
- [x] `tools/ciob-crm/tests/verify_xlsx.py`: PASS.
- [x] `tools/ciob-crm/tests/verify_v3_semantics.py`: PASS.
- [x] Revisión visual de Mi día, Dashboard, Base de contactos y Seguimiento comercial: PASS.
- [x] 27 contactos existentes preservados y literales V2 conservados.
- [x] Seguimiento comercial confirmado como fuente de verdad.
- [x] Build determinista confirmado.
- [x] Release persistida en Library.

## Identidad final

- Tamaño: `220348` bytes
- SHA-256: `f5a39cf8be5f62e402dde98d201410df9830cfab81cc886bcf7315c08250ce9f`