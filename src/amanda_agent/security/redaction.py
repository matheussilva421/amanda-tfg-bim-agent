"""Redact secrets before diagnostic data is persisted.

This module is a hardened boundary for logger and reporter callers. It keeps
diagnostic context such as exception names, hosts, status codes and ordinary
messages while masking credentials in mappings, sequences and free-form text.
The older :mod:`amanda_agent.redaction` module remains a separate compatibility
surface for Phase 01 callers.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

MASK = "[REDACTED]"

SENSITIVE_KEY_FRAGMENTS = (
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "PASSPHRASE",
    "API_KEY",
    "APIKEY",
    "AUTHORIZATION",
    "CREDENTIAL",
    "PRIVATE_KEY",
    "ACCESS_KEY",
    "COOKIE",
    "SESSION",
)

_NORMALIZED_KEY_MARKERS = tuple(
    fragment.lower().replace("_", "") for fragment in SENSITIVE_KEY_FRAGMENTS
)
_FIELD_NAMES = (
    "authorization",
    "proxy[-_]?authorization",
    "x[-_]?api[-_]?key",
    "api[-_]?key",
    "apikey",
    "access[-_]?token",
    "client[-_]?secret",
    "password",
    "passwd",
    "passphrase",
    "private[-_]?key",
    "credential",
    "cookie",
    "session",
    "token",
    "secret",
)
_FIELD_NAME_PATTERN = "(?:" + "|".join(_FIELD_NAMES) + ")"

_SENSITIVE_FIELD_RE = re.compile(
    r"(?ix)"
    r"(?P<prefix>"
    r"(?<![a-z0-9])['\"]?"
    + _FIELD_NAME_PATTERN
    + r"['\"]?\s*(?::|=)\s*)"
    r"(?P<value>"
    r"\"(?:\\.|[^\"\\])*\""
    r"|'(?:\\.|[^'\\])*'"
    r"|(?:bearer|basic)\s+[^\s,;\}\]]+"
    r"|\[REDACTED\]"
    r"|[^\s,;\}\]]+"
    r")"
)

_AUTH_SCHEME_RE = re.compile(
    r"(?i)(?P<scheme>\b(?:bearer|basic)\s+)"
    r"(?P<token>[^\s,;\}\]]+)"
)

_KNOWN_TOKEN_RE = re.compile(
    r"(?i)(?<![a-z0-9])(?:"
    r"sk-(?:proj-)?[a-z0-9_-]{8,}|"
    r"sk_[a-z0-9_-]{8,}|"
    r"github_pat_[a-z0-9_]{8,}|"
    r"gh[pousr]_[a-z0-9_]{8,}|"
    r"xox[baprs]-[a-z0-9-]{8,}|"
    r"AIza[a-z0-9_-]{20,}|"
    r"npm_[a-z0-9]{8,}|"
    r"pypi-[a-z0-9_-]{8,}"
    r")(?=$|[^a-z0-9_])"
)

_PRIVATE_KEY_BLOCK_RE = re.compile(
    r"(?is)-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
    r".*?"
    r"-----END [A-Z0-9 ]*PRIVATE KEY-----"
)
_PRIVATE_KEY_HEADER_RE = re.compile(
    r"(?i)-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
)
_PRIVATE_KEY_UNCLOSED_RE = re.compile(
    r"(?is)-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*\Z"
)


def is_sensitive_key(key: object) -> bool:
    """Return whether a structured field name identifies secret material."""
    normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
    return any(marker in normalized for marker in _NORMALIZED_KEY_MARKERS)


def _replace_sensitive_field(match: re.Match[str]) -> str:
    value = match.group("value")
    if value[:1] in {"'", '"'} and value[-1:] == value[:1]:
        return match.group("prefix") + value[0] + MASK + value[0]
    return match.group("prefix") + MASK


def _field_match_contains_secret(match: re.Match[str]) -> bool:
    value = match.group("value")
    if value[:1] in {"'", '"'} and value[-1:] == value[:1]:
        value = value[1:-1]
    return value not in {"", MASK}


def redact_text(text: str) -> str:
    """Mask credentials in free-form messages, headers and tracebacks."""
    if not isinstance(text, str):
        return text

    result = _PRIVATE_KEY_BLOCK_RE.sub(MASK, text)
    result = _PRIVATE_KEY_UNCLOSED_RE.sub(MASK, result)
    result = _SENSITIVE_FIELD_RE.sub(_replace_sensitive_field, result)
    result = _AUTH_SCHEME_RE.sub(
        lambda match: match.group("scheme") + MASK,
        result,
    )
    result = _KNOWN_TOKEN_RE.sub(MASK, result)
    result = _PRIVATE_KEY_HEADER_RE.sub(MASK, result)
    return result


def redact_payload(payload: Any, *, _depth: int = 0) -> Any:
    """Return a recursively redacted copy of a structured payload.

    Mapping keys are retained for diagnostic readability, while values under
    sensitive keys are replaced in full. Ordinary string values still pass
    through :func:`redact_text` so a credential embedded in a message cannot
    bypass the structured boundary.
    """
    if _depth > 32:
        return MASK
    if isinstance(payload, Mapping):
        result = {}
        for key, value in payload.items():
            if is_sensitive_key(key) and not isinstance(value, Mapping):
                result[key] = MASK
            else:
                result[key] = redact_payload(value, _depth=_depth + 1)
        return result
    if isinstance(payload, list):
        return [redact_payload(item, _depth=_depth + 1) for item in payload]
    if isinstance(payload, tuple):
        return tuple(redact_payload(item, _depth=_depth + 1) for item in payload)
    if isinstance(payload, str):
        return redact_text(payload)
    return payload


def _value_contains_secret(value: Any, *, _depth: int = 0) -> bool:
    if _depth > 32:
        return True
    if isinstance(value, Mapping):
        return contains_secret(value, _depth=_depth + 1)
    if isinstance(value, (list, tuple)):
        return any(
            _value_contains_secret(item, _depth=_depth + 1) for item in value
        )
    if isinstance(value, str):
        return (
            _PRIVATE_KEY_BLOCK_RE.search(value) is not None
            or _PRIVATE_KEY_HEADER_RE.search(value) is not None
            or _PRIVATE_KEY_UNCLOSED_RE.search(value) is not None
            or any(
                _field_match_contains_secret(match)
                for match in _SENSITIVE_FIELD_RE.finditer(value)
            )
            or _AUTH_SCHEME_RE.search(value) is not None
            or _KNOWN_TOKEN_RE.search(value) is not None
        )
    return False


def contains_secret(payload: Any, *, _depth: int = 0) -> bool:
    """Return whether a payload still contains detectable secret material."""
    if _depth > 32:
        return True
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if is_sensitive_key(key):
                if isinstance(value, Mapping):
                    if contains_secret(value, _depth=_depth + 1):
                        return True
                elif value not in (None, "", [], (), MASK):
                    return True
            elif contains_secret(value, _depth=_depth + 1):
                return True
        return False
    if isinstance(payload, (list, tuple)):
        return any(
            contains_secret(item, _depth=_depth + 1) for item in payload
        )
    if isinstance(payload, str):
        return _value_contains_secret(payload, _depth=_depth)
    return False


# Short aliases make the boundary convenient for existing logger/reporter
# conventions while the explicit names document intent at call sites.
redact = redact_payload
contains_secrets = contains_secret


__all__ = [
    "MASK",
    "SENSITIVE_KEY_FRAGMENTS",
    "contains_secret",
    "contains_secrets",
    "is_sensitive_key",
    "redact",
    "redact_payload",
    "redact_text",
]
