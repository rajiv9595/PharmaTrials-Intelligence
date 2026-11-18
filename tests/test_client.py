from pharmatrials.client import ClinicalTrialsClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return self.responses.pop(0)


def test_client_follows_page_tokens_until_the_api_returns_no_next_token():
    session = FakeSession([
        FakeResponse({"studies": [{"id": 1}], "nextPageToken": "next-page"}),
        FakeResponse({"studies": [{"id": 2}]}),
    ])
    client = ClinicalTrialsClient(session=session)
    studies = list(client.iter_studies("Type 2 Diabetes", page_size=20))
    assert studies == [{"id": 1}, {"id": 2}]
    assert session.calls[0]["params"]["query.cond"] == "Type 2 Diabetes"
    assert "pageToken" not in session.calls[0]["params"]
    assert session.calls[1]["params"]["pageToken"] == "next-page"


def test_client_rejects_page_sizes_above_api_limit():
    client = ClinicalTrialsClient(session=FakeSession([]))
    try:
        list(client.iter_studies("diabetes", page_size=1001))
    except ValueError as exc:
        assert "1000" in str(exc)
    else:
        raise AssertionError("Expected page_size validation to fail")
