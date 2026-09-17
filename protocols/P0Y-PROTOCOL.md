# P0y: prospective three-way comparison and enriched open-set cohort

Protocol written 2026-09-06, before any P0y candidate was downloaded or evaluated.
To be frozen (models list, this document, manifests, panel hash) with an RFC 3161
timestamp after neutral download/smoke preflight and before any target response
is produced.

## Questions
Q1 (replication). Does the frozen SoftMap-versus-soft-JS effect replicate on a new
   lineage-disjoint cohort under a thicker oracle?
Q2 (three-way). Is any of SoftMap, metric learning, DKPS sqrt-N-NN better than the
   others when the oracle has 200 items per task?
Q3 (open-set). Can a retrieval geometry flag targets whose capability profile lies
   outside atlas support, on a cohort deliberately enriched with such targets?

## Cohort
Candidates: `code/models_preflight.json` (62 declared lineages, 114 checkpoints).
Every candidate lineage is absent from the 67 lineages used by the atlas and by all
earlier cohorts (P0c, P0d, P0f, P0k, P0n, P0u, P0w); the freeze script refuses any
overlap by family or model id. Candidates carry an a-priori `oos_candidate` flag
(non-English-centric pretraining, <150M parameters, or a narrow specialty corpus)
written before evaluation. Freeze includes every checkpoint that downloads and passes
the neutral smoke test; the freeze is refused below 40 lineages or 55 checkpoints.
Inclusion after evaluation is complete-case by structural checks only (1200 unique
probe rows; 1564 unique oracle rows). Execution-only amendments (loader flags,
microbatch, device) are allowed and logged; no prompt, panel, oracle, method
constant, or endpoint may change after the freeze.

## Fixed inputs
- Probe bank: the 1,200-item MMLU manifest and the frozen static-16 panel
  (sha256 c2257a90...). Probes evaluated by `capability_atlas_p0c/code/evaluate_model.py`.
- Oracle: thick oracle = frozen 48 items per task (capatlas-p0g-20260828-v1) plus the
  152-item extension (capatlas-thick-20260906-v1; HumanEval +116), same evaluator,
  prompts, scoring, and lengths. Profiles are task means (200 items; 164 for HumanEval)
  standardized on the reference atlas.
- Atlas: the 46 reference checkpoints with thick-oracle profiles. A reference whose
  extension run fails after one retry is dropped from the atlas for all P0y analyses.
- Methods and constants: exactly as in the manuscript's Appendix B (SoftMap rank 4,
  lambda 10; metric learning diagonal ridge lambda 10, 5-NN; DKPS classical MDS 8 dims,
  k = round(sqrt(N_ref)); soft-JS; full soft ridge; hard ridge; PLS 4; CCA 4;
  metadata; parameter count; scalar ability; nuisance only; PhyloLM-style;
  BenchPress-style). Random and atlas-mean floors and the split-half ceiling.

## Endpoints and inference
Unit of inference: declared lineage (one released model line per family key).
Primary metric: lineage-macro NDCG@5 with exponential relevance (Eq. 2 of the paper).
Secondary: Recall@5, Kendall tau, top-1 regret, capability RMSE.

Prespecified paired contrasts, each an exact two-sided lineage sign-flip test (lineage
count <= 20 exact enumeration, else 10^6 Monte Carlo signs), Holm-corrected over the
three at alpha 0.05, with the lineage percentile bootstrap reported descriptively:
  C1: SoftMap minus soft-JS
  C2: DKPS sqrt-N-NN minus SoftMap
  C3: metric learning minus SoftMap
Decision rule: a method is declared better only if its Holm-adjusted p <= 0.05 and at
least 60% of lineages have the same sign. Otherwise the pair is reported as not
distinguishable at this oracle resolution. Every other method comparison is
descriptive. Maximum single-lineage influence on each contrast is reported.

Open-set (Q3), prespecified:
- Ground truth: a target is out-of-support (OOS) when the Euclidean distance from its
  standardized thick-oracle profile to its nearest atlas reference exceeds the 95th
  percentile of the leave-one-out nearest-reference distances among the atlas
  references.
- Enrichment check: fraction OOS among a-priori flagged versus unflagged targets
  (Fisher exact test).
- Detectors (all computable at audit time without the target oracle): (D1) distance
  from the SoftMap estimate to its nearest reference; (D2) DKPS joint-embedding
  distance to the nearest reference; (D3) minimum soft-JS distance to any reference;
  (D4) metric-learning distance to the nearest reference.
- Endpoint: AUROC of each detector for ground-truth OOS with a 2,000-draw target
  bootstrap CI. Open-set detection is declared supported for a detector only if there
  are at least 8 ground-truth positives and the CI lower bound exceeds 0.5; otherwise
  the paper keeps its current statement that open-set certification is unsupported.

## Power note
With about 45 lineages and a true 65/35 sign split, the exact sign test has roughly
50% power at alpha 0.05 two-sided; with a 70/30 split about 75%. The cohort is sized
to detect a consistent direction, not a tiny NDCG difference, which is why the
decision rule also requires a 60% sign majority.

## Reporting
All P0y results are reported in the paper as a prospectively frozen replication and
extension regardless of direction, including failed contrasts and an unsupported
open-set conclusion.
