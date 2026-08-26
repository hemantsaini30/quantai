# FILE LOCATION: quantai/apps/ai-service/tests/test_market_data_service.py
"""
These tests mock yfinance entirely — no live network calls, per the
project's testing philosophy (never hit real external services in CI).
They test the transform/aggregation logic in market_data_service.py,
which is where bugs are most likely to hide (sorting, grouping, division).
"""

from unittest.mock import patch, MagicMock

from app.markets import market_data_service as service



class FakeFastInfo:
    """
    Mimics yfinance's real FastInfo object shape (attribute access, not
    dict access) — this distinction caused a real bug during development,
    see test_fetch_quote_snapshot_uses_attribute_access_not_dict_get below.
    """

    def __init__(self, last_price, previous_close, day_high=None, day_low=None, volume=None):
        self.last_price = last_price
        self.previous_close = previous_close
        self.day_high = day_high
        self.day_low = day_low
        self.last_volume = volume


def make_fake_ticker(last_price, previous_close, day_high=None, day_low=None, volume=None):
    fake = MagicMock()
    fake.fast_info = FakeFastInfo(last_price, previous_close, day_high, day_low, volume)
    return fake


@patch("app.markets.market_data_service.yf.Ticker")
def test_fetch_quote_snapshot_computes_change_correctly(mock_ticker_cls):
    mock_ticker_cls.return_value = make_fake_ticker(last_price=110, previous_close=100)

    result = service.fetch_quote_snapshot("FAKE")

    assert result["change"] == 10
    assert result["percent_change"] == 10.0


@patch("app.markets.market_data_service.yf.Ticker")
def test_fetch_quote_snapshot_handles_missing_previous_close(mock_ticker_cls):
    mock_ticker_cls.return_value = make_fake_ticker(last_price=110, previous_close=None)

    result = service.fetch_quote_snapshot("FAKE")

    assert result["change"] is None
    assert result["percent_change"] is None


@patch("app.markets.market_data_service.yf.Ticker")
def test_fetch_quote_snapshot_uses_attribute_access_not_dict_get(mock_ticker_cls):
    """
    Regression test: fast_info is a FastInfo OBJECT, not a dict. Using
    info.get("last_price") instead of info.last_price silently returns
    None for every field with no error — this test fails loudly if that
    mistake is ever reintroduced, by asserting real values come through.
    """
    mock_ticker_cls.return_value = make_fake_ticker(
        last_price=250.5, previous_close=245.0, day_high=252.0, day_low=244.0, volume=1_000_000
    )

    result = service.fetch_quote_snapshot("FAKE")

    assert result["last_price"] == 250.5
    assert result["previous_close"] == 245.0
    assert result["day_high"] == 252.0
    assert result["day_low"] == 244.0
    assert result["volume"] == 1_000_000


@patch("app.markets.market_data_service.yf.Ticker")
def test_fetch_quote_snapshot_handles_yfinance_failure_gracefully(mock_ticker_cls):
    """
    Regression test for a real live bug: when Yahoo Finance rate-limits or
    the network fails, yfinance raises an exception while building fast_info.
    This must return a "no data" snapshot, not crash the whole endpoint.
    """
    mock_ticker = MagicMock()
    # Accessing .fast_info itself raises, simulating yfinance's network/JSON error
    type(mock_ticker).fast_info = property(lambda self: (_ for _ in ()).throw(Exception("429 Too Many Requests")))
    mock_ticker_cls.return_value = mock_ticker

    result = service.fetch_quote_snapshot("FAKE")

    assert result["symbol"] == "FAKE"
    assert result["last_price"] is None
    assert result["change"] is None
    assert result["percent_change"] is None


@patch("app.markets.market_data_service.fetch_quote_snapshot")
def test_get_top_gainers_sorts_descending(mock_fetch):
    def side_effect(symbol):
        values = {"A": 5.0, "B": -2.0, "C": 10.0}
        return {"symbol": symbol, "percent_change": values[symbol], "last_price": 100}

    mock_fetch.side_effect = side_effect

    with patch("app.markets.market_data_service.get_equities") as mock_universe:
        mock_universe.return_value = [
            {"symbol": "A", "name": "A Corp", "sector": "Tech"},
            {"symbol": "B", "name": "B Corp", "sector": "Tech"},
            {"symbol": "C", "name": "C Corp", "sector": "Tech"},
        ]
        result = service.get_top_gainers("IN", limit=2)

    assert [r["symbol"] for r in result] == ["C", "A"]


