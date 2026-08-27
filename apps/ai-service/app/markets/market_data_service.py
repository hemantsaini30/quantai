# FILE LOCATION: quantai/apps/ai-service/app/markets/market_data_service.py
"""
All market data fetch/transform logic lives here, isolated from the router
so it can be unit-tested without needing a live network call in every test
(mock this module's functions instead).

Data source routing (added in Phase 1, Section 7b):
  - US equities/indices: Twelve Data (rotating keys) primary, yfinance fallback
  - Indian equities/indices: yfinance only (Twelve Data's free tier does not
    reliably serve individual NSE stocks — only US market data plus a
    specific set of supported global indices)
  - US search: Finnhub primary, local list fallback
  - Indian search: local list only (Finnhub free tier is US-only)
"""

import yfinance as yf

from app.markets.universe import get_equities, get_indices
from app.markets import twelvedata_client
from app.markets import finnhub_client


def _safe_get(info, attr_name):
    try:
        return getattr(info, attr_name)
    except (KeyError, AttributeError):
        return None


def _fetch_quote_from_yfinance(symbol: str) -> dict:
    """
    Returns a single symbol's current snapshot from yfinance: last price,
    change, % change. Uses yfinance's fast_info where possible (lighter
    than full history download).

    NOTE: fast_info is a yfinance.scrapers.quote.FastInfo object, NOT a
    plain dict — attributes must be accessed as info.last_price, not
    info.get("last_price") (the latter silently returns None for every
    field without erroring).

    NOTE: yfinance calls Yahoo Finance's unofficial API over the network.
    This can fail for reasons outside our control — rate limiting (HTTP
    429), temporary network issues, or Yahoo changing their response
    format. A failure fetching ONE symbol should never crash the whole
    endpoint, so every failure mode here is caught and turned into a
    "no data" result rather than an unhandled exception.
    """
    ticker = yf.Ticker(symbol)

    try:
        info = ticker.fast_info
        last_price = _safe_get(info, "last_price")
        previous_close = _safe_get(info, "previous_close")
        day_high = _safe_get(info, "day_high")
        day_low = _safe_get(info, "day_low")
        volume = _safe_get(info, "last_volume")
    except Exception:
        last_price = previous_close = day_high = day_low = volume = None

    change = None
    percent_change = None
    if last_price is not None and previous_close:
        change = last_price - previous_close
        percent_change = (change / previous_close) * 100

    return {
        "symbol": symbol,
        "last_price": last_price,
        "previous_close": previous_close,
        "change": change,
        "percent_change": percent_change,
        "day_high": day_high,
        "day_low": day_low,
        "volume": volume,
    }


def _normalize_twelvedata_quote(symbol: str, body: dict) -> dict:
    """
    Converts Twelve Data's /quote response shape into the same dict shape
    used everywhere else in this app, so callers never need to know which
    source produced a given snapshot. Twelve Data returns numeric-looking
    values as strings, hence the float() conversions.
    """
    def to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    last_price = to_float(body.get("close"))
    previous_close = to_float(body.get("previous_close"))
    change = to_float(body.get("change"))
    percent_change = to_float(body.get("percent_change"))
    volume = to_float(body.get("volume"))

    return {
        "symbol": symbol,
        "last_price": last_price,
        "previous_close": previous_close,
        "change": change,
        "percent_change": percent_change,
        "day_high": to_float(body.get("high")),
        "day_low": to_float(body.get("low")),
        "volume": int(volume) if volume is not None else None,
    }


def fetch_quote_snapshot(symbol: str, market: str = "IN") -> dict:
    """
    Returns a single symbol's current snapshot, routed by market:
      - US: Twelve Data first, yfinance if Twelve Data fails/exhausts keys
      - IN (or anything else): yfinance only

    `market` defaults to "IN" to preserve backward compatibility with any
    existing call site that hasn't been updated to pass it explicitly yet.
    """
    if market.upper() == "US":
        try:
            body = twelvedata_client.fetch_quote(symbol)
            return _normalize_twelvedata_quote(symbol, body)
        except twelvedata_client.TwelveDataAllKeysExhaustedError:
            # Fall through to yfinance below.
            pass

    return _fetch_quote_from_yfinance(symbol)


def get_indices_snapshot(market: str) -> list[dict]:
    indices = get_indices(market)
    results = []
    for idx in indices:
        snapshot = fetch_quote_snapshot(idx["symbol"], market)
        snapshot["name"] = idx["name"]
        results.append(snapshot)
    return results


