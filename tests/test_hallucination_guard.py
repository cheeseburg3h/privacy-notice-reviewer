from __future__ import annotations

from app.assessment.hallucination_guard import guard_finding


def test_guard_flags_missing_legal_citation() -> None:
    finding = {
        "uu_pdp_reference": [],
        "notice_evidence": [{"excerpt": "We process personal data.", "source_location": "fixture"}],
        "evidence_status": "Supported",
        "status": "Addressed",
        "severity": "Info",
        "gap_explanation": "The company is non-compliant.",
        "risk_explanation": "This violates the law.",
        "recommendation": "Fix the illegal wording.",
    }
    guarded = guard_finding(finding)
    assert guarded["status"] == "Requires Human Legal Review"
    assert guarded["hallucination_guard_result"]["legal_citation_verified"] is False
    assert "violates" not in guarded["risk_explanation"].lower()
    assert "illegal" not in guarded["recommendation"].lower()


def test_guard_accepts_no_evidence_marker() -> None:
    finding = {
        "uu_pdp_reference": [{"source_id": "UU-PDP-2022-P20", "retrieved_legal_excerpt": "Legal text"}],
        "notice_evidence": [],
        "evidence_status": "No Evidence Found",
        "status": "Not Evidenced in Notice",
        "severity": "High",
        "gap_explanation": "Not Evidenced in Notice.",
        "risk_explanation": "May create compliance risk.",
        "recommendation": "Add lawful basis wording.",
    }
    guarded = guard_finding(finding)
    assert guarded["hallucination_guard_result"]["legal_citation_verified"] is True
    assert guarded["hallucination_guard_result"]["notice_evidence_verified"] is True

