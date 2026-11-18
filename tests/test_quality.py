from pharmatrials.quality import inspect_records


def test_quality_report_flags_missing_identifiers_duplicate_ids_and_negative_enrollment():
    records = [
        {"nct_id": "NCT00000001", "brief_title": "One", "enrollment_count": 10},
        {"nct_id": "NCT00000001", "brief_title": "Duplicate", "enrollment_count": -1},
        {"nct_id": None, "brief_title": "Missing ID", "enrollment_count": None},
    ]
    issues = inspect_records(records)
    codes = {issue.code for issue in issues}
    assert "duplicate_nct_id" in codes
    assert "missing_nct_id" in codes
    assert "negative_enrollment" in codes


def test_quality_report_warns_when_title_is_missing():
    issues = inspect_records([{"nct_id": "NCT00000002", "brief_title": None}])
    assert any(issue.code == "missing_title" and issue.severity == "warning" for issue in issues)
