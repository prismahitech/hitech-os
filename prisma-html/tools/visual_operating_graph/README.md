# PRISMA Visual Operating Graph tooling

This package implements the first read-only execution wave for `visual.operating_graph_v1`.

Implemented in Wave 1:

- deterministic canonical graph builder;
- source-set lock verifier;
- generated Master Map projection;
- Live Phase Truth Reducer;
- process-level Drift Sentinel.

Hard boundaries:

- no product/runtime mutation;
- no semantic minting;
- no canonical visual registration;
- no Work Entry mutation;
- no GVAE APPLY;
- no replacement of Code Atlas, NDC, Identity, RIFAT, Target Index, Visual Promotion, Factory Ledger or Authority Mesh;
- all generated outputs remain derived, provenance-bound and non-authorizing.

Typical checks from `prisma-html`:

```bash
PYTHONPATH=tools python -m visual_operating_graph.source_set_verifier
PYTHONPATH=tools python -m visual_operating_graph.builder --out-dir "$TMPDIR/prisma-operating-graph" --write
PYTHONPATH=tools python -m visual_operating_graph.builder --out-dir "$TMPDIR/prisma-operating-graph" --check
PYTHONPATH=tools python -m unittest discover -s tools/visual_operating_graph/tests -p 'test_*.py' -v
```

Generated outputs must not be hand-edited.
