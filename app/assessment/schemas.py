from __future__ import annotations

APPROVED_STATUSES = {
    "Addressed",
    "Partially Addressed",
    "Not Evidenced in Notice",
    "Potential Gap",
    "Contradictory / Ambiguous",
    "Not Applicable Based on Available Evidence",
    "Requires Human Legal Review",
}

APPROVED_SEVERITIES = {"Critical", "High", "Medium", "Low", "Info"}

APPROVED_SCOPES = {
    "Privacy Notice Wording",
    "Consent Mechanism",
    "Data Subject Rights / DSAR Process",
    "Retention and Deletion Governance",
    "Security Governance",
    "Third-Party / Processor Governance",
    "Cross-Border Transfer Governance",
    "Breach Response and Notification",
    "Automated Decision-Making / Profiling",
    "DPIA / High-Risk Processing",
    "PDP Officer / Privacy Governance",
    "Underlying Evidence Required",
    "Legal Review Required",
}

APPROVED_OWNERS = {
    "Legal / Compliance",
    "Data Protection Officer / PDP Function",
    "Cybersecurity / Information Security",
    "IT Governance",
    "Product Owner",
    "Data Governance",
    "Procurement / Vendor Management",
    "Customer Service / DSAR Team",
    "Incident Response Team",
    "Management / Risk Committee",
}


def validate_assessment_shape(payload: dict) -> list[str]:
    errors: list[str] = []
    if payload.get("model_name") != "Privacy Notice Reviewer":
        errors.append("model_name must be Privacy Notice Reviewer")
    if not isinstance(payload.get("findings"), list):
        errors.append("findings must be a list")
        return errors
    for index, finding in enumerate(payload["findings"], start=1):
        prefix = f"findings[{index}]"
        if finding.get("status") not in APPROVED_STATUSES:
            errors.append(f"{prefix}.status is not approved: {finding.get('status')}")
        if finding.get("severity") not in APPROVED_SEVERITIES:
            errors.append(f"{prefix}.severity is not approved: {finding.get('severity')}")
        if not finding.get("uu_pdp_reference"):
            errors.append(f"{prefix}.uu_pdp_reference is required")
        for scope in finding.get("recommendation_scope", []):
            if scope not in APPROVED_SCOPES:
                errors.append(f"{prefix}.recommendation_scope has invalid value: {scope}")
        for owner in finding.get("suggested_owner", []):
            if owner not in APPROVED_OWNERS:
                errors.append(f"{prefix}.suggested_owner has invalid value: {owner}")
        confidence = finding.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
            errors.append(f"{prefix}.confidence must be between 0 and 1")
    return errors

