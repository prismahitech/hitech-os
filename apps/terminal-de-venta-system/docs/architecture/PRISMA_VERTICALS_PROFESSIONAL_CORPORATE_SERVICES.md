# PRISMA Vertical - Servicios Profesionales y Corporativos

## Estado

- verticalId: `professional_corporate_services`
- nombre visible: **Servicios Profesionales y Corporativos**
- market: `professional_services`
- status: `draft`
- capability authority: `verticals.professional_corporate_services`
- relación con `verticals.accounting_management`: **vertical separada; no reemplaza, absorbe ni renombra Contabilidad y gestión**
- alcance actual: arquitectura, contratos y documentación; **sin runtime de producto certificado**

## 1. Qué tipo de negocio cubre

Este vertical sirve como base para firmas que venden conocimiento, acompañamiento, gestión, cumplimiento documental o servicios corporativos recurrentes.

Ejemplos no exhaustivos:

- consultoría empresarial;
- servicios corporativos;
- despachos multidisciplinarios;
- asesoría legal/corporativa;
- contabilidad y soporte fiscal como especialización;
- recursos humanos y laboral;
- asesoría financiera;
- back office administrado;
- compliance y gestión documental;
- soft landing / market entry;
- coordinación de terceros profesionales.

La vertical es deliberadamente general. No debe nombrar, codificar ni depender de un cliente específico.

## 2. Regla madre

PRISMA organiza el ciclo operativo del servicio profesional:

`Prospecto / cliente -> diagnóstico -> propuesta -> engagement -> expediente -> tareas y responsables -> documentos -> entregables -> evidencia -> servicio recurrente -> seguimiento`

La especialidad profesional cambia, pero el significado operativo central permanece.

## 3. Separación de surfaces

### Tablet opera y captura

Tablet sirve para trabajo operativo acotado:

- alta o consulta rápida de cliente;
- intake de reunión;
- levantamiento de necesidades;
- checklist;
- recepción o confirmación de documentos;
- captura de avance;
- registro de observaciones;
- evidencia operativa;
- tareas asignadas;
- pendientes por sincronizar.

Tablet no administra configuraciones profundas ni decisiones sensibles de gobierno.

### PC gobierna

PC es la surface principal de administración:

- expediente completo;
- engagement y servicios contratados;
- pipeline operativo;
- propuestas y contratos referenciados;
- flujos y checklists;
- documentos y requisitos;
- responsables internos;
- terceros y aliados;
- vencimientos;
- aprobaciones;
- servicios recurrentes;
- evidencia y auditoría;
- reportes y configuración.

### Mobile supervisa

Mobile no replica PC. Su función es supervisión ejecutiva:

- alertas;
- vencimientos;
- aprobaciones permitidas;
- clientes en riesgo;
- próximos compromisos;
- bloqueadores;
- carga de trabajo resumida;
- avance de engagements;
- indicadores ejecutivos.

### Core registra; Control audita

El Core conserva identidades y eventos compartidos. Control conserva trazabilidad y auditoría. La vertical no debe duplicar estos mecanismos.

## 4. Entidades de significado vertical

Las siguientes entidades son extensiones del giro, no campos universales del Core:

- `ClientOrganization`: organización cliente.
- `ServiceEngagement`: relación o encargo de servicio.
- `CaseFile`: expediente operativo.
- `DocumentRequirement`: documento requerido o recibido.
- `TaskAssignment`: tarea y responsable.
- `DeadlineCommitment`: fecha límite, compromiso o vencimiento.
- `DeliverableEvidence`: entregable o evidencia asociada.
- `ExternalAdvisor`: tercero, especialista o aliado externo.

No implican que PRISMA certifique la profesión de quien presta el servicio.

## 5. Familias de especialización

Una instalación puede activar una o varias familias:

1. `business_consulting`
2. `corporate_legal_support`
3. `accounting_fiscal_support`
4. `hr_labor_support`
5. `finance_advisory`
6. `managed_back_office`
7. `compliance_document_management`
8. `soft_landing_market_entry`

Estas familias cambian formularios, checklists, lenguaje, documentos y reportes. No cambian la identidad canónica del vertical.

## 6. Capacidades iniciales

