from __future__ import annotations

from app.assessment.control_matrix import split_semicolon

SUPPORTING_DOCUMENTS = {
    "PNR-004": ["DSAR SOP", "Data subject request workflow"],
    "PNR-007": ["Consent records", "Consent capture screenshots", "Withdrawal workflow"],
    "PNR-012": ["DPIA / high-risk processing assessment", "Automated decision-making inventory"],
    "PNR-013": ["Security control summary", "Information security policy"],
    "PNR-014": ["Data retention schedule", "Deletion and destruction SOP"],
    "PNR-015": ["Incident response plan", "Breach notification SOP"],
    "PNR-018": ["Processor/vendor list", "Data processing agreements"],
    "PNR-019": ["PDP officer appointment or privacy governance charter"],
    "PNR-020": ["Cross-border transfer assessment", "Transfer safeguard evidence"],
}

RECOMMENDATIONS = {
    "PNR-001": "Clarify the responsible entity, service scope, and whether the organization acts as controller, processor, or another operational role for the notice.",
    "PNR-002": "Add or refine a data category table that distinguishes general personal data from specific or sensitive personal data where relevant.",
    "PNR-003": "State the identity, purpose, legal basis, and accountability of the party requesting or processing personal data.",
    "PNR-004": "Expand the data subject rights section with request channels, verification steps, expected handling process, and any lawful limitations.",
    "PNR-005": "Map each major processing purpose to a stated UU PDP processing basis and escalate the mapping for legal review.",
    "PNR-006": "Where consent is used, disclose the consent-specific information elements, including purpose, data type, retention or processing period, and withdrawal rights.",
    "PNR-007": "Document the consent mechanism and supporting evidence showing explicit, written, or recorded consent where required.",
    "PNR-008": "Add child and disability data handling language where the service processes those data categories or targets those users.",
    "PNR-009": "Rewrite broad purpose language into specific, limited, and transparent processing purposes tied to data categories or service functions.",
    "PNR-010": "Explain how users can update, correct, or complete inaccurate personal data and how the request is handled.",
    "PNR-011": "Clarify how users can access their personal data, request copies, or obtain relevant processing history where applicable.",
    "PNR-012": "Identify automated decision-making, profiling, large-scale, specific-data, or new-technology processing and determine whether DPIA evidence is required.",
    "PNR-013": "Describe reasonable security and confidentiality safeguards without making absolute security claims.",
    "PNR-014": "Add retention criteria or periods, withdrawal, restriction, deletion, destruction, and related notification wording.",
    "PNR-015": "Align the notice and supporting incident process with personal data breach notification expectations.",
    "PNR-016": "Assign privacy accountability through a privacy contact, PDP function, DPO, or equivalent governance owner.",
    "PNR-017": "Add wording for personal data transfer in merger, acquisition, restructuring, dissolution, or similar corporate events.",
    "PNR-018": "Identify processor or third-party categories, describe processing roles, and summarize safeguards or contractual controls.",
    "PNR-019": "Assess whether PDP officer triggers apply and identify the privacy function or contact point if applicable.",
    "PNR-020": "Disclose domestic and cross-border transfer categories, destination context where available, and transfer safeguards or legal basis.",
    "PNR-021": "Use sanctions only as risk context and avoid any final legal liability statement without human legal confirmation.",
}


def recommendation_for(control: dict[str, str]) -> str:
    return RECOMMENDATIONS.get(control["control_id"], f"Review and strengthen wording for {control['aspect']}.")


def scopes_for(control: dict[str, str], requires_evidence: bool) -> list[str]:
    scopes = split_semicolon(control.get("recommendation_scope"))
    if requires_evidence and "Underlying Evidence Required" not in scopes:
        scopes.append("Underlying Evidence Required")
    return scopes


def owners_for(control: dict[str, str]) -> list[str]:
    return split_semicolon(control.get("suggested_owner"))


def supporting_documents_for(control_id: str, requires_evidence: bool) -> list[str]:
    if not requires_evidence:
        return []
    return SUPPORTING_DOCUMENTS.get(control_id, ["Supporting operational evidence"])

