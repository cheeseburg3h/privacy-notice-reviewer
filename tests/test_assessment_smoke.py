from __future__ import annotations

from pathlib import Path

from app.assessment.gap_assessor import assess
from app.io_utils import write_jsonl


def test_assessment_smoke_generates_21_findings(tmp_path: Path) -> None:
    legal_rows = []
    for pasal in range(1, 77):
        legal_rows.append(
            {
                "source_id": f"UU-PDP-2022-P{pasal}",
                "pasal": str(pasal),
                "ayat": None,
                "huruf": None,
                "legal_text": f"Pasal {pasal} legal fixture text",
                "legal_excerpt": f"Pasal {pasal} legal fixture text",
            }
        )
    notice_rows = [
        {
            "source_id": "NOTICE-FIXTURE-P1-C001",
            "company": "fixture",
            "document_title": "Fixture Privacy Notice",
            "source_type": "text",
            "source_location": "fixture",
            "heading": "Privacy Notice",
            "page": 1,
            "text": "Kami memproses data pribadi untuk tujuan layanan berdasarkan persetujuan dan kontrak. Pengguna memiliki hak akses koreksi hapus dan menarik persetujuan.",
            "excerpt": "Kami memproses data pribadi untuk tujuan layanan berdasarkan persetujuan dan kontrak.",
        }
    ]
    legal_path = tmp_path / "legal.jsonl"
    notice_path = tmp_path / "notice.jsonl"
    output_path = tmp_path / "assessment.json"
    write_jsonl(legal_path, legal_rows)
    write_jsonl(notice_path, notice_rows)

    payload = assess(
        company="fixture",
        notice_chunks_path=notice_path,
        legal_chunks_path=legal_path,
        control_matrix_path="data/legal_sources/uu_pdp_27_2022/legal_control_matrix_uu_pdp.csv",
        output_path=output_path,
    )

    assert output_path.exists()
    assert payload["model_name"] == "Privacy Notice Reviewer"
    assert "company_context" in payload
    assert len(payload["findings"]) == 21
    assert all(finding["uu_pdp_reference"] for finding in payload["findings"])
    assert all("hallucination_guard_result" in finding for finding in payload["findings"])
