"""Small, retry-aware client for the ClinicalTrials.gov API v2."""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_BASE_URL = "https://clinicaltrials.gov/api/v2"


class ClinicalTrialsClient:
    """Read public study records without collecting investigator contact details."""

    def __init__(self, session: requests.Session | None = None, timeout: int = 30) -> None:
        self.timeout = timeout
        self.session = session or requests.Session()
        if session is None:
            retry = Retry(
                total=4,
                connect=4,
                read=4,
                backoff_factor=0.6,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset({"GET"}),
                respect_retry_after_header=True,
            )
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount("https://", adapter)
            self.session.headers.update({
                "User-Agent": "PharmaTrials-Intelligence/0.1 (+educational portfolio project)"
            })

    def iter_studies(
        self,
        condition: str,
        page_size: int = 100,
        max_pages: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield nested study records, following API page tokens until exhausted."""
        if not condition or not condition.strip():
            raise ValueError("condition must be a non-empty search term")
        if not 1 <= page_size <= 1000:
            raise ValueError("page_size must be between 1 and 1000")
        if max_pages is not None and max_pages < 1:
            raise ValueError("max_pages must be at least 1 when provided")

        page_token: str | None = None
        page_number = 0
        while True:
            params: dict[str, Any] = {
                "query.cond": condition.strip(),
                "pageSize": page_size,
                "countTotal": "true",
            }
            if page_token:
                params["pageToken"] = page_token

            response = self.session.get(
                f"{API_BASE_URL}/studies", params=params, timeout=self.timeout
            )
            response.raise_for_status()
            payload = response.json()
            page_number += 1

            for study in payload.get("studies", []):
                if isinstance(study, dict):
                    yield study

            page_token = payload.get("nextPageToken")
            if not page_token or (max_pages is not None and page_number >= max_pages):
                break
