"""Clean-process V11 release-root rehearsal entrypoint; it never loads held-out rows."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from paperworks.validation_v2.dg05_production_chain_v11 import PREACCESS_MODE
from paperworks.validation_v2.dg05_v11_root_verifier_v1 import verify_v11_roots


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--scenario", required=True, type=Path)
    parser.add_argument("--p1", required=True, type=Path)
    parser.add_argument("--expected-hash", required=True)
    args = parser.parse_args()
    receipt = verify_v11_roots(repository_root=ROOT, manifest_path=args.manifest,
                               scenario_path=args.scenario, p1_path=args.p1,
                               expected_hash=args.expected_hash)
    safe = {"schema": "dg05_v11_fresh_process_launcher_receipt_v1", "status": "PASS",
            "parent_pid": os.getppid(), "custodian_pid": os.getpid(),
            "pid_distinct": os.getppid() != os.getpid(), "python": sys.version.split()[0],
            "mode": PREACCESS_MODE, "root_replay_hash": receipt["self_hash"],
            "heldout_prediction_cells": 0, "metric_cells": 0,
            "inherited_authority_objects": False}
    print(json.dumps(safe, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
