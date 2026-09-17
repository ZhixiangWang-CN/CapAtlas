from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class Placement:
    """Output produced before a target oracle is opened."""

    capability_profile: np.ndarray
    ranked_reference_ids: tuple[str, ...]
    distances: np.ndarray

    @property
    def top5(self) -> tuple[str, ...]:
        return self.ranked_reference_ids[:5]


class CapAtlas:
    """Reference-only PCA + multi-output ridge capability map.

    The estimator follows the paper's leakage boundary: all scalers, PCA
    directions, and ridge parameters are fitted on documented references only.
    A target contributes only its frozen behavioral fingerprint.
    """

    def __init__(self, rank: int = 4, alpha: float = 10.0, random_state: int = 20260902):
        if rank < 1 or alpha < 0:
            raise ValueError("rank must be positive and alpha non-negative")
        self.rank = rank
        self.alpha = alpha
        self.random_state = random_state

    def fit(
        self,
        reference_fingerprints: np.ndarray,
        reference_capabilities: np.ndarray,
        reference_ids: Sequence[str],
    ) -> CapAtlas:
        x = _matrix(reference_fingerprints, "reference_fingerprints")
        z = _matrix(reference_capabilities, "reference_capabilities")
        ids = tuple(str(value) for value in reference_ids)
        if len(x) != len(z) or len(ids) != len(x):
            raise ValueError("reference fingerprints, capabilities, and IDs must align")
        if len(set(ids)) != len(ids):
            raise ValueError("reference IDs must be unique")

        effective_rank = min(self.rank, len(x) - 1, x.shape[1])
        if effective_rank < 1:
            raise ValueError("at least two references are required")
        self._x_scaler = StandardScaler().fit(x)
        self._z_scaler = StandardScaler().fit(z)
        x_scaled = self._x_scaler.transform(x)
        self._pca = PCA(n_components=effective_rank, random_state=self.random_state).fit(x_scaled)
        self._ridge = Ridge(alpha=self.alpha).fit(self._pca.transform(x_scaled), self._z_scaler.transform(z))
        self.reference_ids_ = ids
        self.reference_capabilities_ = self._z_scaler.transform(z)
        self.input_width_ = x.shape[1]
        self.effective_rank_ = effective_rank
        return self

    def predict(self, target_fingerprints: np.ndarray) -> np.ndarray:
        self._check_fitted()
        x = _matrix(target_fingerprints, "target_fingerprints", allow_vector=True)
        if x.shape[1] != self.input_width_:
            raise ValueError(f"expected {self.input_width_} fingerprint features, got {x.shape[1]}")
        return self._ridge.predict(self._pca.transform(self._x_scaler.transform(x)))

    def place(self, target_fingerprint: np.ndarray) -> Placement:
        prediction = self.predict(target_fingerprint)
        if len(prediction) != 1:
            raise ValueError("place accepts exactly one target fingerprint")
        distances = np.linalg.norm(self.reference_capabilities_ - prediction[0], axis=1)
        order = np.argsort(distances, kind="stable")
        return Placement(
            capability_profile=prediction[0].copy(),
            ranked_reference_ids=tuple(self.reference_ids_[i] for i in order),
            distances=distances[order].copy(),
        )

    def audit_record(self) -> dict[str, object]:
        self._check_fitted()
        return {
            "reference_rows": len(self.reference_ids_),
            "input_width": self.input_width_,
            "rank": self.effective_rank_,
            "alpha": self.alpha,
            "random_state": self.random_state,
            "fit_scope": "references_only",
        }

    def _check_fitted(self) -> None:
        if not hasattr(self, "_ridge"):
            raise RuntimeError("fit the atlas before prediction")


def _matrix(values: np.ndarray, name: str, allow_vector: bool = False) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if allow_vector and array.ndim == 1:
        array = array[None, :]
    if array.ndim != 2:
        raise ValueError(f"{name} must be a matrix")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains non-finite values")
    return array
