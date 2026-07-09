from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from app.io_utils import read_json

CONTROL_ALIASES: dict[str, list[str]] = {
    "PNR-001": ["data controller", "data processor", "pengelola data", "penanggung jawab data", "platform", "aplikasi"],
    "PNR-002": ["informasi akun", "informasi transaksi", "data pengguna", "data pelanggan", "data mitra", "profil pengguna"],
    "PNR-004": ["hak pengguna", "permintaan pengguna", "akses data", "ubah data", "hapus akun", "keluhan privasi"],
    "PNR-005": ["basis hukum", "legal basis", "lawful basis", "alasan pemrosesan", "kepentingan sah"],
    "PNR-006": ["notifikasi persetujuan", "persetujuan pengguna", "consent notice", "formulir persetujuan"],
    "PNR-007": ["consent log", "rekam persetujuan", "jejak persetujuan", "opt-in", "opt out"],
    "PNR-008": ["anak di bawah umur", "minor", "wali", "orang tua", "aksesibilitas", "disabilitas"],
    "PNR-009": ["tujuan penggunaan", "keperluan layanan", "operasional layanan", "personalisasi", "analitik"],
    "PNR-010": ["ubah profil", "update akun", "edit profil", "perbaiki informasi", "akurasi data"],
    "PNR-011": ["riwayat akun", "riwayat transaksi", "log aktivitas", "salinan data", "download data"],
    "PNR-012": ["profiling", "pemeringkatan", "scoring", "rekomendasi otomatis", "AI", "machine learning"],
    "PNR-013": ["keamanan akun", "perlindungan akun", "enkripsi", "akses terbatas", "sertifikasi keamanan"],
    "PNR-014": ["retensi", "hapus akun", "penutupan akun", "pemusnahan data", "masa simpan"],
    "PNR-015": ["insiden keamanan", "kebocoran data", "pemberitahuan insiden", "data breach"],
    "PNR-016": ["kontak privasi", "tim privasi", "privacy team", "penanggung jawab privasi"],
    "PNR-017": ["pengalihan bisnis", "aksi korporasi", "merger", "akuisisi", "restrukturisasi"],
    "PNR-018": ["vendor", "penyedia layanan", "mitra bisnis", "afiliasi", "kontraktor", "subprosesor"],
    "PNR-019": ["DPO", "data protection officer", "pejabat pelindungan data", "fungsi PDP", "privacy officer"],
    "PNR-020": ["transfer internasional", "luar wilayah indonesia", "cross border", "overseas", "negara tujuan"],
    "PNR-021": ["risiko kepatuhan", "sanksi administratif", "paparan hukum", "legal exposure"],
}

SECTOR_PACKS: dict[str, dict[str, Any]] = {
    "ecommerce": {
        "detection_terms": ["marketplace", "pembeli", "penjual", "merchant", "keranjang", "pesanan", "pengiriman"],
        "primary_terms": ["marketplace", "pembeli", "penjual", "merchant", "pesanan"],
        "user_roles": ["buyer", "seller", "merchant", "customer", "courier"],
        "control_keywords": {
            "PNR-002": ["alamat pengiriman", "riwayat pesanan", "data pembayaran", "ulasan", "wishlist"],
            "PNR-018": ["penjual", "kurir", "payment gateway", "penyedia logistik", "mitra pengiriman"],
            "PNR-020": ["cloud provider", "afiliasi luar negeri", "mitra internasional"],
        },
        "research_focus": ["seller/buyer role split", "payment and logistics vendors", "marketplace ecosystem sharing"],
    },
    "fintech": {
        "detection_terms": ["pinjaman", "paylater", "kredit", "skor kredit", "pembiayaan", "e-wallet", "dompet"],
        "primary_terms": ["pinjaman", "paylater", "kredit", "skor kredit", "pembiayaan", "e-wallet", "dompet"],
        "user_roles": ["borrower", "lender", "cardholder", "payer"],
        "control_keywords": {
            "PNR-002": ["data keuangan", "rekening bank", "skor kredit", "riwayat pembayaran"],
            "PNR-012": ["credit scoring", "skor kredit", "automated decision", "kelayakan kredit"],
            "PNR-020": ["payment processor", "card network", "cross-border payment"],
        },
        "research_focus": ["credit scoring", "financial data categories", "automated eligibility decisions"],
    },
    "ride_hailing": {
        "detection_terms": ["driver", "pengemudi", "mitra", "penumpang", "perjalanan", "lokasi", "maps"],
        "primary_terms": ["driver", "pengemudi", "penumpang", "perjalanan"],
        "user_roles": ["driver", "passenger", "merchant", "courier"],
        "control_keywords": {
            "PNR-002": ["lokasi real-time", "rute perjalanan", "data pengemudi", "data kendaraan"],
            "PNR-012": ["matching", "dispatch", "fraud scoring", "dynamic pricing"],
            "PNR-018": ["merchant", "driver partner", "maps provider", "payment partner"],
        },
        "research_focus": ["location data", "driver-passenger data sharing", "algorithmic matching"],
    },
    "travel": {
        "detection_terms": ["hotel", "penerbangan", "tamu", "booking", "reservasi", "passport", "visa"],
        "primary_terms": ["hotel", "penerbangan", "booking", "reservasi", "passport", "visa"],
        "user_roles": ["guest", "traveler", "passenger", "hotel partner"],
        "control_keywords": {
            "PNR-002": ["nomor paspor", "detail perjalanan", "preferensi tamu", "informasi reservasi"],
            "PNR-018": ["maskapai", "hotel", "agen perjalanan", "global distribution system"],
            "PNR-020": ["hotel luar negeri", "maskapai internasional", "global booking partner"],
        },
        "research_focus": ["passport/travel document data", "hotel/airline transfers", "international booking partners"],
    },
    "health": {
        "detection_terms": ["kesehatan", "rekam medis", "dokter", "klinik", "obat", "pasien", "laboratorium"],
        "primary_terms": ["rekam medis", "dokter", "klinik", "pasien", "laboratorium"],
        "user_roles": ["patient", "doctor", "caregiver"],
        "control_keywords": {
            "PNR-002": ["rekam medis", "data kesehatan", "hasil laboratorium", "resep"],
            "PNR-008": ["pasien anak", "wali pasien", "persetujuan wali"],
            "PNR-012": ["diagnostic support", "risk scoring", "clinical profiling"],
        },
        "research_focus": ["specific personal data", "minor patient consent", "clinical vendor processing"],
    },
    "retail": {
        "detection_terms": ["retail", "loyalty", "member", "store", "gerai", "promo", "poin"],
        "primary_terms": ["retail", "loyalty", "member", "store", "gerai", "poin"],
        "user_roles": ["customer", "member", "store visitor"],
        "control_keywords": {
            "PNR-002": ["membership", "loyalty points", "purchase history", "store visit"],
            "PNR-009": ["loyalty program", "personalized offer", "promosi"],
            "PNR-018": ["loyalty vendor", "marketing partner", "fulfillment partner"],
        },
        "research_focus": ["loyalty data", "marketing partners", "offline-to-online data capture"],
    },
}

