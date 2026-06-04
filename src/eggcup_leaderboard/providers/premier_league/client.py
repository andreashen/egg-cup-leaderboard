"""HTTP client helpers for Premier League JSON APIs."""

from typing import Any, Dict

import httpx

from eggcup_leaderboard.errors import DiscoveryError


def fetch_json(url: str, timeout_seconds: int) -> Dict[str, Any]:
    try:
        response = httpx.get(url, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise DiscoveryError("failed to fetch {url}: {exc}".format(url=url, exc=exc)) from exc
    except ValueError as exc:
        raise DiscoveryError("invalid json from {url}".format(url=url)) from exc

    if not isinstance(payload, dict):
        raise DiscoveryError(
            "unexpected payload type from {url}".format(url=url)
        )

    return payload
