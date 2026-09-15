# arr13: app ZIPs, live progress, screenshots modes

## New modes

- `screenshots`: screenshot-only evidence. It uses the full screenshot capture engine with DeepScroll, page tiles, and internal scroll-container tiles, but without VisualQA DOM/computed-layer aggregation.
- `screenshotsqa`: screenshots plus VisualQA. It captures screenshots and also writes DOM snapshots, computed style records, render-layer indicators, console/network findings, and route status reports.

Existing modes remain available: `discovery`, `quick`, `critical`, `full`, and `visualqa`.

## Artifact rule

When `Surface all` is used, Mamastrophic now follows this rule:

- maximum 6 final ZIPs;
- one ZIP per app/surface;
- no loose child ZIP per phase;
- no extra parent ZIP when the user asked for all apps;
- per-app ZIPs contain phases under `phases/<mode>`.

For menu runs with multiple phases and `ALL` apps, the menu creates a temporary bundle root, runs each phase with `-NoZip`, and packages final evidence into:

- `mamshot chart-lab bundle <stamp> result|fail.zip`
- `mamshot web bundle <stamp> result|fail.zip`
- `mamshot tablet bundle <stamp> result|fail.zip`
- `mamshot pc bundle <stamp> result|fail.zip`
- `mamshot mobile bundle <stamp> result|fail.zip`
- `mamshot control-center bundle <stamp> result|fail.zip`

Temporary staging is moved to `F:\Trash-old` with a manifest after final app ZIPs are created.

## Live progress

The old static `#####` bar was not enough. arr13 adds heartbeat-style progress from the Playwright engine and deep screenshot capture:

- target start;
- skipped offline target;
- legacy screenshot;
- viewport screenshot;
- fullpage screenshot;
- page tile `n/total`;
- scroll container discovery;
- container tile `n/total`;
- target done or failed;
- VisualQA computed-layer step.

Console lines use the prefix:

```text
[MAM-PROGRESS]
```

Each run also writes `reports/progress.jsonl` so a later tool can diagnose whether the process was alive, idle, stuck, or just capturing a heavy route.

## Time control

Do not use phase `6/all` for every small UI change. Recommended daily flow:

1. `discovery` only when routes/ports changed.
2. `screenshots` for visual evidence without QA overhead.
3. `screenshotsqa` when DOM/computed/render-layer context is needed.
4. `full` or `visualqa` only for closure/review runs.

DeepScroll remains on by default because the tool is built for complete evidence, but tile/container limits can be reduced for smoke runs.

## Partial policy

`AllowPartial` now matters for scroll coverage. If a route needs more tiles than the configured limit, that is treated as partial coverage. With `-AllowPartial`, partial coverage can pass as operational evidence instead of becoming a false fail. Hard failures, missing records, Playwright failures, and failed scroll coverage still fail.

<!-- MAMSHOT_UNIVERSAL_ARR13_BRIDGE_V1 -->
## GitHub universal artifact bridge

arr13 remains the local per-app ZIP owner. The GitHub universal fast path reuses the same `screenshots` / `screenshotsqa` engine but publishes one uniform Actions artifact per selected surface instead of the local `F:\descargasf` ZIP convention.

Each hosted bundle contains normalized PNGs under `screenshots/`; `MANIFEST.json`, `INDEX.csv`, `ROUTE_STATUS.json`, `PROVENANCE.json`, `SHA256SUMS.txt`, and `README.md`; plus original Mamastrophic non-PNG reports/logs under `evidence/`.

FAIL evidence is preserved. Internal `continue-on-error` exists only long enough to package diagnostics; the final manifest gate remains red on `FAIL`. `PARTIAL_PASS` is explicit evidence state for bounded partial scroll coverage when allowed and is never relabeled PASS.
