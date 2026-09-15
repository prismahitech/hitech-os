# PRISMA Vertical — Servicios Profesionales y Corporativos

**ID canónico:** `professional_corporate_services`  
**Capability de Factory Ledger:** `verticals.professional_corporate_services`  
**Estado:** `draft / architecture-contract only`  
**Mercado:** `professional_services`

## 1. Propósito

Este vertical adapta PRISMA para firmas que venden conocimiento, acompañamiento y ejecución coordinada en vez de depender de una venta de mostrador como objeto principal.

Aplica de forma general a consultorías, firmas de servicios corporativos, despachos multidisciplinarios, servicios legales/corporativos, contables/fiscales, laborales/RH, financieros, back office, compliance, gestión documental, soft landing y market entry.

**No es un vertical específico para CIOB ni para una firma concreta.** CIOB puede ser un caso de uso comercial posterior, pero la autoridad del vertical debe permanecer neutral y reusable.

## 2. Regla de arquitectura

PRISMA Core conserva identidad, negocio, operadores, eventos, auditoría, sincronización, exportación y capacidades comunes. El vertical agrega semántica de cliente profesional, expediente, engagement, documentos, tareas, vencimientos, responsables, entregables, evidencia, aprobaciones y servicios recurrentes.

Regla operativa:

- **Tablet opera y captura:** intake, datos acotados del cliente, reunión, checklist, recepción documental y avance de servicio.
- **PC gobierna:** expediente completo, engagement, responsables, workflow, contratos/propuestas como referencia documental, vencimientos, servicios recurrentes, evidencia, configuración y reportes.
- **Mobile supervisa:** alertas, aprobaciones, riesgo, vencimientos, próximos pasos, carga ejecutiva y resumen.
- **Core registra:** identidad, actores, auditoría, sync y contratos comunes.
- **Control audita:** evidencia, autoridad y trazabilidad cuando aplique.

## 3. Objeto operativo principal

El recorrido genérico es:

`Prospecto / Cliente → Diagnóstico → Propuesta / Engagement → Onboarding → Expediente → Ejecución → Entregables → Servicio recurrente → Renovación / Cierre`

No todos los negocios usan todas las etapas. El perfil vertical habilita capacidades y especializaciones sin obligar a un despacho a usar módulos ajenos a su práctica.

## 4. Familias de especialización

Las siguientes familias viven dentro del vertical. No son certificaciones profesionales ni implican que PRISMA ejecute la práctica regulada:

1. **Consultoría empresarial**
2. **Servicios corporativos**
3. **Contabilidad y soporte fiscal**
4. **Legal y corporativo**
5. **Recursos humanos y laboral**
6. **Asesoría financiera**
7. **Back office administrado**
8. **Compliance y gestión documental**
9. **Soft landing / market entry**
10. **Coordinación de especialistas y aliados externos**

El vertical separado `verticals.accounting_management` continúa existiendo de manera independiente para escenarios donde contabilidad y gestión constituyen el centro del producto. Este vertical no lo reemplaza ni lo absorbe.

## 5. Entidades verticales

| Entidad | Significado | Autoridad principal | Tablet | Mobile |
|---|---|---|---|---|
| ClientOrganization | Organización cliente atendida | PC | lectura/captura acotada | resumen |
| ClientContact | Persona de contacto | PC | captura acotada | lectura |
| ServiceEngagement | Relación de servicio contratada o propuesta | PC | consulta/avance | resumen |
| CaseFile | Expediente o caso de trabajo | PC | consulta/avance | resumen |
| DocumentRequirement | Documento requerido, recibido, revisado o pendiente | PC | recepción | alerta |
| WorkItem | Tarea operativa | PC | ejecutar/actualizar | supervisar |
| DeadlineCommitment | Fecha límite o compromiso | PC | consultar | alertar |
| ResponsibilityAssignment | Responsable interno o externo | PC | consultar | supervisar |
| ApprovalDecision | Aprobación controlada | PC | solicitar | decidir si la política lo permite |
| EvidenceRecord | Evidencia de ejecución | PC | adjuntar evidencia operativa | consultar |
| RecurringService | Servicio periódico | PC | consulta | resumen |
| ExternalAdvisor | Especialista, aliado o tercero coordinado | PC | consulta | resumen |
| ProposalContractReference | Referencia a propuesta o contrato | PC | consulta | resumen |

## 6. Capacidades

Capacidades mínimas del vertical:

- `professional_services.clients`
- `professional_services.engagements`
- `professional_services.documents`
- `professional_services.tasks`
- `professional_services.deadlines`
- `professional_services.approvals`
- `professional_services.evidence`
- `professional_services.recurring_services`

Capacidades recomendadas para el perfil completo:

- expedientes y casos;
- responsables y colaboradores externos;
- propuestas/contratos como referencias documentales;
- indicadores de avance y riesgo;
- historial de actividad;
- alertas y próximos pasos;
- seguimiento de renovaciones.

## 7. Navegación por surface

### Tablet

Entrada principal: **Clientes**

Navegación recomendada:

