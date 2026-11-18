import json

from pharmatrials import pipeline


STUDY = {
    "protocolSection": {
        "identificationModule": {"nctId": "NCT99999999", "briefTitle": "Test study"},
        "statusModule": {"overallStatus": "RECRUITING"},
    }
}


class FakeClient:
    def iter_studies(self, condition, page_size, max_pages):
        yield STUDY


def test_pipeline_reports_cross_query_duplicates_but_exports_one_study(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "ClinicalTrialsClient", FakeClient)

    result = pipeline.run_pipeline(
        conditions=["condition one", "condition two"],
        output_dir=tmp_path,
        page_size=10,
        max_pages=1,
    )

    issue_codes = {item["code"] for item in result["quality"]["issues"]}
    assert result["records_extracted"] == 2
    assert result["unique_studies"] == 1
    assert "duplicate_nct_id" in issue_codes
    assert len((tmp_path / "raw_studies.jsonl").read_text().splitlines()) == 2
    assert (tmp_path / "studies.csv").exists()
    assert (tmp_path / "pharma_trials_analysis.xlsx").exists()
    summary = json.loads((tmp_path / "quality_summary.json").read_text())
    assert summary["records_checked"] == 2
