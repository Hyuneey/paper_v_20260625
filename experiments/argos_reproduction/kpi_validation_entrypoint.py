"""Container-only execution of one frozen ARGOS rule on validation values."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
from typing import Any

import numpy as np


RESULT_LIMIT_BYTES = 16_384
PREDICTION_LIMIT_BYTES = 65_536


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def validate_rule_structure(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "inference"]
    if len(definitions) != 1:
        raise ValueError("inference function count is invalid")
    function = definitions[0]
    if len(function.args.args) != 1 or function.args.args[0].arg != "sample":
        raise ValueError("inference signature is invalid")


def load_frozen_rule(path: Path, expected_hash: str) -> Any:
    if sha256_file(path) != expected_hash:
        raise ValueError("frozen rule hash mismatch")
    validate_rule_structure(path)
    spec = importlib.util.spec_from_file_location("task034_frozen_rule", path)
    if spec is None or spec.loader is None:
        raise ImportError("frozen rule loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inference = getattr(module, "inference", None)
    if not callable(inference):
        raise AttributeError("inference function unavailable")
    return inference


def load_validation_values(path: Path, expected_hash: str) -> np.ndarray:
    if sha256_file(path) != expected_hash:
        raise ValueError("validation input hash mismatch")
    values = np.load(path, allow_pickle=False)
    if values.ndim != 2 or values.shape[1] != 1:
        raise ValueError("validation input must be N x 1")
    if not np.issubdtype(values.dtype, np.number) or not np.all(np.isfinite(values)):
        raise ValueError("validation input must be finite numeric values")
    return np.asarray(values, dtype=np.float64)


def execute(rule: Path, values_path: Path, output_dir: Path, rule_hash: str, input_hash: str) -> dict[str, Any]:
    values = load_validation_values(values_path, input_hash)
    inference = load_frozen_rule(rule, rule_hash)
    output = np.asarray(inference(values))
    shape_valid = output.shape == (values.shape[0],)
    finite = bool(np.all(np.isfinite(output)))
    binary = bool(np.all(np.isin(output, np.asarray([0, 1]))))
    if not shape_valid or not finite or not binary:
        raise ValueError("prediction output contract failed")
    normalized = output.astype(np.int8, copy=False)
    prediction_path = output_dir / "prediction.npy"
    np.save(prediction_path, normalized, allow_pickle=False)
    if prediction_path.stat().st_size > PREDICTION_LIMIT_BYTES:
        raise ValueError("prediction output exceeds size limit")
    return {
        "rule_sha256": rule_hash,
        "validation_input_sha256": input_hash,
        "validation_row_count": int(values.shape[0]),
        "prediction_sha256": sha256_file(prediction_path),
        "predicted_positive_count": int(np.sum(normalized == 1)),
        "output_count": int(normalized.size),
        "output_shape_valid": shape_valid,
        "output_binary_domain_valid": binary,
        "output_finite": finite,
        "generated_rule_executed_on_host": False,
    }


def _read_cgroup(name: str) -> str | None:
    path = Path("/sys/fs/cgroup") / name
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def isolation_probe() -> dict[str, Any]:
    root_write_blocked = False
    try:
        Path("/task034-root-write-probe").write_text("blocked", encoding="utf-8")
    except OSError:
        root_write_blocked = True
    network_connect_blocked = False
    try:
        socket.create_connection(("192.0.2.1", 9), timeout=0.25)
    except OSError:
        network_connect_blocked = True
    return {
        "uid": os.getuid(),
        "network_interfaces": sorted(os.listdir("/sys/class/net")),
        "root_write_blocked": root_write_blocked,
        "network_connect_blocked": network_connect_blocked,
        "memory_max": _read_cgroup("memory.max"),
        "pids_max": _read_cgroup("pids.max"),
        "cpu_max": _read_cgroup("cpu.max"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rule")
    parser.add_argument("--values")
    parser.add_argument("--output")
    parser.add_argument("--expected-rule-hash")
    parser.add_argument("--expected-input-hash")
    parser.add_argument("--isolation-probe", action="store_true")
    args = parser.parse_args()
    if args.isolation_probe:
        encoded = stable_json_bytes({"isolation_probe": isolation_probe()})
        sys.stdout.buffer.write(encoded + b"\n")
        return 0
    if not all((args.rule, args.values, args.output, args.expected_rule_hash, args.expected_input_hash)):
        parser.error("rule, values, output, expected rule hash, and expected input hash are required")
    result = execute(
        Path(args.rule), Path(args.values), Path(args.output), args.expected_rule_hash, args.expected_input_hash
    )
    encoded = stable_json_bytes(result)
    if len(encoded) > RESULT_LIMIT_BYTES:
        raise ValueError("result metadata exceeds size limit")
    (Path(args.output) / "result.json").write_bytes(encoded)
    sys.stdout.buffer.write(encoded + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
