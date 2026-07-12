"""Offline, mock-only ARGOS reproduction harness for TASK-023.

This module intentionally does not import upstream ARGOS or src/paperworks.  It
validates a fixed mock response and stops before generated-code execution.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CODE_FENCE_RE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


PROHIBITED_CALL_NAMES = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "open",
    "input",
    "globals",
    "locals",
    "vars",
}

PROHIBITED_ATTRIBUTE_CALLS = {
    "os.system",
    "os.popen",
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "pathlib.Path",
}


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(data: Any) -> str:
    return sha256_text(stable_json(data))


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


def extract_python_rule(mock_response: str) -> str:
    match = CODE_FENCE_RE.search(mock_response)
    if not match:
        raise ValueError("mock_response must contain a Python markdown code fence")
    code = match.group(1).strip()
    if not code:
        raise ValueError("extracted Python rule is empty")
    return code + "\n"


def _annotation_name(node: ast.AST | None) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _annotation_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Subscript):
        return _annotation_name(node.value)
    if isinstance(node, ast.Constant):
        return str(node.value)
    return ast.unparse(node)


def validate_required_signature(tree: ast.Module) -> dict[str, Any]:
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    inference_functions = [node for node in functions if node.name == "inference"]
    if len(inference_functions) != 1:
        raise ValueError("expected exactly one function named inference")
    func = inference_functions[0]
    args = func.args
    if args.vararg or args.kwarg or args.kwonlyargs:
        raise ValueError("inference must not use varargs, kwargs, or keyword-only args")
    if len(args.args) != 1 or args.args[0].arg != "sample":
        raise ValueError("inference signature must be inference(sample)")

    return_annotation = _annotation_name(func.returns)
    arg_annotation = _annotation_name(args.args[0].annotation)
    return {
        "function_name": func.name,
        "arg_count": len(args.args),
        "arg_name": args.args[0].arg,
        "arg_annotation": arg_annotation,
        "return_annotation": return_annotation,
        "signature_valid": True,
    }


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def static_safety_checks(code: str, allowed_imports: set[str]) -> dict[str, Any]:
    tree = ast.parse(code)
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            else:
                modules = [(node.module or "").split(".")[0]]
            for module in modules:
                if module not in allowed_imports:
                    violations.append(f"IMPORT_NOT_ALLOWED:{module}")

        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in PROHIBITED_CALL_NAMES:
                violations.append(f"PROHIBITED_CALL:{call_name}")
            if call_name in PROHIBITED_ATTRIBUTE_CALLS:
                violations.append(f"PROHIBITED_ATTRIBUTE_CALL:{call_name}")

    signature = validate_required_signature(tree)
    return {
        "passed": not violations,
        "violations": violations,
        "signature": signature,
    }


def build_report(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    prompt = config["prompt"]
    mock_response = config["mock_response"]
    fixture = config["fixture"]
    sandbox = config["sandbox"]
    allowed_imports = set(config.get("allowed_imports", []))
    rule_code = extract_python_rule(mock_response)
    safety = static_safety_checks(rule_code, allowed_imports)

    execution_requested = bool(sandbox.get("execute_generated_code", False))
    if execution_requested:
        raise ValueError(
            "TASK-023 harness refuses generated-code execution; enable only in a future approved sandbox task"
        )

    hashes = {
        "config_hash": sha256_json(config),
        "fixture_hash": sha256_json(fixture),
        "prompt_hash": sha256_text(prompt),
        "mock_response_hash": sha256_text(mock_response),
        "rule_hash": sha256_text(rule_code),
    }

    config_ref = config_path.resolve().relative_to(REPO_ROOT).as_posix()
    return {
        "schema_version": "1.0",
        "artifact_type": "task023_offline_harness_report",
        "task_id": "TASK-023",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config_path": config_ref,
        "source_commit": config["source_commit"],
        "mode": config["mode"],
        "provider": config["provider"],
        "fixture": {
            "fixture_id": fixture["fixture_id"],
            "fixture_kind": fixture["fixture_kind"],
            "row_count": len(fixture["rows"]),
            "columns": fixture["columns"],
        },
        "hashes": hashes,
        "rule": {
            "origin": config["mock_response_origin"],
            "extracted": True,
            "hash": hashes["rule_hash"],
            "static_safety": safety,
        },
        "execution": {
            "generated_code_executed": False,
            "stop_reason": "generated_code_execution_not_enabled",
            "sandbox_enabled": bool(sandbox.get("enabled", False)),
            "actual_llm_generated_rule_execution_allowed": False,
        },
        "checks": {
            "provider_called": False,
            "network_used": False,
            "api_key_required": False,
            "upstream_argos_imported": False,
            "paperworks_imported": False,
            "actual_llm_generated_python_executed": False,
            "static_safety_passed": safety["passed"],
            "required_signature_valid": safety["signature"]["signature_valid"],
        },
    }


def run(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    report = build_report(config, config_path)
    output_path = REPO_ROOT / config["output_report_path"]
    write_json(output_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="TASK-023 offline ARGOS mock harness")
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task023_offline_harness.json",
        help="Path to the offline harness config JSON.",
    )
    args = parser.parse_args()
    report = run((REPO_ROOT / args.config).resolve())
    print(json.dumps({"config_path": report["config_path"], "rule_hash": report["rule"]["hash"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
