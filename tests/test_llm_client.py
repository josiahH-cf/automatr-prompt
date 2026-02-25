"""Tests for automatr.integrations.llm.LLMClient — all HTTP calls mocked.

Covers: health check (connected / disconnected), completion request payload,
completion response parsing, streaming SSE response handling, and graceful
error handling on connection failure.

All tests use unittest.mock.patch to intercept requests calls — no real
network connections are made.
"""

from unittest.mock import MagicMock, patch

import pytest

from automatr.integrations.llm import LLMClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(port: int = 8080) -> LLMClient:
    """Return an LLMClient pointed at a local test URL."""
    return LLMClient(base_url=f"http://localhost:{port}")


# ---------------------------------------------------------------------------
# 1. Health check — connected
# ---------------------------------------------------------------------------


def test_health_check_returns_true_when_server_ok() -> None:
    """health_check() returns True when the server responds with HTTP 200."""
    client = _make_client()
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("automatr.integrations.llm.requests.get", return_value=mock_response):
        result = client.health_check()

    assert result is True


# ---------------------------------------------------------------------------
# 2. Health check — disconnected
# ---------------------------------------------------------------------------


def test_health_check_returns_false_on_connection_error() -> None:
    """health_check() returns False when requests raises a RequestException."""
    import requests as req_lib

    client = _make_client()
    with patch(
        "automatr.integrations.llm.requests.get",
        side_effect=req_lib.ConnectionError("refused"),
    ):
        result = client.health_check()

    assert result is False


def test_health_check_returns_false_on_non_200_status() -> None:
    """health_check() returns False when server responds with non-200 status."""
    client = _make_client()
    mock_response = MagicMock()
    mock_response.status_code = 503

    with patch("automatr.integrations.llm.requests.get", return_value=mock_response):
        result = client.health_check()

    assert result is False


# ---------------------------------------------------------------------------
# 3. Completion request sends correct payload
# ---------------------------------------------------------------------------


def test_generate_sends_correct_payload() -> None:
    """generate() posts the prompt and generation parameters to /completion."""
    client = _make_client()
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": "result text"}
    mock_response.raise_for_status = MagicMock()

    with patch("automatr.integrations.llm.requests.post", return_value=mock_response) as mock_post:
        client.generate(prompt="Hello world", max_tokens=100, temperature=0.5)

    call_kwargs = mock_post.call_args
    posted_json = call_kwargs.kwargs.get("json") or call_kwargs.args[1] if len(call_kwargs.args) > 1 else call_kwargs.kwargs["json"]
    assert posted_json["prompt"] == "Hello world"
    assert posted_json["n_predict"] == 100
    assert abs(posted_json["temperature"] - 0.5) < 1e-9
    assert "http://localhost:8080/completion" in (call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("url", ""))


# ---------------------------------------------------------------------------
# 4. Completion response parsed correctly
# ---------------------------------------------------------------------------


def test_generate_returns_content_from_response() -> None:
    """generate() extracts and returns the 'content' field from the JSON response."""
    client = _make_client()
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": "Generated output"}
    mock_response.raise_for_status = MagicMock()

    with patch("automatr.integrations.llm.requests.post", return_value=mock_response):
        result = client.generate(prompt="test")

    assert result == "Generated output"


def test_generate_returns_empty_string_when_content_missing() -> None:
    """generate() returns '' when the server response has no 'content' field."""
    client = _make_client()
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status = MagicMock()

    with patch("automatr.integrations.llm.requests.post", return_value=mock_response):
        result = client.generate(prompt="test")

    assert result == ""


# ---------------------------------------------------------------------------
# 5. Streaming response handled (mocked SSE chunks)
# ---------------------------------------------------------------------------


def test_generate_stream_yields_content_tokens() -> None:
    """generate_stream() yields content strings from SSE data lines."""
    client = _make_client()

    sse_lines = [
        b'data: {"content": "Hello"}',
        b'data: {"content": " world"}',
        b'data: {"content": ""}',  # empty content should not yield
        b"",  # blank line (ignored)
    ]

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_lines = MagicMock(return_value=iter(sse_lines))

    with patch("automatr.integrations.llm.requests.post", return_value=mock_response):
        tokens = list(client.generate_stream(prompt="stream me"))

    assert tokens == ["Hello", " world"]


# ---------------------------------------------------------------------------
# 6. Connection error handled gracefully (no crash)
# ---------------------------------------------------------------------------


def test_generate_raises_connection_error_on_refused_connection() -> None:
    """generate() raises ConnectionError (not crashes) when server is unreachable."""
    import requests as req_lib

    client = _make_client()
    with patch(
        "automatr.integrations.llm.requests.post",
        side_effect=req_lib.ConnectionError("connection refused"),
    ):
        with pytest.raises(ConnectionError):
            client.generate(prompt="will fail")


def test_generate_raises_runtime_error_on_timeout() -> None:
    """generate() raises RuntimeError when the request times out."""
    import requests as req_lib

    client = _make_client()
    with patch(
        "automatr.integrations.llm.requests.post",
        side_effect=req_lib.Timeout("timed out"),
    ):
        with pytest.raises(RuntimeError, match="timed out"):
            client.generate(prompt="slow prompt")
