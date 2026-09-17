import numpy as np

from capatlas import CapAtlas, ndcg_at_k, recall_at_k, soft_js_distance


def test_reference_only_fit_and_placement():
    xref = np.asarray([[0, 0], [1, 0], [0, 1], [1, 1], [2, 1]], dtype=float)
    zref = np.asarray([[0, 0], [1, 0], [0, 1], [1, 1], [2, 1]], dtype=float)
    atlas = CapAtlas(rank=2, alpha=0).fit(xref, zref, ["a", "b", "c", "d", "e"])
    placement = atlas.place(np.asarray([1.9, 1.0]))
    assert placement.ranked_reference_ids[0] == "e"
    assert atlas.audit_record()["fit_scope"] == "references_only"


def test_soft_js_is_symmetric_and_zero_on_identity():
    p = np.asarray([[0.7, 0.2, 0.1], [0.1, 0.2, 0.7]])
    q = np.asarray([[0.2, 0.7, 0.1], [0.2, 0.2, 0.6]])
    assert soft_js_distance(p, p) < 1e-12
    assert np.isclose(soft_js_distance(p, q), soft_js_distance(q, p))


def test_retrieval_metrics():
    ranking = ["a", "b", "c", "d", "e"]
    relevance = {"a": 1.0, "b": 0.8, "c": 0.6, "d": 0.4, "e": 0.2}
    assert np.isclose(ndcg_at_k(ranking, relevance), 1.0)
    assert recall_at_k(ranking, ["a", "b", "x", "y", "z"], 5) == 0.4
