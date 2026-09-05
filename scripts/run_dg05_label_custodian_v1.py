"""Fresh-process entry point for the capability-scoped DG-05 custodian."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from paperworks.validation_v2.dg05_label_custodian_v1 import consume_and_extract_v1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    policy = request["resource_policy"]
    result = consume_and_extract_v1(request, input_root=Path(policy["input_root"]), output_root=Path(policy["output_root"]),
                                    forbidden_roots=tuple(Path(v) for v in policy["forbidden_roots"]))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
