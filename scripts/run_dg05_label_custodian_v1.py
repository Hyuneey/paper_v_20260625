"""Fresh-process entry point for the capability-scoped DG-05 custodian."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from paperworks.validation_v2.dg05_label_custodian_v1 import consume_and_extract_v1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--resource-policy-authority", type=Path, required=True)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    result = consume_and_extract_v1(request, resource_policy_authority_path=args.resource_policy_authority)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
