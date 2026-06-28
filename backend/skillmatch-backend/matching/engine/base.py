"""Matcher interface.

Any matching backend (TF-IDF today, Sentence-BERT tomorrow) implements
`similarity(query, documents)` and returns a cosine-style score in [0, 1]
for each document relative to the query.
"""
from abc import ABC, abstractmethod


class BaseMatcher(ABC):
    name: str = "base"

    @abstractmethod
    def similarity(self, query: str, documents: list[str]) -> list[float]:
        """Return a similarity score in [0, 1] for each document vs. the query."""
        raise NotImplementedError
