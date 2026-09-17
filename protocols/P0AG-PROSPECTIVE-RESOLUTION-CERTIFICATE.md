# P0ag — prospective resolution-certificate confirmation

Status: protocol fixed before any P0ag target outcome is generated.

## Question

Can a sparse behavioral model map recognize when its local Top-5 neighborhood is
resolved well enough to report, and abstain otherwise, on target checkpoints and
a capability ontology not used to develop the certificate?

## Fixed map and certificate

- Interface: the unchanged 16 MMLU multiple-choice probability vectors.
- Map: reference-only PCA rank 4 followed by ridge regression with alpha 10.
- Atlas: the unchanged 46 reference checkpoints.
- Certificate features, in this exact order: normalized Top-1 gap, normalized
  Top-5 boundary gap, normalized nearest-atlas distance, leave-one-reference-out
  Top-1 consensus, leave-one-reference-out Top-5 Jaccard, and leave-one-reference-
  out prediction spread.
- Selector: StandardScaler plus class-balanced logistic regression with C=1,
  trained once on the already completed P0ae 48-item/task development ontology.
- Target event: `Recall@5 >= 0.6`, meaning that at least three reported references
  belong to the oracle Top-5.
- The logistic coefficients, scaler, and acceptance threshold are serialized in
  `certificate_freeze.json`; they may not be refit after P0ag evaluation starts.

The threshold is the lowest fitted development score attaining at least 80%
empirical precision among the largest accepted prefix with at least five targets.
This is the rule that produced the earlier exploratory P0af signal; P0af is not
used as training data.

## Target cohort

Fifty exact checkpoints are frozen without consulting P0ag outcomes:

- the 26 checkpoints from the pre-existing P0ad metadata-frozen roster; and
- 24 cached additions chosen before P0ag evaluation for compatibility, size, and
  architectural breadth only.

The experiment is prospective with respect to the P0ag outcome, not a claim that
the checkpoint files have never appeared in earlier experiments. All exact model
IDs, revisions, load paths, declared lineages, and prior-use status are recorded in
`frozen_roster.json`. At least 30 complete checkpoints and 20 complete lineages are
required. No failed checkpoint may be replaced after evaluation begins.

## Untouched third capability ontology

The six coordinates are QASC, RACE, SWAG, SuperGLUE-COPA, SuperGLUE-RTE, and
SuperGLUE-WSC.fixed. None occurs in the original eight-task oracle, the P0ae/P0af
ontology, or the 16-item MMLU interface. Exactly 64 validation items per task are
selected by ascending SHA-256 hash after deterministic eligibility checks, for 384
items/model. The manifest and dataset fingerprints are frozen before any model is
evaluated.

Every coordinate is the mean gold-letter log-likelihood minus the best-wrong-letter
log-likelihood. Reference and target checkpoints use the same prompt builder,
candidate scorer, truncation rule, and item order. Reference-only means and scales
standardize the six coordinates.

## Primary endpoint and success rule

For every target, SoftMap returns a Top-5 list and the frozen selector either
accepts or abstains. The primary endpoint is selective correctness of the event
`Recall@5 >= 0.6`.

P0ag confirms an operational resolution certificate only if all conditions hold:

1. at least 30 targets from at least 20 lineages are technically complete;
2. target-level acceptance coverage is at least 25%;
3. target-level selective precision is at least 90%;
4. the one-sided 95% Clopper--Pearson lower bound for selective precision is
   greater than the unfiltered cohort event rate; and
5. at least 80% of accepted lineages have lineage-mean success at least 0.5.

We report target and lineage-macro coverage/precision, the exact interval, AUROC,
area under the risk--coverage curve, Recall@5, NDCG@5, Kendall tau, Top-1 regret,
and the full per-target ledger. Secondary thresholds and feature ablations are
descriptive only and cannot rescue a failed primary gate.

## Interpretation

- Pass: sparse maps can attach a prospective, transferable local-resolution
  certificate to a nontrivial subset of shifted targets.
- Fail with useful global ranking: the paper retains the global-order/local-neighbor
  validity-envelope result and reports certificate prediction as unresolved.
- Failure of the completeness gate is procedural, not scientific evidence.
