from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def keyword_score(text: str, terms: Iterable[str]) -> float:
    tokens = set(tokenize(text))
    score = 0.0
    lowered = text.lower()
    for raw_term in terms:
        term = raw_term.strip().lower()
        if not term:
            continue
        if " " in term and term in lowered:
            score += 2.5
            continue
        if term in tokens:
            score += 1.0
    return score


class SimpleBM25:
    def __init__(self, documents: list[str]) -> None:
        self.documents = documents
        self.tokenized = [tokenize(document) for document in documents]
        self.doc_count = len(documents)
        self.avg_len = sum(len(tokens) for tokens in self.tokenized) / self.doc_count if self.doc_count else 0.0
        self.df: Counter[str] = Counter()
        for tokens in self.tokenized:
            self.df.update(set(tokens))

    def scores(self, query: str, k1: float = 1.5, b: float = 0.75) -> list[float]:
        query_tokens = tokenize(query)
        scores: list[float] = []
        for tokens in self.tokenized:
            frequencies = Counter(tokens)
            doc_len = len(tokens) or 1
            score = 0.0
            for token in query_tokens:
                df = self.df.get(token, 0)
                if df == 0:
                    continue
                idf = math.log(1 + (self.doc_count - df + 0.5) / (df + 0.5))
                numerator = frequencies[token] * (k1 + 1)
                denominator = frequencies[token] + k1 * (1 - b + b * doc_len / (self.avg_len or 1))
                score += idf * numerator / (denominator or 1)
            scores.append(score)
        return scores

