from __future__ import annotations

from typing import Any

from app.retrieval.hybrid_retriever import retrieve_notice_chunks


def _term_groups(required_terms: str | None) -> list[list[str]]:
    groups: list[list[str]] = []
    if not required_terms:
        return groups
    for group in required_terms.split(";"):
        alternatives = [term.strip().lower() for term in group.split("|") if term.strip()]
        if alternatives:
            groups.append(alternatives)
    return groups


def evidence_coverage(control: dict[str, str], evidence: list[dict[str, Any]]) -> tuple[float, list[str]]:
    groups = _term_groups(control.get("required_terms"))
    if not groups:
        return (1.0 if evidence else 0.0), []
    haystack = " ".join(f"{item.get('heading', '')} {item.get('text', '')}" for item in evidence).lower()
    matched: list[str] = []
    for alternatives in groups:
        if any(term in haystack for term in alternatives):
            matched.append("|".join(alternatives))
    return len(matched) / len(groups), matched


def _is_noise_for_control(control_id: str, chunk: dict[str, Any]) -> bool:
    text = f"{chunk.get('heading', '')} {chunk.get('text', '')}".lower()
    if text.strip().startswith("from <"):
        return True
    if len(text) < 140 and any(
        marker in text
        for marker in (
            "privacy notice",
            "kebijakan privasi",
            "anda berada di",
            "for individual",
            "for business",
            "login untuk",
            "back ",
            "search indonesia",
            "kantor cabang",
            "pusat bantuan",
        )
    ):
        return True
    if control_id == "PNR-010":
        notice_update_terms = ("memperbarui kebijakan privasi", "pembaruan pemberitahuan privasi", "update to this privacy")
        data_update_terms = ("memperbarui data", "pembaruan data", "memperbaiki data", "koreksi data", "correct your data")
        if any(term in text for term in notice_update_terms) and not any(term in text for term in data_update_terms):
            return True
    if control_id == "PNR-020":
        transfer_context = (
            "luar negeri",
            "luar wilayah indonesia",
            "lintas batas",
            "internasional",
            "cross-border",
            "overseas",
            "negara lain",
            "outside indonesia",
        )
        data_transfer = ("transfer data", "pemindahan data", "pengalihan data")
        payment_context = ("pembayaran", "payment", "bank transfer", "transfer yang dilakukan")
        if not (any(term in text for term in transfer_context) or any(term in text for term in data_transfer)):
            return True
        if any(term in text for term in payment_context) and not any(term in text for term in transfer_context):
            return True
    return False


def find_notice_evidence(control: dict[str, str], notice_chunks: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    candidates = retrieve_notice_chunks(control, notice_chunks, top_k=top_k + 4)
    filtered = [chunk for chunk in candidates if not _is_noise_for_control(control["control_id"], chunk)]
    return filtered[:top_k]
