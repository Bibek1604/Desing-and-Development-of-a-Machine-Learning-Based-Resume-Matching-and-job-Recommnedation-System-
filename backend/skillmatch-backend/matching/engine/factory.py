from django.conf import settings

from .base import BaseMatcher
from .tfidf import TfidfMatcher
from .semantic import SentenceTransformerMatcher
from .hybrid import HybridMatcher

_REGISTRY: dict[str, type[BaseMatcher]] = {
    "tfidf":    TfidfMatcher,
    "semantic": SentenceTransformerMatcher,
    "hybrid":   HybridMatcher,
}


def get_matcher(backend: str | None = None) -> BaseMatcher:
    """Return the configured matcher instance.

    Resolve priority: explicit arg > MATCHER_BACKEND env setting > hybrid.
    """
    key = (backend or getattr(settings, "MATCHER_BACKEND", "hybrid")).lower()
    matcher_cls = _REGISTRY.get(key, HybridMatcher)
    return matcher_cls()
