"""Desired-state helpers for the BIM compiler."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .models import DesiredElement, DesiredState


def desired_element_digest(element: DesiredElement | dict[str, Any]) -> str:
    """Return a stable digest for the managed content of an element."""

    payload = (
        element.model_dump(mode="json")
        if isinstance(element, DesiredElement)
        else element
    )
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_desired_state(payload: DesiredState | Mapping[str, Any]) -> DesiredState:
    """Validate a serialized desired state at the compiler boundary."""

    return payload if isinstance(payload, DesiredState) else DesiredState.model_validate(payload)


__all__ = ["DesiredElement", "DesiredState", "desired_element_digest", "load_desired_state"]
