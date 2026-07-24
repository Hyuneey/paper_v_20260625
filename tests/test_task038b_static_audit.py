from __future__ import annotations

from experiments.argos_reproduction.multi_rule_static_audit import audit_response
from experiments.argos_reproduction.repaired_rule_static_audit import (
    classify_static_failure,
)


def test_numpy_only_rule_passes_frozen_static_policy() -> None:
    response = """```python
import numpy as np
def inference(sample):
    return np.zeros(len(sample), dtype=int)
```"""
    audit, _ = audit_response(response)
    assert audit["static_status"] == "static_valid"


def test_dynamic_execution_and_file_access_are_rejected() -> None:
    response = """```python
import numpy as np
def inference(sample):
    exec("x = 1")
    open("x")
    return np.zeros(len(sample))
```"""
    audit, _ = audit_response(response)
    assert audit["static_status"] == "static_invalid"
    assert classify_static_failure(audit) == "repaired_forbidden_operation"
