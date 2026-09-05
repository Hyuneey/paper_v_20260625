"""Static fresh-process entry point for the multi-source DG-05 custodian."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from paperworks.validation_v2.dg05_label_custodian_v2 import CustodianV2Error, consume_and_extract_v2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--resource-policy-authority", type=Path, required=True)
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
        result = consume_and_extract_v2(request, resource_policy_authority_path=args.resource_policy_authority)
    except CustodianV2Error as exc:
        print(json.dumps({"schema": "fresh_process_custodian_failure_v2", "error": str(exc)}, sort_keys=True, separators=(",", ":")))
        return 2
    except Exception:
        # Never return exception text or local paths to the coordinator log.
        print(json.dumps({"schema": "fresh_process_custodian_failure_v2", "error": "UNHANDLED_CUSTODIAN_FAILURE"}, sort_keys=True, separators=(",", ":")))
        return 3
    result["custodian_pid"] = os.getpid()
    result["custodian_parent_pid"] = os.getppid()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
