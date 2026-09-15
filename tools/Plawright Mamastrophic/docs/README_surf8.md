# playmam arr5

Centralized PRISMA Playwright Surfaces runner.

arr4 keeps the Mamastrophic folder as the official motor and restores the ergonomic flow that was missing:

- surface selector via `-Surface`;
- honest `PASS` / `PARTIAL_PASS` / `FAIL` result semantics;
- explicit discovery reports that show selected, filtered and dynamic-skipped targets;
- no process kill, no process start, no DB, no deploy.

## Common usage

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\repos\hitech-os\tools\Plawright Mamastrophic\RUN.ps1" -Mode discovery -Surface all
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\repos\hitech-os\tools\Plawright Mamastrophic\RUN.ps1" -Mode quick -Surface pc -Workers 6
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\repos\hitech-os\tools\Plawright Mamastrophic\RUN.ps1" -Mode full -Surface all -Workers 6
```

If an offline macro is skipped and everything online captures correctly, the run returns `PARTIAL_PASS` and exits `0`. Use `-Strict` only when skipped/offline targets must make the run fail.

## arr5 GPU phases

GPU is optional and governed. The default remains stable:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\repos\hitech-os\tools\Plawright Mamastrophic\RUN.ps1" -Mode quick -Surface pc -Workers 6 -GpuMode off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\repos\hitech-os\tools\Plawright Mamastrophic\RUN.ps1" -Mode quick -Surface pc -Workers 6 -GpuMode auto
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\repos\hitech-os\tools\Plawright Mamastrophic\RUN.ps1" -Mode quick -Surface pc -Workers 6 -GpuMode on
```

- `off`: reproducible baseline.
- `auto`: safe GPU/WebGL/canvas acceleration attempt with Chromium fallback.
- `on`: aggressive GPU flags; compare after `auto`, especially for Cloudglass/WebGL-heavy routes.

Each run writes GPU evidence under `reports/gpu-profile.*` and `screens/gpu-runtime.json`.


## arr5 fix2 GPU parser repair

This fix repairs the GPU profile markdown string quoting in `core/run-surf8-capture.ps1`.
The bug appeared before Playwright execution, so `-GpuMode off`, `auto`, and `on` all failed at PowerShell parse time.
The installer now validates PowerShell parseability before reporting PASS.


## arr5 fix2 validator repair

- Fixes the installer validator itself: PowerShell parse validation now runs through a temporary `-File` validator instead of passing target paths with spaces after `-Command`.
- This prevents false install failure on `F:
epos\hitech-os	ools\Plawright Mamastrophic\...`.
- Keeps the arr5 fix1 GPU string repairs and GPU modes `off|auto|on`.

## arr7 timeout-guard

La version arr7 corrige una inconsistencia de tiempos: el motor podia intentar hasta 3 navegaciones de 45s, pero el test global moria a los 90s. Ahora el timeout del test se calcula de forma coherente y puede ajustarse con `-TestTimeoutMs`, `-GotoTimeoutMs`, `-GotoRetries`, `-ScreenshotTimeoutMs` y `-ProbeTimeoutMs`.

Tambien registra `navigation.softNavigation=true` cuando una ruta reporta timeout de navegacion pero ya esta en la URL esperada con DOM/body renderizado, para capturar evidencia util sin fabricar PASS falso.


## arr8 installer parser guard

El bundle de instalacion corrige el falso `powershell_parse` en rutas con espacios usando un parser temporal invocado por `-File -Path`.

<!-- MAMSHOT_UNIVERSAL_SURF8_CI_V1 -->
## Hosted CI adapter

The universal GitHub workflow may start isolated ephemeral runtimes in its own runner, while surf8 itself keeps the no-start/no-kill contract. Runtime ownership stays outside the capture engine.

Canonical CI runtime mapping: Chart Lab 3000, Web 3110, Tablet 3120, PC 3130, Mobile/PWA 3140, Control Center 3150. Tablet and PC may use runner-local ephemeral SQLite only. Mobile means the existing PWA/Web app, not native Android/iOS tooling. Control Center uses its canonical local Python panel on 3150, not a static-file-only server, because the real UI depends on local API routes.

Cross-platform rule: when `-ArtifactRoot` is supplied, all output placement must remain under that root. Windows-only defaults are local fallback behavior, not a hosted CI contract.
