from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.argos_reproduction.agent_validity_metrics import (
    AgentValiditySchemaError,
    MethodologicalValidityRecord,
    ValidityConclusion,
    future_metric_schema,
    validate_validity_record,
)
from experiments.argos_reproduction.expanded_kpi_cohort import sha256_json


ROOT = Path(__file__).resolve().parents[1]


def test_validity_schema_supports_all_qualified_conclusions() -> None:
    schema = future_metric_schema()
    assert schema["conclusion_categories"] == [
        "strongly_supported",
        "partially_supported",
        "not_supported",
    ]
    for conclusion in ValidityConclusion:
        record = MethodologicalValidityRecord(
            conclusion=conclusion,
            operational_validity="pending",
            incremental_review_value="pending",
            generalization="pending",
            detector_complementarity="pending",
            efficiency="pending",
            safety_and_reproducibility="pending",
            sealed_test_confirmed=conclusion is ValidityConclusion.STRONGLY_SUPPORTED,
            rationale=("protocol only",),
        )
        validate_validity_record(record.to_dict())


def test_strong_conclusion_requires_sealed_test_confirmation() -> None:
    record = {
        "conclusion": "strongly_supported",
        "operational_validity": "supported",
        "incremental_review_value": "supported",
        "generalization": "supported",
        "detector_complementarity": "supported",
        "efficiency": "supported",
        "safety_and_reproducibility": "supported",
        "sealed_test_confirmed": False,
    }
    with pytest.raises(AgentValiditySchemaError, match="STRONG_REQUIRES_SEALED_TEST"):
        validate_validity_record(record)


def test_task038a_reports_are_hash_valid_and_protocol_only_when_present() -> None:
    for path in sorted((ROOT / "docs/task_reports").glob("TASK-038A_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        expected = payload.pop("report_hash")
        assert expected == sha256_json(payload)
        serialized = json.dumps(payload)
        assert "C:\\\\Users" not in serialized
        assert payload.get("outer_accessed", payload.get("outer_access", False)) is False
        assert payload.get(
            "sealed_test_accessed", payload.get("sealed_test_access", False)
        ) is False
