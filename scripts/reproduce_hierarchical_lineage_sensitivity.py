from __future__ import annotations

"""Reproduce the released hierarchical sensitivity analysis.

This public version reads the sanitized release manifest. It preserves the
original resampling seeds and estimands and writes a separate recomputed file.
"""

import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
PRIMARY = PROJECT / "results/p0y_primary.json"
MODELS = PROJECT / "data/manifests/target_models.json"
METADATA = PROJECT / "data/manifests/model_metadata.json"
OUT = PROJECT / "results/hierarchical_lineage_sensitivity_recomputed.json"
SEED = 20260916
BOOTSTRAP_DRAWS = 100_000
SIGN_DRAWS = 1_000_000
EXPECTED_HASHES = {
    str(PRIMARY.relative_to(PROJECT)): "7fa3eaec68aab53fb3e93aeb180126ece7cb28583c33a48754f248b72edef42f",
    str(MODELS.relative_to(PROJECT)): "a7dd03f8409c001181c25fd28aecd9db42cfb5df8852a2d233d41ea76907b999",
    str(METADATA.relative_to(PROJECT)): "f1bd48a5707119c9dfeb977bbdfedbe99d0b1032286fdcfbf5388a3f65f60e8f",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def bootstrap_ci(values, draws=BOOTSTRAP_DRAWS, seed=SEED):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    samples = np.empty(draws, dtype=float)
    chunk = 10_000
    for start in range(0, draws, chunk):
        n = min(chunk, draws - start)
        idx = rng.integers(0, len(values), size=(n, len(values)))
        samples[start:start + n] = values[idx].mean(axis=1)
    return [float(x) for x in np.quantile(samples, [0.025, 0.975])]


def sign_flip(values, seed=SEED):
    values = np.asarray(values, dtype=float)
    observed = abs(float(values.mean()))
    n = len(values)
    exceed = 0
    if n <= 20:
        total = 1 << n
        chunk = 1 << min(n, 15)
        bit_positions = np.arange(n, dtype=np.uint64)
        for start in range(0, total, chunk):
            codes = np.arange(start, min(start + chunk, total), dtype=np.uint64)[:, None]
            signs = np.where(((codes >> bit_positions) & 1) == 1, 1.0, -1.0)
            means = np.sum(signs * values[None, :], axis=1) / n
            exceed += int(np.sum(np.abs(means) >= observed - 1e-15))
        return {"two_sided_p": exceed / total, "permutations": total, "exact": True}
    rng = np.random.default_rng(seed)
    chunk = 20_000
    for start in range(0, SIGN_DRAWS, chunk):
        m = min(chunk, SIGN_DRAWS - start)
        signs = np.where(rng.integers(0, 2, size=(m, n), dtype=np.int8) == 1, 1.0, -1.0)
        means = np.sum(signs * values[None, :], axis=1) / n
        exceed += int(np.sum(np.abs(means) >= observed - 1e-15))
    return {
        "two_sided_p": (exceed + 1) / (SIGN_DRAWS + 1),
        "permutations": SIGN_DRAWS,
        "exact": False,
    }


def group_effects(target_effect, grouping):
    grouped = defaultdict(list)
    for target, effect in target_effect.items():
        grouped[grouping[target]].append(effect)
    return {group: float(np.mean(values)) for group, values in sorted(grouped.items())}


def summarize(effect_by_group, seed):
    values = np.asarray(list(effect_by_group.values()), dtype=float)
    ci = bootstrap_ci(values, seed=seed)
    test = sign_flip(values, seed=seed + 1000)
    positive = int(np.sum(values > 0))
    return {
        "groups": len(values),
        "group_size_min": None,
        "group_size_median": None,
        "group_size_max": None,
        "mean": float(values.mean()),
        "ci95": ci,
        **test,
        "positive_groups": positive,
        "positive_fraction": positive / len(values),
        "registered_style_pass": bool(ci[0] > 0 and test["two_sided_p"] <= 0.05 and positive / len(values) >= 0.60),
        "per_group": effect_by_group,
    }


def holm(p_values):
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted = {}
    running = 0.0
    for i, (name, value) in enumerate(ordered):
        running = max(running, value * (len(ordered) - i))
        adjusted[name] = min(1.0, running)
    return adjusted


def lineage_to_cluster(targets, declared, coarse):
    values = defaultdict(set)
    for target in targets:
        values[declared[target]].add(coarse[target])
    violations = {lineage: sorted(groups) for lineage, groups in values.items() if len(groups) != 1}
    if violations:
        raise RuntimeError(f"Declared lineages cross coarse clusters: {violations}")
    return {lineage: next(iter(groups)) for lineage, groups in values.items()}


def lineage_to_labels(targets, declared, coarse):
    values = defaultdict(set)
    for target in targets:
        values[declared[target]].add(coarse[target])
    return {lineage: set(groups) for lineage, groups in values.items()}


def connected_lineage_clusters(targets, declared, coarse):
    """Coarsen crossed lineage/coarse labels by bipartite connected component."""
    lineages = sorted(set(declared.values()))
    coarse_groups = sorted(set(coarse.values()))
    adjacency = defaultdict(set)
    for target in targets:
        lineage_node = f"L::{declared[target]}"
        coarse_node = f"C::{coarse[target]}"
        adjacency[lineage_node].add(coarse_node)
        adjacency[coarse_node].add(lineage_node)
    mapping = {}
    component_members = {}
    seen = set()
    component_index = 0
    for lineage in lineages:
        start = f"L::{lineage}"
        if start in seen:
            continue
        stack, nodes = [start], []
        seen.add(start)
        while stack:
            node = stack.pop()
            nodes.append(node)
            for neighbor in adjacency[node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        member_lineages = sorted(node[3:] for node in nodes if node.startswith("L::"))
        member_coarse = sorted(node[3:] for node in nodes if node.startswith("C::"))
        name = f"component_{component_index:02d}::" + "+".join(member_coarse)
        component_index += 1
        component_members[name] = {"declared_lineages": member_lineages, "coarse_labels": member_coarse}
        for member in member_lineages:
            mapping[member] = name
    if set(mapping) != set(lineages) or len(set(mapping.values())) > len(coarse_groups):
        raise RuntimeError("Connected-component clustering failed")
    return mapping, component_members


def clustered_declared_inference(declared_effects, lineage_cluster, seed):
    cluster_values = defaultdict(list)
    for lineage, effect in declared_effects.items():
        cluster_values[lineage_cluster[lineage]].append(effect)
    names = sorted(cluster_values)
    sums = np.asarray([sum(cluster_values[name]) for name in names], dtype=float)
    counts = np.asarray([len(cluster_values[name]) for name in names], dtype=int)
    observed = abs(float(sums.sum() / counts.sum()))
    n_clusters = len(names)

    # Cluster sign flips preserve the registered equal-lineage estimand.
    if n_clusters <= 20:
        total = 1 << n_clusters
        exceed = 0
        chunk = 1 << min(n_clusters, 15)
        bit_positions = np.arange(n_clusters, dtype=np.uint64)
        for start in range(0, total, chunk):
            codes = np.arange(start, min(start + chunk, total), dtype=np.uint64)[:, None]
            signs = np.where(((codes >> bit_positions) & 1) == 1, 1.0, -1.0)
            stats = np.sum(signs * sums[None, :], axis=1) / counts.sum()
            exceed += int(np.sum(np.abs(stats) >= observed - 1e-15))
        p_value, permutations, exact = exceed / total, total, True
    else:
        rng = np.random.default_rng(seed + 1)
        exceed = 0
        for start in range(0, SIGN_DRAWS, 20_000):
            m = min(20_000, SIGN_DRAWS - start)
            signs = np.where(
                rng.integers(0, 2, size=(m, n_clusters), dtype=np.int8) == 1,
                1.0,
                -1.0,
            )
            stats = np.sum(signs * sums[None, :], axis=1) / counts.sum()
            exceed += int(np.sum(np.abs(stats) >= observed - 1e-15))
        p_value, permutations, exact = (exceed + 1) / (SIGN_DRAWS + 1), SIGN_DRAWS, False

    # Pairs cluster sums and counts so the bootstrap statistic remains an
    # equal-declared-lineage mean after cluster resampling.
    rng = np.random.default_rng(seed + 2)
    boot = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    for start in range(0, BOOTSTRAP_DRAWS, 10_000):
        m = min(10_000, BOOTSTRAP_DRAWS - start)
        idx = rng.integers(0, n_clusters, size=(m, n_clusters))
        boot[start:start + m] = sums[idx].sum(1) / counts[idx].sum(1)
    return {
        "clusters": n_clusters,
        "declared_lineages": int(counts.sum()),
        "mean_equal_declared_lineage": float(sums.sum() / counts.sum()),
        "cluster_bootstrap_ci95": [float(x) for x in np.quantile(boot, [0.025, 0.975])],
        "cluster_sign_flip_p": float(p_value),
        "permutations": permutations,
        "exact": exact,
        "cluster_lineage_counts": {name: len(cluster_values[name]) for name in names},
        "per_cluster_sum_of_lineage_effects": {name: float(sum(cluster_values[name])) for name in names},
    }


def main():
    actual_hashes = {str(path.relative_to(PROJECT)): sha256(path) for path in (PRIMARY, MODELS, METADATA)}
    if actual_hashes != EXPECTED_HASHES:
        raise RuntimeError(f"Immutable input hash mismatch: {actual_hashes}")

    primary = json.loads(PRIMARY.read_text())
    model_rows = {row["key"]: row for row in json.loads(MODELS.read_text())}
    metadata = json.loads(METADATA.read_text())["records"]
    softmap = primary["per_target_ndcg5"]["softmap"]
    soft_js = primary["per_target_ndcg5"]["soft_js"]
    targets = sorted(set(softmap) & set(soft_js))
    if len(targets) != primary["targets"] or set(softmap) != set(soft_js):
        raise RuntimeError("Target vectors do not match the frozen primary artifact")
    target_effect = {target: float(softmap[target] - soft_js[target]) for target in targets}

    groupings = {
        "checkpoint": {target: target for target in targets},
        "declared_lineage": {target: model_rows[target]["family"] for target in targets},
        "publisher_namespace": {target: model_rows[target]["model_id"].split("/", 1)[0].lower() for target in targets},
        "implementation_architecture": {target: str(metadata[target]["model_type"]).lower() for target in targets},
    }

    aggregation = {}
    for index, (name, grouping) in enumerate(groupings.items()):
        effects = group_effects(target_effect, grouping)
        result = summarize(effects, SEED + 100 * index)
        sizes = Counter(grouping.values())
        size_values = np.asarray(list(sizes.values()))
        result.update({
            "group_size_min": int(size_values.min()),
            "group_size_median": float(np.median(size_values)),
            "group_size_max": int(size_values.max()),
            "group_members": {
                group: sorted(target for target in targets if grouping[target] == group)
                for group in sorted(sizes)
            },
        })
        aggregation[name] = result
    adjusted = holm({name: row["two_sided_p"] for name, row in aggregation.items()})
    for name, value in adjusted.items():
        aggregation[name]["holm_p_across_sensitivity_levels"] = value

    registered = primary["contrasts"]["C1_softmap_minus_soft_js"]
    reproduced = aggregation["declared_lineage"]
    reproduction_checks = {
        "groups_equal": reproduced["groups"] == registered["n"],
        "mean_abs_error": abs(reproduced["mean"] - registered["mean"]),
        "positive_groups_equal": reproduced["positive_groups"] == registered["positive_groups"],
        # Bootstrap RNGs differ, so the registered CI is retained as source of truth.
        "registered_ci95": registered["ci95"],
        "registered_two_sided_p": registered["two_sided_p"],
    }

    declared = groupings["declared_lineage"]
    declared_effects = group_effects(target_effect, declared)
    preserving = {}
    cluster_definitions = {}
    for index, coarse_name in enumerate(("publisher_namespace", "implementation_architecture")):
        if coarse_name == "implementation_architecture":
            lineage_cluster, components = connected_lineage_clusters(
                targets, declared, groupings[coarse_name]
            )
            cluster_definitions[coarse_name] = {
                "rule": "connected components of declared-lineage--model_type bipartite graph",
                "components": components,
            }
        else:
            lineage_cluster = lineage_to_cluster(targets, declared, groupings[coarse_name])
            cluster_definitions[coarse_name] = {
                "rule": "strictly nested frozen namespace",
                "lineage_to_cluster": lineage_cluster,
            }
        preserving[coarse_name] = clustered_declared_inference(
            declared_effects, lineage_cluster, SEED + 500 + 100 * index
        )

    # Exhaustive leave-one-declared-lineage-out influence.
    loo_rows = []
    for lineage in sorted(declared_effects):
        remaining = {key: value for key, value in declared_effects.items() if key != lineage}
        values = np.asarray(list(remaining.values()))
        loo_rows.append({
            "omitted": lineage,
            "groups": len(values),
            "mean": float(values.mean()),
            "positive_fraction": float(np.mean(values > 0)),
        })
    worst_loo = min(loo_rows, key=lambda row: (row["mean"], row["omitted"]))
    worst_loo_effects = {key: value for key, value in declared_effects.items() if key != worst_loo["omitted"]}
    loo_full = summarize(worst_loo_effects, SEED + 800)

    # Enumerate all single merges allowed by either reproducible coarsening.
    publisher_by_lineage = lineage_to_cluster(targets, declared, groupings["publisher_namespace"])
    architecture_by_lineage = lineage_to_labels(targets, declared, groupings["implementation_architecture"])
    lineages = sorted(declared_effects)
    target_counts = Counter(declared.values())
    merge_rows = []
    for left, right in itertools.combinations(lineages, 2):
        shared = []
        if publisher_by_lineage[left] == publisher_by_lineage[right]:
            shared.append("publisher_namespace")
        if architecture_by_lineage[left] & architecture_by_lineage[right]:
            shared.append("implementation_architecture")
        if not shared:
            continue
        merged_value = (
            declared_effects[left] * target_counts[left]
            + declared_effects[right] * target_counts[right]
        ) / (target_counts[left] + target_counts[right])
        values = [value for key, value in declared_effects.items() if key not in {left, right}] + [merged_value]
        values = np.asarray(values)
        merge_rows.append({
            "left": left,
            "right": right,
            "shared_by": shared,
            "groups": len(values),
            "mean": float(values.mean()),
            "positive_fraction": float(np.mean(values > 0)),
            "merged_effect": float(merged_value),
        })
    if not merge_rows:
        raise RuntimeError("No admissible single-lineage merges found")
    worst_merge = min(merge_rows, key=lambda row: (row["mean"], row["left"], row["right"]))
    left, right = worst_merge["left"], worst_merge["right"]
    merged_key = f"MERGED::{left}+{right}"
    merged_effects = {key: value for key, value in declared_effects.items() if key not in {left, right}}
    merged_effects[merged_key] = worst_merge["merged_effect"]
    merge_full = summarize(merged_effects, SEED + 900)

    robustness_conditions = {
        "registered_reproduced": bool(
            reproduction_checks["groups_equal"]
            and reproduction_checks["mean_abs_error"] < 1e-12
            and reproduction_checks["positive_groups_equal"]
        ),
        "all_aggregation_levels_pass": all(row["registered_style_pass"] for row in aggregation.values()),
        "publisher_cluster_p_le_0.05": preserving["publisher_namespace"]["cluster_sign_flip_p"] <= 0.05,
        "architecture_cluster_p_le_0.05": preserving["implementation_architecture"]["cluster_sign_flip_p"] <= 0.05,
        "worst_loo_ci_positive_and_p_le_0.05": loo_full["ci95"][0] > 0 and loo_full["two_sided_p"] <= 0.05,
        "worst_merge_ci_positive_and_p_le_0.05": merge_full["ci95"][0] > 0 and merge_full["two_sided_p"] <= 0.05,
    }

    output = {
        "analysis": "P0y hierarchical-lineage sensitivity",
        "status": "retrospective robustness analysis; does not alter the frozen P0y decision",
        "input_hashes": actual_hashes,
        "targets": len(targets),
        "contrast": "SoftMap minus soft-JS NDCG@5",
        "aggregation_levels": aggregation,
        "registered_reproduction": reproduction_checks,
        "estimand_preserving_cluster_inference": preserving,
        "estimand_preserving_cluster_definitions": cluster_definitions,
        "leave_one_declared_lineage_out": {
            "analyses": len(loo_rows),
            "mean_range": [min(row["mean"] for row in loo_rows), max(row["mean"] for row in loo_rows)],
            "positive_fraction_range": [min(row["positive_fraction"] for row in loo_rows), max(row["positive_fraction"] for row in loo_rows)],
            "worst_mean_case": worst_loo,
            "worst_mean_full_inference": loo_full,
            "all_cases": loo_rows,
        },
        "single_admissible_lineage_merge": {
            "analyses": len(merge_rows),
            "mean_range": [min(row["mean"] for row in merge_rows), max(row["mean"] for row in merge_rows)],
            "positive_fraction_range": [min(row["positive_fraction"] for row in merge_rows), max(row["positive_fraction"] for row in merge_rows)],
            "worst_mean_case": worst_merge,
            "worst_mean_full_inference": merge_full,
            "all_cases": merge_rows,
        },
        "robustness_conditions": robustness_conditions,
        "taxonomy_robust": all(robustness_conditions.values()),
        "interpretation_guardrail": (
            "Publisher namespace and model_type are reproducible coarsenings used for sensitivity analysis; "
            "they are not asserted to be canonical ancestry."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "aggregation_levels": {name: {key: row[key] for key in (
            "groups", "mean", "ci95", "two_sided_p", "positive_groups", "positive_fraction", "registered_style_pass"
        )} for name, row in aggregation.items()},
        "cluster_inference": preserving,
        "worst_loo": output["leave_one_declared_lineage_out"]["worst_mean_case"],
        "worst_loo_inference": {key: loo_full[key] for key in ("mean", "ci95", "two_sided_p", "positive_fraction")},
        "worst_merge": output["single_admissible_lineage_merge"]["worst_mean_case"],
        "worst_merge_inference": {key: merge_full[key] for key in ("mean", "ci95", "two_sided_p", "positive_fraction")},
        "robustness_conditions": robustness_conditions,
        "taxonomy_robust": output["taxonomy_robust"],
    }, indent=2))


if __name__ == "__main__":
    main()
