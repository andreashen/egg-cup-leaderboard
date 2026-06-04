import httpx
import pytest

from eggcup_leaderboard.errors import DiscoveryError
from eggcup_leaderboard.providers.premier_league.client import fetch_json


class DummyResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://www.premierleague.com/api/standings")
            raise httpx.HTTPStatusError(
                "bad status",
                request=request,
                response=httpx.Response(self.status_code, request=request),
            )

    def json(self) -> dict:
        return self._payload


def test_fetch_json_returns_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: int) -> DummyResponse:
        assert url == "https://www.premierleague.com/api/standings"
        assert timeout == 5
        return DummyResponse({"tables": []})

    monkeypatch.setattr(httpx, "get", fake_get)

    payload = fetch_json(
        url="https://www.premierleague.com/api/standings",
        timeout_seconds=5,
    )

    assert payload == {"tables": []}


def test_fetch_json_raises_discovery_error_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, timeout: int) -> DummyResponse:
        return DummyResponse({"detail": "missing"}, status_code=404)

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(DiscoveryError):
        fetch_json(
            url="https://www.premierleague.com/api/standings",
            timeout_seconds=5,
        )
