# Reproducibility guide

## Lightweight verification

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
python scripts/verify_release.py
```

This verifies the public implementation, artifact checksums, the primary registered decision,
and the hierarchical-lineage sensitivity decision without downloading model weights.

To recompute the full hierarchical-lineage sensitivity analysis (100,000 bootstrap
draws and up to one million sign flips per comparison), run:

```bash
python scripts/reproduce_hierarchical_lineage_sensitivity.py
```

The output is written to `results/hierarchical_lineage_sensitivity_recomputed.json`
without overwriting the released authoritative artifact.

## Full evaluation boundary

The full evaluation requires the model checkpoints and benchmark datasets listed in the paper.
They are not redistributed here. The frozen protocol documents specify the probe interface,
oracle tasks, seeds, exclusion rules, estimands, and decision gates. The released manifests and
item identifiers allow a licensed user to reconstruct the evaluations from the original sources.

All transforms in `CapAtlas.fit` are reference-only. The target capability oracle is not an input
to `predict` or `place`; it is opened only for post-hoc scoring.
