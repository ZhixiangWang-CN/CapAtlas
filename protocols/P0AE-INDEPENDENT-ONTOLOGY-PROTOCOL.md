# P0ae — Independent capability-ontology confirmation

Status: protocol fixed before any P0ae target outcome is generated.

## Question

Does a 16-item MMLU behavioral map predict model neighborhoods under a second,
benchmark-disjoint capability ontology, and does it add information beyond
calibration-only statistics?

## Cohort

Use the unchanged 46-model reference atlas and the 70 complete P0y targets from
43 atlas-disjoint lineages. The two P0y procedural failures remain excluded.
No new checkpoints are added. Completion requires all six ontology coordinates
for every included reference and target; failures are procedural and cannot be
replaced based on outcomes.

## Second ontology

The six coordinates are TruthfulQA-MC1, WinoGrande-XL, PIQA, CommonsenseQA,
BoolQ, and SciQ. These datasets do not occur in the original eight-coordinate
oracle or the MMLU probe bank. For each coordinate, select 48 validation items
by ascending SHA-256 hash of the stable item ID after excluding every item in
the frozen P0q 240-item probe bank. Thus P0ae is item-disjoint from P0q as well
as benchmark-disjoint from the original oracle. The manifest is frozen before
model evaluation.

Each coordinate is the mean gold-answer minus best-wrong continuation
log-likelihood margin. The same prompt, candidate scoring, tokenizer handling,
and symmetric profile builder are used for references and targets.

## Frozen methods and endpoints

All methods receive the original frozen MMLU static-16 probability vectors.
Fit only on the 46 reference models:

- SoftMap: reference-only PCA rank 4 followed by ridge alpha 10;
- direct soft-JS;
- calibration-only ridge using mean entropy, maximum probability, margin, and
  answer-choice bias from the same 16 responses;
- scalar 16-item ability;
- full soft ridge.

Primary endpoint: P0y-lineage-macro NDCG@5 under the second ontology.
Co-primary contrasts: SoftMap minus soft-JS and SoftMap minus calibration-only.
Report 95% lineage-bootstrap intervals, deterministic Monte Carlo sign flips,
Recall@5, Kendall's tau, top-1 regret, and capability-vector RMSE. Holm-adjust
the two primary p-values. The experiment confirms ontology transfer only if
both adjusted p-values are at most 0.05, both mean effects are positive, and at
least 60% of lineages improve in both contrasts.

## Interpretation

Failure against calibration-only means the external-validity result is real but
largely attributable to low-dimensional response confidence under the tested
interfaces. Failure against soft-JS means the original mapping relation does
not transfer to the new ontology. Neither outcome changes the already frozen
P0y result.
