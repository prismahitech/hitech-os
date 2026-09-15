# PRISMA Mamastrophic MENU fix1

Corrige el selector de fases del menú interactivo.

## Fix

Antes el menú mostraba:

- `5) quick,full  combo comun`
- `6) all         todas las fases`

pero `Resolve-Phases` no aceptaba `5` ni `6` cuando venían dentro de listas como `1,5`.

Ahora acepta:

- `5`
- `6`
- `1,5`
- `discovery,5`
- `quick_full`
- `quick+full`
- `all`

## Política

- GPU default: `off`.
- No start.
- No kill.
- No DB.
- No deploy.
- Sólo instala `MENU.ps1` y esta documentación.

<!-- MAMSHOT_UNIVERSAL_MENU_NOTE_V1 -->
## GitHub fast path

The interactive local menu is unchanged. Hosted CI uses `.github/workflows/mamastrophic-universal-screenshots.yml` directly with typed inputs for surface, mode, workers, partial policy, and DeepScroll.

Do not add a second per-surface menu/engine for CI. Local menu orchestration and hosted GitHub orchestration are two entry surfaces over the same Mamastrophic core.
