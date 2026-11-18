import os

import pytest
from sqlalchemy import text

from pharmatrials.storage import initialize_database, make_engine, upsert_studies


def test_postgres_schema_and_upsert_are_repeatable():
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is configured by the PostgreSQL CI service")

    nct_id = "NCT99999001"
    raw = [{"protocolSection": {"identificationModule": {"nctId": nct_id}}}]
    row = {
        "nct_id": nct_id,
        "brief_title": "Storage integration test",
        "official_title": None,
        "overall_status": "RECRUITING",
        "study_type": "INTERVENTIONAL",
        "phases": ["PHASE2"],
        "start_date": "2025-01",
        "primary_completion_date": None,
        "completion_date": None,
        "enrollment_count": 42,
        "enrollment_type": "ESTIMATED",
        "lead_sponsor_name": "Example Sponsor",
        "lead_sponsor_class": "INDUSTRY",
        "last_update_posted_date": None,
        "has_results": False,
        "source_url": f"https://clinicaltrials.gov/study/{nct_id}",
        "conditions": ["Type 2 Diabetes"],
        "interventions": [{
            "name": "Example Drug", "intervention_type": "DRUG", "description": None
        }],
        "locations": [{
            "facility": "Example Hospital", "city": "Hyderabad",
            "state": "Telangana", "country": "India", "location_status": "RECRUITING"
        }],
    }

    engine = make_engine(database_url)
    try:
        initialize_database(engine)
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM raw_studies WHERE nct_id=:nct_id"), {"nct_id": nct_id}
            )
            connection.execute(
                text("DELETE FROM studies WHERE nct_id=:nct_id"), {"nct_id": nct_id}
            )

        upsert_studies(engine, raw, [row])
        upsert_studies(engine, raw, [row])

        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT COUNT(*) FROM studies WHERE nct_id=:nct_id"),
                {"nct_id": nct_id},
            ).scalar_one() == 1
            assert connection.execute(
                text("SELECT COUNT(*) FROM study_conditions WHERE nct_id=:nct_id"),
                {"nct_id": nct_id},
            ).scalar_one() == 1
            assert connection.execute(
                text("SELECT COUNT(*) FROM study_interventions WHERE nct_id=:nct_id"),
                {"nct_id": nct_id},
            ).scalar_one() == 1
            assert connection.execute(
                text("SELECT COUNT(*) FROM study_locations WHERE nct_id=:nct_id"),
                {"nct_id": nct_id},
            ).scalar_one() == 1
            stored_id = connection.execute(
                text(
                    "SELECT payload->'protocolSection'->'identificationModule'->>'nctId' "
                    "FROM raw_studies WHERE nct_id=:nct_id"
                ),
                {"nct_id": nct_id},
            ).scalar_one()
            assert stored_id == nct_id
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM raw_studies WHERE nct_id=:nct_id"), {"nct_id": nct_id}
            )
            connection.execute(
                text("DELETE FROM studies WHERE nct_id=:nct_id"), {"nct_id": nct_id}
            )
        engine.dispose()
