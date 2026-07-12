"""TASK-025 ARGOS prompt-fidelity and provider-ready capture harness.

This module reconstructs the pinned ARGOS DetectionAgentV3 prompt path without
importing ARGOS. It captures prompts and mock/manual responses, validates
generated Python statically, and never executes generated Python.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.argos_reproduction import mock_harness


ARGOS_DETECTION_PROMPT_PATH = Path("external/argos/agent/prompts/detection.py")
DEFAULT_TEMPLATE_NAME = "DETECTION_AGENT_V3_DEFAULT_PROMPT_TEMPLATE"
PROMPT_FIDELITY_STATEMENT = (
    "This is an ARGOS rule-only prompt-capture smoke. It is not a benchmark "
    "result and must not be used as a thesis performance claim."
)


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(data: Any) -> str:
    return sha256_text(stable_json(data))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    resolved = path.resolve()
    if not resolved.is_relative_to(REPO_ROOT):
        raise ValueError(f"Refusing to write outside repository: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    resolved = path.resolve()
    if not resolved.is_relative_to(REPO_ROOT):
        raise ValueError(f"Refusing to write outside repository: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text, encoding="utf-8", newline="\n")


def assert_private_artifact_path(path: Path) -> None:
    resolved = path.resolve()
    private_root = (REPO_ROOT / "artifacts").resolve()
    if not resolved.is_relative_to(private_root):
        raise ValueError(f"Private prompt artifacts must stay under ignored artifacts/: {resolved}")


def extract_string_constant(source_path: Path, name: str) -> str:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            target_names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if name in target_names:
                value = ast.literal_eval(node.value)
                if not isinstance(value, str):
                    raise TypeError(f"{name} is not a string literal")
                return value
    raise KeyError(f"Cannot find string literal {name} in {source_path}")


def build_system_prompt(chunk_size: int, prompt_path: Path | None = None) -> dict[str, Any]:
    source_path = prompt_path or (REPO_ROOT / ARGOS_DETECTION_PROMPT_PATH)
    template = extract_string_constant(source_path, DEFAULT_TEMPLATE_NAME)
    system_prompt = template.format(chunk_size=chunk_size).strip()
    return {
        "system_prompt": system_prompt,
        "template_hash": sha256_text(template),
        "system_prompt_hash": sha256_text(system_prompt),
        "source_path": source_path.relative_to(REPO_ROOT).as_posix(),
        "template_name": DEFAULT_TEMPLATE_NAME,
    }


def load_argos_rows(csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["value", "label", "index"]:
            raise ValueError(f"Unexpected ARGOS CSV schema: {reader.fieldnames}")
        for row in reader:
            label = int(row["label"])
            if label not in {0, 1}:
                raise ValueError(f"Non-binary label: {label}")
            rows.append(
                {
                    "value": float(row["value"]),
                    "label": label,
                    "index": int(row["index"]),
                }
            )
    if not rows:
        raise ValueError("Converted ARGOS CSV is empty")
    return rows


def select_prompt_chunk(rows: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    chunk_size = int(policy["chunk_size"])
    full_train_end = int(len(rows) * float(policy["train_test_split"]))
    train_end = int(full_train_end * (1.0 - float(policy["val_split"])))
    if train_end <= 0:
        raise ValueError("Empty ARGOS train partition under configured split policy")

    for start in range(0, train_end, chunk_size):
        end = min(start + chunk_size, train_end)
        chunk_rows = rows[start:end]
        labels = Counter(str(row["label"]) for row in chunk_rows)
        if (
            len(chunk_rows) > 0
            and labels.get("0", 0) > 0
            and labels.get("1", 0) > 0
            and all(set(row) == {"value", "label", "index"} for row in chunk_rows)
        ):
            return {
                "start_position": start,
                "end_position_exclusive": end,
                "start_index": chunk_rows[0]["index"],
                "end_index_inclusive": chunk_rows[-1]["index"],
                "row_count": len(chunk_rows),
                "label_counts": dict(sorted(labels.items())),
                "rows": chunk_rows,
                "chunk_hash": sha256_json({"columns": ["value", "label", "index"], "rows": chunk_rows}),
            }
    raise ValueError("No eligible train chunk with both normal and anomaly labels")


def serialize_chunk_like_argos(chunk_rows: list[dict[str, Any]]) -> str:
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - bundled runtime includes pandas
        raise RuntimeError("pandas is required to match ARGOS DataFrame.to_string serialization") from exc

    df = pd.DataFrame(chunk_rows, columns=["value", "label", "index"])
    return df.to_string(index=False, header=False)


def build_user_prompt(chunk_rows: list[dict[str, Any]]) -> dict[str, Any]:
    data_string = serialize_chunk_like_argos(chunk_rows)
    user_prompt = "##### DATA 0\n" + data_string + "\n"
    return {
        "user_prompt": user_prompt,
        "user_prompt_hash": sha256_text(user_prompt),
        "serialization": "pandas.DataFrame.to_string(index=False, header=False)",
        "data_header": "##### DATA 0",
    }


def credential_audit_text(text: str) -> dict[str, Any]:
    forbidden_markers = [
        "OPENAI_AZURE_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "API_KEY=",
        "TOKEN=",
        "SECRET=",
        "sk-",
    ]
    matches = [marker for marker in forbidden_markers if marker.lower() in text.lower()]
    for key, value in os.environ.items():
        key_upper = key.upper()
        if any(token in key_upper for token in ("API", "TOKEN", "SECRET", "KEY")) and value and len(value) >= 12:
            if value in text:
                matches.append(f"ENV_VALUE:{key}")
    return {
        "passed": not matches,
        "matches": sorted(set(matches)),
    }


def provider_approval_ready(approval: dict[str, Any]) -> dict[str, Any]:
    required_budget_fields = [
        "max_input_tokens",
        "max_output_tokens",
        "max_cost_usd",
        "temperature",
    ]
    blockers: list[str] = []
    if approval.get("approved") is not True:
        blockers.append("approval_not_true")
    if not approval.get("provider"):
        blockers.append("provider_missing")
    if not approval.get("model"):
        blockers.append("model_missing")
    for field in required_budget_fields:
        if approval.get(field) is None:
            blockers.append(f"{field}_missing")
    if not approval.get("approved_by"):
        blockers.append("approved_by_missing")
    if not approval.get("approval_date"):
        blockers.append("approval_date_missing")
    return {
        "ready": not blockers,
        "blockers": blockers,
    }


def require_provider_gate(
    config: dict[str, Any], allow_real_provider_call: bool, approval: dict[str, Any] | None
) -> dict[str, Any]:
    if config["provider"]["mode"] != "provider":
        return {
            "real_provider_call_allowed": False,
            "real_provider_call_requested": False,
            "blockers": [],
        }
    blockers: list[str] = []
    if not allow_real_provider_call:
        blockers.append("cli_allow_real_provider_call_missing")
    if approval is None:
        blockers.append("approval_artifact_missing")
        readiness = {"ready": False, "blockers": []}
    else:
        readiness = provider_approval_ready(approval)
        blockers.extend(readiness["blockers"])
    credential_names = config["provider"].get("required_credential_env", [])
    missing_credentials = [name for name in credential_names if not os.environ.get(name)]
    blockers.extend(f"credential_missing:{name}" for name in missing_credentials)
    return {
        "real_provider_call_allowed": not blockers,
        "real_provider_call_requested": True,
        "blockers": blockers,
        "approval_readiness": readiness,
        "credentials_checked": credential_names,
    }


def capture_response(config: dict[str, Any], allow_real_provider_call: bool) -> dict[str, Any]:
    mode = config["provider"]["mode"]
    approval = None
    approval_path_value = config["provider"].get("approval_path")
    if approval_path_value:
        approval_path = REPO_ROOT / approval_path_value
        if approval_path.exists():
            approval = read_json(approval_path)
    gate = require_provider_gate(config, allow_real_provider_call, approval)
    if mode == "mock":
        return {
            "mode": mode,
            "response": config["mock_response"],
            "status": "captured",
            "provider_gate": gate,
        }
    if mode == "manual_capture":
        manual_path = REPO_ROOT / config["provider"]["manual_response_path"]
        assert_private_artifact_path(manual_path)
        if not manual_path.exists():
            raise FileNotFoundError(f"Manual response file not found: {manual_path}")
        return {
            "mode": mode,
            "response": manual_path.read_text(encoding="utf-8"),
            "status": "captured",
            "provider_gate": gate,
        }
    if mode == "provider":
        if not gate["real_provider_call_allowed"]:
            raise PermissionError(f"Real provider call refused: {gate['blockers']}")
        raise RuntimeError("Real provider execution is intentionally not implemented in TASK-025")
    raise ValueError(f"Unknown provider mode: {mode}")


def prompt_mapping() -> list[dict[str, str]]:
    return [
        {
            "ARGOS component": "Detection Agent system prompt",
            "Pinned file/function": "agent/prompts/detection.py::build_detection_agent_v3_prompt",
            "Reproduced field": "system_prompt",
            "Deviation": "Template literal is read by AST instead of importing ARGOS to avoid provider/client side effects.",
        },
        {
            "ARGOS component": "train-LLM-only mode selection",
            "Pinned file/function": "driver.py --mode default and runtime/engine.py::Engine(... mode='train-LLM-only')",
            "Reproduced field": "mode",
            "Deviation": "Only the first DetectionAgentV3 request is reconstructed; RepairAgent and ReviewAgent are not run.",
        },
        {
            "ARGOS component": "sample serialization",
            "Pinned file/function": "agent/detection_agent.py::DetectionAgentV3.run curr_df.to_string(index=False, header=False)",
            "Reproduced field": "user_prompt",
            "Deviation": "Chunk selection is deterministic first eligible chunk, not np.random.randint(0, 1000).",
        },
        {
            "ARGOS component": "chunk-size resolution",
            "Pinned file/function": "driver.py --chunk_size default=1000 and runtime/engine.py::Engine(chunk_size=1000)",
            "Reproduced field": "chunk_selection.chunk_size",
            "Deviation": "No CLI override is used in TASK-025.",
        },
        {
            "ARGOS component": "expected Python code fence",
            "Pinned file/function": "agent/prompts/detection.py DETECTION_AGENT_V3_DEFAULT_PROMPT_TEMPLATE",
            "Reproduced field": "static_validation.code_fence_extracted",
            "Deviation": "Captured response is validated but never executed.",
        },
        {
            "ARGOS component": "required inference signature",
            "Pinned file/function": "agent/agent.py::Agent.extract_code and prompt text",
            "Reproduced field": "static_validation.signature",
            "Deviation": "TASK-025 validates exactly one inference function with AST.",
        },
        {
            "ARGOS component": "normal-rule comments",
            "Pinned file/function": "agent/prompts/detection.py default V3 prompt",
            "Reproduced field": "system_prompt",
            "Deviation": "No deviation.",
        },
        {
            "ARGOS component": "abnormal-rule conditions",
            "Pinned file/function": "agent/prompts/detection.py default V3 prompt",
            "Reproduced field": "system_prompt",
            "Deviation": "No deviation.",
        },
        {
            "ARGOS component": "iteration history behavior",
            "Pinned file/function": "agent/detection_agent.py::DetectionAgentV3.run appends CODE FROM LAST ITERATION",
            "Reproduced field": "iteration_history",
            "Deviation": "First capture uses no previous rule, so no history block is appended.",
        },
    ]


def run_capture(config_path: Path, allow_real_provider_call: bool = False) -> dict[str, Any]:
    config = read_json(config_path)
    task024_manifest = read_json(REPO_ROOT / config["task024_manifest_path"])
    converted_info = task024_manifest["converted_argos_csv"]
    converted_path = REPO_ROOT / converted_info["converted_path"]
    if sha256_file(converted_path) != config["frozen_inputs"]["converted_csv_sha256"]:
        raise ValueError("Converted CSV SHA-256 does not match frozen TASK-024 input")

    rows = load_argos_rows(converted_path)
    chunk = select_prompt_chunk(rows, config["chunk_selection"])
    user_prompt_info = build_user_prompt(chunk["rows"])
    system_prompt_info = build_system_prompt(config["chunk_selection"]["chunk_size"])

    request = {
        "messages": [
            {"role": "system", "content": system_prompt_info["system_prompt"]},
            {"role": "user", "content": user_prompt_info["user_prompt"]},
        ],
        "provider": {
            "mode": config["provider"]["mode"],
            "default_mode": config["provider"]["default_mode"],
            "allow_network": config["provider"]["allow_network"],
        },
        "mode": config["mode"],
    }
    credential_audit = credential_audit_text(stable_json(request))
    if not credential_audit["passed"]:
        raise ValueError(f"Credential-like content found in prompt request: {credential_audit['matches']}")

    private_root = REPO_ROOT / config["private_artifact_root"]
    assert_private_artifact_path(private_root)
    chunk_path = private_root / "chunks" / "selected_chunk.json"
    request_path = private_root / "requests" / "complete_request.json"
    write_json(chunk_path, {"columns": ["value", "label", "index"], "rows": chunk["rows"]})
    write_json(request_path, request)

    response_capture = capture_response(config, allow_real_provider_call)
    raw_response = response_capture["response"]
    response_hash = sha256_text(raw_response)
    rule_code = mock_harness.extract_python_rule(raw_response)
    rule_hash = sha256_text(rule_code)
    static_safety = mock_harness.static_safety_checks(rule_code, set(config["allowed_imports"]))

    response_path = private_root / "responses" / "captured_response.md"
    rule_path = private_root / "quarantine" / f"{rule_hash}.py"
    write_text(response_path, raw_response)
    write_text(rule_path, rule_code)

    chunk_manifest = {
        "schema_version": "1.0",
        "artifact_type": "task025_prompt_chunk_manifest",
        "task_id": "TASK-025",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "statement": PROMPT_FIDELITY_STATEMENT,
        "frozen_inputs": config["frozen_inputs"],
        "source_converted_csv_hash": config["frozen_inputs"]["converted_csv_sha256"],
        "selected_kpi_id": config["frozen_inputs"]["selected_kpi_id"],
        "selection_policy": {
            key: value for key, value in config["chunk_selection"].items() if key != "notes"
        },
        "selection_policy_hash": sha256_json(config["chunk_selection"]),
        "chunk": {
            "start_position": chunk["start_position"],
            "end_position_exclusive": chunk["end_position_exclusive"],
            "start_index": chunk["start_index"],
            "end_index_inclusive": chunk["end_index_inclusive"],
            "row_count": chunk["row_count"],
            "label_counts": chunk["label_counts"],
            "chunk_hash": chunk["chunk_hash"],
            "private_chunk_artifact": chunk_path.relative_to(REPO_ROOT).as_posix(),
        },
        "raw_rows_tracked": False,
        "performance_selection_used": False,
    }
    chunk_manifest["manifest_hash"] = sha256_json(chunk_manifest)

    request_hash = sha256_json(request)
    capture_report = {
        "schema_version": "1.0",
        "artifact_type": "task025_prompt_capture_report",
        "task_id": "TASK-025",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "statement": PROMPT_FIDELITY_STATEMENT,
        "frozen_inputs": config["frozen_inputs"],
        "prompt_fidelity": {
            "argos_commit": config["frozen_inputs"]["argos_commit"],
            "mapping": prompt_mapping(),
            "system_prompt_source": system_prompt_info["source_path"],
            "system_prompt_template_name": system_prompt_info["template_name"],
        },
        "hashes": {
            "config_hash": sha256_json(config),
            "system_prompt_template_hash": system_prompt_info["template_hash"],
            "system_prompt_hash": system_prompt_info["system_prompt_hash"],
            "user_prompt_hash": user_prompt_info["user_prompt_hash"],
            "chunk_hash": chunk["chunk_hash"],
            "complete_request_hash": request_hash,
            "raw_response_hash": response_hash,
            "rule_hash": rule_hash,
        },
        "private_artifacts": {
            "complete_request_path": request_path.relative_to(REPO_ROOT).as_posix(),
            "selected_chunk_path": chunk_path.relative_to(REPO_ROOT).as_posix(),
            "captured_response_path": response_path.relative_to(REPO_ROOT).as_posix(),
            "quarantined_rule_path": rule_path.relative_to(REPO_ROOT).as_posix(),
        },
        "provider": {
            "mode": response_capture["mode"],
            "default_mode": config["provider"]["default_mode"],
            "real_provider_call_requested": response_capture["provider_gate"]["real_provider_call_requested"],
            "real_provider_call_allowed": response_capture["provider_gate"]["real_provider_call_allowed"],
            "provider_gate": response_capture["provider_gate"],
        },
        "response_capture": {
            "status": response_capture["status"],
            "code_extracted": True,
            "signature_valid": static_safety["signature"]["signature_valid"],
            "static_safety_passed": static_safety["passed"],
            "static_safety": static_safety,
            "execution_performed": False,
            "performance_metric_reported": False,
        },
        "prompt_retention": {
            "full_prompt_tracked": False,
            "raw_response_tracked": False,
            "raw_rows_tracked": False,
            "ignored_private_only": True,
            "credential_audit": credential_audit,
        },
        "boundaries": config["boundaries"],
    }
    capture_report["report_hash"] = sha256_json(capture_report)

    write_json(REPO_ROOT / config["output_chunk_manifest_path"], chunk_manifest)
    write_json(REPO_ROOT / config["output_capture_report_path"], capture_report)
    return {
        "chunk_manifest": chunk_manifest,
        "capture_report": capture_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="TASK-025 ARGOS prompt capture harness")
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task025_prompt_capture.json",
        help="Path to TASK-025 prompt capture config JSON.",
    )
    parser.add_argument(
        "--allow-real-provider-call",
        action="store_true",
        help="Require explicit researcher approval artifact before any future provider call.",
    )
    args = parser.parse_args()
    result = run_capture((REPO_ROOT / args.config).resolve(), args.allow_real_provider_call)
    report = result["capture_report"]
    print(
        json.dumps(
            {
                "selected_kpi_id": report["frozen_inputs"]["selected_kpi_id"],
                "chunk_hash": report["hashes"]["chunk_hash"],
                "rule_hash": report["hashes"]["rule_hash"],
                "execution_performed": report["response_capture"]["execution_performed"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