- `professional_services.clients`
- `professional_services.engagements`
- `professional_services.documents`
- `professional_services.tasks`
- `professional_services.deadlines`
- `professional_services.approvals`
- `professional_services.evidence`
- `professional_services.recurring_services`
- `professional_services.proposals_contracts`
- `professional_services.external_advisors`
- `professional_services.intake`
- `professional_services.case_management`

## 7. Navegación objetivo por surface

### Tablet

`Clientes -> Expedientes -> Diagnóstico -> Checklists -> Documentos -> Tareas -> Pendientes por enviar`

### PC

`Clientes -> Expedientes -> Servicios -> Propuestas y contratos -> Flujos -> Documentos -> Responsables -> Vencimientos -> Servicios recurrentes -> Evidencia -> Reportes -> Configuración`

### Mobile

`Hoy -> Clientes en riesgo -> Alertas -> Aprobaciones -> Vencimientos -> Próximas acciones -> Resumen ejecutivo`

## 8. Eventos mínimos

- `professional_services.client.created`
- `professional_services.intake.completed`
- `professional_services.engagement.opened`
- `professional_services.engagement.status_changed`
- `professional_services.document.received`
- `professional_services.document.requested`
- `professional_services.task.assigned`
- `professional_services.task.completed`
- `professional_services.deadline.at_risk`
- `professional_services.approval.requested`
- `professional_services.approval.completed`
- `professional_services.deliverable.recorded`
- `professional_services.recurring_service.scheduled`
- `professional_services.external_advisor.assigned`

## 9. Permisos de referencia

- `professional_services.client.view`
- `professional_services.client.edit`
- `professional_services.intake.capture`
- `professional_services.engagement.view`
- `professional_services.engagement.manage`
- `professional_services.document.view`
- `professional_services.document.record`
- `professional_services.task.manage`
- `professional_services.deadline.manage`
- `professional_services.approval.request`
- `professional_services.approval.complete`
- `professional_services.evidence.record`
- `professional_services.recurring_service.manage`
- `professional_services.external_advisor.manage`
- `professional_services.audit.view`

## 10. Offline y sincronización

La política inicial es `restricted`.

Tablet puede conservar localmente intake, checklist, observaciones, recepción documental y progreso cuando la política del engagement lo permita.

No debe concluir offline, por defecto:

- aprobaciones sensibles;
- cambios de responsables con privilegios;
- cierre contractual;
- decisiones que impliquen certificación legal/fiscal/laboral;
- configuración global;
- acciones cuyo resultado dependa de una fuente externa vigente.

Toda captura local pendiente debe mostrar estado humano claro y entrar al mecanismo compartido de sincronización.

## 11. KPIs

- clientes activos;
- engagements activos;
- tiempo de onboarding;
- documentos pendientes;
- tareas vencidas;
- compromisos próximos;
- bloqueadores por cliente;
- entregables completados;
- servicios recurrentes próximos;
- carga por responsable;
- tiempo de ciclo por tipo de servicio;
- porcentaje de expedientes completos.

## 12. Criterios de aceptación

1. Un usuario entiende en menos de cinco segundos qué requiere atención.
2. Cada cliente tiene un expediente único y trazable.
3. Cada engagement declara responsable, estado, próximos pasos y evidencia.
4. Tablet no expone administración pesada.
5. PC conserva gobierno profundo.
6. Mobile resume y supervisa; no duplica PC.
7. Un documento o tarea puede relacionarse con cliente, engagement, responsable y fecha.
8. Los estados offline y pendientes son explícitos.
9. Las especializaciones no contaminan el Core.
10. No se presentan afirmaciones de certificación profesional que PRISMA no pueda probar.

## 13. Lo que este vertical no prueba

Esta arquitectura no prueba:

- que exista hoy una aplicación runtime para este giro;
- que PRISMA preste servicios legales, contables, fiscales, laborales o financieros;
- que una firma usuaria tenga licencias o certificaciones profesionales;
- cumplimiento normativo por sí mismo;
- presentación, timbrado, declaraciones, trámites o actuaciones ante autoridades;
- exactitud jurídica o fiscal de contenido capturado.

## 14. Relación con futuras demos

Una demo HTML puede proyectar este vertical usando el lenguaje visual canónico de PRISMA/Atlasfin.

La demo es una **proyección de producto** y debe permanecer desacoplada del Atlas público: puede reutilizar materiales, patrones y componentes, pero no necesita exponer navegación hacia el cockpit Atlasfin.

La demo tampoco eleva el estado de la vertical a runtime implementado.
