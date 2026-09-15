"""Secret redaction shared by snapshots, logs and reports.

Redaction is applied before anything is persisted, so a crash cannot leak a
credential into a log or a Git-tracked summary. Keys are matched
case-insensitively against the sensitive fragments, and values that look like
authorization headers or bearer tokens are masked even when the key is bland.
"""

from __future__ import annotations

import re

SENSITIVE_KEY_FRAGMENTS = (
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "API_KEY",
    "APIKEY",
    "AUTHORIZATION",
    "CREDENTIAL",
    "PRIVATE_KEY",
    "ACCESS_KEY",
    "COOKIE",
    "SESSION",
)

MASK = "[REDACTED]"

_VALUE_PATTERNS = (
    re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._\-+=/]{8,}"),
    re.compile(r"(?i)\b(sk|ghp|gho|xox[baprs])[-_][A-Za-z0-9._\-]{8,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def is_sensitive_key(key: object) -> bool:
    text = str(key).upper()
    return any(fragment in text for fragment in SENSITIVE_KEY_FRAGMENTS)


def _mask_value(value: object) -> object:
    if not isinstance(value, str):
        return value
    for pattern in _VALUE_PATTERNS:
        if pattern.search(value):
            return MASK
    return value


def redact(value, *, _depth: int = 0):
    """Return a deep copy with sensitive keys and values masked."""
    if _depth > 12:
        return "[TRUNCATED]"
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if is_sensitive_key(key):
                result[key] = MASK
            else:
                result[key] = redact(item, _depth=_depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        return [redact(item, _depth=_depth + 1) for item in value]
    return _mask_value(value)


def redact_text(text: str) -> str:
    """Mask credentials that appear inside free-form text or tracebacks."""
    result = text
    for pattern in _VALUE_PATTERNS:
        result = pattern.sub(MASK, result)
    for fragment in SENSITIVE_KEY_FRAGMENTS:
        result = re.sub(
            r"(?i)(" + re.escape(fragment) + r'\s*["' + "'" + r"]?\s*[:=]\s*)"
            r'("[^"]*"|'
            + "'"
            + r"[^'\n]*"
            + "'"
            + r"|[^\s,;\}]+)",
            r"\1" + MASK,
            result,
        )
    return result


def contains_secret(value) -> bool:
    """Detect leftovers of a secret; used to gate what may be committed."""
    if isinstance(value, dict):
        for key, item in value.items():
            if is_sensitive_key(key) and item not in (None, MASK, "", [], {}):
                return True
            if contains_secret(item):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(contains_secret(item) for item in value)
    if isinstance(value, str):
        if value == MASK:
            return False
        return any(pattern.search(value) for pattern in _VALUE_PATTERNS)
    return False
