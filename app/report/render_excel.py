from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.io_utils import read_json
from app.report.evidence_pack import build_evidence_pack, write_evidence_pack
from app.report.simple_xlsx import write_xlsx


def _join(values: list[Any]) -> str:
    return "; ".join(str(value) for value in values if value is not None)


def _pasals(finding: dict[str, Any]) -> str:
    return "; ".join(f"Pasal {ref.get('pasal')}" for ref in finding.get("uu_pdp_reference", []))


def _ayat_huruf(finding: dict[str, Any]) -> str:
    values = []
    for ref in finding.get("uu_pdp_reference", []):
        ayat = ref.get("ayat")
        huruf = ref.get("huruf")
        values.append(f"{ayat or '-'} / {huruf or '-'}")
    return "; ".join(values)


def _legal_evidence(finding: dict[str, Any]) -> str:
    return " || ".join(ref.get("retrieved_legal_excerpt", "") for ref in finding.get("uu_pdp_reference", [])[:3])


def _notice_evidence(finding: dict[str, Any]) -> str:
    if finding.get("evidence_status") == "No Evidence Found":
        return "No Evidence Found"
    return " || ".join(item.get("excerpt", "") for item in finding.get("notice_evidence", [])[:3])


def build_workbook_rows(assessment: dict[str, Any]) -> dict[str, list[list[Any]]]:
    summary = assessment["executive_summary"]
    context = assessment.get("company_context", {})
    sheets: dict[str, list[list[Any]]] = {
        "Executive Summary": [
            ["Field", "Value"],
            ["Company", assessment.get("company_name")],
            ["Document", assessment["document_reviewed"].get("title")],
            ["Overall Rating", summary.get("overall_rating")],
            ["Company Aliases Considered", _join(context.get("company_aliases", []))],
            ["Detected or Supplied Sectors", _join(context.get("sectors", []))],
            ["User or Stakeholder Roles", _join(context.get("user_roles", []))],
            ["Research Focus", _join(context.get("research_focus", []))],
            ["Key Strengths", _join(summary.get("key_strengths", []))],
            ["Priority Gaps", _join(summary.get("priority_gaps", []))],
            ["Human Review Notes", _join(summary.get("human_review_notes", []))],
        ]
    }

    gap_header = [
        "Finding ID",
        "Aspect",
        "Control ID",
        "Company Aspect Label",
        "UU PDP Pasal",
        "UU PDP Ayat/Huruf",
        "Status",
        "Severity",
        "Confidence",
        "Notice Evidence",
        "Legal Evidence",
        "Gap Explanation",
        "Risk Explanation",
        "Recommendation",
        "Recommendation Scope",
        "Suggested Owner",
        "Supporting Document Needed",
        "Human Review Required",
        "Hallucination Guard Result",
    ]
    gap_rows = [gap_header]
    for finding in assessment.get("findings", []):
        guard = finding.get("hallucination_guard_result", {})
        gap_rows.append(
            [
                finding.get("finding_id"),
                finding.get("aspect"),
                finding.get("control_id"),
                finding.get("company_aspect_label"),
                _pasals(finding),
                _ayat_huruf(finding),
                finding.get("status"),
                finding.get("severity"),
                finding.get("confidence"),
                _notice_evidence(finding),
                _legal_evidence(finding),
                finding.get("gap_explanation"),
                finding.get("risk_explanation"),
                finding.get("recommendation"),
                _join(finding.get("recommendation_scope", [])),
                _join(finding.get("suggested_owner", [])),
                "Yes" if finding.get("requires_supporting_document") else "No",
                "Yes" if finding.get("status") == "Requires Human Legal Review" else "No",
                json.dumps(guard, ensure_ascii=False),
            ]
        )
    sheets["Gap Assessment"] = gap_rows

    per_pasal = [["Pasal", "Finding ID", "Control ID", "Aspect", "Status", "Severity", "Legal Evidence"]]
    for finding in assessment.get("findings", []):
        for ref in finding.get("uu_pdp_reference", []):
            per_pasal.append(
                [
                    ref.get("pasal"),
                    finding.get("finding_id"),
                    finding.get("control_id"),
                    finding.get("aspect"),
                    finding.get("status"),
                    finding.get("severity"),
                    ref.get("retrieved_legal_excerpt"),
                ]
            )
    sheets["Per Pasal Review"] = per_pasal

    recommendations = [["Finding ID", "Control ID", "Severity", "Recommendation", "Scope", "Owner", "Supporting Documents"]]
    for finding in assessment.get("findings", []):
        recommendations.append(
            [
                finding.get("finding_id"),
                finding.get("control_id"),
                finding.get("severity"),
                finding.get("recommendation"),
                _join(finding.get("recommendation_scope", [])),
                _join(finding.get("suggested_owner", [])),
                _join(finding.get("supporting_document_requested", [])),
            ]
        )
    sheets["Recommendations"] = recommendations

    pack = build_evidence_pack(assessment)
    evidence_rows = [["Type", "Finding ID", "Control ID", "Source ID", "Page/Section", "Excerpt"]]
    for item in pack["legal_evidence"]:
        evidence_rows.append(["Legal", item.get("finding_id"), item.get("control_id"), item.get("source_id"), f"Pasal {item.get('pasal')}", item.get("retrieved_legal_excerpt")])
    for item in pack["notice_evidence"]:
        evidence_rows.append(["Notice", item.get("finding_id"), item.get("control_id"), item.get("source_id"), item.get("page_or_section"), item.get("excerpt")])
    sheets["Evidence Pack"] = evidence_rows

    questions = [["Related Control ID", "Question", "Reason"]]
    for question in assessment.get("questions_for_client", []):
        questions.append([question.get("related_control_id"), question.get("question"), question.get("reason")])
    sheets["Questions for Client"] = questions

    hallucination = [["Finding ID", "Legal Citation Verified", "Notice Evidence Verified", "Unsupported Claims Removed", "Notes"]]
    for finding in assessment.get("findings", []):
        guard = finding.get("hallucination_guard_result", {})
        hallucination.append(
            [
                finding.get("finding_id"),
                guard.get("legal_citation_verified"),
                guard.get("notice_evidence_verified"),
                guard.get("unsupported_claims_removed"),
                guard.get("notes"),
            ]
        )
    sheets["Hallucination Check"] = hallucination
    return sheets


def render_file(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    assessment = read_json(input_path)
    output = Path(output_path) if output_path else Path(input_path).with_suffix(".xlsx")
    write_xlsx(output, build_workbook_rows(assessment))
    write_evidence_pack(assessment, output.parent)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Excel report from assessment JSON.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    output = render_file(args.input, args.output)
    print(f"Wrote Excel report to {output}")


if __name__ == "__main__":
    main()
