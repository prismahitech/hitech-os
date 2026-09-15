# Mamastrophic universal screenshot artifacts

This is the hosted GitHub Actions fast path for the existing PRISMA Plawright Mamastrophic engine.

## Scope

Workflow: `.github/workflows/mamastrophic-universal-screenshots.yml`

Supported surfaces: `pc` (3130), `tablet` (3120), `mobile` (3140, existing Mobile/PWA web surface), `web` (3110), `chart-lab` (3000), `control-center` (3150), and `all` for all six in parallel.

Supported modes: `screenshots` and `screenshotsqa`.

The workflow is an adapter. Route discovery, Playwright capture, DeepScroll, route status and raw evidence remain owned by Mamastrophic.

## Artifact contract

Schema: `prisma.mamastrophic.universal-screenshot-artifact.v1`.

```text
screenshots/
  *.png
INDEX.csv
MANIFEST.json
ROUTE_STATUS.json
PROVENANCE.json
SHA256SUMS.txt
README.md
evidence/
  ...original Mamastrophic non-PNG evidence...
```

`INDEX.csv` preserves the original relative path beside normalized filename, SHA-256, bytes and PNG dimensions. Normalized filenames are filesystem-bounded and use a deterministic hash suffix when needed.

## Honest status

Allowed states are `PASS`, `PARTIAL_PASS`, and `FAIL`.

Fail-closed rules:
- missing/invalid Mamastrophic summary -> `FAIL`;
- nonzero Mamastrophic exit -> `FAIL`;
- screenshot-mode PASS/PARTIAL without PNGs -> `FAIL`;
- hard route/capture/scroll failures remain `FAIL`.

Bounded partial scroll coverage may be accepted only when explicitly allowed. It remains `PARTIAL_PASS` with `partialReasons`.

Internal `continue-on-error` exists only to preserve/upload diagnostic evidence. `Enforce honest final status` is the final gate.

## Runtime ownership in CI

Mamastrophic itself keeps no-start/no-kill. GitHub Actions owns isolated ephemeral runtime startup outside the engine.

- PC and Tablet may prepare runner-local SQLite prerequisites only.
- Web remains off-release; isolated dependencies are materialized inside the checkout without tracked manifest/lockfile mutation.
- Mobile is the existing PWA/Next runtime, not native Android/iOS.
- Control Center uses the canonical Python panel owner with local API routes, not a static-only file server.
- No customer database, production service or deployment is part of this workflow.

## Cross-platform contract

Hosted runners cannot assume Windows drive paths.

- `RUN.ps1` resolves Windows PowerShell or PowerShell Core portably.
- `ArtifactRoot` governs output placement when provided.
- Python launcher executable and arguments remain separate.
- Bundle filenames are path-length-safe.

Local Windows runs may still use existing `F:\descargasf` fallback conventions when `ArtifactRoot` is absent.

## What PASS does not prove

A PASS artifact does not by itself prove production deployment, customer production data correctness, human visual quality approval, legal/compliance approval, device-native mobile behavior, arbitrary environment portability, or distribution/deployment readiness beyond the bounded CI run.
