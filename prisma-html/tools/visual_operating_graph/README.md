# PRISMA Visual Operating Graph tooling

This package implements the read-only execution waves for `visual.operating_graph_v1`.

Implemented in Wave 1:

- deterministic canonical graph builder;
- source-set lock verifier;
- generated Master Map projection;
- Live Phase Truth Reducer;
- process-level Drift Sentinel.

Implemented in Wave 2:

- **Next Safe Action Engine** for `WHAT_CAN_I_DO_NEXT?`;
- target-specific readiness explanation for `WHY_NOT_APPLY_READY(targetId)`;
- **What-if Digital Twin** over copied graph/target state;
- deterministic blocker-family classification with an explicit fail-closed fallback;
- stale/unknown flags and provenance-preserving, non-authorizing outputs.

Hard boundaries:

- no product/runtime mutation;
- no semantic minting;
- no canonical visual registration;
- no Work Entry mutation;
- no GVAE APPLY;
- no replacement of Code Atlas, NDC, Identity, RIFAT, Target Index, Visual Promotion, Factory Ledger or Authority Mesh;
- all generated/planned outputs remain derived, provenance-bound and non-authorizing;
- possible next gates never become authorization.

Typical checks from `prisma-html`:

```bash
PYTHONPATH=tools python -m visual_operating_graph.source_set_verifier
PYTHONPATH=tools python -m visual_operating_graph.builder --out-dir "$TMPDIR/prisma-operating-graph" --write
PYTHONPATH=tools python -m visual_operating_graph.builder --out-dir "$TMPDIR/prisma-operating-graph" --check
PYTHONPATH=tools python -m unittest discover -s tools/visual_operating_graph/tests -p 'test_*.py' -v
```

Wave 2 examples:

```bash
PYTHONPATH=tools python -m visual_operating_graph.next_safe_action \
  --graph /path/to/PRISMA_PROCESS_GRAPH.generated.json \
  --query 'WHAT_CAN_I_DO_NEXT?'

PYTHONPATH=tools python -m visual_operating_graph.next_safe_action \
  --graph /path/to/PRISMA_PROCESS_GRAPH.generated.json \
  --repo-root /path/to/repo \
  --target-id TGT.CENSUS.PC.EXAMPLE.V1 \
  --query 'WHY_NOT_APPLY_READY(targetId)'
```

The second command reads the existing generated Target Index only; it never edits it.

Generated Wave 1 outputs remain non-authoritative and must not be hand-edited.
