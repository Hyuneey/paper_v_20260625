from __future__ import annotations

import inspect

from experiments.argos_reproduction import repaired_rule_runtime


def _valid(output_hash: str = "a") -> dict[str, object]:
    return {
        "status": "valid",
        "output_hash": output_hash,
        "output_count": 4,
        "predicted_positive_count": 1,
    }


def test_two_exact_replays_are_required() -> None:
    assert repaired_rule_runtime._replay_valid([_valid(), _valid()])
    assert not repaired_rule_runtime._replay_valid([_valid("a"), _valid("b")])


def test_static_invalid_rules_cannot_enter_runtime() -> None:
    source = inspect.getsource(repaired_rule_runtime.run_repaired_rules)
    assert 'static_record["static_status"] != "static_valid"' in source
    assert "execute_container_once" in source
    assert 'for fixture in ("target", "contrast")' in source


def test_host_does_not_import_repaired_source() -> None:
    source = inspect.getsource(repaired_rule_runtime)
    assert "importlib" not in source
    assert "exec(" not in source
    assert "eval(" not in source
    assert "compile(" not in source
