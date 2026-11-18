"""Convert ClinicalTrials.gov nested records into a safe, analytics-friendly shape."""
from __future__ import annotations

from typing import Any


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _date(module: dict[str, Any], key: str) -> str | None:
    return _text(_mapping(module.get(key)).get("date"))


def _integer(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_study(study: dict[str, Any]) -> dict[str, Any]:
    """Flatten one registry record; deliberately exclude names/emails/phone contacts."""
    protocol = _mapping(study.get("protocolSection"))
    identification = _mapping(protocol.get("identificationModule"))
    status = _mapping(protocol.get("statusModule"))
    design = _mapping(protocol.get("designModule"))
    enrollment = _mapping(design.get("enrollmentInfo"))
    sponsor_module = _mapping(protocol.get("sponsorCollaboratorsModule"))
    sponsor = _mapping(sponsor_module.get("leadSponsor"))
    conditions_module = _mapping(protocol.get("conditionsModule"))
    intervention_module = _mapping(protocol.get("armsInterventionsModule"))
    location_module = _mapping(protocol.get("contactsLocationsModule"))

    nct_id = _text(identification.get("nctId"))
    phases = [_text(item) for item in _items(design.get("phases"))]
    conditions = sorted({
        text for item in _items(conditions_module.get("conditions")) if (text := _text(item))
    })

    interventions: list[dict[str, str | None]] = []
    for item in _items(intervention_module.get("interventions")):
        item = _mapping(item)
        name = _text(item.get("name"))
        if name:
            interventions.append({
                "name": name,
                "intervention_type": _text(item.get("type")),
                "description": _text(item.get("description")),
            })

    locations: list[dict[str, str | None]] = []
    for item in _items(location_module.get("locations")):
        item = _mapping(item)
        # Keep institutional site attributes only. Investigator/contact PII is excluded.
        location = {
            "facility": _text(item.get("facility")),
            "city": _text(item.get("city")),
            "state": _text(item.get("state")),
            "country": _text(item.get("country")),
            "location_status": _text(item.get("status")),
        }
        if any(location.values()):
            locations.append(location)

    return {
        "nct_id": nct_id,
        "brief_title": _text(identification.get("briefTitle")),
        "official_title": _text(identification.get("officialTitle")),
        "overall_status": _text(status.get("overallStatus")),
        "study_type": _text(design.get("studyType")),
        "phases": [phase for phase in phases if phase],
        "start_date": _date(status, "startDateStruct"),
        "primary_completion_date": _date(status, "primaryCompletionDateStruct"),
        "completion_date": _date(status, "completionDateStruct"),
        "enrollment_count": _integer(enrollment.get("count")),
        "enrollment_type": _text(enrollment.get("type")),
        "lead_sponsor_name": _text(sponsor.get("name")),
        "lead_sponsor_class": _text(sponsor.get("class")),
        "last_update_posted_date": _date(status, "studyLastUpdatePostDateStruct"),
        "has_results": bool(study.get("hasResults", False)),
        "source_url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else None,
        "conditions": conditions,
        "interventions": interventions,
        "locations": locations,
    }
