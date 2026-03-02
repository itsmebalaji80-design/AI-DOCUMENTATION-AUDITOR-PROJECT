from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass(frozen=True)
class EmbeddingModel:
    max_features: int = 50_000
    ngram_range: tuple[int, int] = (1, 2)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_vectorizer",
            TfidfVectorizer(
                max_features=self.max_features,
                ngram_range=self.ngram_range,
                lowercase=True,
                strip_accents="unicode",
                token_pattern=r"(?u)\b[\w/\-]+\b",
                norm="l2",
            ),
        )

    def fit_transform(self, texts: list[str]):
        return self._vectorizer.fit_transform(texts)

    def transform(self, texts: list[str]):
        return self._vectorizer.transform(texts)


def cosine_sim_matrix(a, b) -> np.ndarray:
    # TF-IDF vectors are L2-normalized (norm="l2"), so cosine similarity is dot product.
    sims = a @ b.T
    if hasattr(sims, "toarray"):
        sims = sims.toarray()
    return np.asarray(sims, dtype=np.float32)

