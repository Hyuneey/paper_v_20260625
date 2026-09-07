"""Freeze the non-approvable V11R2R1 execution binding and candidate.

This utility only serializes release-engineering artifacts.  It never opens a
protected source, constructs a projection, or performs prediction/metrics.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from paperworks.validation_v2.dg05_production_chain_v11 import canonical_bytes, load_self_hashed
from paperworks.validation_v2.dg05_production_chain_v11r2r1 import build_manifest
from paperworks.validation_v2.dg05_v11r2r1_execution_binding import build_execution_binding_v11r2r1


def _paths() -> dict[str, Path]:
    relative = {
        "successor_gate": "src/paperworks/validation_v2/dg05_production_chain_v11r2r1.py",
        "successor_runner": "scripts/run_dg05_v11r2r1.py",
        "complete_preflight": "src/paperworks/validation_v2/dg05_v11r2r1_preflight.py",
        "preflight_receipt": "src/paperworks/validation_v2/dg05_v11r2r1_preflight_receipt.py",
        "execution_binding": "src/paperworks/validation_v2/dg05_v11r2r1_execution_binding.py",
        "execution_ledger": "src/paperworks/validation_v2/dg05_v11r2_execution_ledger.py",
        "shared_route_core": "src/paperworks/validation_v2/dg05_v11r1_route_core.py",
        "resource_loader": "src/paperworks/validation_v2/dg05_v11r1_resource_loader.py",
        "resource_materializer": "src/paperworks/validation_v2/dg05_v11r1_resource_materializer.py",
        "container_materializer": "src/paperworks/validation_v2/dg05_v11r1_container_materializer.py",
        "resource_orchestrator": "src/paperworks/validation_v2/dg05_real_resource_orchestrator_v11r1.py",
        "production_executor": "src/paperworks/validation_v2/dg05_v11r1_production_executor.py",
        "execution_closure": "src/paperworks/validation_v2/dg05_execution_closure_v1.py",
        "normal_source": "src/paperworks/validation_v2/dg05_normal_source_v2.py",
        "normal_materializer": "scripts/materialize_dg05_normal_sources_v2.py",
        "v5_compatibility": "src/paperworks/validation_v2/dg05_v11r1_v5_compatibility.py",
        "v11_bridge": "src/paperworks/validation_v2/dg05_schedule_release_provenance_bridge_v11.py",
        "v5_kernel": "src/paperworks/validation_v2/dg05_production_route_v5.py",
        "source_file_crosswalk": "src/paperworks/validation_v2/dg05_v11r1_source_file_crosswalk.py",
        "postfreeze_metric_binding": "src/paperworks/validation_v2/dg05_v11r1_postfreeze_metric_binding.py",
        "metric_primitives": "src/paperworks/validation_v2/dg05_metric_surface_execution_v2.py",
        "metric_surface": "src/paperworks/validation_v2/dg05_metric_surface_v2.py",
        "metric_oracle": "src/paperworks/validation_v2/dg05_metric_surface_oracle_v2.py",
        "terminal_chain": "src/paperworks/validation_v2/dg05_v11r1_terminal_chain.py",
        "legacy_v11_route": "src/paperworks/validation_v2/dg05_production_chain_v11.py",
        "legacy_v11_custodian": "src/paperworks/validation_v2/dg05_label_custodian_v3.py",
        "metric_contract": "src/paperworks/validation_v2/metric_contract_v1.py",
    }
    return {name: ROOT / path for name, path in relative.items()}


def _write(path: Path, document: dict) -> None:
    if path.exists():
        raise RuntimeError("V11R2R1_ARTIFACT_NAMESPACE_REUSE_REJECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(document) + b"\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--legacy-v10-release", type=Path, required=True)
    parser.add_argument("--predecessor-v4-manifest", type=Path, required=True)
    parser.add_argument("--predecessor-v4-closure", type=Path, required=True)
    parser.add_argument("--historical-v1-manifest", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError("V11R2R1_ARTIFACT_NAMESPACE_REUSE_REJECTED")
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    roots = {
        "legacy_v10_release_hash": load_self_hashed(args.legacy_v10_release, "dg05_production_release_manifest_v2")["self_hash"],
        "predecessor_v4_manifest_hash": load_self_hashed(args.predecessor_v4_manifest, "dg05_production_release_manifest_v1")["self_hash"],
        "predecessor_v4_closure_hash": load_self_hashed(args.predecessor_v4_closure, "dg05_executable_closure_authority_v4")["self_hash"],
        "historical_v1_manifest_hash": load_self_hashed(args.historical_v1_manifest, "dg05_executable_authority_manifest_v1")["self_hash"],
    }
    paths = _paths()
    rows = [{"logical_name": name, "relative_path": path.relative_to(ROOT).as_posix(),
             "byte_hash": __import__("paperworks.validation_v2.dg05_production_chain_v11", fromlist=["file_hash"]).file_hash(path)}
            for name, path in sorted(paths.items())]
    binding = build_execution_binding_v11r2r1(
        repository_root=ROOT, implementation_source_commit=source_commit,
        implementation_authorities=rows, authority_hashes={**roots, "release_engineering": "0" * 64},
        predecessor_release_hash="440ee8aaad1790369f4f5012e43d7483e25b146c694e1446b0c1f42777d91897",
        predecessor_closure_hash="1e782da29b1756f57b8e4341bb40e92f1a1a8a4192d3c004425f36dcf8e33fa1",
        predecessor_execution_binding_hash="52ac10321b2db865f9630d1da659aa336ac94e908ed19510f4d96d7423770224",
    )
    manifest = build_manifest(repository_root=ROOT, source_commit=source_commit,
                              implementation_paths=paths, execution_binding_hash=binding["self_hash"])
    # Candidate authority hashes add the required predecessor bindings while
    # retaining the frozen scientific roots from its gate.
    manifest = {**manifest, "authority_hashes": {**manifest["authority_hashes"], **roots}}
    from paperworks.validation_v2.dg05_production_chain_v11 import self_hashed
    manifest = self_hashed({key: value for key, value in manifest.items() if key != "self_hash"})
    # Rebuild the binding with the exact candidate authority census, then the
    # candidate with the resulting binding.  This is a one-way Phase-A link.
    binding = build_execution_binding_v11r2r1(
        repository_root=ROOT, implementation_source_commit=source_commit,
        implementation_authorities=rows, authority_hashes=manifest["authority_hashes"],
        predecessor_release_hash=manifest["predecessor_release_hash"],
        predecessor_closure_hash=manifest["predecessor_closure_hash"],
        predecessor_execution_binding_hash=manifest["predecessor_execution_binding_hash"],
    )
    manifest = build_manifest(repository_root=ROOT, source_commit=source_commit,
                              implementation_paths=paths, execution_binding_hash=binding["self_hash"])
    manifest = self_hashed({key: value for key, value in {**manifest, "authority_hashes": {**manifest["authority_hashes"], **roots}}.items() if key != "self_hash"})
    _write(args.output / "V11R2R1_EXECUTION_BINDING_MANIFEST.json", binding)
    _write(args.output / "DG05_EXECUTABLE_V11R2R1_FINAL_MANIFEST.json", manifest)
    print(manifest["self_hash"])


if __name__ == "__main__":
    main()
