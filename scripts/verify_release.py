#!/usr/bin/env python3
"""Verify released artifacts and print the headline paper results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    manifest = json.loads((ROOT / "results/checksums.json").read_text())
    for relative, expected in manifest.items():
        observed = sha256(ROOT / relative)
        if observed != expected:
            raise SystemExit(f"checksum mismatch: {relative}: {observed} != {expected}")

    primary = json.loads((ROOT / "results/p0y_primary.json").read_text())
    hierarchy = json.loads((ROOT / "results/hierarchical_lineage_sensitivity.json").read_text())
    ontology = json.loads((ROOT / "results/p0ae_resolution.json").read_text())
    prospective = json.loads((ROOT / "results/p0ag_results.json").read_text())
    contrast = primary["contrasts"]["C1_softmap_minus_soft_js"]
    if not contrast["declared_better"] or not hierarchy["taxonomy_robust"]:
        raise SystemExit("released primary decision or taxonomy sensitivity does not pass")

    report = {
        "references": primary["references"],
        "targets": primary["targets"],
        "lineages": primary["lineages"],
        "softmap_ndcg5": primary["ndcg5_lineage_macro"]["softmap"],
        "soft_js_ndcg5": primary["ndcg5_lineage_macro"]["soft_js"],
        "paired_difference": contrast["mean"],
        "holm_p": contrast["holm_p"],
        "positive_lineages": f"{contrast['positive_groups']}/{contrast['n']}",
        "taxonomy_robust": hierarchy["taxonomy_robust"],
        "ontology2_kendall_difference": ontology["nested_bootstrap"]["softmap_minus_soft_js"]["kendall_tau"]["mean"],
        "prospective_auroc": prospective["primary"]["auroc"],
        "prospective_precision": prospective["primary"]["selective_precision"],
        "prospective_coverage": prospective["primary"]["coverage"],
        "registered_certificate_decision": prospective["decision"],
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
