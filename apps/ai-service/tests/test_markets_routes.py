# FILE LOCATION: quantai/apps/ai-service/tests/test_markets_routes.py
"""
Integration tests for the /api/markets/* HTTP routes, using FastAPI's
TestClient (calls the app in-process, no real server needed). The
underlying market_data_service functions are mocked here too — this
layer's job is to verify routing, query params, and response shapes,
not to re-test the business logic already covered in
test_market_data_service.py.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.api.markets.service.get_indices_snapshot")
def test_indices_route_returns_200_and_passes_market_param(mock_get_indices):
    mock_get_indices.return_value = [{"symbol": "^NSEI", "name": "NIFTY 50"}]

    response = client.get("/api/markets/indices?market=IN")

    assert response.status_code == 200
    assert response.json() == [{"symbol": "^NSEI", "name": "NIFTY 50"}]
    mock_get_indices.assert_called_once_with("IN")


@patch("app.api.markets.service.get_indices_snapshot")
def test_indices_route_defaults_to_IN_market(mock_get_indices):
    mock_get_indices.return_value = []

    client.get("/api/markets/indices")

    mock_get_indices.assert_called_once_with("IN")


@patch("app.api.markets.service.get_top_gainers")
def test_gainers_route_respects_limit_param(mock_get_gainers):
    mock_get_gainers.return_value = []

    client.get("/api/markets/gainers?market=US&limit=10")

    mock_get_gainers.assert_called_once_with("US", 10)


def test_gainers_route_rejects_limit_above_50():
    response = client.get("/api/markets/gainers?limit=999")

    assert response.status_code == 422  # FastAPI validation error, Query(le=50)


@patch("app.api.markets.service.fetch_quote_snapshot")
def test_quote_route_passes_symbol_from_path(mock_fetch):
    mock_fetch.return_value = {"symbol": "AAPL", "last_price": 200}

    response = client.get("/api/markets/quote/AAPL")

    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"
    mock_fetch.assert_called_once_with("AAPL")


@patch("app.api.markets.service.search_symbols")
def test_search_route_requires_query_param(mock_search):
    response_missing_q = client.get("/api/markets/search")
    assert response_missing_q.status_code == 422  # q is required, no default

    mock_search.return_value = [{"symbol": "TCS.NS"}]
    response_with_q = client.get("/api/markets/search?q=tcs")
    assert response_with_q.status_code == 200
    mock_search.assert_called_once_with("tcs", "IN")


@patch("app.api.markets.service.get_sector_performance")
@patch("app.api.markets.service.get_most_active")
@patch("app.api.markets.service.get_top_losers")
@patch("app.api.markets.service.get_top_gainers")
@patch("app.api.markets.service.get_indices_snapshot")
def test_overview_route_aggregates_all_five_pieces(
    mock_indices, mock_gainers, mock_losers, mock_active, mock_sectors
):
    mock_indices.return_value = [{"symbol": "^NSEI"}]
    mock_gainers.return_value = [{"symbol": "A"}]
    mock_losers.return_value = [{"symbol": "B"}]
    mock_active.return_value = [{"symbol": "C"}]
    mock_sectors.return_value = [{"sector": "IT", "average_percent_change": 1.0}]

    response = client.get("/api/markets/overview?market=IN")

    assert response.status_code == 200
    body = response.json()
    assert body["indices"] == [{"symbol": "^NSEI"}]
    assert body["top_gainers"] == [{"symbol": "A"}]
    assert body["top_losers"] == [{"symbol": "B"}]
    assert body["most_active"] == [{"symbol": "C"}]
    assert body["sector_performance"] == [{"sector": "IT", "average_percent_change": 1.0}]


def test_health_route_still_works_alongside_markets():
    """
    Sanity check that adding the markets router didn't break the Phase 0
    health check route.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"