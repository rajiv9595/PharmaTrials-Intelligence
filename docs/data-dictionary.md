# Data dictionary

The pipeline uses public study-registration data from ClinicalTrials.gov API v2. It does not retrieve central contacts, investigator names, emails or telephone numbers.

| Field | Meaning | Source module |
|---|---|---|
| `nct_id` | ClinicalTrials.gov unique study identifier | Identification |
| `brief_title`, `official_title` | Public study titles | Identification |
| `overall_status` | Registered recruitment/status value | Status |
| `study_type`, `phases` | Study design category and registered phases | Design |
| `start_date`, `primary_completion_date`, `completion_date` | Registry date strings; precision may be year or month | Status |
| `enrollment_count`, `enrollment_type` | Registered enrollment value and estimated/actual marker | Design |
| `lead_sponsor_name`, `lead_sponsor_class` | Lead sponsor and registry classification | Sponsor/collaborators |
| `conditions` | Conditions indexed on the registry record | Conditions |
| `interventions` | Intervention name, type and description | Arms/interventions |
| `locations` | Institution/site facility and geographic attributes | Contacts/locations |
| `has_results` | Whether registry results are posted | Top-level registry field |
| `source_url` | Public study record URL | Derived from NCT ID |

**Interpretation limits:** Registry entries are not a complete representation of all research activity. Recruitment status and study phase are registry metadata, not proof of efficacy, safety, quality or regulatory approval. Enrollment counts may be estimated. Date precision is retained as text to avoid inventing missing day/month values.
