# Privacy Notice Reviewer

Privacy Notice Reviewer is a source-grounded MVP for assessing company privacy notices against Indonesia UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP).

It is intentionally not a chatbot. The pipeline ingests legal and notice documents, segments them into source-grounded chunks, evaluates a fixed UU PDP control matrix, validates findings with a Hallucination Guard pass, and renders JSON, Markdown, Excel, and an evidence pack for human review.

The legal control matrix stays stable, but company terminology is flexible. A company may call the same concept a privacy policy, data protection notice, help center privacy request, account deletion flow, partner ecosystem, merchant platform, guest booking flow, or something else. The assessor therefore infers company context from the uploaded notice and can also accept an optional company profile JSON to expand retrieval terms by sector, brand, service, user role, and control-specific aliases.

## Quick Start

```powershell
python -m app.ingestion.segment_legal `
  --source data/legal_sources/uu_pdp_27_2022/UU_No_27_Tahun_2022_PDP_official.pdf `
  --law "UU PDP" `
  --jurisdiction "Indonesia" `
  --output data/processed/uu_pdp_legal_chunks.jsonl

python -m app.ingestion.segment_notice `
  --company "client_x" `
  --source data/client_inputs/client_x/privacy_notice.pdf `
  --output data/processed/client_x_notice_chunks.jsonl

python -m app.assessment.gap_assessor `
  --company "client_x" `
  --notice data/processed/client_x_notice_chunks.jsonl `
  --legal data/processed/uu_pdp_legal_chunks.jsonl `
  --control-matrix data/legal_sources/uu_pdp_27_2022/legal_control_matrix_uu_pdp.csv `
  --output outputs/client_x/privacy_notice_gap_assessment.json

python -m app.report.render_markdown --input outputs/client_x/privacy_notice_gap_assessment.json
python -m app.report.render_excel --input outputs/client_x/privacy_notice_gap_assessment.json
```

The notice source can be a local PDF, local HTML/text file, or a direct website URL:

```powershell
python -m app.ingestion.segment_notice `
  --company "client_x" `
  --source "https://example.com/privacy" `
  --title "Client X Privacy Notice" `
  --output data/processed/client_x_notice_chunks.jsonl
```

URL ingestion fetches static HTML pages directly. If the URL returns a PDF, the tool extracts the PDF text through a temporary local file and keeps the original URL as the evidence source location. JavaScript-only pages may need a browser-rendered HTML export or uploaded PDF because the MVP URL fetcher does not run a browser.

## Company-Aware Review

Use `--company-profile` when a company uses different product names, user roles, or notice labels than the generic control wording.

```powershell
python -m app.assessment.gap_assessor `
  --company "client_x" `
  --notice data/processed/client_x_notice_chunks.jsonl `
  --legal data/processed/uu_pdp_legal_chunks.jsonl `
  --control-matrix data/legal_sources/uu_pdp_27_2022/legal_control_matrix_uu_pdp.csv `
  --company-profile examples/company_profile.example.json `
  --output outputs/client_x/privacy_notice_gap_assessment.json
```

The profile can define:

- company aliases, brands, services, and user roles;
- sector context such as e-commerce, fintech, ride hailing, travel, health, or retail;
- alternate notice names such as `Kebijakan Privasi`, `Privacy Policy`, or `Data Protection Notice`;
- per-control aliases for company-specific naming, for example `account deletion` for DSAR or `payment gateway` for processor review;
- whether external public research is allowed for the engagement.

The report keeps standardized UU PDP aspects for consistency, while the retrieval layer uses company-specific language to find evidence.

## Output Files

Each assessment writes:

- `privacy_notice_gap_assessment.json`
- `privacy_notice_gap_assessment.md`
- `privacy_notice_gap_assessment.xlsx`
- `evidence_pack.json`

## Guardrails

- Legal findings cite retrieved UU PDP chunks.
- Notice claims cite retrieved notice evidence or say `No Evidence Found`.
- Missing notice evidence is not labeled as non-compliance.
- Client documents are treated as confidential and isolated by company folder.
- Website URL evidence is stored as extracted chunks under the client-specific processed path.
- Company benchmarking and research notes should stay local unless explicitly approved for publication.

## Tests

```powershell
python -m pytest
```
