"""Generate the offline TASK-039E2 execution-configuration freeze artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paperworks.v6.task039e2_execution_configuration_v1 import (  # noqa: E402
    DIRECT_NUMBER_PROMPT_V1,
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1,
    MAIN_INITIAL_PROMPT_V1,
    MAIN_PROVIDER_SCHEMA_V1,
    PUBLIC_REPORT_FILES,
    T2_FOLLOWUP_PROMPT_V1,
    build_task039e2_artifacts_v1,
    schema_documents_v1,
)


def _write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip("\n") + "\n", encoding="utf-8", newline="\n")


def generate_v1(repository_root: Path) -> dict[str, str]:
    root = repository_root.resolve()
    artifacts = build_task039e2_artifacts_v1(root)

    prompt_root = root / "prompts" / "task039e2"
    _write_text(prompt_root / "main_initial_v1.txt", MAIN_INITIAL_PROMPT_V1)
    _write_text(prompt_root / "t2_followup_v1.txt", T2_FOLLOWUP_PROMPT_V1)
    _write_text(prompt_root / "direct_number_v1.txt", DIRECT_NUMBER_PROMPT_V1)

    schema_root = root / "schemas" / "v6"
    _write_json(schema_root / "task039e2_provider_proposal_core_v1_schema.json", MAIN_PROVIDER_SCHEMA_V1)
    _write_json(schema_root / "task039e2_direct_number_response_v1_schema.json", DIRECT_NUMBER_PROVIDER_SCHEMA_V1)
    for artifact_type, schema in schema_documents_v1(artifacts).items():
        _write_json(schema_root / f"{artifact_type}_schema.json", schema)

    reports = root / "docs" / "task_reports"
    for name, artifact in artifacts.items():
        _write_json(reports / PUBLIC_REPORT_FILES[name], artifact.to_dict())

    bundle = artifacts["protocol_bundle"].to_dict()
    hashes = {name: artifact.artifact_hash for name, artifact in artifacts.items()}
    report = f"""# TASK-039E2 Report

## Status

`{bundle['status']}`

TASK-039E2 freezes the future rule-construction execution configuration only.
It contacted no provider, inspected no credential, read no E1 private evidence,
generated no proposal, and granted no Rule v2 or runtime authority.

## Frozen execution

- Provider: `openai`
- Endpoint: `/v1/chat/completions`
- Exact snapshot: `gpt-5.4-2026-03-05`
- Sampling: reasoning `none`, temperature `0.7`, top-p `1.0`, maximum completion tokens `1024`, seed `null`
- Strict structured output: enabled for main and direct-number outputs
- Main initial prompt equality: T1 = T1-B1 = T1-B2 = T1-B3 = T2-call1
- Schedule: relation-major, 42 relations, maximum 336 scientific calls, concurrency 1
- Transport retries: at most 2 when no model response was obtained; scientific retries 0
- Direct-number roles: source step threshold, source stability tolerance, target noise scale

## Boundaries

- Provider contacted: `false`
- Credential checked: `false`
- Capability probe executed: `false`
- LLM called: `false`
- Real T0 generated: `false`
- E3 authorization created: `false`
- Rule v2 authorized: `false`
- Runtime authority: `false`

Next task: `TASK-039E2-AUDIT`.

## Component hashes

""" + "\n".join(f"- `{name}`: `{digest}`" for name, digest in hashes.items()) + "\n"
    _write_text(reports / "TASK-039E2_REPORT.md", report)
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    args = parser.parse_args()
    hashes = generate_v1(args.repository_root)
    print(json.dumps(hashes, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