def get_equities_snapshot(market: str) -> list[dict]:
    """
    Fetches a snapshot for every equity in the starter universe for this
    market, ONCE. This is the single source of truth that gainers/losers/
    most-active/sector views all derive from via pure in-memory sorting —
    none of those functions make their own network calls.
    """
    equities = get_equities(market)
    results = []
    for eq in equities:
        try:
            snapshot = fetch_quote_snapshot(eq["symbol"], market)
        except Exception:
            # A single bad/delisted symbol shouldn't break the whole dashboard.
            continue
        snapshot["name"] = eq["name"]
        snapshot["sector"] = eq["sector"]
        results.append(snapshot)
    return results


def get_top_gainers(market: str, limit: int = 5, snapshot: list[dict] | None = None) -> list[dict]:
    data = snapshot if snapshot is not None else get_equities_snapshot(market)
    filtered = [s for s in data if s["percent_change"] is not None]
    filtered.sort(key=lambda s: s["percent_change"], reverse=True)
    return filtered[:limit]


def get_top_losers(market: str, limit: int = 5, snapshot: list[dict] | None = None) -> list[dict]:
    data = snapshot if snapshot is not None else get_equities_snapshot(market)
    filtered = [s for s in data if s["percent_change"] is not None]
    filtered.sort(key=lambda s: s["percent_change"])
    return filtered[:limit]


def get_most_active(market: str, limit: int = 5, snapshot: list[dict] | None = None) -> list[dict]:
    data = snapshot if snapshot is not None else get_equities_snapshot(market)
    filtered = [s for s in data if s["volume"] is not None]
    filtered.sort(key=lambda s: s["volume"], reverse=True)
    return filtered[:limit]


def get_sector_performance(market: str, snapshot: list[dict] | None = None) -> list[dict]:
    """
    Groups the equity snapshot by sector and averages percent_change.
    Simple mean, not volume/market-cap-weighted — good enough for a Phase 1
    overview; weighted aggregation can be added later without changing the shape.
    """
    data = snapshot if snapshot is not None else get_equities_snapshot(market)
    filtered = [s for s in data if s["percent_change"] is not None]

    sectors: dict[str, list[float]] = {}
    for s in filtered:
        sectors.setdefault(s["sector"], []).append(s["percent_change"])

    return [
        {"sector": sector, "average_percent_change": sum(changes) / len(changes)}
        for sector, changes in sectors.items()
    ]


def get_market_overview(market: str) -> dict:
    """
    Fetches the equity universe ONCE and derives gainers/losers/most-active/
    sectors from that single snapshot, instead of each making its own
    redundant pass over the data source. This is the fix for a real problem
    seen live during Phase 1 development: the old approach made ~40 network
    calls per dashboard load, which triggered Yahoo's rate limiting almost
    immediately. This version makes roughly (equities + indices) calls.
    """
    equities_snapshot = get_equities_snapshot(market)

    return {
        "indices": get_indices_snapshot(market),
        "top_gainers": get_top_gainers(market, snapshot=equities_snapshot),
        "top_losers": get_top_losers(market, snapshot=equities_snapshot),
        "most_active": get_most_active(market, snapshot=equities_snapshot),
        "sector_performance": get_sector_performance(market, snapshot=equities_snapshot),
    }


def get_price_history(symbol: str, period: str = "3mo") -> list[dict]:
    """
    Used for the interactive price chart on a single stock's page (later
    phase). period follows yfinance's format: '1mo', '3mo', '6mo', '1y', '5y'.
    Stays yfinance-only for now — Twelve Data's time_series endpoint has a
    different shape and isn't needed until a chart feature actually exists.
    """
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)

    return [
        {
            "date": index.strftime("%Y-%m-%d"),
            "open": round(row["Open"], 2),
            "high": round(row["High"], 2),
            "low": round(row["Low"], 2),
            "close": round(row["Close"], 2),
            "volume": int(row["Volume"]),
        }
        for index, row in hist.iterrows()
    ]


def search_symbols(query: str, market: str) -> list[dict]:
    """
    Routed search:
      - US: Finnhub first (broader coverage), local list if Finnhub fails
      - IN (or anything else): local list only (Finnhub free tier is US-only)
    """
    if market.upper() == "US":
        try:
            results = finnhub_client.search_us_symbols(query)
            if results:
                return results
        except finnhub_client.FinnhubSearchError:
            pass  # fall through to local list search below

    query_lower = query.lower()
    equities = get_equities(market)
    return [
        eq
        for eq in equities
        if query_lower in eq["symbol"].lower() or query_lower in eq["name"].lower()
    ]