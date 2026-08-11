"""Run authorized TASK-039E1 materialization without any HAI loader."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from paperworks.v6.task039e1_evidence_materialization_v1 import (
    D1_DIRECTIONAL_LEDGER_HASH,
    D1_SOURCE_LEDGER_HASH,
    D1_TARGET_LEDGER_HASH,
    D2_CONFIRMATION_LEDGER_HASH,
    E1_AUTHORIZATION_HASH,
    PRIVATE_D2_LEDGER_NAME,
    PRIVATE_DIRECTIONAL_LEDGER_NAME,
    PRIVATE_E1_LEDGER_NAME,
    PRIVATE_SOURCE_LEDGER_NAME,
    PRIVATE_TARGET_LEDGER_NAME,
    SCHEMA_FILES,
    build_public_result_artifacts_v1,
    load_e0_cohort_v1,
    load_private_ledger_v1,
    materialize_from_ledgers_v1,
    schema_documents_v1,
    validate_e1_authorization_v1,
    validate_external_roots_v1,
    verify_self_hash_v1,
    write_json_v1,
)


PUBLIC_NAMES = {
    "window": "TASK-039E1_WINDOW_CONSTANT_BUNDLE.json",
    "private_binding": "TASK-039E1_PRIVATE_LEDGER_BINDING.json",
    "manifest": "TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json",
    "cohort": "TASK-039E1_CONSTRUCTION_EVIDENCE_COHORT.json",
    "result": "TASK-039E1_MATERIALIZATION_RESULT.json",
    "access": "TASK-039E1_DATA_ACCESS_AUDIT.json",
    "receipt": "TASK-039E1_EXECUTION_RECEIPT.json",
}


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def _head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, encoding="utf-8"
    ).strip()


def write_schemas(root: Path) -> None:
    schemas = schema_documents_v1()
    if set(schemas) != set(SCHEMA_FILES):
        raise RuntimeError("E1 schema inventory differs")
    for name, relative in SCHEMA_FILES.items():
        write_json_v1(root / relative, schemas[name], public=True)


def _report(result: dict, materialized: dict, artifacts: dict, execution_code_commit: str) -> str:
    return f"""# TASK-039E1 Materialization Report

## Status

`{result['status']}`

## Frozen input

- execution code commit: `{execution_code_commit}`
- confirmed directional relations: `42`
- confirmed pair contexts: `23`
- D1 source/target/directional ledgers: verified
- D2 confirmation ledger: verified

## Materialization

- private evidence records: `42`
- numeric bindings: `462`
- public confirmed relation primitives: `42`
- approved numeric evidence bundles: `42`
- public manifest entries: `42`
- skipped/failed relations: `0 / 0`
- window constant bundle: `{materialized['window']['artifact_hash']}`
- private E1 ledger: `{materialized['private_ledger']['artifact_hash']}`
- public manifest: `{materialized['manifest']['artifact_hash']}`
- construction-evidence cohort: `{materialized['cohort']['artifact_hash']}`
- result: `{result['artifact_hash']}`
- access audit: `{artifacts['access']['artifact_hash']}`
- execution receipt: `{artifacts['receipt']['artifact_hash']}`

## Authority boundary

