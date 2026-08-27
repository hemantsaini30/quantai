# FILE LOCATION: quantai/apps/ai-service/tests/test_finnhub_client.py
from unittest.mock import patch, MagicMock

import pytest

from app.markets import finnhub_client as client


def make_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


@pytest.fixture
def finnhub_key(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "test-key")
    yield


def test_search_us_symbols_normalizes_common_stock_results(finnhub_key):
    with patch("app.markets.finnhub_client.httpx.get") as mock_get:
        mock_get.return_value = make_response(200, {
            "result": [
                {"symbol": "AAPL", "description": "Apple Inc", "type": "Common Stock"},
                {"symbol": "AAPL.SW", "description": "Apple Inc (Swiss)", "type": "Common Stock"},
            ]
        })

        result = client.search_us_symbols("apple")

        assert len(result) == 2
        assert result[0]["symbol"] == "AAPL"
        assert result[0]["name"] == "Apple Inc"


def test_search_us_symbols_filters_out_non_stock_types(finnhub_key):
    with patch("app.markets.finnhub_client.httpx.get") as mock_get:
        mock_get.return_value = make_response(200, {
            "result": [
                {"symbol": "AAPL", "description": "Apple Inc", "type": "Common Stock"},
                {"symbol": "AAPL240101C00150000", "description": "Apple Option", "type": "Option"},
            ]
        })

        result = client.search_us_symbols("apple")

        assert len(result) == 1
        assert result[0]["symbol"] == "AAPL"


def test_search_us_symbols_raises_when_no_api_key(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)

    with pytest.raises(client.FinnhubSearchError):
        client.search_us_symbols("apple")


def test_search_us_symbols_raises_on_non_200_response(finnhub_key):
    with patch("app.markets.finnhub_client.httpx.get") as mock_get:
        mock_get.return_value = make_response(500)

        with pytest.raises(client.FinnhubSearchError):
            client.search_us_symbols("apple")


def test_search_us_symbols_caps_results_at_10(finnhub_key):
    with patch("app.markets.finnhub_client.httpx.get") as mock_get:
        many_results = [
            {"symbol": f"SYM{i}", "description": f"Company {i}", "type": "Common Stock"}
            for i in range(20)
        ]
        mock_get.return_value = make_response(200, {"result": many_results})

        result = client.search_us_symbols("test")

        assert len(result) == 10