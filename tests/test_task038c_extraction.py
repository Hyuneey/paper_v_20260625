from experiments.argos_reproduction.repaired_rule_extraction import extraction_status


def test_review_extraction_requires_one_complete_inference_rule() -> None:
    status, code, count = extraction_status(
        "```python\nimport numpy as np\n\ndef inference(sample):\n    return np.zeros(len(sample), dtype=int)\n```"
    )
    assert status == "extracted_single_rule"
    assert code is not None
    assert count == 1


def test_multiple_code_blocks_are_not_accepted() -> None:
    status, _, _ = extraction_status(
        "```python\ndef inference(sample): return sample\n```\n"
        "```python\ndef other(): return 1\n```"
    )
    assert status == "multiple_code_blocks"
