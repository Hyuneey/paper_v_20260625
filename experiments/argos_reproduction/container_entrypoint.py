"""In-container runner for one frozen ARGOS rule and synthetic fixtures only."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
from typing import Any

import numpy as np


OUTPUT_LIMIT_BYTES = 65_536


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sanitized_exception_type(error: BaseException) -> str:
    return type(error).__name__ if type(error).__module__ == "builtins" else "RuleRuntimeError"


def load_fixture(path: Path) -> tuple[str, np.ndarray]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("input_kind") != "synthetic_non_kpi":
        raise ValueError("fixture input kind is not approved")
    shape = payload.get("shape")
    values = payload.get("values")
    if not isinstance(shape, list) or len(shape) != 2 or shape[1] != 1 or shape[0] < 0:
        raise ValueError("fixture shape must be N x 1")
    if not isinstance(values, list) or len(values) != shape[0]:
        raise ValueError("fixture values do not match declared shape")
    if shape[0] == 0:
        sample = np.empty((0, 1), dtype=np.float64)
    else:
        if any(not isinstance(row, list) or len(row) != 1 for row in values):
            raise ValueError("fixture rows must contain one value")
        sample = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(sample)):
        raise ValueError("fixture must contain finite numeric values")
    return str(payload["fixture_id"]), sample


def load_frozen_rule(path: Path, expected_hash: str) -> Any:
    if sha256_file(path) != expected_hash:
        raise ValueError("frozen rule hash mismatch inside container")
    spec = importlib.util.spec_from_file_location("task033_frozen_rule", path)
    if spec is None or spec.loader is None:
        raise ImportError("frozen rule module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inference = getattr(module, "inference", None)
    if not callable(inference):
        raise AttributeError("inference function is unavailable")
    return inference


def output_digest(output: np.ndarray) -> str:
    normalized = np.asarray(output, dtype=np.int8)
    return hashlib.sha256(normalized.tobytes(order="C")).hexdigest()


def run_rule(rule_path: Path, fixture_path: Path, expected_hash: str) -> dict[str, Any]:
    fixture_id = "unloaded"
    input_count = 0
    result: dict[str, Any] = {
        "fixture_id": fixture_id,
        "rule_sha256": expected_hash,
        "loaded": False,
        "exception_type": None,
        "output_returned": False,
        "output_count": None,
        "output_shape_valid": False,
        "output_binary_domain_valid": False,
        "output_finite": False,
        "output_sha256": None,
    }
    try:
        fixture_id, sample = load_fixture(fixture_path)
        input_count = int(sample.shape[0])
        result["fixture_id"] = fixture_id
        inference = load_frozen_rule(rule_path, expected_hash)
        result["loaded"] = True
        output = np.asarray(inference(sample))
        result["output_returned"] = True
        result["output_count"] = int(output.size)
        result["output_shape_valid"] = output.shape == (input_count,)
        result["output_binary_domain_valid"] = bool(
            np.all(np.isin(output, np.asarray([0, 1])))
        )
        result["output_finite"] = bool(np.all(np.isfinite(output)))
        result["output_sha256"] = output_digest(output)
    except BaseException as error:  # The exception boundary is part of the smoke contract.
        result["exception_type"] = sanitized_exception_type(error)
    result["input_count"] = input_count
    return result


def _read_cgroup(name: str) -> str | None:
    path = Path("/sys/fs/cgroup") / name
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def isolation_probe() -> dict[str, Any]:
    root_write_blocked = False
    try:
        Path("/task033-root-write-probe").write_text("blocked", encoding="utf-8")
    except OSError:
        root_write_blocked = True
    network_connect_blocked = False
    try:
        socket.create_connection(("192.0.2.1", 9), timeout=0.25)
    except OSError:
        network_connect_blocked = True
    return {
        "uid": os.getuid(),
        "gid": os.getgid(),
        "root_write_blocked": root_write_blocked,
        "network_connect_blocked": network_connect_blocked,
        "network_interfaces": sorted(os.listdir("/sys/class/net")),
        "memory_max": _read_cgroup("memory.max"),
        "pids_max": _read_cgroup("pids.max"),
        "cpu_max": _read_cgroup("cpu.max"),
    }


def emit_result(result: dict[str, Any]) -> None:
    encoded = stable_json(result).encode("utf-8")
    if len(encoded) > OUTPUT_LIMIT_BYTES:
        raise ValueError("result exceeds output limit")
    output = Path("/output/result.json")
    output.write_bytes(encoded)
    sys.stdout.buffer.write(encoded + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rule")
    parser.add_argument("--fixture")
    parser.add_argument("--expected-rule-hash")
    parser.add_argument("--isolation-probe", action="store_true")
    args = parser.parse_args()
    if args.isolation_probe:
        emit_result({"isolation_probe": isolation_probe()})
        return 0
    if not args.rule or not args.fixture or not args.expected_rule_hash:
        parser.error("rule, fixture, and expected hash are required")
    emit_result(run_rule(Path(args.rule), Path(args.fixture), args.expected_rule_hash))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
