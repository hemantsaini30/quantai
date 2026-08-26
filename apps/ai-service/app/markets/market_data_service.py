# FILE LOCATION: quantai/apps/ai-service/app/markets/market_data_service.py
"""
All yfinance calls live here, isolated from the router so this fetch/
transform logic can be unit-tested without needing a live network call
in every test (mock this module's functions instead).
"""

import yfinance as yf

from app.markets.universe import get_equities, get_indices


def _safe_get(info, attr_name):
    try:
        return getattr(info, attr_name)
    except (KeyError, AttributeError):
        return None


def fetch_quote_snapshot(symbol: str) -> dict:
    """
    Returns a single symbol's current snapshot: last price, change, % change.
    Uses yfinance's fast_info where possible (lighter than full history download).

    NOTE: fast_info is a yfinance.scrapers.quote.FastInfo object, NOT a plain
    dict — attributes must be accessed as info.last_price, not info.get("last_price")
    (the latter silently returns None for every field without erroring).

    NOTE: yfinance calls Yahoo Finance's unofficial API over the network. This
    can fail for reasons outside our control — rate limiting (HTTP 429),
    temporary network issues, or Yahoo changing their response format. A
    failure fetching ONE symbol should never crash the whole endpoint, so
    every failure mode here is caught and turned into a "no data" result
    rather than an unhandled exception.
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


def get_indices_snapshot(market: str) -> list[dict]:
    indices = get_indices(market)
    results = []
    for idx in indices:
        snapshot = fetch_quote_snapshot(idx["symbol"])
        snapshot["name"] = idx["name"]
        results.append(snapshot)
    return results


def get_equities_snapshot(market: str) -> list[dict]:
    """
    Fetches a snapshot for every equity in the starter universe for this
    market, ONCE. This is the single source of truth that gainers/losers/
    most-active/sector views all derive from via pure in-memory sorting —
    none of those functions make their own yfinance calls anymore (see
    the "N+1 yfinance calls" fix below).
    """
    equities = get_equities(market)
    results = []
    for eq in equities:
        try:
            snapshot = fetch_quote_snapshot(eq["symbol"])
        except Exception:
            # A single bad/delisted symbol shouldn't break the whole dashboard.
            continue
        snapshot["name"] = eq["name"]
        snapshot["sector"] = eq["sector"]
        results.append(snapshot)
    return results


def get_top_gainers(market: str, limit: int = 5, snapshot: list[dict] | None = None) -> list[dict]:
    """
    snapshot can be passed in (already-fetched equities data) to avoid a
    redundant yfinance re-fetch when called as part of get_market_overview.
    If not passed, fetches fresh — used when this endpoint is hit on its own.
    """
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
    redundant pass over yfinance. This is the fix for a real problem seen
    live: the old approach made ~40 yfinance calls per dashboard load
    (10 symbols x 4 derived views), which triggered Yahoo's rate limiting
    (HTTP 429) almost immediately. This version makes 10 (equities) + a
    couple (indices) calls per load instead.
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
    Used for the interactive price chart on a single stock's page (later phase).
    period follows yfinance's format: '1mo', '3mo', '6mo', '1y', '5y', etc.
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
    Phase 1 search is a simple substring match against the starter universe
    (name or symbol). This is NOT a live yfinance search — good enough until
    the universe grows large enough to need a real search index.
    """
    query_lower = query.lower()
    equities = get_equities(market)
    return [
        eq
        for eq in equities
        if query_lower in eq["symbol"].lower() or query_lower in eq["name"].lower()
    ]