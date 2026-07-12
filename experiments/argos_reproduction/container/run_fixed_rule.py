"""Container entrypoint for future TASK-024-compatible fixed-rule execution."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np


INPUT_PATH = Path("/input/input.json")
RULE_PATH = Path("/input/fixed_rule.py")
OUTPUT_PATH = Path("/output/output.json")


def main() -> int:
    spec = importlib.util.spec_from_file_location("fixed_rule", RULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    sample = np.asarray(payload["sample"], dtype=float)
    labels = np.asarray(module.inference(sample))
    flat = labels.astype(int).reshape(-1)
    output = {
        "shape": list(labels.shape),
        "binary_domain": set(int(x) for x in flat.tolist()).issubset({0, 1}),
        "label_count": int(flat.size),
        "positive_count": int(np.sum(flat == 1)),
        "negative_count": int(np.sum(flat == 0)),
    }
    OUTPUT_PATH.write_text(json.dumps(output, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
