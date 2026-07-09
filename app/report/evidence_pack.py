from __future__ import annotations

from pathlib import Path
from typing import Any

from app.io_utils import write_json


def build_evidence_pack(assessment: dict[str, Any]) -> dict[str, Any]:
    legal_evidence = []
    notice_evidence = []
    for finding in assessment.get("findings", []):
        for ref in finding.get("uu_pdp_reference", []):
            legal_evidence.append(
                {
                    "finding_id": finding.get("finding_id"),
                    "control_id": finding.get("control_id"),
                    **ref,
                }
            )
        if finding.get("evidence_status") == "No Evidence Found":
            notice_evidence.append(
                {
                    "finding_id": finding.get("finding_id"),
                    "control_id": finding.get("control_id"),
                    "evidence_status": "No Evidence Found",
                    "excerpt": "No Evidence Found",
                }
            )
        for ref in finding.get("notice_evidence", []):
            notice_evidence.append(
                {
                    "finding_id": finding.get("finding_id"),
                    "control_id": finding.get("control_id"),
                    **ref,
                }
            )
    return {
        "model_name": assessment.get("model_name"),
        "company_name": assessment.get("company_name"),
        "document_reviewed": assessment.get("document_reviewed"),
        "company_context": assessment.get("company_context", {}),
        "legal_evidence": legal_evidence,
        "notice_evidence": notice_evidence,
        "audit_metadata": assessment.get("audit_metadata", {}),
    }


def write_evidence_pack(assessment: dict[str, Any], output_dir: str | Path) -> Path:
    path = Path(output_dir) / "evidence_pack.json"
    write_json(path, build_evidence_pack(assessment))
    return path
