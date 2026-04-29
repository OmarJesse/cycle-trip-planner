from src.api.middleware.redaction import REDACTED, redact, redact_headers


def test_redact_masks_known_sensitive_keys():
    payload = {
        "Authorization": "Bearer xxx",
        "ANTHROPIC_API_KEY": "sk-...",
        "X-Api-Key": "abcd",
        "password": "p4ss",
        "secret_token": "s3cret",
        "user": {"refresh_token": "rrr", "name": "Omar"},
        "list_field": [{"access_token": "tok"}, {"safe_field": "ok"}],
    }
    out = redact(payload)
    assert out["Authorization"] == REDACTED
    assert out["ANTHROPIC_API_KEY"] == REDACTED
    assert out["X-Api-Key"] == REDACTED
    assert out["password"] == REDACTED
    assert out["secret_token"] == REDACTED
    assert out["user"]["refresh_token"] == REDACTED
    assert out["user"]["name"] == "Omar"
    assert out["list_field"][0]["access_token"] == REDACTED
    assert out["list_field"][1]["safe_field"] == "ok"


def test_redact_leaves_non_sensitive_payload_unchanged():
    payload = {
        "conversation_id": "abc",
        "message": "Plan a trip",
        "preferences": {"daily_km": 100, "lodging_preference": "camping"},
        "tool_calls": [{"name": "get_route", "is_error": False}],
    }
    assert redact(payload) == payload


def test_redact_headers_masks_authorization_and_api_keys():
    headers = {
        "Authorization": "Bearer sk-secret",
        "X-Api-Key": "abcd",
        "x-api-key": "efgh",
        "Content-Type": "application/json",
        "User-Agent": "tests/1.0",
    }
    out = redact_headers(headers)
    assert out["Authorization"] == REDACTED
    assert out["X-Api-Key"] == REDACTED
    assert out["x-api-key"] == REDACTED
    assert out["Content-Type"] == "application/json"
    assert out["User-Agent"] == "tests/1.0"


def test_redact_headers_handles_iterables_and_starlette_style_objects():
    class FakeHeaders:
        def __init__(self, items):
            self._items = items

        def items(self):
            return iter(self._items)

    headers = FakeHeaders([("Authorization", "Bearer x"), ("X-Trace-Id", "trace-42")])
    out = redact_headers(headers)
    assert out["Authorization"] == REDACTED
    assert out["X-Trace-Id"] == "trace-42"
