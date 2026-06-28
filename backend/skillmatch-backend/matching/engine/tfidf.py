"""TF-IDF + cosine similarity matcher (the thesis baseline).

Tuned for short job/resume texts:
  * 1-2 grams capture phrases ("machine learning", "data engineer")
  * sublinear_tf dampens long-document term spam
  * token pattern keeps tech tokens like c++, c#, node.js, ci-cd
"""
from .base import BaseMatcher

# Keeps programming-language style tokens intact.
TOKEN_PATTERN = r"(?u)\b[a-zA-Z0-9][a-zA-Z0-9+#.\-]*\b"


def build_vectorizer():
    from sklearn.feature_extraction.text import TfidfVectorizer
    return TfidfVectorizer(
        stop_words="english",
        lowercase=True,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
        max_features=60_000,
        token_pattern=TOKEN_PATTERN,
    )


class TfidfMatcher(BaseMatcher):
    name = "tfidf"

    def similarity(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []
        # Imported lazily so the rest of the app does not require scikit-learn
        # just to start (e.g. for `manage.py check` or migrations).
        from sklearn.metrics.pairwise import cosine_similarity

        corpus = [query or ""] + [doc or "" for doc in documents]
        try:
            matrix = build_vectorizer().fit_transform(corpus)
        except ValueError:
            # Empty vocabulary (all stop words / blank) -> no signal.
            return [0.0 for _ in documents]
        scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        return [float(s) for s in scores]
