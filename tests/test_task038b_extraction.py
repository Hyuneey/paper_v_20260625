from __future__ import annotations

from experiments.argos_reproduction.repaired_rule_extraction import (
    extraction_status,
)


def test_exactly_one_complete_inference_rule_is_required() -> None:
    response = """```python
import numpy as np
def inference(sample):
    return np.zeros(len(sample), dtype=int)
```"""
    status, code, count = extraction_status(response)
    assert status == "extracted_single_rule"
    assert code is not None
    assert count == 1


def test_multiple_fences_and_wrong_signature_fail_without_retry() -> None:
    multiple = "```python\ndef inference(sample): return []\n```\n```python\nx=1\n```"
    assert extraction_status(multiple)[0] == "multiple_code_blocks"
    wrong = "```python\ndef inference(values, labels): return []\n```"
    assert extraction_status(wrong)[0] == "invalid_function_signature"
