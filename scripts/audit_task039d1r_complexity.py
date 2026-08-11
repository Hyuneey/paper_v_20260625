"""Build the pre-data TASK-039D1R recovery receipts and schemas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paperworks.profiling.task039d1_execution_optimization_v1 import (
    TASK039D1AbortedExecutionRecordV1,
    TASK039D1ExecutionComplexityReceiptV1,
    build_aborted_execution_record_v1,
    build_complexity_receipt_v1,
    schema_for_recovery_artifact_v1,
    source_file_sha256_v1,
    verify_recovery_artifact_v1,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
SCHEMAS = ROOT / "schemas" / "v6"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build() -> dict[str, str]:
    source_paths = (
        "src/paperworks/profiling/task039d1_fit_v1.py",
        "src/paperworks/profiling/task039d1_execution_optimization_v1.py",
        "src/paperworks/v6/continuous_step_protocol_v1.py",
        "src/paperworks/v6/relation_profiling_protocol_v1.py",
        "src/paperworks/feasibility/hai_continuous_step_v1.py",
    )
    source_hashes = {name: source_file_sha256_v1(ROOT / name) for name in source_paths}
    complexity = build_complexity_receipt_v1(source_file_hashes=source_hashes)
    aborted = build_aborted_execution_record_v1()
    for document in (complexity, aborted):
        verify_recovery_artifact_v1(document)

    _write_json(REPORTS / "TASK-039D1R_EXECUTION_COMPLEXITY_RECEIPT.json", complexity)
    _write_json(REPORTS / "TASK-039D1_ABORTED_EXECUTION_RECORD.json", aborted)
    _write_json(
        SCHEMAS / "task039d1_execution_complexity_receipt_v1_schema.json",
        schema_for_recovery_artifact_v1(complexity),
    )
    _write_json(
        SCHEMAS / "task039d1_aborted_execution_record_v1_schema.json",
        schema_for_recovery_artifact_v1(aborted),
    )
    return {
        "status": str(complexity["status"]),
        "complexity_receipt_hash": str(complexity["artifact_hash"]),
        "aborted_execution_record_hash": str(aborted["artifact_hash"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    print(json.dumps(build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
