# FILE LOCATION: quantai/apps/ai-service/app/markets/twelvedata_client.py
"""
Twelve Data client with automatic API key rotation.

Twelve Data's free tier rate-limits per key (roughly 8 requests/minute,
800/day per key as of when this was written — verify current limits at
https://twelvedata.com/pricing if behavior seems off). With 5 keys, we
round-robin across them, and if a key comes back rate-limited, we
immediately retry the same request with the next key rather than failing
the whole call.

Free tier also does NOT reliably cover individual Indian (NSE) equities —
only US market data and a specific set of supported global indices
(NIFTY 50 among them). Routing logic for which market uses this client
lives in market_data_service.py, not here — this module only knows how
to make a Twelve Data request and rotate keys, not which requests it
should be making.
"""

import os
import httpx

TWELVE_DATA_BASE_URL = "https://api.twelvedata.com"

# Rate-limit / quota-exceeded indicators from Twelve Data. Their API
# returns HTTP 200 with an error code in the JSON body for some failure
# modes (not just HTTP-level 429), so we check both.
RATE_LIMIT_CODES = {429, 400}
RATE_LIMIT_MESSAGE_MARKERS = ("run out of api credits", "api rate limit")


def _get_api_keys() -> list[str]:
    """
    Reads all configured TWELVE_API_KEY* env vars, in order, skipping any
    that are unset or empty. Re-read on every call (not cached at import
    time) so tests can freely monkeypatch os.environ.
    """
    keys = []
    for i in range(1, 6):
        key = os.environ.get(f"TWELVE_API_KEY{i}")
        if key:
            keys.append(key)
    return keys


def _is_rate_limit_response(response: httpx.Response) -> bool:
    if response.status_code in RATE_LIMIT_CODES:
        try:
            body = response.json()
        except Exception:
            return response.status_code == 429
        message = str(body.get("message", "")).lower()
        if any(marker in message for marker in RATE_LIMIT_MESSAGE_MARKERS):
            return True
        return response.status_code == 429
    return False


class TwelveDataAllKeysExhaustedError(Exception):
    """Raised when every configured API key has been rate-limited or failed."""


def fetch_quote(symbol: str) -> dict:
    """
    Fetches a real-time quote for a single symbol from Twelve Data's
    /quote endpoint, rotating through configured API keys on rate-limit
    responses.

    Returns the raw parsed JSON body from Twelve Data on success.
    Raises TwelveDataAllKeysExhaustedError if every key is rate-limited
    or every request otherwise fails.
    """
    keys = _get_api_keys()
    if not keys:
        raise TwelveDataAllKeysExhaustedError("No Twelve Data API keys configured")

    last_error = None

    for key in keys:
        try:
            response = httpx.get(
                f"{TWELVE_DATA_BASE_URL}/quote",
                params={"symbol": symbol, "apikey": key},
                timeout=8.0,
            )
        except httpx.HTTPError as exc:
            last_error = exc
            continue

        if _is_rate_limit_response(response):
            last_error = f"Rate limited on key ending in ...{key[-4:]}"
            continue

        if response.status_code != 200:
            last_error = f"HTTP {response.status_code} on key ending in ...{key[-4:]}"
            continue

        body = response.json()
        # Twelve Data returns HTTP 200 with a "code"/"message" error body
        # for some invalid-symbol or other failures too.
        if isinstance(body, dict) and body.get("status") == "error":
            last_error = body.get("message", "Unknown Twelve Data error")
            continue

        return body

    raise TwelveDataAllKeysExhaustedError(
        f"All {len(keys)} Twelve Data key(s) exhausted or failed for '{symbol}'. Last error: {last_error}"
    )