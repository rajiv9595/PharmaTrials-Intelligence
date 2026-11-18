-- PostgreSQL schema for the public ClinicalTrials.gov registry dataset.
CREATE TABLE IF NOT EXISTS raw_studies (
    nct_id TEXT PRIMARY KEY,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS studies (
    nct_id TEXT PRIMARY KEY,
    brief_title TEXT,
    official_title TEXT,
    overall_status TEXT,
    study_type TEXT,
    phases TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    start_date TEXT,
    primary_completion_date TEXT,
    completion_date TEXT,
    enrollment_count INTEGER CHECK (enrollment_count IS NULL OR enrollment_count >= 0),
    enrollment_type TEXT,
    lead_sponsor_name TEXT,
    lead_sponsor_class TEXT,
    last_update_posted_date TEXT,
    has_results BOOLEAN NOT NULL DEFAULT FALSE,
    source_url TEXT NOT NULL,
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS study_conditions (
    nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
    condition TEXT NOT NULL,
    PRIMARY KEY (nct_id, condition)
);

CREATE TABLE IF NOT EXISTS study_interventions (
    nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
    intervention_key TEXT NOT NULL,
    name TEXT NOT NULL,
    intervention_type TEXT,
    description TEXT,
    PRIMARY KEY (nct_id, intervention_key)
);

CREATE TABLE IF NOT EXISTS study_locations (
    nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
    location_key TEXT NOT NULL,
    facility TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    location_status TEXT,
    PRIMARY KEY (nct_id, location_key)
);

CREATE INDEX IF NOT EXISTS idx_studies_status ON studies(overall_status);
CREATE INDEX IF NOT EXISTS idx_studies_sponsor ON studies(lead_sponsor_name);
CREATE INDEX IF NOT EXISTS idx_studies_type ON studies(study_type);
CREATE INDEX IF NOT EXISTS idx_study_locations_country ON study_locations(country);
CREATE INDEX IF NOT EXISTS idx_study_conditions_condition ON study_conditions(condition);
