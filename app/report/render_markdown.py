from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.io_utils import read_json
from app.report.evidence_pack import write_evidence_pack


def _join(values: list[Any]) -> str:
    return "; ".join(str(value) for value in values if value)


def _evidence_text(finding: dict[str, Any]) -> str:
    if finding.get("evidence_status") == "No Evidence Found":
        return "No Evidence Found"
    excerpts = [item.get("excerpt", "") for item in finding.get("notice_evidence", [])[:2]]
    return " / ".join(excerpt for excerpt in excerpts if excerpt)


def render_markdown(assessment: dict[str, Any]) -> str:
    summary = assessment["executive_summary"]
    context = assessment.get("company_context", {})
    lines: list[str] = [
        "# Privacy Notice Gap Assessment Review",
        "",
        "## 1. Executive Summary",
        f"- Overall rating: {summary['overall_rating']}",
        f"- Key strengths: {_join(summary.get('key_strengths', []))}",
        f"- Priority gaps: {_join(summary.get('priority_gaps', []))}",
        f"- Limitations: {_join(assessment.get('limitations', []))}",
        "",
        "## 2. Scope and Methodology",
        f"- Company: {assessment.get('company_name')}",
        f"- Document reviewed: {assessment['document_reviewed'].get('title')} ({assessment['document_reviewed'].get('source_type')})",
        f"- Source location: {assessment['document_reviewed'].get('source_location')}",
        f"- Primary law: {assessment['assessment_scope'].get('primary_law')}",
        f"- Company aliases considered: {_join(context.get('company_aliases', [])) or 'None supplied'}",
        f"- Detected or supplied sectors: {_join(context.get('sectors', [])) or 'None detected'}",
        f"- User or stakeholder roles considered: {_join(context.get('user_roles', [])) or 'None supplied'}",
        f"- Company-specific research focus: {_join(context.get('research_focus', [])) or 'None identified'}",
        "- Method: article-level UU PDP retrieval, notice evidence retrieval, deterministic control assessment, Hallucination Guard validation.",
        "- Flexibility note: aspect names remain standardized for reporting, while retrieval expands to company-specific labels, product terms, and sector vocabulary.",
        "- Human review requirement: output is draft reviewer support and is not final legal advice.",
        "",
        "## 3. Gap Assessment by Aspect",
        "| Aspect | UU PDP Reference | Status | Severity | Evidence | Gap | Recommendation | Scope | Owner |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for finding in assessment.get("findings", []):
        pasals = ", ".join(f"Pasal {ref.get('pasal')}" for ref in finding.get("uu_pdp_reference", []))
        lines.append(
            "| "
            + " | ".join(
                [
                    str(finding.get("aspect", "")).replace("|", "/"),
                    pasals.replace("|", "/"),
                    str(finding.get("status", "")).replace("|", "/"),
                    str(finding.get("severity", "")).replace("|", "/"),
                    _evidence_text(finding).replace("|", "/"),
                    str(finding.get("gap_explanation", "")).replace("|", "/"),
                    str(finding.get("recommendation", "")).replace("|", "/"),
                    _join(finding.get("recommendation_scope", [])).replace("|", "/"),
                    _join(finding.get("suggested_owner", [])).replace("|", "/"),
                ]
            )
            + " |"
        )

    by_pasal: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in assessment.get("findings", []):
        for ref in finding.get("uu_pdp_reference", []):
            by_pasal[str(ref.get("pasal"))].append(finding)

    lines.extend(["", "## 4. Detailed Findings Per Pasal"])
    for pasal in sorted(by_pasal, key=lambda value: int(value) if value.isdigit() else 999):
        lines.append(f"### Pasal {pasal}")
        for finding in by_pasal[pasal]:
            lines.append(
                f"- {finding['finding_id']} {finding['control_id']} - {finding['status']} / {finding['severity']}: {finding['gap_explanation']}"
            )

    lines.extend(["", "## 5. Recommendations Roadmap", "### Immediate 0-30 days"])
    for finding in assessment.get("findings", []):
        if finding["severity"] in {"Critical", "High"} and finding["status"] != "Addressed":
            lines.append(f"- {finding['control_id']}: {finding['recommendation']}")
    lines.append("### Short Term 30-90 days")
    for finding in assessment.get("findings", []):
        if finding["severity"] == "Medium" and finding["status"] != "Addressed":
            lines.append(f"- {finding['control_id']}: {finding['recommendation']}")
    lines.append("### Medium Term 90-180 days")
    for finding in assessment.get("findings", []):
        if finding["severity"] in {"Low", "Info"}:
            lines.append(f"- {finding['control_id']}: Validate and maintain evidence for {finding['aspect']}.")

    lines.extend(["", "## 6. Questions and Evidence Requests for Client"])
    for question in assessment.get("questions_for_client", []):
        lines.append(f"- {question['related_control_id']}: {question['question']} Reason: {question['reason']}")

    lines.extend(["", "## 7. Hallucination and Evidence Check"])
    for finding in assessment.get("findings", []):
        guard = finding.get("hallucination_guard_result", {})
        lines.append(
            f"- {finding['finding_id']}: legal citation verified={guard.get('legal_citation_verified')}; "
            f"notice evidence verified={guard.get('notice_evidence_verified')}; notes={guard.get('notes')}"
        )

    lines.extend(["", "## 8. Appendix", "- Legal control matrix: data/legal_sources/uu_pdp_27_2022/legal_control_matrix_uu_pdp.csv", "- Evidence extracts: evidence_pack.json"])
    return "\n".join(lines) + "\n"


def render_file(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    assessment = read_json(input_path)
    output = Path(output_path) if output_path else Path(input_path).with_suffix(".md")
    output.write_text(render_markdown(assessment), encoding="utf-8", newline="\n")
    write_evidence_pack(assessment, output.parent)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Markdown report from assessment JSON.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    output = render_file(args.input, args.output)
    print(f"Wrote Markdown report to {output}")


if __name__ == "__main__":
    main()
