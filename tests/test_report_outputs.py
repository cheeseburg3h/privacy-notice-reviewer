from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from app.report.render_excel import build_workbook_rows
from app.report.simple_xlsx import write_xlsx


def test_simple_xlsx_writer_creates_workbook(tmp_path: Path) -> None:
    output = tmp_path / "report.xlsx"
    write_xlsx(output, {"Executive Summary": [["Field", "Value"], ["Overall", "Low"]]})
    with ZipFile(output) as archive:
        names = set(archive.namelist())
    assert "xl/workbook.xml" in names
    assert "xl/worksheets/sheet1.xml" in names


def test_excel_rows_include_required_sheets() -> None:
    assessment = {
        "company_name": "fixture",
        "document_reviewed": {"title": "Fixture Notice"},
        "executive_summary": {"overall_rating": "Low", "key_strengths": [], "priority_gaps": [], "human_review_notes": []},
        "findings": [
            {
                "finding_id": "PNR-F-001",
                "aspect": "Lawful basis",
                "control_id": "PNR-005",
                "uu_pdp_reference": [{"pasal": "20", "ayat": None, "huruf": None, "source_id": "UU-PDP-2022-P20", "retrieved_legal_excerpt": "Legal text"}],
                "notice_evidence": [{"excerpt": "Notice text", "source_id": "NOTICE-1", "page_or_section": "page 1"}],
                "evidence_status": "Supported",
                "status": "Addressed",
                "severity": "Info",
                "confidence": 0.9,
                "gap_explanation": "Supported.",
                "risk_explanation": "Observation.",
                "recommendation": "Maintain.",
                "recommendation_scope": ["Privacy Notice Wording"],
                "suggested_owner": ["Legal / Compliance"],
                "requires_supporting_document": False,
                "supporting_document_requested": [],
                "hallucination_guard_result": {
                    "legal_citation_verified": True,
                    "notice_evidence_verified": True,
                    "unsupported_claims_removed": True,
                    "notes": "ok",
                },
            }
        ],
        "questions_for_client": [],
    }
    sheets = build_workbook_rows(assessment)
    assert {"Executive Summary", "Gap Assessment", "Per Pasal Review", "Recommendations", "Evidence Pack", "Questions for Client", "Hallucination Check"}.issubset(sheets)
    assert "Finding ID" in sheets["Gap Assessment"][0]

