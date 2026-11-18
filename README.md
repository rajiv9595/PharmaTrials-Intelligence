# PharmaTrials Intelligence

**Clinical Research Data Analytics & Quality Platform**

An educational portfolio project that extracts public clinical-trial registry records, transforms nested JSON into analytics-ready data, validates data quality, stores normalized records in PostgreSQL, and produces CSV/Excel outputs for Power BI.

> **Scope and safety:** This project uses public study-registration metadata from ClinicalTrials.gov. It does not collect patient-level data or investigator/central-contact personal information. Registry status, phase and results availability are descriptive metadata; they are not evidence of treatment effectiveness, safety, regulatory approval or clinical recommendations.

## Architecture

```text
ClinicalTrials.gov API v2
          |
          v
   Python API client  ---- retry / page-token handling
          |
          v
   Raw JSONL archive
          |
          v
   Normalizer
          |
          +---------> Data-quality checks / JSON report
          |
          +---------> CSV + multi-sheet Excel exports
          |
          v
       PostgreSQL
   raw_studies (JSONB)
   studies (study-level facts)
   study_conditions
   study_interventions
   study_locations
          |
          v
     Power BI report
```

## Technology stack

- Python 3.11+
- ClinicalTrials.gov API v2
- Requests, Pandas, SQLAlchemy
- PostgreSQL 16 and psycopg 3
- Excel export with openpyxl
- Power BI Desktop (connected locally)
- Pytest and GitHub Actions

## Quick start (Windows PowerShell)

### 1. Clone and create the environment

```powershell
git clone https://github.com/rajiv9595/PharmaTrials-Intelligence.git
cd PharmaTrials-Intelligence
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

### 2. Start PostgreSQL

Install Docker Desktop, then run:

```powershell
docker compose up -d postgres
docker compose ps
```

The Compose file creates a local development database named `pharma_trials`. Its sample credentials are for local development only; change them before exposing the database beyond localhost.

### 3. Run the pipeline

```powershell
python -m pharmatrials.cli run --conditions "Type 2 Diabetes" "Breast Cancer" "Hypertension" --page-size 100 --max-pages 2
```

The command extracts up to two pages per condition. Set `--max-pages 0` to follow all available pages. Start small, inspect the output and increase the limit deliberately.

Outputs are written to `data/processed/`:

- `raw_studies.jsonl` — source API records for traceability
- `studies.csv` — flat study-level export for Power BI
- `pharma_trials_analysis.xlsx` — Studies, Conditions, Interventions, Locations and Data Quality sheets
- `quality_report.json` and `quality_summary.json` — issue-level and summary reports

If `DATABASE_URL` is present in `.env`, the pipeline creates/updates the PostgreSQL schema and loads the study facts and related condition, intervention and location records. If the variable is absent, file exports still run and the database load is skipped.

### 4. Run tests

```powershell
python -m pytest
```

### 5. Connect Power BI

Follow [`docs/power-bi-guide.md`](docs/power-bi-guide.md). SQL analysis examples are in [`sql/analytics.sql`](sql/analytics.sql).

## Project layout

```text
src/pharmatrials/   API client, normalization, validation, storage, exports, CLI
sql/                PostgreSQL schema and analytical SQL
tests/              deterministic unit tests (no network or database required)
data/               local raw/processed outputs (ignored by Git)
docs/               data dictionary and Power BI setup
.github/workflows/  CI test workflow
```

## Data source and API behavior

- API base: `https://clinicaltrials.gov/api/v2`
- Search endpoint: `/studies`
- Condition query: `query.cond`
- Cursor pagination: `pageToken` returned by the API as `nextPageToken`
- Page size is restricted to 1–1000 by this client.

The client does not request contact-person records. Site facility and geography fields are retained for aggregate location analysis. The API may return dates with different precision; the pipeline stores date strings rather than guessing missing components.

Official references:

- [ClinicalTrials.gov](https://clinicaltrials.gov/)
- [API documentation](https://clinicaltrials.gov/data-api/api)
- [API metadata](https://clinicaltrials.gov/api/v2/studies/metadata)
- [Data element definitions](https://clinicaltrials.gov/policy/protocol-definitions)

## Initial implementation status

The repository includes API extraction, normalization, quality checks, PostgreSQL persistence, CSV/Excel exports, analytical SQL, Power BI instructions and unit tests. Live API extraction, local PostgreSQL loading and Power BI report creation must be run and verified in the developer's environment; this repository does not claim those environment-specific steps have already been executed.

## Limitations

- The registry is a public registration dataset, not a complete source for all clinical research.
- A study's phase or recruitment status may change; extracts should be timestamped and refreshed for current reporting.
- The first release does not infer causal treatment effects, compare efficacy, assess safety or provide medical advice.
- Power BI `.pbix` files are user-created in Power BI Desktop using the provided data model and guide; the project includes reusable source data and measures, not a prebuilt binary report.

## License

MIT. See [LICENSE](LICENSE).
