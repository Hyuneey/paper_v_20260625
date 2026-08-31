"""Validate the EXP-02 runner authority shell without scientific data I/O.

This entry point deliberately stops at binding replay.  A later, separately
frozen scientific adapter must provide all three binding objects before any
train1/train2/train4 opener can be invoked through ``exp02_runner_v1``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from paperworks.validation_v2.exp02_runner_v1 import (
    Exp02RunnerError,
    frozen_scientific_binding_from_dict_v1,
    start_split_open_ledger_v1,
    validate_scientific_binding_bundle_v1,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="EXP-02 외부 동결 scientific binding 3종을 데이터 I/O 전에 재생 검증합니다."
    )
    parser.add_argument(
        "--binding-bundle", required=True, type=Path,
        help="공개 가능한 외부 동결 binding bundle JSON",
    )
    parser.add_argument(
        "--receipt-out", type=Path,
        help="선택 사항: 공개-safe preflight receipt JSON 출력",
    )
    return parser


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise Exp02RunnerError(
            "EXP02_RUNNER_CLI_DOCUMENT_INVALID", "binding bundle must be an exact JSON object"
        )
    return value


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        document = _load(args.binding_bundle)
        if set(document) != {
            "schema", "source_commit", "bindings", "expected_binding_hashes"
        } or document["schema"] != "paperworks.validation_v2.exp02_runner_binding_input_v1":
            raise Exp02RunnerError(
                "EXP02_RUNNER_CLI_SCHEMA_INVALID", "binding input schema differs"
            )
        if type(document["bindings"]) is not list or type(document["expected_binding_hashes"]) is not dict:
            raise Exp02RunnerError(
                "EXP02_RUNNER_CLI_SCHEMA_INVALID", "binding collection types differ"
            )
        bindings = tuple(
            frozen_scientific_binding_from_dict_v1(item)
            for item in document["bindings"]
        )
        receipt = validate_scientific_binding_bundle_v1(
            bindings,
            expected_binding_hashes=document["expected_binding_hashes"],
            source_commit=document["source_commit"],
        )
        ledger = start_split_open_ledger_v1(receipt)
        output = {
            "schema": "paperworks.validation_v2.exp02_runner_preflight_receipt_v1",
            "status": "BINDINGS_REPLAYED_DATA_NOT_OPENED",
            "binding_bundle": receipt.to_dict(),
            "split_open_ledger": ledger.to_dict(),
            "scientific_execution_count": 0,
            "test1_accesses": 0,
            "test2_accesses": 0,
            "label_accesses": 0,
            "heldout_accesses": 0,
        }
        payload = json.dumps(output, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        if args.receipt_out is not None:
            args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.receipt_out.with_suffix(args.receipt_out.suffix + ".tmp")
            temporary.write_text(payload, encoding="utf-8", newline="\n")
            temporary.replace(args.receipt_out)
        print("EXP-02 binding preflight: PASS (scientific data I/O = 0)")
        print(receipt.self_hash)
        return 0
    except (Exp02RunnerError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"EXP-02 binding preflight: FAIL_CLOSED ({exc})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
