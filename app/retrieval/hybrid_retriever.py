from __future__ import annotations

from typing import Any

from app.retrieval.bm25 import SimpleBM25, keyword_score


def _split_terms(value: str | None) -> list[str]:
    if not value:
        return []
    terms: list[str] = []
    for part in value.replace("|", ";").split(";"):
        cleaned = part.strip()
        if cleaned:
            terms.append(cleaned)
    return terms


def retrieve_notice_chunks(control: dict[str, str], notice_chunks: list[dict[str, Any]], top_k: int = 7) -> list[dict[str, Any]]:
    if not notice_chunks:
        return []

    query_parts = [
        control.get("aspect", ""),
        control.get("review_question", ""),
        control.get("expected_evidence", ""),
        control.get("keywords", ""),
        control.get("required_terms", ""),
    ]
    query = " ".join(part for part in query_parts if part)
    bm25 = SimpleBM25([chunk.get("text", "") for chunk in notice_chunks])
    bm25_scores = bm25.scores(query)
    keywords = _split_terms(control.get("keywords")) + _split_terms(control.get("required_terms"))

    ranked: list[tuple[float, dict[str, Any]]] = []
    for chunk, bm25_score in zip(notice_chunks, bm25_scores, strict=True):
        text = f"{chunk.get('heading', '')} {chunk.get('text', '')}"
        score = bm25_score + keyword_score(text, keywords)
        if score > 0:
            ranked.append((score, chunk))

    ranked.sort(key=lambda item: item[0], reverse=True)
    evidence: list[dict[str, Any]] = []
    for score, chunk in ranked[:top_k]:
        enriched = dict(chunk)
        enriched["retrieval_score"] = round(score, 4)
        evidence.append(enriched)
    return evidence

