from __future__ import annotations

import json
from typing import Any


SENSITIVE_KEY_TOKENS = (
    "authorization",
    "api_key",
    "apikey",
    "x-api-key",
    "access_token",
    "refresh_token",
    "token",
    "bearer",
    "secret",
    "password",
    "passwd",
)
REDACTED = "***REDACTED***"


def _is_sensitive_key(key: str) -> bool:
    lowered = str(key).lower()
    return any(token in lowered for token in SENSITIVE_KEY_TOKENS)


def try_parse_json(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: REDACTED if _is_sensitive_key(k) else redact(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


def redact_headers(headers: Any) -> dict[str, str]:
    try:
        items = headers.items()
    except AttributeError:
        items = headers or []
    return {str(k): REDACTED if _is_sensitive_key(k) else str(v) for k, v in items}
