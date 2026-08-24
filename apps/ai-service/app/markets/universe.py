# FILE LOCATION: quantai/apps/ai-service/app/markets/universe.py
"""
Starter list of symbols per market. This is intentionally small for Phase 1 —
enough to make the dashboard real and useful, not an exhaustive listing.
Expand this list any time; nothing else needs to change to support more symbols.
"""

INDICES = {
    "IN": [
        {"symbol": "^NSEI", "name": "NIFTY 50"},
        {"symbol": "^BSESN", "name": "SENSEX"},
    ],
    "US": [
        {"symbol": "^GSPC", "name": "S&P 500"},
        {"symbol": "^DJI", "name": "Dow Jones"},
        {"symbol": "^IXIC", "name": "NASDAQ"},
    ],
}

# Starter equity universe used for gainers/losers/most-active/sector views.
# IN symbols use the .NS (NSE) suffix that yfinance expects.
EQUITIES = {
    "IN": [
        {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy"},
        {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "IT"},
        {"symbol": "INFY.NS", "name": "Infosys", "sector": "IT"},
        {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Financials"},
        {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Financials"},
        {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "sector": "Consumer Goods"},
        {"symbol": "ITC.NS", "name": "ITC", "sector": "Consumer Goods"},
        {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Financials"},
        {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel", "sector": "Telecom"},
        {"symbol": "LT.NS", "name": "Larsen & Toubro", "sector": "Industrials"},
    ],
    "US": [
        {"symbol": "AAPL", "name": "Apple", "sector": "Technology"},
        {"symbol": "MSFT", "name": "Microsoft", "sector": "Technology"},
        {"symbol": "GOOGL", "name": "Alphabet", "sector": "Technology"},
        {"symbol": "AMZN", "name": "Amazon", "sector": "Consumer Discretionary"},
        {"symbol": "NVDA", "name": "NVIDIA", "sector": "Technology"},
        {"symbol": "META", "name": "Meta Platforms", "sector": "Technology"},
        {"symbol": "TSLA", "name": "Tesla", "sector": "Consumer Discretionary"},
        {"symbol": "JPM", "name": "JPMorgan Chase", "sector": "Financials"},
        {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
        {"symbol": "XOM", "name": "Exxon Mobil", "sector": "Energy"},
    ],
}


def get_equities(market: str):
    return EQUITIES.get(market.upper(), [])


def get_indices(market: str):
    return INDICES.get(market.upper(), [])