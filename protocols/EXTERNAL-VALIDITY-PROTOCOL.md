# P0y external-validity analysis protocol (frozen before execution)

Freeze date: 2026-09-11 (America/Chicago)

## Status and scope

This is a retrospective, existing-data analysis of the already completed P0y
cohort. It does not alter the frozen P0y primary decision, its multiplicity
family, or the status of any earlier experiment. The scientific question is
whether a sparse behavioral map learned on the 46-model reference atlas retains
meaningful geometry under lineage shift, and whether that geometry contains
more than a one-dimensional overall-ability signal.

The authoritative P0y primary result is
`server_results/capatlas_p0y/final_analysis/p0y_primary.json`. The analysis
script must record the SHA-256 hashes of this file, the target roster, model
metadata, probe panel, and thick-oracle file in its output. It must never write
to or replace the authoritative primary result.

## Cohort and exclusions

- References: the frozen 46-model reference atlas used by P0y.
- Targets: only P0y checkpoints with exactly 1,200 unique probe rows and the
  complete frozen thick-oracle item set.
- Unit of inference: declared target lineage. Multiple checkpoints in one
  lineage are averaged before uncertainty or sign inference.
- No checkpoint, endpoint, hyperparameter, or item is selected using the
  analyses below.

## Frozen analyses

### A. Full comparator and secondary-endpoint table

Evaluate SoftMap, direct soft-JS, full soft ridge, hard ridge, scalar ability,
PLS-4, metric learning, DKPS-OLS, DKPS-1NN, and DKPS-sqrt(N)-NN. Add three
metadata controls fitted on references only:

1. parameter count only: ridge from standardized log parameter count;
2. metadata only: ridge from log parameter count, log vocabulary size,
   base/instruct stage, model type, and reference-family indicators;
3. nuisance only: the metadata variables above plus probe entropy, maximum
   probability, and answer-letter bias.

Report lineage-macro NDCG@5, Recall@5, Kendall's tau, top-1 regret, and
capability-vector RMSE. For every comparator, report the paired lineage effect
relative to SoftMap with a 20,000-draw percentile bootstrap interval and an
exact sign-flip p-value when computationally feasible (otherwise deterministic
Monte Carlo sign flips, labeled as such).

### B. Remove the dominant oracle ability direction

Fit PCA only to standardized reference oracle profiles. Remove reference PC1
from reference and target oracle profiles. Evaluate:

- criterion-residualized retrieval: rank predictions in the residual oracle
  space and score against residual-oracle relevance;
- residual-target SoftMap: fit the otherwise unchanged SoftMap decoder from
  the frozen probe panel to the seven-dimensional residual oracle target.

The main diagnostic is lineage-macro NDCG@5 after PC1 removal. The full-space
P0y result remains the primary scientific result.

### C. Ability-matched retrieval

For each target, define an evaluation-only candidate atlas as the 15 references
closest to that target on true reference-fitted oracle PC1. This use of target
oracle information only defines a difficulty-controlled evaluation stratum and
is not available to the retrieval algorithm. Rank within the same candidate set
using SoftMap and soft-JS. Report NDCG@5, Recall@5, Kendall's tau, and top-1
regret. Repeat with candidate sizes 10 and 20 as sensitivity analyses.

### D. Within-domain retrieval

Evaluate retrieval separately in five prespecified oracle subspaces:

- biomedical: PubMedQA;
- legal: CaseHOLD;
- mathematical: GSM8K and MATH;
- code: MBPP and HumanEval;
- general reasoning: ARC-Challenge and HellaSwag.

For each subspace, standardize using references only and compare SoftMap with
soft-JS on the same target lineages. Single-benchmark domains are explicitly
descriptive. The across-domain mean is not a new confirmatory endpoint.

### E. Independent-ontology priority

The existing P0q experiment changes the probe source but retains the original
eight-task oracle, so it is not evidence from an independent capability
ontology. Before any new model-count expansion, freeze a second oracle made of
benchmarks absent from the original eight-task oracle and absent from the MMLU
probe bank. Reuse the same 46 references and P0y targets if complete evaluations
can be obtained. Until those rows exist, any split or regrouping of the original
eight tasks is labeled an internal ontology sensitivity analysis, not an
independent ontology confirmation.

## Interpretation gates

- If SoftMap remains above soft-JS after PC1 removal and in ability-matched
  retrieval, the evidence supports multidimensional geometry beyond overall
  strength.
- If it does not, the paper must state that sparse mapping primarily estimates
  a dominant ability direction and narrow the claim accordingly.
- Metadata or nuisance controls matching SoftMap preclude a behavioral-geometry
  interpretation.
- Domain results support only the domains in which the paired lineage interval
  is compatible with a practically meaningful benefit.
