# CIOB CRM local agent contract

Este directorio es una isla de tooling comercial. No concede autoridad para tocar otras superficies del monorepo.

## Allowed scope

- `tools/ciob-crm/**`
- Baseline XLSX del CRM CIOB.
- Especificaciones, reglas, verificadores y evidencia del CRM.

## Forbidden without separate authority

- `apps/terminal-de-venta-system/**`
- `products/**`
- `prisma-html/**`
- Prisma schema, DB, sync, licensing, auth, deployment o runtime.
- Workflows globales y Factory Ledger salvo tarea de gobierno explícita.

## Working rules

1. Preservar el baseline; nunca editarlo destructivamente.
2. Construir cambios por capas: blindaje, inteligencia, productividad, visual.
3. No declarar PASS sólo porque el XLSX abre.
4. Verificar estructura ZIP/XML, hojas, tablas, validaciones, nombres definidos, fórmulas y errores de referencia.
5. Para cambios visuales, revisar renders/capturas de las hojas clave.
6. Mantener el archivo intuitivo: menos columnas visibles, grupos colapsables y colores con función semántica.
7. Evitar macros VBA salvo necesidad explícitamente aprobada.
8. El historial de Seguimiento comercial sigue siendo la fuente de verdad.