- Clientes
- Expediente
- Documentos
- Tareas
- Vencimientos
- Servicios
- Pendientes por enviar

Tablet **no** debe convertirse en back office. Configuración profunda, matrices de servicio, contratos complejos, reporting consolidado, administración de permisos y gobierno de terceros permanecen fuera.

### PC

- Clientes
- Expedientes
- Servicios
- Documentos
- Tareas y responsables
- Vencimientos
- Propuestas y contratos
- Servicios recurrentes
- Aliados externos
- Evidencia y auditoría
- Reportes
- Configuración

### Mobile

- Resumen
- Alertas
- Aprobaciones
- Vencimientos
- Clientes en riesgo
- Próximas acciones
- Servicios recurrentes
- Actividad reciente

Mobile supervisa. No sustituye el gobierno PC.

## 8. Eventos mínimos

Los eventos verticales usan namespace `professional_services.*`. Como mínimo deben existir eventos para:

- alta/actualización de cliente;
- apertura de engagement;
- apertura de expediente;
- solicitud y recepción de documento;
- asignación y cierre de tarea;
- creación y riesgo de vencimiento;
- solicitud y resolución de aprobación;
- adjunto de evidencia;
- programación de servicio recurrente;
- asignación de aliado externo.

Todo cambio sensible conserva actor, contexto, fecha y rastro auditable.

## 9. Permisos

La autorización se separa de la navegación. Ver un módulo no implica poder ejecutar una acción sensible.

Permisos mínimos:

- ver/editar cliente;
- ver/administrar engagement;
- ver/administrar expediente;
- solicitar/recibir documentos;
- asignar/completar tareas;
- administrar vencimientos;
- solicitar/decidir aprobaciones;
- adjuntar/ver evidencia;
- administrar servicios recurrentes;
- administrar aliados;
- consultar reportes;
- exportar cuando la política lo permita.

Tablet nunca otorga permisos.

## 10. Offline y sincronización

El vertical es **restricted offline**.

Tablet puede continuar únicamente con información local previamente autorizada y con acciones que no dependan de una decisión externa inmediata. Puede:

- capturar intake;
- registrar avance;
- recibir un documento como pendiente de revisión;
- actualizar tareas permitidas;
- adjuntar evidencia local;
- marcar elementos pendientes por enviar.

Debe bloquear o diferir:

- decisiones que requieran autoridad remota;
- cambios de permisos;
- cierre contractual definitivo;
- aprobación sensible no autorizada;
- gobierno de configuración;
- consolidación multi-entidad.

El usuario siempre debe ver si algo está **guardado localmente**, **pendiente por enviar** o **requiere revisión**.

## 11. KPIs

KPIs genéricos y no regulatorios:

- clientes activos;
- engagements abiertos;
- tiempo promedio de onboarding;
- tareas vencidas;
- vencimientos próximos;
- documentos faltantes;
- porcentaje de expedientes completos;
- tiempo de ciclo por servicio;
- servicios recurrentes por vencer;
- carga por responsable;
- bloqueadores por cliente;
- aprobaciones pendientes;
- tasa de renovación;
- tiempo desde solicitud hasta entrega.

## 12. Criterios de aceptación

1. El usuario identifica cliente, etapa y siguiente acción sin depender de memoria externa.
2. Todo expediente muestra responsables, documentos, tareas, vencimientos y evidencia relevante.
3. Tablet permite operación acotada sin exponer gobierno profundo.
4. PC concentra autoridad operativa y configuración profunda.
5. Mobile resume y supervisa sin convertirse en un duplicado de PC.
6. Los estados empty/loading/error/success/disabled/offline/pending_sync están definidos.
7. Las acciones sensibles exigen permiso y dejan evidencia.
8. La pérdida de conexión no convierte pendientes en completados.
9. Ninguna especialización del vertical se presenta como certificación legal, fiscal, contable, laboral o regulatoria.
10. El vertical puede deshabilitarse sin contaminar otros giros.

## 13. No demuestra

Esta especificación **no demuestra**:

- implementación runtime en Tablet, PC o Mobile;
- cumplimiento legal/fiscal/contable/laboral;
- certificación profesional;
- integración SAT/PAC;
- ejecución de trámites;
- portal cliente;
- producción o deployment;
- readiness de un cliente concreto.

Es una **fuente de diseño funcional y contractual** para construir o demostrar el vertical posteriormente.

## 14. Guía para demo HTML

Una demo comercial puede proyectar este vertical sobre el lenguaje visual de Atlasfin sin convertir Atlasfin en navegación pública.

Para una primera demo rápida se recomiendan dos vistas:

- **PC — Operations Center:** cliente, etapa, expediente, workstreams, documentos, responsables, vencimientos, evidencia, bloqueadores y siguiente acción.
- **Mobile — Executive Companion:** alertas, aprobaciones, clientes en riesgo, vencimientos y próximos pasos.

La URL de demo debe ser independiente y no exponer botones o enlaces de regreso a Atlasfin. Atlasfin funciona como backstage visual y biblioteca de patrones, no como destino del prospecto.
