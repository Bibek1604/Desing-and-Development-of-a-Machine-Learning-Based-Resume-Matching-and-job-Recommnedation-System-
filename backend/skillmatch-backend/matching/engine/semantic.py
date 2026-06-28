"""Sentence-Transformer semantic similarity matcher.

Uses the all-MiniLM-L6-v2 model (22 MB, fast CPU inference) as the default.
Falls back gracefully to TF-IDF if sentence-transformers is not installed.
"""
from __future__ import annotations
import json
import logging

from .base import BaseMatcher

log = logging.getLogger(__name__)

_MODEL_NAME = "all-MiniLM-L6-v2"


class SentenceTransformerMatcher(BaseMatcher):
    """Semantic similarity using sentence-transformers."""

    name = "semantic"
    _model = None

    # ── Model singleton ───────────────────────────────────────────────────
    @classmethod
    def _get_model(cls):
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                cls._model = SentenceTransformer(_MODEL_NAME)
                log.info("Loaded SentenceTransformer model: %s", _MODEL_NAME)
            except Exception as exc:
                log.warning("sentence-transformers unavailable (%s) — falling back to TF-IDF", exc)
                cls._model = None
        return cls._model

    # ── BaseMatcher interface ─────────────────────────────────────────────
    def similarity(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []
        model = self._get_model()
        if model is None:
            from .tfidf import TfidfMatcher
            return TfidfMatcher().similarity(query, documents)

        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        corpus = [query or ""] + [d or "" for d in documents]
        embeddings = model.encode(corpus, batch_size=64, show_progress_bar=False,
                                  convert_to_numpy=True, normalize_embeddings=True)
        # dot product of normalised vectors == cosine similarity
        scores = (embeddings[0:1] @ embeddings[1:].T).flatten()
        return [max(0.0, float(s)) for s in scores]

    # ── Embed helpers (used by embedding pipeline) ─────────────────────────
    def embed(self, text: str) -> list[float]:
        """Return a flat list[float] embedding for a single text."""
        model = self._get_model()
        if model is None:
            return []
        import numpy as np
        vec = model.encode([text or ""], normalize_embeddings=True)[0]
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        if model is None:
            return [[] for _ in texts]
        import numpy as np
        vecs = model.encode(texts, batch_size=64, show_progress_bar=False,
                            normalize_embeddings=True, convert_to_numpy=True)
        return vecs.tolist()

    @classmethod
    def model_name(cls) -> str:
        return _MODEL_NAME