GENERAL_NOTICE_ALIASES = [
    "privacy policy",
    "kebijakan privasi",
    "pemberitahuan privasi",
    "privacy notice",
    "data protection notice",
    "notice",
]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def _append_semicolon(existing: str | None, additions: list[str]) -> str:
    values = [part.strip() for part in (existing or "").split(";") if part.strip()]
    return ";".join(_unique(values + additions))


def load_company_profile(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    profile = read_json(path)
    if not isinstance(profile, dict):
        raise ValueError("Company profile must be a JSON object.")
    return profile


def infer_company_context(company: str, notice_chunks: list[dict[str, Any]], profile: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = profile or {}
    text = " ".join(str(chunk.get("text", "")) for chunk in notice_chunks).lower()
    detected_sectors: list[str] = []
    sector_signals: dict[str, list[str]] = {}
    for sector, pack in SECTOR_PACKS.items():
        matched_terms = [term for term in pack["detection_terms"] if term.lower() in text]
        primary_matches = [term for term in pack.get("primary_terms", []) if term.lower() in text]
        if matched_terms:
            sector_signals[sector] = matched_terms
        if len(matched_terms) >= 2 and primary_matches:
            detected_sectors.append(sector)

    profile_sector = profile.get("sector")
    sectors = _unique([str(profile_sector)] if profile_sector else detected_sectors)
    brands = _unique([*profile.get("company_aliases", []), *profile.get("brands", []), company])
    services = _unique(profile.get("services", []))
    user_roles = _unique(profile.get("user_roles", []))
    research_focus = _unique(profile.get("research_focus", []))

    for sector in sectors:
        pack = SECTOR_PACKS.get(sector)
        if not pack:
            continue
        user_roles = _unique(user_roles + pack.get("user_roles", []))
        research_focus = _unique(research_focus + pack.get("research_focus", []))

    return {
        "company_aliases": brands,
        "services": services,
        "sectors": sectors,
        "user_roles": user_roles,
        "notice_title_aliases": _unique(GENERAL_NOTICE_ALIASES + profile.get("notice_title_aliases", [])),
        "research_focus": research_focus,
        "sector_signals": sector_signals,
        "profile_notes": profile.get("notes", []),
        "profile_source": profile.get("profile_source"),
        "external_research_allowed": bool(profile.get("external_research_allowed", False)),
        "control_aliases": profile.get("control_aliases", {}),
    }


def adapt_controls_for_company(controls: list[dict[str, str]], context: dict[str, Any]) -> list[dict[str, str]]:
    adapted = deepcopy(controls)
    sectors = context.get("sectors", [])
    company_terms = _unique([*context.get("company_aliases", []), *context.get("notice_title_aliases", [])])
    service_terms = _unique(context.get("services", []))
    role_terms = _unique(context.get("user_roles", []))
    scoped_common_terms = {
        "PNR-001": _unique(company_terms + service_terms),
        "PNR-002": role_terms,
        "PNR-004": role_terms,
        "PNR-018": _unique(company_terms + service_terms),
    }

    for control in adapted:
        control_id = control["control_id"]
        additions = _unique([*CONTROL_ALIASES.get(control_id, []), *scoped_common_terms.get(control_id, [])])
        for sector in sectors:
            pack = SECTOR_PACKS.get(sector)
            if pack:
                additions = _unique(additions + pack.get("control_keywords", {}).get(control_id, []))

        profile_alias = context.get("control_aliases", {}).get(control_id, {})
        if isinstance(profile_alias, dict):
            additions = _unique(additions + profile_alias.get("keywords", []))
            if profile_alias.get("aspect_label"):
                control["company_aspect_label"] = str(profile_alias["aspect_label"])
            if profile_alias.get("required_terms"):
                control["required_terms"] = _append_semicolon(control.get("required_terms"), profile_alias["required_terms"])

        control["keywords"] = _append_semicolon(control.get("keywords"), additions)
        control["company_context_terms"] = "; ".join(additions)
    return adapted
