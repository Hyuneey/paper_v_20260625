from experiments.argos_reproduction.multi_rule_static_audit import audit_response


def test_frozen_static_policy_accepts_bounded_numpy_rule() -> None:
    response = """```python
import numpy as np
def inference(sample):
    return np.zeros(len(sample), dtype=int)
```"""
    audit, _ = audit_response(response)
    assert audit["static_status"] == "static_valid"


def test_frozen_static_policy_rejects_dynamic_execution_and_file_access() -> None:
    response = """```python
def inference(sample):
    exec(open("x").read())
    return [0]
```"""
    audit, _ = audit_response(response)
    assert audit["static_status"] == "static_invalid"
