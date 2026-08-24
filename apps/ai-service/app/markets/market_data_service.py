# FILE LOCATION: quantai/apps/ai-service/app/markets/market_data_service.py
"""
All yfinance calls live here, isolated from the router (built in Section 2)
so this fetch/transform logic can be unit-tested without needing a live
network call in every test (mock this module's functions instead).
"""

import yfinance as yf

from app.markets.universe import get_equities, get_indices


def fetch_quote_snapshot(symbol: str) -> dict:
    """
    Returns a single symbol's current snapshot: last price, change, % change.
    Uses yfinance's fast_info where possible (lighter than full history download).

    NOTE: fast_info is a yfinance.scrapers.quote.FastInfo object, NOT a plain
    dict — attributes must be accessed as info.last_price, not info.get("last_price")
    (the latter silently returns None for every field without erroring, which
    is an easy, quiet bug to introduce here).
    """
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info

    def safe_get(attr_name):
        try:
            return getattr(info, attr_name)
        except (KeyError, AttributeError):
            return None

    last_price = safe_get("last_price")
    previous_close = safe_get("previous_close")

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
        "day_high": safe_get("day_high"),
        "day_low": safe_get("day_low"),
        "volume": safe_get("last_volume"),
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
    market. This is the base data that gainers/losers/most-active/sector
    views are all derived from — one fetch, multiple views.
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


def get_top_gainers(market: str, limit: int = 5) -> list[dict]:
    snapshots = [s for s in get_equities_snapshot(market) if s["percent_change"] is not None]
    snapshots.sort(key=lambda s: s["percent_change"], reverse=True)
    return snapshots[:limit]


def get_top_losers(market: str, limit: int = 5) -> list[dict]:
    snapshots = [s for s in get_equities_snapshot(market) if s["percent_change"] is not None]
    snapshots.sort(key=lambda s: s["percent_change"])
    return snapshots[:limit]


def get_most_active(market: str, limit: int = 5) -> list[dict]:
    snapshots = [s for s in get_equities_snapshot(market) if s["volume"] is not None]
    snapshots.sort(key=lambda s: s["volume"], reverse=True)
    return snapshots[:limit]


def get_sector_performance(market: str) -> list[dict]:
    """
    Groups the equity snapshot by sector and averages percent_change.
    Simple mean, not volume/market-cap-weighted — good enough for a Phase 1
    overview; weighted aggregation can be added later without changing the shape.
    """
    snapshots = [s for s in get_equities_snapshot(market) if s["percent_change"] is not None]

    sectors: dict[str, list[float]] = {}
    for s in snapshots:
        sectors.setdefault(s["sector"], []).append(s["percent_change"])

    return [
        {"sector": sector, "average_percent_change": sum(changes) / len(changes)}
        for sector, changes in sectors.items()
    ]


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