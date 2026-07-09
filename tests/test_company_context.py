from __future__ import annotations

from app.assessment.company_context import adapt_controls_for_company, infer_company_context
from app.assessment.control_matrix import load_control_matrix


def test_context_detects_sector_and_adds_sector_terms() -> None:
    chunks = [
        {
            "text": "Pengguna dapat membuat booking hotel dan reservasi penerbangan untuk tamu serta penumpang.",
        }
    ]
    context = infer_company_context("travelco", chunks, {"brands": ["TravelCo"], "services": ["hotel booking"]})
    assert "travel" in context["sectors"]
    assert "TravelCo" in context["company_aliases"]
    assert "guest" in context["user_roles"]

    controls = load_control_matrix("data/legal_sources/uu_pdp_27_2022/legal_control_matrix_uu_pdp.csv")
    adapted = adapt_controls_for_company(controls, context)
    transfer = next(control for control in adapted if control["control_id"] == "PNR-020")
    assert "hotel luar negeri" in transfer["keywords"]
    assert "hotel booking" in transfer["keywords"]


def test_profile_control_alias_can_rename_company_aspect() -> None:
    profile = {
        "sector": "ecommerce",
        "control_aliases": {
            "PNR-018": {
                "aspect_label": "Marketplace vendor ecosystem",
                "keywords": ["payment gateway", "last-mile courier"],
            }
        },
    }
    context = infer_company_context("shopco", [], profile)
    controls = load_control_matrix("data/legal_sources/uu_pdp_27_2022/legal_control_matrix_uu_pdp.csv")
    adapted = adapt_controls_for_company(controls, context)
    processor = next(control for control in adapted if control["control_id"] == "PNR-018")
    assert processor["company_aspect_label"] == "Marketplace vendor ecosystem"
    assert "payment gateway" in processor["keywords"]
    assert "last-mile courier" in processor["keywords"]


def test_single_broad_sector_term_is_only_a_signal() -> None:
    context = infer_company_context("marketco", [{"text": "Kami dapat menggunakan lokasi untuk keamanan akun."}], {})
    assert "ride_hailing" not in context["sectors"]
    assert context["sector_signals"]["ride_hailing"] == ["lokasi"]