@patch("app.markets.market_data_service.fetch_quote_snapshot")
def test_get_top_losers_sorts_ascending(mock_fetch):
    def side_effect(symbol):
        values = {"A": 5.0, "B": -2.0, "C": -10.0}
        return {"symbol": symbol, "percent_change": values[symbol], "last_price": 100}

    mock_fetch.side_effect = side_effect

    with patch("app.markets.market_data_service.get_equities") as mock_universe:
        mock_universe.return_value = [
            {"symbol": "A", "name": "A Corp", "sector": "Tech"},
            {"symbol": "B", "name": "B Corp", "sector": "Tech"},
            {"symbol": "C", "name": "C Corp", "sector": "Tech"},
        ]
        result = service.get_top_losers("IN", limit=2)

    assert [r["symbol"] for r in result] == ["C", "B"]


@patch("app.markets.market_data_service.fetch_quote_snapshot")
def test_get_sector_performance_averages_correctly(mock_fetch):
    def side_effect(symbol):
        values = {"A": 10.0, "B": 20.0, "C": -6.0}
        return {"symbol": symbol, "percent_change": values[symbol], "last_price": 100}

    mock_fetch.side_effect = side_effect

    with patch("app.markets.market_data_service.get_equities") as mock_universe:
        mock_universe.return_value = [
            {"symbol": "A", "name": "A Corp", "sector": "Tech"},
            {"symbol": "B", "name": "B Corp", "sector": "Tech"},
            {"symbol": "C", "name": "C Corp", "sector": "Energy"},
        ]
        result = service.get_sector_performance("IN")

    by_sector = {r["sector"]: r["average_percent_change"] for r in result}
    assert by_sector["Tech"] == 15.0  # (10 + 20) / 2
    assert by_sector["Energy"] == -6.0


@patch("app.markets.market_data_service.fetch_quote_snapshot")
def test_get_equities_snapshot_skips_symbols_that_error(mock_fetch):
    def side_effect(symbol):
        if symbol == "BAD":
            raise Exception("delisted or bad symbol")
        return {"symbol": symbol, "percent_change": 1.0, "last_price": 100}

    mock_fetch.side_effect = side_effect

    with patch("app.markets.market_data_service.get_equities") as mock_universe:
        mock_universe.return_value = [
            {"symbol": "GOOD", "name": "Good Corp", "sector": "Tech"},
            {"symbol": "BAD", "name": "Bad Corp", "sector": "Tech"},
        ]
        result = service.get_equities_snapshot("IN")

    # BAD should be silently skipped, not crash the whole dashboard
    assert len(result) == 1
    assert result[0]["symbol"] == "GOOD"


def test_search_symbols_matches_name_or_symbol_case_insensitive():
    with patch("app.markets.market_data_service.get_equities") as mock_universe:
        mock_universe.return_value = [
            {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "IT"},
            {"symbol": "INFY.NS", "name": "Infosys", "sector": "IT"},
        ]

        result_by_name = service.search_symbols("infosys", "IN")
        result_by_symbol = service.search_symbols("tcs", "IN")
        result_no_match = service.search_symbols("zzz", "IN")

    assert len(result_by_name) == 1
    assert result_by_name[0]["symbol"] == "INFY.NS"
    assert len(result_by_symbol) == 1
    assert result_by_symbol[0]["symbol"] == "TCS.NS"
    assert len(result_no_match) == 0




def test_get_market_overview_fetches_equities_only_once():
    """
    Regression test for a real live bug: gainers/losers/most-active/sectors
    were each independently re-fetching the whole equity universe, causing
    ~40 yfinance calls per dashboard load and triggering Yahoo's rate limit
    (HTTP 429) almost immediately. This test fails if that N+1 pattern is
    ever reintroduced.
    """
    with patch("app.markets.market_data_service.fetch_quote_snapshot") as mock_fetch, \
         patch("app.markets.market_data_service.get_equities") as mock_equities, \
         patch("app.markets.market_data_service.get_indices") as mock_indices:

        mock_equities.return_value = [
            {"symbol": "A", "name": "A Corp", "sector": "Tech"},
            {"symbol": "B", "name": "B Corp", "sector": "Tech"},
        ]
        mock_indices.return_value = [{"symbol": "^NSEI", "name": "NIFTY 50"}]
        mock_fetch.side_effect = lambda symbol: {
            "symbol": symbol,
            "percent_change": 1.0,
            "last_price": 100,
            "volume": 1000,
        }

        service.get_market_overview("IN")

        # 2 equities + 1 index = 3 total fetch_quote_snapshot calls,
        # NOT 2 equities x 4 derived views + 1 index = 9 calls.
        assert mock_fetch.call_count == 3