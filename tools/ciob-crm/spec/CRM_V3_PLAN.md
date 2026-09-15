# CIOB CRM V3 — plan de fortalecimiento

Estado: PROPOSED
Base funcional: CIOB CRM V2
Objetivo: aumentar blindaje, velocidad operativa y calidad visual sin elevar la complejidad percibida.

## 1. Blindaje

- Catálogos de Configuración autoexpandibles.
- Validar porcentajes 0–100%, pesos no negativos, días enteros positivos y Score HOT > WARM.
- Validaciones cruzadas:
  - actividad => Fecha + ID prospecto;
  - próximo seguimiento >= fecha de actividad;
  - Negociación => valor potencial recomendado/obligatorio configurable;
  - Propuesta enviada => servicio potencial definido;
  - Cliente/Perdido/No viable => resultado/cierre coherente;
  - prospecto activo => siguiente acción o fecha.
- Validación suave de correo, teléfono, WhatsApp y URL.
- Normalización para duplicados por correo/teléfono/WhatsApp.
- Proteger celdas automáticas preservando filtros, orden y captura.

## 2. Inteligencia

- Motivo de pérdida/cierre.
- Días en etapa.
- Intentos consecutivos sin respuesta.
- Completitud contextual por etapa.
- Próxima fecha sugerida según resultado.
- Canal sugerido según historial/canal preferido.
- Siguiente acción sugerida enriquecida.

## 3. Productividad

- Mi día priorizado:
  1. Vencido + HOT
  2. Vencido
  3. Hoy + HOT
  4. Hoy
  5. Próximo
  6. HOT sin fecha
  7. WARM sin fecha
  8. datos incompletos
  9. posibles duplicados
- Orden secundario: Score desc, Valor potencial desc.
- Selector de Responsable.
- Accesos de un clic: WhatsApp, correo, web y registrar actividad.
- Campos nuevos de bajo costo:
  - Idioma preferido.
  - Canal preferido.

## 4. Visual premium

- Reducir densidad visible de Base de contactos.
- Grupos colapsables: contacto, perfil empresa, oportunidad, inteligencia.
- Núcleo visible aproximado:
  Empresa | Contacto | Cargo | Teléfono | Correo | Temp. | Prioridad | Estatus | Próx. fecha | Acción | Score | Valor | Responsable | Alerta
- Paleta funcional:
  - navy: navegación/títulos;
  - blanco: captura;
  - azul grisáceo tenue: automático;
  - dorado: acción/próximo;
  - rojo: problema;
  - verde: éxito.
- HOT/WARM/COLD y alertas como badges discretos.
- Dashboard ejecutivo:
  Pipeline | Ponderado | HOT | Vencidos | Clientes | Conversión
  + funnel + temperatura + salud de seguimiento + fuentes + motivos de pérdida.

## 5. No objetivos

- No agregar docenas de etapas MQL/SQL innecesarias.
- No crear una hoja por vendedor.
- No duplicar conceptos como prioridad/interés/temperatura.
- No VBA por defecto.
- No tocar runtime PRISMA.

## Definition of done

- XLSX abre correctamente.
- No #REF!, #VALUE!, #NAME?, #DIV/0! ni referencias rotas en zonas clave.
- Catálogos y validaciones operan en filas nuevas.
- Fórmulas automáticas están protegidas.
- Seguimiento gobierna último contacto, próxima fecha, próxima acción y estatus.
- Mi día presenta una cola accionable y priorizada.
- Dashboard es legible y ejecutivo.
- Revisión visual de cuatro hojas clave aprobada.
