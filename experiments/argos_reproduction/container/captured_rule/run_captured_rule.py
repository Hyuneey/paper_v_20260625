"""Future container entrypoint for one approved fixed-hash synthetic run.

TASK-027 prepares this runner but does not build it or invoke it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import sys
from pathlib import Path

import numpy as np


RULE_PATH = Path("/rule/captured_rule.py")
INPUT_PATH = Path("/input/input.json")
OUTPUT_PATH = Path("/output/result.json")
MAX_OUTPUT_BYTES = 65536
EXECUTION_TIMEOUT_SECONDS = 2


def _raise_timeout(signum: int, frame: object) -> None:
    raise TimeoutError("Captured rule execution exceeded two seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def reject_provider_credentials() -> None:
    sensitive_markers = ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")
    exposed = sorted(name for name in os.environ if any(marker in name.upper() for marker in sensitive_markers))
    if exposed:
        raise RuntimeError("Provider-like credential environment variables are prohibited")


def load_synthetic_input() -> np.ndarray:
    payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    if payload.get("input_kind") != "synthetic_non_kpi":
        raise ValueError("Only synthetic_non_kpi input is permitted")
    values = np.asarray(payload.get("values"), dtype=float)
    if values.ndim != 2 or values.shape[1] < 1:
        raise ValueError("Input values must be a two-dimensional nonempty-column array")
    return values


def write_validated_output(output: np.ndarray, expected_rows: int) -> None:
    labels = np.asarray(output)
    if labels.shape != (expected_rows,):
        raise ValueError("Rule output must be one-dimensional and match the input row count")
    unique = set(np.unique(labels).tolist())
    if not unique.issubset({0, 1}):
        raise ValueError("Rule output must contain only binary labels")
    encoded = json.dumps(
        {"schema_version": "1.0", "row_count": expected_rows, "labels": labels.astype(int).tolist()},
        separators=(",", ":"),
    ).encode("utf-8")
    if len(encoded) > MAX_OUTPUT_BYTES:
        raise ValueError("Validated output exceeds the configured file-size limit")
    OUTPUT_PATH.write_bytes(encoded)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-rule-hash", required=True)
    args = parser.parse_args()

    reject_provider_credentials()
    actual_hash = sha256_file(RULE_PATH)
    if actual_hash != args.expected_rule_hash:
        raise ValueError("Captured rule hash mismatch")

    values = load_synthetic_input()
    sys.path.insert(0, str(RULE_PATH.parent))
    from captured_rule import inference

    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.alarm(EXECUTION_TIMEOUT_SECONDS)
    try:
        output = inference(values)
    finally:
        signal.alarm(0)
    write_validated_output(output, values.shape[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
