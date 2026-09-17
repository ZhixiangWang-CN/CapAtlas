# CapAtlas

**CapAtlas** maps a language model from only 16 standardized multiple-choice probe distributions
into a reference-supervised capability geometry. It then returns a relative capability profile
and ranked peer models while keeping the target's capability oracle sealed until scoring.

The repository accompanies the ICLR submission **“CapAtlas: From Sparse Fingerprints to Valid
Claims.”** It contains the clean reference implementation, frozen protocols and manifests,
derived result artifacts, and checksum-backed verification scripts.

## What is new

- A leakage-controlled `fit -> freeze -> place -> unseal` audit protocol.
- A capability-aligned geometry learned only from documented reference models.
- Claim-specific validation at four resolutions: global order, local Top-5 retrieval, relative
  risk, and fixed-precision acceptance.
- Lineage-disjoint evaluation with hierarchical taxonomy sensitivity.

## Install and verify

```bash
git clone https://github.com/ZhixiangWang-CN/CapAtlas.git
cd CapAtlas
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
python scripts/verify_release.py
```

The verification script reproduces the released primary decision from checksum-protected result
artifacts. It does not download model weights.

## Minimal use

```python
from capatlas import CapAtlas

atlas = CapAtlas(rank=4, alpha=10.0)
atlas.fit(reference_fingerprints, reference_capabilities, reference_ids)
placement = atlas.place(target_fingerprint)

print(placement.capability_profile)
print(placement.top5)
```

Fingerprints are flattened probe probability vectors. With 16 four-choice probes, each input has
64 dimensions. Capability profiles have one coordinate per declared capability task.

## Released evidence

The main released artifact contains 46 references and 70 targets from 43 held-out lineages.
SoftMap reaches lineage-macro NDCG@5 of 0.8609 versus 0.8181 for matched-information soft-JS;
the paired lineage difference is +0.0428 (Holm-adjusted p = 0.000375; 31/43 positive lineages).
Under a benchmark-disjoint capability ontology, the nested item-by-lineage analysis gives a
+0.1731 Kendall difference. On the separately frozen 50-target prospective cohort, the reliability
score reaches AUROC 0.731 and 80.95% precision at 42.0% coverage; the registered 90% certificate
gate remains unmet, as reported in the paper.

See [the reproducibility guide](docs/REPRODUCIBILITY.md) and [data card](docs/DATA_CARD.md) for the
scope of the public release. Model weights and benchmark question text are intentionally excluded
and remain subject to their source licenses.

## Repository layout

```text
src/capatlas/       reference implementation
tests/              leakage and metric unit tests
scripts/            artifact verification
data/manifests/     sanitized frozen cohorts and panel identifiers
results/            derived and aggregate paper results
protocols/          frozen analysis and sensitivity protocols
```

The full hierarchical taxonomy analysis is independently rerunnable with
`python scripts/reproduce_hierarchical_lineage_sensitivity.py`.

## License

Code is released under the MIT License. Third-party models and datasets retain their original
licenses.
