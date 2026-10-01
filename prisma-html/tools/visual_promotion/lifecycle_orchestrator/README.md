# PRISMA Visual Lifecycle Orchestrator

This package records and coordinates one exact visual target through the existing promotion authorities. It owns transition receipts only. NDC, Identity, RIFAT, Authority Mesh, Factory Ledger, Work Entry Gate, GVAE, Target Index, Canonical Registration, projection generators, Runtime Evidence, and Code Atlas remain their existing authorities.

The transition order is fixed:

```text
DISCOVER → ASSESS_RESOLVE → REGISTER_TARGET → CANONICAL_BINDING
→ AUTHORIZATION → APPLY → DERIVE → RECONCILE → RUNTIME_VERIFY
→ VISUAL_CERTIFY → CHANGE_ASSURANCE → CLOSE
```

Each invocation advances one transition. The request contract is [transition.schema.json](transition.schema.json). Replays with the same lifecycle id, transition, request, and HEAD return the original receipt. Out of order transitions, stale HEADs, ambiguous targets, missing evidence, and invalid authority responses fail closed. Receipts and lifecycle records are written under `prisma-html/governance/visual-promotion/lifecycle-orchestrator/` at runtime; generated records should not be committed as implementation source.

## CLI

Run from the repository root:

```powershell
$env:PYTHONPATH = "prisma-html/tools"
python -m visual_promotion.lifecycle_orchestrator doctor
python -m visual_promotion.lifecycle_orchestrator inspect --lifecycle-id vlo-example-001
python -m visual_promotion.lifecycle_orchestrator advance --request transition.json
python -m visual_promotion.lifecycle_orchestrator receipt --lifecycle-id vlo-example-001 --transition-id 001-DISCOVER-<12 hex>
```

`doctor` and `inspect` are read-only. A doctor request file may contain a `workEntryRequest` and, optionally, a fresh `authority` bundle to evaluate Work Entry, the Authority Mesh / Layer Map, and the Factory Ledger MUTATION decision. `advance` accepts one JSON object per call:

```json
{
  "schema": "prisma.visual.lifecycle-transition.v1",
  "lifecycleId": "vlo-example-001",
  "transition": "DISCOVER",
  "expectedHead": "<current 40-character commit SHA>",
  "payload": {
    "workEntryRequest": {
      "schema": "prisma.visual.work-entry.request.v1",
      "task": "Resolve one exact tablet visual target",
      "surface": "tablet",
      "targetIds": ["TGT.CENSUS.<exact-id>"],
      "intent": "ADVANCE",
      "expectedHead": "<same current commit SHA>"
    }
  }
}
```

Supply stage-specific evidence in later calls. `ASSESS_RESOLVE` requires a promotion-readiness row and verified Authority Mesh / Layer Map evidence. Pass the composed Mesh ZIP as a repo-relative regular file (for example, in an untracked `.governance` evidence directory); the verifier rejects external paths and symlinks. The Layer Map digest is read from the task-specific map embedded in that same artifact. `REGISTER_TARGET` also requires the exact source path and digest plus explicit canonical registration authorization. `AUTHORIZATION` re-evaluates Work Entry against the same HEAD, then rechecks the fresh Mesh and Factory Ledger MUTATION gate. The canonical registration writer runs only when `APPLY` specifies `applyKind: "canonical_registration"` after those checks pass.

The `authority` object used at assessment, registration planning, authorization, and reconciliation has this shape:

```json
{
  "authorityCommit": "<current 40-character commit SHA>",
  "authorityTaskId": "<exact mesh task id>",
  "authorityMeshArtifact": ".governance/<task>/prisma-automesh-composed-result.zip",
  "authorityMeshArtifactSha256": "<64-character SHA-256>",
  "authorityMeshRequestDigest": "<64-character request digest>",
  "layerMapSha256": "<optional 64-character digest of the embedded exact Layer Map>"
}
```

The `REGISTER_TARGET` payload uses `source: {"path": "<repo-relative canonical source>", "digest": "<64-character SHA-256>"}` and the existing Canonical Registration authorization fields: `canonicalRegistrationAuthorized: true`, `automaticSemanticInference: false`, and `automaticApplicationSource: false`. No caller-supplied canonical target, binding, or recipe IDs are used to replace the owning allocator.

The current Factory Ledger capability does not authorize a product/runtime GVAE mutation. `APPLY` with `applyKind: "product_visual"` therefore returns `BLOCKED` and does not invoke GVAE. A successful canonical registration is not a product visual apply, runtime pass, or G-01 closure.

`DERIVE` requires `executeDerivedSteps: true`; it runs only the canonical identity and Target Index derivation commands and their existing verification commands. Reconciliation requires explicit projection classification and supporting digests or decision evidence. `RUNTIME_VERIFY` requires an exact-target GVAE `VERIFY` request and a build commit equal to that transition's current HEAD. It records GVAE's `STATIC_GREEN` result as source-static evidence; this does not claim runtime green. Runtime evidence is then accepted only through `runtime_evidence_bridge.py`; all runtime, console, network, geometry, accessibility, and visual verdicts must be `PASS` before `VISUAL_CERTIFY`. `CLOSE` additionally requires a passing Code Atlas Change Assurance verification.

`cloud-center` is recognized but blocked with `SURFACE_VISUAL_AUTHORITY_MISSING:cloud-center`. Web, Chart Lab, and Control Center remain known governed surfaces but are outside this capability's canonical registration cohort and return `SURFACE_CANONICAL_PROMOTION_UNSUPPORTED`. The coordinator does not create new surface authority.

Explicit maintenance commands are available:

```powershell
python -m visual_promotion.lifecycle_orchestrator rollback-registration --lifecycle-id vlo-example-001
python -m visual_promotion.lifecycle_orchestrator supersede --lifecycle-id vlo-example-001 --superseded-by vlo-example-002 --decision-ref NDC-DECISION-123
```

Rollback delegates to Canonical Registration's transaction-scoped rollback and newer-work protection. Supersession records the decision reference and uses the canonical lifecycle state mapper. Neither operation authorizes a new visual mutation.
