"""Public CapAtlas reference implementation."""

from .core import CapAtlas, Placement
from .metrics import ndcg_at_k, recall_at_k, soft_js_distance

__all__ = ["CapAtlas", "Placement", "ndcg_at_k", "recall_at_k", "soft_js_distance"]
__version__ = "0.1.0"