- HAI access: `false`
- train1/train2/train3 reread: `false`
- private input ledgers modified: `false`
- private calibrated values public: `false`
- LLM called: `false`
- T0/T1/T1-B/T2 generated: `false`
- Rule v2 authorized: `false`
- runtime authority: `false`
- next task: `TASK-039E1-AUDIT`
"""


def execute(
    *, root: Path, d1_private_value: str, d2_private_value: str,
    e1_private_value: str, execution_code_commit: str,
) -> dict[str, str]:
    # Public authorization and cohort validation deliberately precede all
    # private-root resolution or file operations.
    authorization = _read_json(root / "docs/task_reports/TASK-039E1_AUTHORIZATION.json")
    validate_e1_authorization_v1(authorization)
    cohort_document = _read_json(root / "docs/task_reports/TASK-039E0_CONFIRMED_RELATION_COHORT.json")
    cohort = load_e0_cohort_v1(cohort_document)
    if _head(root) != execution_code_commit:
        raise RuntimeError("execution must start from exact clean Commit A")

    d1_root, d2_root, e1_root = validate_external_roots_v1(
        repository_root=root,
        d1_private_value=d1_private_value,
        d2_private_value=d2_private_value,
        e1_private_value=e1_private_value,
    )
    source = load_private_ledger_v1(
        d1_root / PRIVATE_SOURCE_LEDGER_NAME,
        expected_hash=D1_SOURCE_LEDGER_HASH,
        expected_type="task039d1_source_parameter_ledger_v1",
        expected_count=12,
    )
    target = load_private_ledger_v1(
        d1_root / PRIVATE_TARGET_LEDGER_NAME,
        expected_hash=D1_TARGET_LEDGER_HASH,
        expected_type="task039d1_target_parameter_ledger_v1",
        expected_count=12,
    )
    directional = load_private_ledger_v1(
        d1_root / PRIVATE_DIRECTIONAL_LEDGER_NAME,
        expected_hash=D1_DIRECTIONAL_LEDGER_HASH,
        expected_type="task039d1_directional_fit_ledger_v1",
        expected_count=94,
    )
    d2 = load_private_ledger_v1(
        d2_root / PRIVATE_D2_LEDGER_NAME,
        expected_hash=D2_CONFIRMATION_LEDGER_HASH,
        expected_type="task039d2_directional_confirmation_ledger_v1",
        expected_count=45,
    )
    materialized = materialize_from_ledgers_v1(
        cohort=cohort, source_ledger=source, target_ledger=target,
        directional_ledger=directional, d2_ledger=d2,
        execution_code_commit=execution_code_commit,
    )
    write_json_v1(e1_root / PRIVATE_E1_LEDGER_NAME, materialized["private_ledger"], public=False)

    # Revalidate all inputs after the only output write to prove no mutation.
    for path, expected in (
        (d1_root / PRIVATE_SOURCE_LEDGER_NAME, D1_SOURCE_LEDGER_HASH),
        (d1_root / PRIVATE_TARGET_LEDGER_NAME, D1_TARGET_LEDGER_HASH),
        (d1_root / PRIVATE_DIRECTIONAL_LEDGER_NAME, D1_DIRECTIONAL_LEDGER_HASH),
        (d2_root / PRIVATE_D2_LEDGER_NAME, D2_CONFIRMATION_LEDGER_HASH),
    ):
        verify_self_hash_v1(_read_json(path), expected_hash=expected)

    artifacts = build_public_result_artifacts_v1(
        materialized=materialized, execution_code_commit=execution_code_commit
    )
    reports = root / "docs/task_reports"
    public = {
        "window": materialized["window"],
        "private_binding": materialized["private_binding"],
        "manifest": materialized["manifest"],
        "cohort": materialized["cohort"],
        **artifacts,
    }
    for key, document in public.items():
        write_json_v1(reports / PUBLIC_NAMES[key], document, public=True)
    (reports / "TASK-039E1_REPORT.md").write_text(
        _report(artifacts["result"], materialized, artifacts, execution_code_commit),
        encoding="utf-8", newline="\n",
    )
    return {key: document["artifact_hash"] for key, document in public.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-schemas-only", action="store_true")
    parser.add_argument("--execution-code-commit")
    parser.add_argument("--d1-private-root", default=os.environ.get("TASK039D_PRIVATE_ROOT", ""))
    parser.add_argument("--d2-private-root", default=os.environ.get("TASK039D2_PRIVATE_ROOT", ""))
    parser.add_argument("--e1-private-root", default=os.environ.get("TASK039E1_PRIVATE_ROOT", ""))
    args = parser.parse_args()
    root = args.repository_root.resolve(strict=True)
    if args.write_schemas_only:
        write_schemas(root)
        return 0
    if not args.execution_code_commit:
        parser.error("--execution-code-commit is required")
    hashes = execute(
        root=root,
        d1_private_value=args.d1_private_root,
        d2_private_value=args.d2_private_root,
        e1_private_value=args.e1_private_root,
        execution_code_commit=args.execution_code_commit,
    )
    print(json.dumps(hashes, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
