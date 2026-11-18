"""PostgreSQL persistence for raw registry JSON and normalized analytics tables."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, future=True)


def initialize_database(engine: Engine) -> None:
    schema_path = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Database schema not found: {schema_path}")
    statements = [
        part.strip()
        for part in schema_path.read_text(encoding="utf-8").split(";")
        if part.strip()
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)


def _key(*parts: Any) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def upsert_studies(
    engine: Engine, raw_studies: list[dict[str, Any]], rows: list[dict[str, Any]]
) -> None:
    """Upsert study facts and replace each study's child collections atomically."""
    raw_by_id = {}
    for study in raw_studies:
        protocol = study.get("protocolSection") or {}
        ident = protocol.get("identificationModule") or {}
        nct_id = ident.get("nctId")
        if nct_id:
            raw_by_id[nct_id] = study

    study_sql = text("""
        INSERT INTO studies (
            nct_id, brief_title, official_title, overall_status, study_type, phases,
            start_date, primary_completion_date, completion_date, enrollment_count,
            enrollment_type, lead_sponsor_name, lead_sponsor_class,
            last_update_posted_date, has_results, source_url
        ) VALUES (
            :nct_id, :brief_title, :official_title, :overall_status, :study_type, :phases,
            :start_date, :primary_completion_date, :completion_date, :enrollment_count,
            :enrollment_type, :lead_sponsor_name, :lead_sponsor_class,
            :last_update_posted_date, :has_results, :source_url
        ) ON CONFLICT (nct_id) DO UPDATE SET
            brief_title=EXCLUDED.brief_title, official_title=EXCLUDED.official_title,
            overall_status=EXCLUDED.overall_status, study_type=EXCLUDED.study_type,
            phases=EXCLUDED.phases, start_date=EXCLUDED.start_date,
            primary_completion_date=EXCLUDED.primary_completion_date,
            completion_date=EXCLUDED.completion_date, enrollment_count=EXCLUDED.enrollment_count,
            enrollment_type=EXCLUDED.enrollment_type, lead_sponsor_name=EXCLUDED.lead_sponsor_name,
            lead_sponsor_class=EXCLUDED.lead_sponsor_class,
            last_update_posted_date=EXCLUDED.last_update_posted_date,
            has_results=EXCLUDED.has_results, source_url=EXCLUDED.source_url,
            extracted_at=now()
    """)
    with engine.begin() as connection:
        for row in rows:
            nct_id = row.get("nct_id")
            if not nct_id:
                continue
            raw = raw_by_id.get(nct_id)
            if raw is not None:
                connection.execute(text("""
                    INSERT INTO raw_studies (nct_id, payload)
                    VALUES (:nct_id, CAST(:payload AS JSONB))
                    ON CONFLICT (nct_id) DO UPDATE
                    SET payload=EXCLUDED.payload, fetched_at=now()
                """), {"nct_id": nct_id, "payload": json.dumps(raw, ensure_ascii=False)})
            values = {key: row.get(key) for key in (
                "nct_id", "brief_title", "official_title", "overall_status", "study_type", "phases",
                "start_date", "primary_completion_date", "completion_date", "enrollment_count",
                "enrollment_type", "lead_sponsor_name", "lead_sponsor_class",
                "last_update_posted_date", "has_results", "source_url"
            )}
            connection.execute(study_sql, values)
            for table in ("study_conditions", "study_interventions", "study_locations"):
                connection.execute(
                    text(f"DELETE FROM {table} WHERE nct_id = :nct_id"), {"nct_id": nct_id}
                )
            connection.execute(text("""
                INSERT INTO study_conditions (nct_id, condition)
                VALUES (:nct_id, :condition) ON CONFLICT DO NOTHING
            """), [
                {"nct_id": nct_id, "condition": item}
                for item in row.get("conditions", [])
            ])
            interventions = []
            for item in row.get("interventions", []):
                interventions.append({
                    "nct_id": nct_id,
                    "intervention_key": _key(
                        item.get("name"), item.get("intervention_type"), item.get("description")
                    ),
                    "name": item.get("name"),
                    "intervention_type": item.get("intervention_type"),
                    "description": item.get("description"),
                })
            if interventions:
                connection.execute(text("""
                    INSERT INTO study_interventions
                    (nct_id, intervention_key, name, intervention_type, description)
                    VALUES (:nct_id, :intervention_key, :name, :intervention_type, :description)
                    ON CONFLICT DO NOTHING
                """), interventions)
            locations = []
            for item in row.get("locations", []):
                locations.append({
                    "nct_id": nct_id,
                    "location_key": _key(
                        item.get("facility"), item.get("city"), item.get("state"), item.get("country")
                    ),
                    "facility": item.get("facility"),
                    "city": item.get("city"),
                    "state": item.get("state"),
                    "country": item.get("country"),
                    "location_status": item.get("location_status"),
                })
            if locations:
                connection.execute(text("""
                    INSERT INTO study_locations
                    (nct_id, location_key, facility, city, state, country, location_status)
                    VALUES (:nct_id, :location_key, :facility, :city, :state, :country, :location_status)
                    ON CONFLICT DO NOTHING
                """), locations)
