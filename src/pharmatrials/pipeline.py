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
    raw_by_id: dict[str, dict[str, Any]] = {}
    raw_without_id: list[dict[str, Any]] = []

    for condition in conditions:
        logger.info("Extracting condition: %s", condition)
        for study in client.iter_studies(condition, page_size=page_size, max_pages=max_pages):
            protocol = study.get("protocolSection") or {}
            ident = protocol.get("identificationModule") or {}
            nct_id = ident.get("nctId")
            if nct_id:
                raw_by_id[nct_id] = study
            else:
                raw_without_id.append(study)

    raw_studies = list(raw_by_id.values()) + raw_without_id
    records = [normalize_study(study) for study in raw_studies]
    issues = inspect_records(records)
    quality = summarize_quality(records, issues)

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "raw_studies.jsonl"
    with raw_path.open("w", encoding="utf-8") as stream:
        for study in raw_studies:
            stream.write(json.dumps(study, ensure_ascii=False) + "\n")

    issue_dicts = [issue.to_dict() for issue in issues]
    export_paths = write_exports(records, issue_dicts, output_dir)
    quality_path = output_dir / "quality_summary.json"
    quality_path.write_text(json.dumps(quality, indent=2), encoding="utf-8")

    database_loaded = False
    if database_url:
        engine = make_engine(database_url)
        try:
            initialize_database(engine)
            upsert_studies(engine, raw_studies, records)
            database_loaded = True
        finally:
            engine.dispose()

    return {
        "records_extracted": len(raw_studies),
        "unique_studies": len(raw_by_id),
        "quality": quality,
        "database_loaded": database_loaded,
        "raw_jsonl": str(raw_path),
        **export_paths,
    }
