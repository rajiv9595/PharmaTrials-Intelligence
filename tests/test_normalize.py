from pharmatrials.normalize import normalize_study


def test_normalize_flattens_clinical_trial_record_without_contact_personal_data():
    study = {
        "hasResults": True,
        "protocolSection": {
            "identificationModule": {"nctId": "NCT12345678", "briefTitle": "Study of Drug A"},
            "statusModule": {
                "overallStatus": "RECRUITING",
                "startDateStruct": {"date": "2025-01"},
                "completionDateStruct": {"date": "2027-06"},
            },
            "designModule": {
                "studyType": "INTERVENTIONAL",
                "phases": ["PHASE2"],
                "enrollmentInfo": {"count": 120, "type": "ESTIMATED"},
            },
            "conditionsModule": {"conditions": ["Type 2 Diabetes", "Diabetes Mellitus"]},
            "sponsorCollaboratorsModule": {
                "leadSponsor": {"name": "Example Pharma", "class": "INDUSTRY"}
            },
            "armsInterventionsModule": {
                "interventions": [
                    {"type": "DRUG", "name": "Drug A", "description": "Study treatment"}
                ]
            },
            "contactsLocationsModule": {
                "centralContacts": [
                    {"name": "Private Person", "email": "person@example.org"}
                ],
                "locations": [{
                    "facility": "Research Hospital", "city": "Hyderabad",
                    "state": "Telangana", "country": "India", "status": "RECRUITING"
                }],
            },
        },
    }
    row = normalize_study(study)
    assert row["nct_id"] == "NCT12345678"
    assert row["brief_title"] == "Study of Drug A"
    assert row["overall_status"] == "RECRUITING"
    assert row["phases"] == ["PHASE2"]
    assert row["enrollment_count"] == 120
    assert row["conditions"] == ["Diabetes Mellitus", "Type 2 Diabetes"]
    assert row["interventions"][0]["name"] == "Drug A"
    assert row["locations"][0]["country"] == "India"
    assert "centralContacts" not in row
    assert "person@example.org" not in str(row)


def test_normalize_handles_missing_optional_modules():
    row = normalize_study({
        "protocolSection": {"identificationModule": {"nctId": "NCT00000001"}}
    })
    assert row["nct_id"] == "NCT00000001"
    assert row["brief_title"] is None
    assert row["phases"] == []
    assert row["conditions"] == []
    assert row["interventions"] == []
    assert row["locations"] == []
