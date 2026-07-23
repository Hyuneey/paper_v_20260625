from pathlib import Path

import numpy as np

from experiments.argos_reproduction.combined_prompt_capture import (
    CONTRAST_HEADERS,
    build_combined_request,
    combined_system_prompt,
    verify_pinned_sources,
)
from experiments.argos_reproduction.expanded_kpi_cohort import read_json, sha256_json


ROOT = Path(__file__).resolve().parents[1]
CONFIG = read_json(ROOT / "configs/argos_reproduction/task037d_error_conditioned_rules.json")


def _chunk(label: int) -> dict[str, np.ndarray]:
    return {
        "values": np.array([1.0, 2.0]),
        "labels": np.array([label, label], dtype=np.int8),
        "indices": np.array([0, 1], dtype=np.int64),
    }


def test_combined_templates_and_source_hashes_are_exact() -> None:
    verify_pinned_sources(CONFIG)
    assert combined_system_prompt(CONFIG, "FN")["template_name"].endswith("_FN_PROMPT_TEMPLATE")
    assert combined_system_prompt(CONFIG, "FP")["template_name"].endswith("_FP_PROMPT_TEMPLATE")


def test_fn_and_fp_user_sections_are_not_swapped() -> None:
    for direction, contrast_label in (("FN", 0), ("FP", 1)):
        request, hashes = build_combined_request(
            CONFIG, direction, _chunk(1 if direction == "FN" else 0), _chunk(contrast_label)
        )
        user = request["messages"][1]["content"]
        assert user.startswith("##### DATA 0\n")
        assert CONTRAST_HEADERS[direction] in user
        assert "CODE FROM LAST ITERATION" not in user
        assert hashes["complete_request_hash"] == sha256_json(request)
