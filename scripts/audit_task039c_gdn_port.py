#!/usr/bin/env python
"""Build the TASK-039C-GDNP pre-data compatibility closure receipts."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from paperworks.gdn.gdn_remediation_environment_v1 import (  # noqa: E402
    assert_public_payload_sanitized_v1,
)
from paperworks.gdn.pyg_port_compatibility_v1 import (  # noqa: E402
    COMPATIBILITY_STATUS,
    GDNPortCompatibilityError,
    assert_gdnp_patch_scope_v1,
    build_api_drift_matrix_v1,
    build_compatibility_closure_receipt_v1,
    build_legacy_oracle_receipt_v1,
    build_source_inventories_v1,
    confirm_node_dim_root_cause_v1,
    run_gnn_layer_parity_v1,
    run_graph_layer_backward_parity_v1,
    run_graph_layer_forward_parity_v1,
    run_index_semantics_gate_v1,
    run_tiny_full_gdn_gate_v1,
    run_tiny_training_loop_gate_v1,
)
from paperworks.v6.common import canonical_json_v1, parse_iso_datetime  # noqa: E402

import run_task039c_gdn_compat as gdnc  # noqa: E402


REPORT_ROOT = ROOT / "docs" / "task_reports"
MATRIX_OUTPUT = REPORT_ROOT / "TASK-039C_GDNP_API_DRIFT_MATRIX.json"
INDEX_OUTPUT = REPORT_ROOT / "TASK-039C_GDNP_INDEX_SEMANTICS_RECEIPT.json"
COMPATIBILITY_OUTPUT = REPORT_ROOT / "TASK-039C_GDNP_COMPATIBILITY_RECEIPT.json"
LEGACY_OUTPUT = REPORT_ROOT / "TASK-039C_GDNP_LEGACY_ORACLE_RECEIPT.json"


def _write_public(path: Path, payload: Mapping[str, Any]) -> None:
    assert_public_payload_sanitized_v1(payload)
    path.write_text(canonical_json_v1(dict(payload)) + "\n", encoding="utf-8")


def build(args: argparse.Namespace) -> None:
    parse_iso_datetime(args.created_at, "created_at")
    gdnc._validate_exact_environment()
    upstream_root = Path(args.upstream_root).resolve(strict=True)
    pyg_source_root = Path(args.pyg_source_root).resolve(strict=True)
    source = build_source_inventories_v1(
        upstream_root=upstream_root,
        pyg_source_root=pyg_source_root,
    )
    root_cause = confirm_node_dim_root_cause_v1(
        repository_root=ROOT,
        upstream_root=upstream_root,
        pyg_source_root=pyg_source_root,
    )
    matrix = build_api_drift_matrix_v1(
        source_inventories=source,
        created_at=args.created_at,
    )
    forward = run_graph_layer_forward_parity_v1()
    backward = run_graph_layer_backward_parity_v1()
    index = run_index_semantics_gate_v1()
    gnn = run_gnn_layer_parity_v1()
    tiny = run_tiny_full_gdn_gate_v1()
    training = run_tiny_training_loop_gate_v1()
    if shutil.which("podman") is None:
        legacy = build_legacy_oracle_receipt_v1(
            status="blocked_official_legacy_environment_unavailable",
            reason="rootless Podman is unavailable; no legacy environment was constructed",
            created_at=args.created_at,
        )
    else:
        raise GDNPortCompatibilityError(
            "legacy Podman is available; use the separately reviewed exact-oracle recipe"
        )
    patched_hash = assert_gdnp_patch_scope_v1(repository_root=ROOT)
    compatibility = build_compatibility_closure_receipt_v1(
        source_inventories=source,
        api_matrix=matrix,
        root_cause=root_cause,
        forward_parity=forward,
        backward_parity=backward,
        index_semantics=index,
        gnn_parity=gnn,
        tiny_full_gdn=tiny,
        tiny_training_loop=training,
        legacy_oracle=legacy,
        patched_implementation_hash=patched_hash,
        created_at=args.created_at,
    )
    for path in (MATRIX_OUTPUT, INDEX_OUTPUT, COMPATIBILITY_OUTPUT, LEGACY_OUTPUT):
        if path.exists():
            raise GDNPortCompatibilityError(f"refusing to overwrite {path.name}")
    _write_public(MATRIX_OUTPUT, matrix)
    _write_public(INDEX_OUTPUT, index)
    _write_public(LEGACY_OUTPUT, legacy)
    _write_public(COMPATIBILITY_OUTPUT, compatibility)
    print(
        canonical_json_v1(
            {
                "status": COMPATIBILITY_STATUS,
                "api_drift_matrix_hash": matrix["artifact_hash"],
                "index_semantics_receipt_hash": index["artifact_hash"],
                "legacy_oracle_status": legacy["status"],
                "compatibility_receipt_hash": compatibility["artifact_hash"],
            }
        )
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--upstream-root", required=True)
    result.add_argument("--pyg-source-root", required=True)
    result.add_argument("--created-at", required=True)
    return result


def main() -> int:
    try:
        build(parser().parse_args())
    except GDNPortCompatibilityError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
