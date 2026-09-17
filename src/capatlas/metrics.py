from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def soft_js_distance(left: np.ndarray, right: np.ndarray) -> float:
    """Mean square-root Jensen--Shannon distance over probe distributions."""
    p = _probabilities(left)
    q = _probabilities(right)
    if p.shape != q.shape:
        raise ValueError("probe arrays must have identical shapes")
    midpoint = 0.5 * (p + q)
    kl_p = np.sum(np.where(p > 0, p * np.log(p / midpoint), 0.0), axis=1)
    kl_q = np.sum(np.where(q > 0, q * np.log(q / midpoint), 0.0), axis=1)
    return float(np.mean(np.sqrt(0.5 * (kl_p + kl_q))))


def ndcg_at_k(ranking: Sequence[str], relevance: dict[str, float], k: int = 5) -> float:
    """NDCG@k for a ranked list and non-negative graded relevance."""
    if k < 1:
        raise ValueError("k must be positive")
    gains = np.asarray([relevance[item] for item in ranking[:k]], dtype=float)
    if np.any(gains < 0) or not np.all(np.isfinite(gains)):
        raise ValueError("relevance must be finite and non-negative")
    discounts = 1.0 / np.log2(np.arange(2, len(gains) + 2))
    dcg = float(np.sum(gains * discounts))
    ideal = np.sort(np.asarray(list(relevance.values()), dtype=float))[::-1][:k]
    idcg = float(np.sum(ideal * discounts[: len(ideal)]))
    return dcg / idcg if idcg > 0 else 0.0


def recall_at_k(predicted: Sequence[str], oracle: Sequence[str], k: int = 5) -> float:
    if k < 1:
        raise ValueError("k must be positive")
    truth = set(oracle[:k])
    if len(truth) != k:
        raise ValueError("oracle Top-k must contain k unique items")
    return len(set(predicted[:k]) & truth) / k


def _probabilities(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[1] < 2:
        raise ValueError("probabilities must have shape [probes, choices]")
    if np.any(array < 0) or not np.all(np.isfinite(array)):
        raise ValueError("probabilities must be finite and non-negative")
    totals = array.sum(axis=1, keepdims=True)
    if np.any(totals <= 0):
        raise ValueError("each probe distribution must have positive mass")
    array = array / totals
    return np.clip(array, np.finfo(float).tiny, 1.0)
