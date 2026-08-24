# FILE LOCATION: quantai/apps/ai-service/app/api/markets.py
from fastapi import APIRouter, Query

from app.markets import market_data_service as service

router = APIRouter()


@router.get("/overview")
def market_overview(market: str = Query("IN", description="'IN' or 'US'")):
    """Single call the dashboard homepage uses to load everything at once."""
    return {
        "indices": service.get_indices_snapshot(market),
        "top_gainers": service.get_top_gainers(market),
        "top_losers": service.get_top_losers(market),
        "most_active": service.get_most_active(market),
        "sector_performance": service.get_sector_performance(market),
    }


@router.get("/indices")
def indices(market: str = Query("IN")):
    return service.get_indices_snapshot(market)


@router.get("/gainers")
def gainers(market: str = Query("IN"), limit: int = Query(5, ge=1, le=50)):
    return service.get_top_gainers(market, limit)


@router.get("/losers")
def losers(market: str = Query("IN"), limit: int = Query(5, ge=1, le=50)):
    return service.get_top_losers(market, limit)


@router.get("/most-active")
def most_active(market: str = Query("IN"), limit: int = Query(5, ge=1, le=50)):
    return service.get_most_active(market, limit)


@router.get("/sectors")
def sectors(market: str = Query("IN")):
    return service.get_sector_performance(market)


@router.get("/quote/{symbol}")
def quote(symbol: str):
    return service.fetch_quote_snapshot(symbol)


@router.get("/history/{symbol}")
def history(symbol: str, period: str = Query("3mo")):
    return service.get_price_history(symbol, period)


@router.get("/search")
def search(q: str = Query(..., min_length=1), market: str = Query("IN")):
    return service.search_symbols(q, market)