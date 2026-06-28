"""Hybrid matcher: weighted blend of TF-IDF + Sentence-Transformer scores.

Default weights: 30 % TF-IDF  +  70 % semantic.
Override via settings.MATCHER_HYBRID_WEIGHTS = {"tfidf": 0.2, "semantic": 0.8}.
"""
from __future__ import annotations
import logging

from django.conf import settings

from .base import BaseMatcher
from .tfidf import TfidfMatcher
from .semantic import SentenceTransformerMatcher

log = logging.getLogger(__name__)


def _weights() -> tuple[float, float]:
    cfg = getattr(settings, "MATCHER_HYBRID_WEIGHTS", {})
    w_tfidf  = float(cfg.get("tfidf",   0.30))
    w_sem    = float(cfg.get("semantic", 0.70))
    total = w_tfidf + w_sem
    return w_tfidf / total, w_sem / total


class HybridMatcher(BaseMatcher):
    """Combines TF-IDF lexical signal with SBERT semantic signal."""

    name = "hybrid"

    def __init__(self):
        self._tfidf  = TfidfMatcher()
        self._sbert  = SentenceTransformerMatcher()

    def similarity(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []
        w_tf, w_sem = _weights()
        tfidf_scores = self._tfidf.similarity(query, documents)
        sem_scores   = self._sbert.similarity(query, documents)
        blended = [w_tf * t + w_sem * s
                   for t, s in zip(tfidf_scores, sem_scores)]
        return blended
