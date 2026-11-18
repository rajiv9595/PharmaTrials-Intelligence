"""Transparent data-quality checks for normalized registry records."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class QualityIssue:
    code: str
    severity: str
    nct_id: str | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def inspect_records(records: list[dict[str, Any]]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    counts = Counter(record.get("nct_id") for record in records if record.get("nct_id"))
    duplicate_ids = {nct_id for nct_id, count in counts.items() if count > 1}

    for record in records:
        nct_id = record.get("nct_id")
        if not nct_id:
            issues.append(QualityIssue(
                "missing_nct_id", "error", None, "Study record has no NCT identifier."
            ))
        elif nct_id in duplicate_ids:
            issues.append(QualityIssue(
                "duplicate_nct_id", "warning", nct_id,
                "NCT identifier appears more than once in this extract."
            ))
        if not record.get("brief_title"):
            issues.append(QualityIssue(
                "missing_title", "warning", nct_id, "Study brief title is missing."
            ))
        enrollment = record.get("enrollment_count")
        if enrollment is not None and enrollment < 0:
            issues.append(QualityIssue(
                "negative_enrollment", "error", nct_id, "Enrollment count cannot be negative."
            ))

    return issues


def summarize_quality(
    records: list[dict[str, Any]], issues: list[QualityIssue]
) -> dict[str, Any]:
    return {
        "records_checked": len(records),
        "unique_nct_ids": len({row.get("nct_id") for row in records if row.get("nct_id")}),
        "error_count": sum(issue.severity == "error" for issue in issues),
        "warning_count": sum(issue.severity == "warning" for issue in issues),
        "issues": [issue.to_dict() for issue in issues],
    }
