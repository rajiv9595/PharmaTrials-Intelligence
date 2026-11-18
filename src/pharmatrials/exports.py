"""CSV and Excel exports for downstream Power BI and analyst review."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _flat_study(row: dict[str, Any]) -> dict[str, Any]:
    flat = dict(row)
    flat["phases"] = "; ".join(row.get("phases", []))
    flat["conditions"] = "; ".join(row.get("conditions", []))
    flat["interventions"] = "; ".join(
        " — ".join(part for part in (item.get("name"), item.get("intervention_type")) if part)
        for item in row.get("interventions", [])
    )
    flat["locations"] = "; ".join(
        ", ".join(
            part for part in (item.get("city"), item.get("state"), item.get("country")) if part
        )
        for item in row.get("locations", [])
    )
    return flat


def write_exports(
    records: list[dict[str, Any]], issues: list[dict[str, Any]], output_dir: Path
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    studies = [_flat_study(row) for row in records]
    studies_path = output_dir / "studies.csv"
    pd.DataFrame(studies).to_csv(studies_path, index=False, encoding="utf-8-sig")

    condition_rows = [
        {"nct_id": row["nct_id"], "condition": condition}
        for row in records for condition in row.get("conditions", []) if row.get("nct_id")
    ]
    intervention_rows = [
        {"nct_id": row["nct_id"], **intervention}
        for row in records for intervention in row.get("interventions", []) if row.get("nct_id")
    ]
    location_rows = [
        {"nct_id": row["nct_id"], **location}
        for row in records for location in row.get("locations", []) if row.get("nct_id")
    ]

    quality_path = output_dir / "quality_report.json"
    quality_path.write_text(json.dumps({"issues": issues}, indent=2), encoding="utf-8")
    workbook_path = output_dir / "pharma_trials_analysis.xlsx"
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        pd.DataFrame(studies).to_excel(writer, sheet_name="Studies", index=False)
        pd.DataFrame(
            condition_rows, columns=["nct_id", "condition"]
        ).to_excel(writer, sheet_name="Conditions", index=False)
        pd.DataFrame(
            intervention_rows,
            columns=["nct_id", "name", "intervention_type", "description"],
        ).to_excel(writer, sheet_name="Interventions", index=False)
        pd.DataFrame(
            location_rows,
            columns=["nct_id", "facility", "city", "state", "country", "location_status"],
        ).to_excel(writer, sheet_name="Locations", index=False)
        pd.DataFrame(
            issues, columns=["code", "severity", "nct_id", "message"]
        ).to_excel(writer, sheet_name="Data Quality", index=False)

    return {
        "studies_csv": str(studies_path),
        "excel_workbook": str(workbook_path),
        "quality_report": str(quality_path),
    }
