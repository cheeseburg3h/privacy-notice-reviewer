from __future__ import annotations
from app.assessment.control_matrix import load_control_matrix, pasal_numbers_for_control


def test_control_matrix_has_required_controls() -> None:
    controls = load_control_matrix("data/legal_sources/uu_pdp_27_2022/legal_control_matrix_uu_pdp.csv")
    assert len(controls) == 21
    assert controls[0]["control_id"] == "PNR-001"
    assert controls[-1]["control_id"] == "PNR-021"


def test_control_matrix_source_ids_parse_to_expected_pasals() -> None:
    required_pasals: set[str] = set()
    for control in load_control_matrix("data/legal_sources/uu_pdp_27_2022/legal_control_matrix_uu_pdp.csv"):
        required_pasals.update(pasal_numbers_for_control(control))
    assert {"1", "20", "21", "46", "56", "57"}.issubset(required_pasals)
    assert len(required_pasals) >= 40
