from __future__ import annotations

from copy import deepcopy
from typing import Any

UNSUPPORTED_LIABILITY_TERMS = {
    "violates": "may create compliance risk under",
    "violate": "may create compliance risk under",
    "illegal": "requires legal review",
    "unlawful": "requires legal review",
    "non-compliant": "requires legal review",
    "non compliant": "requires legal review",
}


def _soften_liability(text: str) -> tuple[str, bool]:
    lowered = text.lower()
    changed = False
    result = text
    for risky, replacement in UNSUPPORTED_LIABILITY_TERMS.items():
        if risky in lowered:
            result = result.replace(risky, replacement)
            result = result.replace(risky.title(), replacement)
            changed = True
    return result, changed


def guard_finding(finding: dict[str, Any]) -> dict[str, Any]:
    guarded = deepcopy(finding)
    refs = guarded.get("uu_pdp_reference") or []
    legal_ok = bool(refs) and all(ref.get("source_id") and ref.get("retrieved_legal_excerpt") for ref in refs)
    evidence_status = guarded.get("evidence_status")
    evidence = guarded.get("notice_evidence") or []
    notice_ok = evidence_status == "No Evidence Found" or all(item.get("excerpt") for item in evidence)
    changed = False

    for key in ("gap_explanation", "risk_explanation", "recommendation"):
        softened, did_change = _soften_liability(str(guarded.get(key, "")))
        guarded[key] = softened
        changed = changed or did_change

    if not legal_ok or not notice_ok:
        guarded["status"] = "Requires Human Legal Review"
        guarded["severity"] = "High" if guarded.get("severity") in {"Critical", "High"} else "Medium"
        changed = True

    guarded["hallucination_guard_result"] = {
        "legal_citation_verified": bool(legal_ok),
        "notice_evidence_verified": bool(notice_ok),
        "unsupported_claims_removed": bool(changed or (legal_ok and notice_ok)),
        "notes": (
            "Finding is supported by legal citation and notice evidence marker."
            if legal_ok and notice_ok
            else "Finding requires human review because legal citation or notice evidence support is incomplete."
        ),
    }
    return guarded
