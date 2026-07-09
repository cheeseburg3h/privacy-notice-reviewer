from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.assessment.company_context import adapt_controls_for_company, infer_company_context, load_company_profile
from app.assessment.control_matrix import load_control_matrix, pasal_numbers_for_control
from app.assessment.evidence_extractor import evidence_coverage, find_notice_evidence
from app.assessment.hallucination_guard import guard_finding
from app.assessment.recommendation_engine import (
    owners_for,
    recommendation_for,
    scopes_for,
    supporting_documents_for,
)
from app.assessment.schemas import validate_assessment_shape
from app.config import APP_NAME, JURISDICTION, PRIMARY_LAW
from app.ingestion.clean_text import compact_for_excerpt
from app.io_utils import read_jsonl, write_json

HIGH_IMPORTANCE_CONTROLS = {"PNR-005", "PNR-006", "PNR-014", "PNR-018", "PNR-020"}
GOVERNANCE_CONTROLS = {"PNR-007", "PNR-012", "PNR-013", "PNR-015", "PNR-016", "PNR-019", "PNR-021"}
CONTEXTUAL_CONTROLS = {"PNR-008", "PNR-012", "PNR-017", "PNR-021"}


def _legal_refs(control: dict[str, str], legal_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pasals = set(pasal_numbers_for_control(control))
    refs: list[dict[str, Any]] = []
    for chunk in legal_chunks:
        if str(chunk.get("pasal")) not in pasals:
            continue
        refs.append(
            {
                "pasal": str(chunk.get("pasal")),
                "ayat": chunk.get("ayat"),
                "huruf": chunk.get("huruf"),
                "source_id": chunk.get("source_id"),
                "retrieved_legal_excerpt": chunk.get("legal_excerpt") or compact_for_excerpt(chunk.get("legal_text", ""), 1000),
            }
        )
    return refs


def _notice_refs(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for item in evidence:
        refs.append(
            {
                "excerpt": item.get("excerpt") or compact_for_excerpt(item.get("text", ""), 700),
                "page_or_section": f"page {item.get('page')}" if item.get("page") else item.get("heading"),
                "source_location": item.get("source_location"),
                "source_id": item.get("source_id"),
                "heading": item.get("heading"),
                "retrieval_score": item.get("retrieval_score"),
            }
        )
    return refs


def _status_for(control_id: str, evidence: list[dict[str, Any]], coverage: float) -> tuple[str, str]:
    if not evidence:
        if control_id in CONTEXTUAL_CONTROLS:
            return "Not Applicable Based on Available Evidence", "No Evidence Found"
        return "Not Evidenced in Notice", "No Evidence Found"
    if coverage >= 0.72:
        return "Addressed", "Supported"
    if coverage >= 0.38:
        return "Partially Addressed", "Partially Supported"
    return "Potential Gap", "Partially Supported"


def _severity_for(control_id: str, status: str, output_category: str) -> str:
    if status == "Addressed":
        return "Info"
    if status == "Not Applicable Based on Available Evidence":
        return "Info"
    if status == "Requires Human Legal Review":
        return "Medium"
    if control_id in {"PNR-005", "PNR-006", "PNR-014", "PNR-020"}:
        return "High" if status in {"Not Evidenced in Notice", "Potential Gap"} else "Medium"
    if control_id in GOVERNANCE_CONTROLS or "Governance" in output_category:
        return "Medium"
    return "Medium" if status in {"Not Evidenced in Notice", "Potential Gap"} else "Low"


def _confidence(evidence: list[dict[str, Any]], coverage: float, legal_refs: list[dict[str, Any]]) -> float:
    if not legal_refs:
        return 0.25
    if not evidence:
        return 0.58
    score = 0.45 + min(len(evidence), 5) * 0.055 + coverage * 0.25
    return round(min(0.92, score), 2)


def _gap_explanation(control: dict[str, str], status: str, matched_terms: list[str]) -> str:
    aspect = control["aspect"]
    if status == "Addressed":
        return f"The notice contains evidence addressing {aspect}. Matched evidence themes include: {', '.join(matched_terms[:5]) or 'core control terms'}."
    if status == "Partially Addressed":
        return f"The notice discusses {aspect}, but the retrieved evidence does not cover all expected elements for this UU PDP control."
    if status == "Not Applicable Based on Available Evidence":
        return f"The retrieved notice evidence does not indicate that this contextual control is applicable. This should be verified with the client if the processing activity exists."
    if status == "Not Evidenced in Notice":
        return f"Not Evidenced in Notice: the reviewed notice did not surface wording addressing {aspect}. This is an evidence gap, not a final legal non-compliance conclusion."
    return f"The retrieved wording suggests a potential weakness for {aspect} and should be checked by a human reviewer against operational evidence."


def _risk_explanation(control: dict[str, str], status: str, severity: str) -> str:
    if status in {"Addressed", "Not Applicable Based on Available Evidence"}:
        return "Observation only based on available notice evidence."
    return (
        f"{severity} review priority because weak or missing notice wording for {control['aspect']} "
        "may reduce transparency, auditability, or evidence readiness under the cited UU PDP article(s)."
    )


def _requires_supporting_document(control: dict[str, str], status: str) -> bool:
    output_category = control.get("output_category", "")
    if status != "Addressed":
        return True
    return any(marker in output_category for marker in ("Governance", "Process", "Third-Party", "Transfer"))


def _question_for(control: dict[str, str], status: str) -> dict[str, str] | None:
    if status == "Addressed":
        return None
    label = control.get("company_aspect_label") or control["aspect"]
    return {
        "question": f"Please provide supporting evidence or confirm notice wording for {label}.",
        "reason": f"The assessment classified {control['control_id']} as {status} based on available notice evidence.",
        "related_control_id": control["control_id"],
    }


def _overall_rating(findings: list[dict[str, Any]]) -> str:
    high = sum(1 for item in findings if item["severity"] in {"Critical", "High"} and item["status"] != "Addressed")
    medium = sum(1 for item in findings if item["severity"] == "Medium" and item["status"] != "Addressed")
    if not findings:
        return "Insufficient Evidence"
    if high >= 4:
        return "Critical"
    if high >= 1:
        return "High"
    if medium >= 4:
        return "Moderate"
    if medium:
        return "Moderate"
    return "Low"


def assess(
    company: str,
    notice_chunks_path: str | Path,
    legal_chunks_path: str | Path,
    control_matrix_path: str | Path,
    output_path: str | Path,
    document_title: str | None = None,
    company_profile_path: str | Path | None = None,
) -> dict[str, Any]:
    notice_chunks = read_jsonl(notice_chunks_path)
    legal_chunks = read_jsonl(legal_chunks_path)
    base_controls = load_control_matrix(control_matrix_path)
    company_profile = load_company_profile(company_profile_path)
    company_context = infer_company_context(company, notice_chunks, company_profile)
    controls = adapt_controls_for_company(base_controls, company_context)
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    source_location = str(notice_chunks_path)
    source_type = "text"
    if notice_chunks:
        source_location = str(notice_chunks[0].get("source_location") or notice_chunks_path)
        source_type = str(notice_chunks[0].get("source_type") or source_type)
        document_title = document_title or str(notice_chunks[0].get("document_title") or "Privacy Notice")

    findings: list[dict[str, Any]] = []
    questions: list[dict[str, str]] = []

    for index, control in enumerate(controls, start=1):
        legal_refs = _legal_refs(control, legal_chunks)
        evidence = find_notice_evidence(control, notice_chunks, top_k=5)
        coverage, matched_terms = evidence_coverage(control, evidence)
        status, evidence_status = _status_for(control["control_id"], evidence, coverage)
        severity = _severity_for(control["control_id"], status, control.get("output_category", ""))
        requires_docs = _requires_supporting_document(control, status)

        finding = {
            "finding_id": f"PNR-F-{index:03d}",
            "aspect": control["aspect"],
            "company_aspect_label": control.get("company_aspect_label"),
            "control_id": control["control_id"],
            "uu_pdp_reference": legal_refs,
            "notice_evidence": _notice_refs(evidence),
            "evidence_status": evidence_status,
            "status": status,
            "severity": severity,
            "confidence": _confidence(evidence, coverage, legal_refs),
            "gap_explanation": _gap_explanation(control, status, matched_terms),
            "risk_explanation": _risk_explanation(control, status, severity),
            "recommendation": recommendation_for(control),
            "recommendation_scope": scopes_for(control, requires_docs),
            "suggested_owner": owners_for(control),
            "requires_supporting_document": requires_docs,
            "supporting_document_requested": supporting_documents_for(control["control_id"], requires_docs),
            "matched_terms": matched_terms,
            "company_context_terms": control.get("company_context_terms", ""),
        }
        guarded = guard_finding(finding)
        findings.append(guarded)
        question = _question_for(control, guarded["status"])
        if question:
            questions.append(question)

    strengths = [
        f"{finding['control_id']} {finding['aspect']}"
        for finding in findings
        if finding["status"] == "Addressed"
    ][:5]
    priority_gaps = [
        f"{finding['control_id']} {finding['aspect']}: {finding['status']} ({finding['severity']})"
        for finding in findings
        if finding["severity"] in {"Critical", "High", "Medium"} and finding["status"] != "Addressed"
    ][:8]

    payload = {
        "model_name": APP_NAME,
        "company_name": company,
        "document_reviewed": {
            "title": document_title or "Privacy Notice",
            "source_type": source_type,
            "source_location": source_location,
            "retrieval_timestamp": timestamp,
            "document_date": None,
        },
        "assessment_scope": {
            "primary_law": PRIMARY_LAW,
            "jurisdiction": JURISDICTION,
            "included_sources": [
                str(legal_chunks_path),
                str(notice_chunks_path),
                str(control_matrix_path),
                *([str(company_profile_path)] if company_profile_path else []),
            ],
            "excluded_sources": ["Sectoral laws and implementing regulations not supplied as validated legal sources."],
        },
        "company_context": company_context,
        "executive_summary": {
            "overall_rating": _overall_rating(findings),
            "key_strengths": strengths or ["No strong addressed controls were identified from the retrieved notice evidence."],
            "priority_gaps": priority_gaps or ["No high-priority gaps identified from the available evidence."],
            "human_review_notes": [
                "This automated output supports reviewer triage and is not final legal advice.",
                "Statuses reflect notice evidence only unless supporting documents are listed.",
            ],
        },
        "findings": findings,
        "questions_for_client": questions[:15],
        "limitations": [
            "Assessment is limited to supplied notice chunks and local UU PDP source chunks.",
            "Article-level UU PDP segmentation is used in the MVP; paragraph-level legal refinement is a planned enhancement.",
            "Deterministic retrieval may miss clauses with unusual wording and should be checked by a human reviewer.",
            "Company-specific naming, user roles, sector terms, and service labels are used only to improve evidence retrieval; legal controls remain anchored to UU PDP.",
        ],
        "audit_metadata": {
            "generated_at": timestamp,
            "control_count": len(controls),
            "notice_chunk_count": len(notice_chunks),
            "legal_chunk_count": len(legal_chunks),
            "reviewer_approval_state": "draft_requires_human_review",
        },
    }

    errors = validate_assessment_shape(payload)
    if errors:
        raise ValueError("Assessment schema validation failed: " + "; ".join(errors))
    write_json(output_path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Privacy Notice Reviewer assessment.")
    parser.add_argument("--company", required=True)
    parser.add_argument("--notice", required=True)
    parser.add_argument("--legal", required=True)
    parser.add_argument("--control-matrix", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--document-title")
    parser.add_argument("--company-profile", help="Optional JSON profile with company aliases, sector, services, user roles, and control aliases.")
    args = parser.parse_args()

    payload = assess(
        company=args.company,
        notice_chunks_path=args.notice,
        legal_chunks_path=args.legal,
        control_matrix_path=args.control_matrix,
        output_path=args.output,
        document_title=args.document_title,
        company_profile_path=args.company_profile,
    )
    print(f"Wrote {len(payload['findings'])} findings to {args.output}")


if __name__ == "__main__":
    main()
