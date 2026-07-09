from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from app.io_utils import read_json


def _finding_map(assessment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {finding["control_id"]: finding for finding in assessment.get("findings", [])}


def render_comparison(assessments: list[dict[str, Any]]) -> str:
    companies = [assessment.get("company_name", "unknown") for assessment in assessments]
    maps = [_finding_map(assessment) for assessment in assessments]
    control_ids = sorted({control_id for mapping in maps for control_id in mapping})

    lines = [
        "# Privacy Notice Assessment Comparison",
        "",
        "This comparison is generated from assessment JSON outputs. It compares reviewer findings, not the full source notices.",
        "",
        "| Control | Aspect | " + " | ".join(companies) + " |",
        "|---|---|" + "|".join("---" for _ in companies) + "|",
    ]
    for control_id in control_ids:
        first = next((mapping[control_id] for mapping in maps if control_id in mapping), {})
        cells = []
        for mapping in maps:
            finding = mapping.get(control_id)
            if not finding:
                cells.append("Not assessed")
            else:
                cells.append(f"{finding.get('status')} / {finding.get('severity')} / {finding.get('confidence')}")
        lines.append(f"| {control_id} | {str(first.get('aspect', '')).replace('|', '/')} | " + " | ".join(cells) + " |")

    lines.extend(["", "## Priority Gap Delta"])
    for assessment, mapping in zip(assessments, maps, strict=True):
        lines.append(f"### {assessment.get('company_name', 'unknown')}")
        priority = [
            finding
            for finding in mapping.values()
            if finding.get("status") != "Addressed" and finding.get("severity") in {"Critical", "High", "Medium"}
        ]
        if not priority:
            lines.append("- No medium-or-higher gaps in generated assessment.")
        for finding in sorted(priority, key=lambda item: (item.get("severity") != "High", item.get("control_id", ""))):
            lines.append(f"- {finding['control_id']} {finding['aspect']}: {finding['status']} / {finding['severity']}")
    return "\n".join(lines) + "\n"


def render_file(inputs: list[str | Path], output: str | Path) -> Path:
    assessments = [read_json(path) for path in inputs]
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_comparison(assessments), encoding="utf-8", newline="\n")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare multiple Privacy Notice Reviewer assessment JSON files.")
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = render_file(args.inputs, args.output)
    print(f"Wrote comparison report to {output}")


if __name__ == "__main__":
    main()

