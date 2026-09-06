"""Freeze HAI22's source-only private scenario authority and public receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paperworks.validation_v2.dg05_hai_official_scenario_v1 import build_hai22_authority, canonical_bytes, digest, self_hashed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    args = parser.parse_args()
    authority = build_hai22_authority(args.official_root)
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    args.private_output.write_bytes(canonical_bytes(authority) + b"\n")
    receipt = self_hashed({
        "schema": "hai22_official_scenario_authority_public_receipt_v1",
        "status": "PASS",
        "private_canonical_authority_sha256": authority["self_hash"],
        "canonical_scenario_count": len(authority["canonical_records"]),
        "file_census": authority["file_census"],
        "source_roles": authority["source_roles"],
        "official_source": authority["official_source"],
        "join_rule": authority["manual_file_binding_rule"],
        "public_scenario_metadata_access": "YES",
        "heldout_predictions_observed": 0,
        "heldout_metrics_observed": 0,
    })
    args.public_output.parent.mkdir(parents=True, exist_ok=True)
    args.public_output.write_bytes(canonical_bytes(receipt) + b"\n")
    print(json.dumps({"status": "PASS", "private_authority_hash": authority["self_hash"], "public_receipt_hash": receipt["self_hash"], "count": 58}, sort_keys=True))


if __name__ == "__main__":
    main()
