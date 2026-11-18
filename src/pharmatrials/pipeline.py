"""Orchestrate extraction, normalization, quality checks, exports and database load."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pharmatrials.client import ClinicalTrialsClient
from pharmatrials.exports import write_exports
from pharmatrials.normalize import normalize_study
from pharmatrials.quality import inspect_records, summarize_quality
from pharmatrials.storage import initialize_database, make_engine, upsert_studies

logger = logging.getLogger(__name__)


def run_pipeline(
    conditions: list[str],
    output_dir: Path,
    page_size: int = 100,
    max_pages: int | None = 2,
    database_url: str | None = None,
) -> dict[str, Any]:
    client = ClinicalTrialsClient()
    extracted_studies: list[dict[str, Any]] = []
    raw_by_id: dict[str, dict[str, Any]] = {}

    for condition in conditions:
        logger.info("Extracting condition: %s", condition)
        for study in client.iter_studies(condition, page_size=page_size, max_pages=max_pages):
            extracted_studies.append(study)
            protocol = study.get("protocolSection") or {}
            ident = protocol.get("identificationModule") or {}
            nct_id = ident.get("nctId")
            if nct_id:
                raw_by_id[nct_id] = study

    # Check all extracted rows before de-duplicating, so duplicate retrievals remain visible.
    extracted_records = [normalize_study(study) for study in extracted_studies]
    issues = inspect_records(extracted_records)
    quality = summarize_quality(extracted_records, issues)

    # Persist/export one latest-seen row per NCT ID; malformed records remain in raw archive
    # and quality report but cannot be safely keyed in the relational model.
    unique_raw_studies = list(raw_by_id.values())
    unique_records = [normalize_study(study) for study in unique_raw_studies]

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "raw_studies.jsonl"
    with raw_path.open("w", encoding="utf-8") as stream:
        for study in extracted_studies:
            stream.write(json.dumps(study, ensure_ascii=False) + "\n")

    issue_dicts = [issue.to_dict() for issue in issues]
    export_paths = write_exports(unique_records, issue_dicts, output_dir)
    quality_path = output_dir / "quality_summary.json"
    quality_path.write_text(json.dumps(quality, indent=2), encoding="utf-8")

    database_loaded = False
    if database_url:
        engine = make_engine(database_url)
        try:
            initialize_database(engine)
            upsert_studies(engine, unique_raw_studies, unique_records)
            database_loaded = True
        finally:
            engine.dispose()

    return {
        "records_extracted": len(extracted_studies),
        "unique_studies": len(unique_records),
        "quality": quality,
        "database_loaded": database_loaded,
        "raw_jsonl": str(raw_path),
        **export_paths,
    }
