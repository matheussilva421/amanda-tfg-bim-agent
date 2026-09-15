"""Behavioral contract for the hardened security redactor."""

import json
from pathlib import Path

from amanda_agent.logging import EventLog
from amanda_agent.security.redaction import (
    contains_secret,
    redact_payload,
    redact_text,
)


BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secret-value-123"
API_KEY = "sk-live-api-key-123456789"
CLIENT_SECRET = "client-secret-value-123456789"
PASSWORD = "correct-horse-battery-staple"
PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAprivate-material-123456789
-----END RSA PRIVATE KEY-----"""


def test_redact_payload_masks_nested_credentials_and_preserves_diagnostics():
    payload = {
        "error_type": "ConnectionError",
        "host": "bim.example.test",
        "status_code": 503,
        "message": "GET /health returned HTTP 503 Service Unavailable",
        "headers": {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "X-Api-Key": API_KEY,
        },
        "credentials": {
            "client_secret": CLIENT_SECRET,
            "password": PASSWORD,
        },
        "private_key": PRIVATE_KEY,
        "attempts": [
            {"authorization": f"Basic {API_KEY}"},
            {"ordinary_diagnostic": "retry scheduled"},
        ],
    }

    redacted = redact_payload(payload)

    assert contains_secret(payload) is True
    assert contains_secret(redacted) is False
    assert payload["headers"]["Authorization"] == f"Bearer {BEARER_TOKEN}"
    assert redacted["headers"]["Authorization"] == "[REDACTED]"
    assert redacted["headers"]["X-Api-Key"] == "[REDACTED]"
    assert redacted["credentials"]["client_secret"] == "[REDACTED]"
    assert redacted["credentials"]["password"] == "[REDACTED]"
    assert redacted["private_key"] == "[REDACTED]"
    assert redacted["error_type"] == "ConnectionError"
    assert redacted["host"] == "bim.example.test"
    assert redacted["status_code"] == 503
    assert redacted["message"] == payload["message"]
    assert redacted["attempts"][1]["ordinary_diagnostic"] == "retry scheduled"


def test_redact_text_masks_credentials_inside_tracebacks_without_losing_context():
    traceback = (
        "Traceback (most recent call last):\n"
        "  File \"worker.py\", line 42, in call_provider\n"
        "    raise ConnectionError(...)\n"
        "ConnectionError: GET https://bim.example.test/api failed with "
        "HTTP 503 Service Unavailable; Authorization: Bearer "
        f"{BEARER_TOKEN}; password={PASSWORD}; api_key={API_KEY}; "
        f"client_secret='{CLIENT_SECRET}'\n"
        f"{PRIVATE_KEY}"
    )

    redacted = redact_text(traceback)

    for secret in (BEARER_TOKEN, PASSWORD, API_KEY, CLIENT_SECRET, PRIVATE_KEY):
        assert secret not in redacted
    for diagnostic in (
        "Traceback (most recent call last):",
        "ConnectionError",
        "bim.example.test",
        "HTTP 503 Service Unavailable",
        "worker.py",
    ):
        assert diagnostic in redacted
    assert contains_secret(redacted) is False


def test_contains_secret_detects_structured_and_free_form_secrets():
    assert contains_secret({"password": PASSWORD}) is True
    assert contains_secret({"details": f"Bearer {BEARER_TOKEN}"}) is True
    assert contains_secret("authorization=Bearer " + BEARER_TOKEN) is True
    assert contains_secret({"password": "[REDACTED]"}) is False
    assert contains_secret("ordinary diagnostic for HTTP 503") is False


def test_event_log_redacts_secret_payload_before_persisting(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    log = EventLog(path, task="P07-T10")

    log.record(
        operation="provider-request",
        status="FAIL",
        provider="bim.example.test",
        detail="ConnectionError while requesting HTTP 503 Service Unavailable",
        data={
            "error_type": "ConnectionError",
            "status_code": 503,
            "authorization": f"Bearer {BEARER_TOKEN}",
            "password": PASSWORD,
        },
    )

    raw = path.read_text(encoding="utf-8")

    assert BEARER_TOKEN not in raw
    assert PASSWORD not in raw
    assert "ConnectionError" in raw
    assert "bim.example.test" in raw
    assert "503" in raw
    assert json.loads(raw)["data"]["status_code"] == 503
