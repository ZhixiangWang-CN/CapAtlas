# Released artifacts

The repository releases model identifiers, frozen cohort metadata, selected probe IDs,
per-target derived scores, aggregate results, and audit hashes. It does **not** redistribute
model weights or benchmark question text. Those remain governed by their original licenses.

The target manifest is sanitized: machine-local cache paths, execution hostnames, tracebacks,
and scheduler information are excluded. The released result files contain derived model-level
measurements only and no human-subject or private user data.

## Main files

- `data/manifests/reference_models.json`: 46 documented atlas checkpoints.
- `data/manifests/target_models.json`: frozen unseen-lineage target roster.
- `data/manifests/model_metadata.json`: public architecture and size metadata.
- `data/manifests/frozen_panels.json`: frozen probe identifiers.
- `results/p0y_primary.json`: primary per-target and aggregate results.
- `results/hierarchical_lineage_sensitivity.json`: lineage-taxonomy sensitivity analysis.
- `results/external_validity.json`: independent analyses and mechanism controls.
- `results/p0ae_resolution.json`: benchmark-disjoint ontology resolution analysis.
- `results/p0ag_results.json`: prospective reliability and registered certificate result.

Benchmark content must be obtained from the original sources. Model access may require accepting
the corresponding model-card license or access conditions.
