# FILE LOCATION: quantai/apps/ai-service/app/markets/finnhub_client.py
"""
Finnhub client for US stock symbol search. Finnhub's free tier is US-only —
international exchanges (including NSE) are premium-gated, so this is only
used for the US market. Indian market search continues to use the local
starter-universe substring match in market_data_service.search_symbols.
"""

import os
import httpx

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


class FinnhubSearchError(Exception):
    """Raised when the Finnhub search request fails outright (not just zero results)."""


def search_us_symbols(query: str) -> list[dict]:
    """
    Searches Finnhub's symbol lookup for US-listed instruments matching
    the query. Returns a list of {symbol, name} dicts, normalized to the
    same shape as market_data_service.search_symbols's local results so
    the router doesn't need to know which source it came from.
    """
    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        raise FinnhubSearchError("FINNHUB_API_KEY is not configured")

    try:
        response = httpx.get(
            f"{FINNHUB_BASE_URL}/search",
            params={"q": query, "token": api_key},
            timeout=8.0,
        )
    except httpx.HTTPError as exc:
        raise FinnhubSearchError(f"Finnhub request failed: {exc}") from exc

    if response.status_code != 200:
        raise FinnhubSearchError(f"Finnhub returned HTTP {response.status_code}")

    body = response.json()
    results = body.get("result", [])

    # Finnhub's raw results include many instrument types (options, etc.)
    # and non-US-suffixed duplicates. Keep it simple for Phase 1: filter to
    # common stock type and cap the result count.
    normalized = []
    for r in results:
        if r.get("type") not in ("Common Stock", "EQS", ""):
            continue
        normalized.append({
            "symbol": r.get("symbol"),
            "name": r.get("description", r.get("symbol")),
            "sector": None,  # Finnhub's search endpoint doesn't return sector
        })

    return normalized[:10]