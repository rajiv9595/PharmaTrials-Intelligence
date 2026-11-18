import pandas as pd

from pharmatrials.exports import write_exports


def test_study_csv_includes_location_geography_not_empty_placeholders(tmp_path):
    records = [{
        "nct_id": "NCT00000003",
        "brief_title": "Example trial",
        "phases": ["PHASE2"],
        "conditions": ["Asthma"],
        "interventions": [{"name": "Example drug", "intervention_type": "DRUG"}],
        "locations": [{"city": "Hyderabad", "state": "Telangana", "country": "India"}],
    }]
    write_exports(records, [], tmp_path)
    exported = pd.read_csv(tmp_path / "studies.csv")
    assert "Hyderabad" in exported.loc[0, "locations"]
    assert "India" in exported.loc[0, "locations"]
