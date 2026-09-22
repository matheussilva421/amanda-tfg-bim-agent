from __future__ import annotations

from scripts.run_amanda_production import _new_idempotency_key, _select_revit_target


class _Transport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def call(self, tool, arguments):
        self.calls.append((tool, arguments))
        return self.response


def test_select_revit_target_sets_and_verifies_the_requested_pid():
    transport = _Transport({"result": {"structuredContent": {"selected_pid": 37588}}})

    selected = _select_revit_target(transport, 37588)

    assert selected == {"selected_pid": 37588}
    assert transport.calls == [("horizun_target", {"pid": 37588})]


def test_final_save_key_is_unique_per_production_attempt():
    assert _new_idempotency_key("save", "run-abc123") == "amanda-save-run-abc123"
