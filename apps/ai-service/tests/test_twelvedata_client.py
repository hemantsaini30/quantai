# FILE LOCATION: quantai/apps/ai-service/tests/test_twelvedata_client.py
"""
All httpx calls are mocked — no real network calls, no real API keys
consumed while testing, per the project's testing philosophy.
"""

from unittest.mock import patch, MagicMock

import pytest

from app.markets import twelvedata_client as client


def make_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


@pytest.fixture
def five_keys(monkeypatch):
    for i in range(1, 6):
        monkeypatch.setenv(f"TWELVE_API_KEY{i}", f"key{i}")
    yield


def test_fetch_quote_returns_body_on_first_key_success(five_keys):
    with patch("app.markets.twelvedata_client.httpx.get") as mock_get:
        mock_get.return_value = make_response(200, {"symbol": "AAPL", "close": "200.50"})

        result = client.fetch_quote("AAPL")

        assert result == {"symbol": "AAPL", "close": "200.50"}
        assert mock_get.call_count == 1


def test_fetch_quote_rotates_to_next_key_on_429(five_keys):
    with patch("app.markets.twelvedata_client.httpx.get") as mock_get:
        mock_get.side_effect = [
            make_response(429, {"message": "You have run out of API credits"}),
            make_response(200, {"symbol": "AAPL", "close": "200.50"}),
        ]

        result = client.fetch_quote("AAPL")

        assert result == {"symbol": "AAPL", "close": "200.50"}
        assert mock_get.call_count == 2
        # Confirm the second call used a DIFFERENT key than the first
        first_key = mock_get.call_args_list[0].kwargs["params"]["apikey"]
        second_key = mock_get.call_args_list[1].kwargs["params"]["apikey"]
        assert first_key != second_key


def test_fetch_quote_raises_when_all_keys_exhausted(five_keys):
    with patch("app.markets.twelvedata_client.httpx.get") as mock_get:
        mock_get.return_value = make_response(429, {"message": "run out of API credits"})

        with pytest.raises(client.TwelveDataAllKeysExhaustedError):
            client.fetch_quote("AAPL")

        # Should have tried all 5 keys before giving up
        assert mock_get.call_count == 5


def test_fetch_quote_raises_when_no_keys_configured(monkeypatch):
    for i in range(1, 6):
        monkeypatch.delenv(f"TWELVE_API_KEY{i}", raising=False)

    with pytest.raises(client.TwelveDataAllKeysExhaustedError):
        client.fetch_quote("AAPL")


def test_fetch_quote_handles_network_error_and_tries_next_key(five_keys):
    with patch("app.markets.twelvedata_client.httpx.get") as mock_get:
        mock_get.side_effect = [
            client.httpx.ConnectError("connection failed"),
            make_response(200, {"symbol": "AAPL", "close": "200.50"}),
        ]

        result = client.fetch_quote("AAPL")

        assert result == {"symbol": "AAPL", "close": "200.50"}
        assert mock_get.call_count == 2


def test_fetch_quote_treats_error_status_body_as_failure_and_rotates(five_keys):
    """
    Twelve Data sometimes returns HTTP 200 with a JSON error body
    (status: 'error') instead of a proper HTTP error code — must be
    detected and treated as a failed attempt, not a successful result.
    """
    with patch("app.markets.twelvedata_client.httpx.get") as mock_get:
        mock_get.side_effect = [
            make_response(200, {"status": "error", "message": "Invalid symbol"}),
            make_response(200, {"symbol": "AAPL", "close": "200.50"}),
        ]

        result = client.fetch_quote("AAPL")

        assert result == {"symbol": "AAPL", "close": "200.50"}
        assert mock_get.call_count == 2


def test_only_configured_keys_are_used_not_all_five_slots(monkeypatch):
    """If only 2 of the 5 key env vars are set, only those 2 should be tried."""
    monkeypatch.setenv("TWELVE_API_KEY1", "key1")
    monkeypatch.setenv("TWELVE_API_KEY2", "key2")
    monkeypatch.delenv("TWELVE_API_KEY3", raising=False)
    monkeypatch.delenv("TWELVE_API_KEY4", raising=False)
    monkeypatch.delenv("TWELVE_API_KEY5", raising=False)

    with patch("app.markets.twelvedata_client.httpx.get") as mock_get:
        mock_get.return_value = make_response(429, {"message": "run out of API credits"})

        with pytest.raises(client.TwelveDataAllKeysExhaustedError):
            client.fetch_quote("AAPL")

        assert mock_get.call_count == 2