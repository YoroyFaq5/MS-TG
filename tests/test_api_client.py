from unittest.mock import MagicMock, patch

import pytest

from bot.api_client.client import ApiClient
from bot.api_client.exceptions import ApiError, ApiNotFound, ApiServerError, ApiUnauthorized


def _make_client() -> ApiClient:
    return ApiClient(base_url="http://example.test", service_token="tok")


def _fake_response(status_code: int, json_body=None, text: str = ""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = text.encode() if text else b"{}"
    resp.text = text
    if json_body is not None:
        resp.json.return_value = json_body
    else:
        resp.json.side_effect = ValueError("no json")
    return resp


def test_unwraps_envelope_data_on_success():
    client = _make_client()
    fake = _fake_response(200, {"status": "ok", "message": "ok", "data": {"foo": "bar"}})
    with patch.object(client.session, "request", return_value=fake):
        result = client.get("/whatever")
    assert result == {"foo": "bar"}


def test_business_error_message_extracted_from_json_body():
    client = _make_client()
    fake = _fake_response(
        400, {"status": "error", "message": "У вас уже есть драфт для этого турнира."},
    )
    with patch.object(client.session, "request", return_value=fake):
        with pytest.raises(ApiError) as exc_info:
            client.post("/fantasy/draft", json={})
    assert "уже есть драфт" in str(exc_info.value)


def test_404_maps_to_api_not_found_with_clean_message():
    client = _make_client()
    fake = _fake_response(404, {"status": "error", "message": "Турнир не найден."})
    with patch.object(client.session, "request", return_value=fake):
        with pytest.raises(ApiNotFound) as exc_info:
            client.get("/tournaments/999")
    assert "Турнир не найден" in str(exc_info.value)


def test_401_maps_to_api_unauthorized():
    client = _make_client()
    fake = _fake_response(401, {"status": "error", "message": "Unauthorized"})
    with patch.object(client.session, "request", return_value=fake):
        with pytest.raises(ApiUnauthorized):
            client.get("/resolve")


def test_500_maps_to_api_server_error():
    client = _make_client()
    fake = _fake_response(500, text="Internal Server Error")
    with patch.object(client.session, "request", return_value=fake):
        with pytest.raises(ApiServerError):
            client.get("/resolve")


def test_non_json_error_body_falls_back_to_raw_text():
    client = _make_client()
    fake = _fake_response(400, json_body=None, text="plain text error")
    with patch.object(client.session, "request", return_value=fake):
        with pytest.raises(ApiError) as exc_info:
            client.get("/whatever")
    assert "plain text error" in str(exc_info.value)


def test_fast_get_uses_fast_session_with_short_timeout_and_no_retries():
    client = _make_client()
    fake = _fake_response(200, {"status": "ok", "message": "ok", "data": {"foo": "bar"}})
    with patch.object(client.session, "request") as slow_request, \
         patch.object(client.fast_session, "request", return_value=fake) as fast_request:
        result = client.get("/whatever", fast=True)

    slow_request.assert_not_called()
    fast_request.assert_called_once()
    assert fast_request.call_args.kwargs["timeout"] == client._fast_timeout
    assert result == {"foo": "bar"}
