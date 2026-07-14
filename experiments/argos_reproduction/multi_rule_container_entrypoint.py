"""Container-only TASK-035A generated-rule runtime-contract entrypoint."""

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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_rule(path: Path, expected_hash: str) -> Any:
    if sha256_file(path) != expected_hash:
        raise ValueError("rule hash mismatch")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "inference"]
    if len(definitions) != 1:
        raise ValueError("inference definition invalid")
    spec = importlib.util.spec_from_file_location("task035a_generated_rule", path)
    if spec is None or spec.loader is None:
        raise ImportError("rule loader unavailable")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.inference


def execute(rule: Path, values_path: Path, output: Path, rule_hash: str, input_hash: str) -> dict[str, Any]:
    if sha256_file(values_path) != input_hash:
        raise ValueError("input hash mismatch")
    values = np.load(values_path, allow_pickle=False)
    if values.ndim != 2 or values.shape[1] != 1 or not np.issubdtype(values.dtype, np.number) or not np.all(np.isfinite(values)):
        raise ValueError("input contract invalid")
    prediction = np.asarray(load_rule(rule, rule_hash)(values))
    shape = prediction.shape == (len(values),); finite = bool(np.all(np.isfinite(prediction))); binary = bool(np.all(np.isin(prediction, [0, 1])))
    if not shape or not finite or not binary:
        raise ValueError("output contract invalid")
    prediction = prediction.astype(np.int8, copy=False)
    path = output / "output_labels.npy"; np.save(path, prediction, allow_pickle=False)
    return {"rule_sha256": rule_hash, "input_sha256": input_hash, "input_count": len(values), "output_count": len(prediction), "output_shape_valid": shape, "output_binary_domain_valid": binary, "output_finite": finite, "output_sha256": sha256_file(path)}


def probe() -> dict[str, Any]:
    blocked = False
    try: Path("/root-write-probe").write_text("x")
    except OSError: blocked = True
    network = False
    try: socket.create_connection(("192.0.2.1", 9), timeout=0.2)
    except OSError: network = True
    read = lambda name: (Path("/sys/fs/cgroup") / name).read_text().strip()
    return {"uid": os.getuid(), "interfaces": sorted(os.listdir("/sys/class/net")), "root_write_blocked": blocked, "network_blocked": network, "memory_max": read("memory.max"), "pids_max": read("pids.max"), "cpu_max": read("cpu.max")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rule"); parser.add_argument("--values"); parser.add_argument("--output")
    parser.add_argument("--rule-hash"); parser.add_argument("--input-hash"); parser.add_argument("--isolation-probe", action="store_true")
    args = parser.parse_args()
    if args.isolation_probe:
        print(json.dumps({"isolation_probe": probe()}, sort_keys=True)); return 0
    result = execute(Path(args.rule), Path(args.values), Path(args.output), args.rule_hash, args.input_hash)
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")); (Path(args.output) / "runtime_result.json").write_text(encoded)
    print(encoded); return 0


if __name__ == "__main__": raise SystemExit(main())
