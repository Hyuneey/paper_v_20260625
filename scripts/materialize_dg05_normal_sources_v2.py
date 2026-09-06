#!/usr/bin/env python3
"""Materialize only the DEC-031-authorized frozen normal source lineage.

This program never discovers or opens attack/test resources.  It restores
already-fitted detector objects and already-frozen Rule runtime assets, then
executes them on the exact preregistered normal authorities.  It does not fit,
calibrate, select, prune, tune, train, or contact a provider.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from freeze_dg05_execution_closure_v1 import (  # noqa: E402
    build_detectors,
    build_dispatch,
    build_rule_runtime_registry,
)
from materialize_hai_2305_normal_v2 import _cache_root as hai23_cache_root  # noqa: E402
from xver_execution_common import cache_root as xver_cache_root, load_projection  # noqa: E402

from paperworks.data.hai_normal_materialization_v2 import canonical_hash  # noqa: E402
from paperworks.data.hai_xver_normal_v1 import sha256_file  # noqa: E402
from paperworks.validation_v2.dg05_execution_closure_v1 import (  # noqa: E402
    DG05ExecutableAuthorityManifestV1,
    DG05ProductionExecutorV1,
    PrivateDetectorAssetV1,
    PrivateRuleRuntimeAssetV1,
    fuse_dense_masks_v1,
    file_sha256,
)
from paperworks.validation_v2.dg05_normal_source_v2 import (  # noqa: E402
    build_normal_source_bundle_v2,
    build_normal_source_registry_v2,
    persist_normal_source_bundle_v2,
    replay_normal_source_registry_v2,
)
from paperworks.validation_v2.dg05_dec031_v1 import (  # noqa: E402
    build_physical_timeline_authority_v1,
    require_valid_physical_timeline_v1,
)
from paperworks.validation_v2.dg05_production_chain_v1 import (  # noqa: E402
    canonical_bytes_v1,
    digest_v1,
    self_hashed_v1,
)
from paperworks.validation_v2.dg05_runtime_adapter_v4 import execute_normal_method_v4  # noqa: E402
from paperworks.validation_v2.multipanel_custody_v1 import (  # noqa: E402
    FROZEN_PANEL_ORDER_V2,
    frozen_feature_allowlist_authorities_v2,
)


OUT = ROOT / "research_control_center/validation_v2/dg05_dec031_binding"
DEC031 = OUT / "DEC031_BINDING_AUTHORITY_V1.json"
PRE = ROOT / "research_control_center/validation_v2/multipanel_pre_dg05"
EXEC = ROOT / "research_control_center/validation_v2/dg05_exec_closure"
HISTORICAL_EXECUTOR = ROOT / "src/paperworks/validation_v2/dg05_execution_closure_v1.py"
PUBLIC_OUTPUT_NAMES = (
    "NORMAL_SOURCE_DISCOVERY_CENSUS_V1.json",
    "NORMAL_RUNTIME_PROJECTION_AUTHORITIES_V1.json",
    "NORMAL_BURDEN_SOURCE_REGISTRY_V2.json",
    "NORMAL_BURDEN_HISTORICAL_COMPARISON_V1.json",
    "NORMAL_SOURCE_CLOSURE_RECEIPT_V1.json",
)


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _vault_root() -> Path:
    common = Path(subprocess.check_output(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=ROOT, text=True,
    ).strip()).resolve()
    value = common.parent.parent / "paper_v_20260625_private_vault"
    if not value.is_dir() or value.is_symlink() or value.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("APPROVED_PRIVATE_VAULT_REQUIRED")
    return value


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _publish(path: Path, value: dict[str, Any]) -> str:
    payload = canonical_bytes_v1(value) + b"\n"
    if path.exists() or path.is_symlink():
        raise RuntimeError(f"APPEND_ONLY_PUBLIC_CONFLICT:{path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    with temporary.open("xb") as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    except FileExistsError as exc:
        raise RuntimeError(f"APPEND_ONLY_PUBLIC_CONFLICT:{path.name}") from exc
    finally:
        if temporary.exists():
            temporary.unlink()
    if path.read_bytes() != payload:
        raise RuntimeError("PUBLIC_REOPEN_MISMATCH")
    return sha256(payload).hexdigest()


def _require_unused_public_namespace() -> None:
    conflicts = [name for name in PUBLIC_OUTPUT_NAMES if (OUT / name).exists() or (OUT / name).is_symlink()]
    if conflicts:
        raise RuntimeError("APPEND_ONLY_PUBLIC_NAMESPACE_CONFLICT:" + ",".join(conflicts))


def _historical_detector_replay(replay: dict[str, Any]) -> dict[str, Any]:
    """Compare exact external detector/data/metric authorities before release.

    The older documents contain source-derived alarm counts for the identical
    external detector and normal-audit authorities.  Rule and Fusion summaries
    are deliberately excluded: their historical guard aggregates are not the
    retained-only runtime source bundles prospectively required by DEC-031.
    """
    expected: dict[tuple[str, str, str], tuple[int, int, int]] = {}
    for panel_id, name in (
        (FROZEN_PANEL_ORDER_V2[1], "HAI22_DETECTOR_AUTHORITY_V1.json"),
        (FROZEN_PANEL_ORDER_V2[2], "HAI21_DETECTOR_AUTHORITY_V1.json"),
    ):
        authority = _read(PRE / name)
        for component, methods in authority["normal_audits"].items():
            file_id = "HAI21_TRAIN3_BLOCK_B" if component == "train3_block_b" else f"HAI22_{component.upper()}"
            for legacy_id, row in methods.items():
                method_id = "M0_PCA_SPE" if legacy_id == "PCA" else "ISOLATION_FOREST"
                expected[(panel_id, method_id, file_id)] = (
                    row["alarm_seconds"], row["alarm_episodes"], row["row_count"]
                )
    observed = {
        (component["panel_id"], component["method_id"], component["file_id"]): (
            component["false_seconds"], component["false_episodes"], component["exposure_seconds"]
        )
        for method in replay["methods"]
        for component in method["components"]
    }
    rows = []
    for identity, historical in sorted(expected.items()):
        prospective = observed.get(identity)
        status = "EXACT_REPLAY_PASS" if prospective == historical else "NORMAL_BURDEN_REPLAY_MISMATCH"
        rows.append({
            "panel_id": identity[0], "method_id": identity[1], "file_id": identity[2],
            "historical": {"false_seconds": historical[0], "false_episodes": historical[1], "exposure_seconds": historical[2]},
            "prospective": None if prospective is None else {
                "false_seconds": prospective[0], "false_episodes": prospective[1], "exposure_seconds": prospective[2]
            },
            "status": status,
        })
    if any(row["status"] != "EXACT_REPLAY_PASS" for row in rows):
        raise RuntimeError("NORMAL_BURDEN_REPLAY_MISMATCH")
    exact_rule_expectations = {
        (FROZEN_PANEL_ORDER_V2[1], "M1_T0_RULE_ONLY", "HAI22_TRAIN5"): (102, 102, 237600),
        (FROZEN_PANEL_ORDER_V2[1], "M1_T0_RULE_ONLY", "HAI22_TRAIN6"): (91, 90, 259200),
        (FROZEN_PANEL_ORDER_V2[1], "M2_T2_RULE_ONLY", "HAI22_TRAIN5"): (231, 231, 237600),
        (FROZEN_PANEL_ORDER_V2[1], "M2_T2_RULE_ONLY", "HAI22_TRAIN6"): (237, 236, 259200),
    }
    rule_rows = []
    for identity, historical in sorted(exact_rule_expectations.items()):
        prospective = observed.get(identity)
        status = "EXACT_REPLAY_PASS" if prospective == historical else "NORMAL_BURDEN_REPLAY_MISMATCH"
        rule_rows.append({
            "panel_id": identity[0], "method_id": identity[1], "file_id": identity[2],
            "historical": {"false_seconds": historical[0], "false_episodes": historical[1], "exposure_seconds": historical[2]},
            "prospective": None if prospective is None else {
                "false_seconds": prospective[0], "false_episodes": prospective[1], "exposure_seconds": prospective[2]
            },
            "status": status,
        })
    if any(row["status"] != "EXACT_REPLAY_PASS" for row in rule_rows):
        raise RuntimeError("NORMAL_BURDEN_REPLAY_MISMATCH")
    return self_hashed_v1({
        "schema": "normal_burden_historical_comparison_v1",
        "status": "PASS",
        "exact_detector_component_replays": rows,
        "exact_hai22_retained_rule_component_replays": rule_rows,
        "hai23_rule_history_classification": "NOT_COMPARABLE_ORIGINAL_ARM_GROUP_CONTEXT",
        "hai21_rule_history_classification": "NOT_COMPARABLE_CONTEXT_DIFFERENCE",
        "fusion_history_classification": "NO_IDENTICAL_PERSISTED_SOURCE_COMPARATOR",
        "historical_values_overwritten": False,
    })


def _discover_prior_registries(vault: Path, staging_root: Path, source_commit: str, dispatch: Any) -> dict[str, Any]:
    """Perform NS-A before any scoring or private source materialization."""
    public_matches = sorted(
        path for path in (ROOT / "research_control_center/validation_v2").rglob("NORMAL_BURDEN_SOURCE_REGISTRY*.json")
        if path.resolve() != (OUT / "NORMAL_BURDEN_SOURCE_REGISTRY_V2.json").resolve()
    )
    private_matches = sorted(vault.rglob("NORMAL_BURDEN_SOURCE_REGISTRY*.json"))
    if public_matches or private_matches:
        raise RuntimeError("EXISTING_NORMAL_SOURCE_REPLAY_REQUIRED")
    components = [{
        "panel_id": entry.panel_id,
        "method_id": entry.method_id,
        "status": "FOUND_PARTIAL",
        "dispatch_entry_hash": digest_v1(entry.document()),
        "complete_source_bundle_found": False,
    } for entry in sorted(dispatch.entries, key=lambda entry: (entry.panel_id, entry.method_id))]
    if len(components) != 23:
        raise RuntimeError("NS_A_REQUIRED_METHOD_CENSUS_MISMATCH")
    discovery = self_hashed_v1({
        "schema": "normal_source_discovery_census_v1", "stage": "NS_A",
        "required_method_bundles": 23, "found_complete": 0,
        "found_partial": 23, "not_found": 0, "authority_mismatch": 0,
        "prior_source_registries_found": 0,
        "component_findings": components,
        "scoped_materialization_required": True,
        "private_paths_published": False, "attack_test_accesses": 0,
        "normal_label_values_parsed": 0, "source_commit": source_commit,
    })
    _publish(staging_root / "NORMAL_SOURCE_DISCOVERY_CENSUS_PRIVATE_V1.json", discovery)
    return discovery


def _manifest_from_document(value: dict[str, Any]) -> DG05ExecutableAuthorityManifestV1:
    manifest = DG05ExecutableAuthorityManifestV1(
        tuple(sorted(value["scientific_authorities"].items())),
        value["detector_registry_hash"], value["dispatch_registry_hash"],
        value["rule_runtime_registry_hash"], tuple(value["rule_portfolio_authority_hashes"]),
        value["full_process_scope_hash"], value["p1_custodian_v3_hash"],
        tuple(sorted(value["implementation_hashes"].items())),
        value["nested_authority_replay_bundle_hash"], value["source_commit"],
    )
    manifest.validate()
    if manifest.document() != value:
        raise RuntimeError("HISTORICAL_EXECUTABLE_MANIFEST_REPLAY_MISMATCH")
    return manifest


def _hai23_detector_path(vault: Path) -> Path:
    binding = _read(PRE / "HAI23_DETECTOR_PRIVATE_HASH_BINDING_V1.json")
    snapshot_path = vault / "gdn-front-exp04-001" / "snapshots" / f"{binding['private_manifest_hash']}.json"
    snapshot = _read(snapshot_path)
    if snapshot.get("self_hash") != canonical_hash({k: v for k, v in snapshot.items() if k != "self_hash"}):
        raise RuntimeError("HAI23_PRIVATE_SNAPSHOT_REPLAY_FAILED")
    matches = [row for row in snapshot["records"] if row["artifact_id"] == binding["private_model_artifact_id"]]
    if len(matches) != 1:
        raise RuntimeError("HAI23_PRIVATE_MODEL_CENSUS_FAILED")
    path = Path(matches[0]["private_source"])
    if file_sha256(path) != binding["private_model_bytes_hash"] or matches[0]["content_hash"] != binding["private_model_bytes_hash"]:
        raise RuntimeError("HAI23_PRIVATE_MODEL_BYTES_MISMATCH")
    return path


def _detector_assets(vault: Path, detector_registry: Any) -> tuple[PrivateDetectorAssetV1, ...]:
    ext = xver_cache_root() / "xver_execution_v1" / "multipanel_pre_dg05_v1"
    paths = {
        (FROZEN_PANEL_ORDER_V2[0], "PCA_SPE"): _hai23_detector_path(vault),
        (FROZEN_PANEL_ORDER_V2[0], "ISOLATION_FOREST"): _hai23_detector_path(vault),
        (FROZEN_PANEL_ORDER_V2[1], "PCA_SPE"): ext / "HAI22_PCA.pkl",
        (FROZEN_PANEL_ORDER_V2[1], "ISOLATION_FOREST"): ext / "HAI22_IF.pkl",
        (FROZEN_PANEL_ORDER_V2[2], "PCA_SPE"): ext / "HAI21_PCA.pkl",
        (FROZEN_PANEL_ORDER_V2[2], "ISOLATION_FOREST"): ext / "HAI21_IF.pkl",
    }
    output = []
    for panel_id, detector_id in sorted(paths):
        authority = detector_registry.lookup(panel_id, detector_id)
        path = paths[(panel_id, detector_id)]
        output.append(PrivateDetectorAssetV1(
            panel_id, detector_id, authority.private_container_format,
            path, authority.private_container_hash,
        ))
    return tuple(output)


def _rule_assets(sources: dict[tuple[str, str], tuple[Path, Path, Path]]) -> tuple[PrivateRuleRuntimeAssetV1, ...]:
    return tuple(
        PrivateRuleRuntimeAssetV1(panel, role, paths[0], paths[1], paths[2])
        for (panel, role), paths in sorted(sources.items())
    )


def _load_hai23_normal(features: tuple[str, ...]) -> tuple[np.ndarray, list[str], dict[str, Any]]:
    root = hai23_cache_root(ROOT)
    public_receipt = _read(ROOT / "research_control_center/validation_v2/receipts/HAI_NORMAL_ONLY_MATERIALIZATION_RECEIPT_V2.json")
    if public_receipt.get("self_hash") != canonical_hash(public_receipt):
        raise RuntimeError("HAI23_PUBLIC_NORMAL_RECEIPT_REPLAY_FAILED")
    manifest_path = root / ".validation_v2_normal_materialization_manifest.json"
    manifest = _read(manifest_path)
    if (
        manifest.get("self_hash") != canonical_hash(manifest)
        or manifest.get("self_hash") != public_receipt.get("private_manifest_hash")
    ):
        raise RuntimeError("HAI23_NORMAL_MANIFEST_REPLAY_FAILED")
    matches = [row for row in manifest["files"] if row["symbolic_id"] == "HAI_TRAIN4"]
    if len(matches) != 1:
        raise RuntimeError("HAI23_TRAIN4_AUTHORITY_REQUIRED")
    row = matches[0]; path = Path(row["absolute_path"])
    public_row = next(item for item in public_receipt["normal_splits"] if item["symbolic_id"] == "HAI_TRAIN4")
    if (
        path.is_symlink()
        or not path.resolve().is_relative_to(root.resolve())
        or row["sha256"] != public_row["sha256_git_lfs_oid"]
        or sha256_file(path) != row["sha256"]
    ):
        raise RuntimeError("HAI23_TRAIN4_BYTE_MISMATCH")
    requested = ["timestamp", *features]
    frame = pd.read_csv(path, usecols=requested, dtype={"timestamp": "string"})
    if tuple(frame.columns) != tuple(requested):
        frame = frame.loc[:, requested]
    timestamps = [str(value) for value in frame["timestamp"].tolist()]
    matrix = frame.loc[:, list(features)].to_numpy(dtype=np.float64, copy=True)
    if (
        matrix.shape != (public_row["row_count"], len(features))
        or len(timestamps) != public_row["row_count"]
        or not np.isfinite(matrix).all()
        or sha256_file(path) != row["sha256"]
    ):
        raise RuntimeError("HAI23_POSITIVE_ALLOWLIST_PROJECTION_INVALID")
    return matrix, timestamps, {
        "source_hash": row["sha256"], "file_id": "HAI_TRAIN4",
        "component_role": "TRAIN4_GUARD_CONDITIONED_NORMAL",
        "authority_class": "GUARD_CONDITIONED_NORMAL",
        "label_columns_present": False,
    }


def _load_external_normal(version: str, split: str, *, block: tuple[int, int] | None = None) -> tuple[np.ndarray, list[str], tuple[str, ...], dict[str, Any]]:
    matrix, order, row = load_projection(version, split)
    path = xver_cache_root() / "projections_v2" / f"HAI{version[:2]}_{split.upper()}.csv"
    timestamp_name = row["timestamp_identity"]
    frame = pd.read_csv(path, usecols=[timestamp_name], dtype={timestamp_name: "string"})
    timestamps = [str(value) for value in frame[timestamp_name].tolist()]
    if block is not None:
        start, end = block
        if version != "21.03" or split != "train3" or (start, end) != (239430, 478801) or end > len(matrix):
            raise RuntimeError("UNAPPROVED_EXTERNAL_NORMAL_BLOCK")
        matrix = matrix[start:end]
        timestamps = timestamps[start:end]
        projection_source_hash = sha256((row["projection_hash"] + f":{start}:{end}").encode()).hexdigest()
    else:
        projection_source_hash = row["projection_hash"]
    if len(timestamps) != len(matrix) or sha256_file(path) != row["projection_hash"]:
        raise RuntimeError("EXTERNAL_TIMESTAMP_MATRIX_CENSUS_MISMATCH")
    return matrix, timestamps, tuple(order), {
        "source_hash": row["projection_hash"],
        "projection_source_hash": projection_source_hash,
        "file_id": f"HAI{version[:2]}_{split.upper()}" if block is None else "HAI21_TRAIN3_BLOCK_B",
        "component_role": split.upper() if block is None else "TRAIN3_BLOCK_B_GUARD_CONDITIONED_NORMAL",
        "authority_class": "POST_FREEZE_NORMAL_AUDIT" if version == "22.04" else "GUARD_CONDITIONED_NORMAL",
        "label_columns_present": False,
    }


def _projection_authority(*, panel_id: str, dataset_version: str, feature_order: tuple[str, ...],
                          matrix: np.ndarray, timestamps: list[str], source: dict[str, Any], source_commit: str) -> dict[str, Any]:
    matrix_hash = sha256(np.ascontiguousarray(matrix, dtype="<f8").tobytes()).hexdigest()
    return self_hashed_v1({
        "schema": "normal_runtime_projection_authority_v4",
        "panel_id": panel_id, "dataset_version": dataset_version,
        "file_id": source["file_id"], "component_role": source["component_role"],
        "authority_class": source["authority_class"],
        "source_byte_hash": source["source_hash"],
        "feature_order_hash": digest_v1(list(feature_order)),
        "feature_count": len(feature_order), "row_count": len(timestamps),
        "timestamp_vector_hash": digest_v1(timestamps), "matrix_content_hash": matrix_hash,
        "projection_content_hash": digest_v1({"timestamps": digest_v1(timestamps), "matrix": matrix_hash,
                                               "features": digest_v1(list(feature_order))}),
        "projection_policy": "TIMESTAMP_PLUS_APPROVED_FEATURE_ALLOWLIST",
        "label_columns_present": source["label_columns_present"],
        "label_values_parsed": 0, "label_values_inspected": 0,
        "label_values_validated": 0, "label_values_used": 0,
        "source_commit": source_commit,
    })


def _fuse(detector: tuple[bool, ...], rule: tuple[bool, ...], trace: dict[str, Any]) -> tuple[tuple[bool, ...], dict[str, Any]]:
    output = fuse_dense_masks_v1(detector, trace["fail_sources_by_row"])
    if len(output) != len(rule):
        raise RuntimeError("FUSION_COMPONENT_LENGTH_MISMATCH")
    return output, {
        **trace,
        "rule_component_alarm_rows": trace["rule_alarm_rows"],
        "fusion_base_alarm_rows": [index for index, value in enumerate(detector) if value],
        "fusion_output_alarm_rows": [index for index, value in enumerate(output) if value],
        "base_preservation": all((not base) or value for base, value in zip(detector, output, strict=True)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--seal-failed-attempt", action="store_true")
    args = parser.parse_args()
    if args.seal_failed_attempt:
        vault = _vault_root()
        staging = vault / "dg05-dec031-normal-source-001.part"
        failed = vault / "dg05-dec031-normal-source-001.attempt-001-failed"
        if (
            not staging.is_dir() or staging.is_symlink() or failed.exists()
            or sorted(path.relative_to(staging).as_posix() for path in staging.rglob("*"))
               != ["NORMAL_SOURCE_DISCOVERY_CENSUS_PRIVATE_V1.json"]
        ):
            raise RuntimeError("EXACT_FAILED_STAGING_ATTEMPT_REQUIRED")
        receipt = self_hashed_v1({
            "schema": "normal_source_materialization_failed_attempt_v1",
            "attempt": 1, "status": "ENGINEERING_FAILURE_BEFORE_SCIENTIFIC_SCORING",
            "source_commit": "7243f4d012ba712518d422864cf00ffa55891475",
            "failure_code": "HAI23_PRIVATE_MANIFEST_ROW_COUNT_FIELD_ABSENT",
            "scientific_scorer_invocations": 0, "attack_test_accesses": 0,
            "label_scenario_accesses": 0, "provider_calls": 0,
        })
        _publish(staging / "FAILED_ATTEMPT_RECEIPT_V1.json", receipt)
        os.rename(staging, failed)
        print(json.dumps({"status": "FAILED_ATTEMPT_PRESERVED", "receipt_hash": receipt["self_hash"]}, sort_keys=True))
        return
    if not args.execute:
        raise SystemExit("--execute required")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise RuntimeError("COMMITTED_CLEAN_EXECUTION_SOURCE_REQUIRED")
    source_commit = _head()
    decision = _read(DEC031)
    if decision["self_hash"] != digest_v1({k: v for k, v in decision.items() if k != "self_hash"}) or decision["dg05_real_access_authorized"]:
        raise RuntimeError("DEC031_PREACCESS_BINDING_REQUIRED")

    _require_unused_public_namespace()
    vault = _vault_root()
    private_root = vault / "dg05-dec031-normal-source-001"
    staging_root = vault / "dg05-dec031-normal-source-001.part"
    if private_root.exists() or private_root.is_symlink():
        raise RuntimeError("APPEND_ONLY_PRIVATE_TASK_NAMESPACE_CONFLICT")
    if staging_root.exists() or staging_root.is_symlink():
        raise RuntimeError("STALE_PRIVATE_TASK_STAGING_NAMESPACE")
    staging_root.mkdir(parents=True)

    detectors = build_detectors()
    rules, rule_sources = build_rule_runtime_registry()
    dispatch = build_dispatch(detectors, rules)
    manifest_doc = _read(EXEC / "DG05_EXECUTABLE_AUTHORITY_MANIFEST_V1.json")
    manifest = _manifest_from_document(manifest_doc)
    executor = DG05ProductionExecutorV1(
        executable_manifest_hash=manifest_doc["self_hash"],
        detector_registry=detectors, dispatch_registry=dispatch,
        rule_runtime_registry=rules, authority_mode="PRODUCTION",
        detector_assets=_detector_assets(vault, detectors),
        rule_assets=_rule_assets(rule_sources),
        fusion_implementation_hash=file_sha256(HISTORICAL_EXECUTOR),
        adapter_implementation_hash=file_sha256(HISTORICAL_EXECUTOR),
        repository_root=ROOT, executable_manifest=manifest,
    )
    executor.validate()
    discovery = _discover_prior_registries(vault, staging_root, source_commit, dispatch)

    allowlists = frozen_feature_allowlist_authorities_v2()
    panel_specs: list[tuple[str, str, np.ndarray, list[str], tuple[str, ...], dict[str, Any]]] = []
    h23 = FROZEN_PANEL_ORDER_V2[0]
    h23_features = tuple(allowlists[h23].feature_ids)
    matrix, timestamps, source = _load_hai23_normal(h23_features)
    panel_specs.append((h23, "23.05", matrix, timestamps, h23_features, source))
    for split in ("train5", "train6"):
        matrix, timestamps, order, source = _load_external_normal("22.04", split)
        panel_specs.append((FROZEN_PANEL_ORDER_V2[1], "22.04", matrix, timestamps, order, source))
    matrix, timestamps, order, source = _load_external_normal("21.03", "train3", block=(239430, 478801))
    panel_specs.append((FROZEN_PANEL_ORDER_V2[2], "21.03", matrix, timestamps, order, source))

    projection_authorities = []
    receipts = []
    metadata = []
    expected_roster = []
    private_records = []
    component_paths: dict[str, Path] = {}
    for panel_id, version, matrix, timestamps, feature_order, source in panel_specs:
        projection = _projection_authority(panel_id=panel_id, dataset_version=version,
            feature_order=feature_order, matrix=matrix, timestamps=timestamps,
            source=source, source_commit=source_commit)
        timeline_gate = build_physical_timeline_authority_v1(
            panel_id=panel_id, file_id=source["file_id"], timestamps=timestamps,
            physical_file_authority_hash=source["source_hash"],
            projection_authority_hash=projection["self_hash"], source_commit=source_commit,
        )
        # DEC-031 requires the timeline gate before any scientific scorer.
        require_valid_physical_timeline_v1(timeline_gate)
        projection_authorities.append(projection)
        for bound_entry in sorted(
            (entry for entry in dispatch.entries if entry.panel_id == panel_id),
            key=lambda entry: entry.method_id,
        ):
            expected_roster.append({
                "component_id": digest_v1([panel_id, source["file_id"], bound_entry.method_id, projection["self_hash"]]),
                "panel_id": panel_id, "dataset_version": version,
                "method_id": bound_entry.method_id, "file_id": source["file_id"],
                "component_role": source["component_role"],
                "authority_class": source["authority_class"],
            })
        base: dict[str, tuple[tuple[bool, ...], dict[str, Any] | None]] = {}
        for method_id in ("M0_PCA_SPE", "M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "ISOLATION_FOREST"):
            entry = dispatch.lookup(panel_id, method_id)
            alarms, trace = execute_normal_method_v4(executor=executor, entry=entry,
                feature_order=feature_order, matrix=matrix, file_id=source["file_id"],
                projection_hash=projection["projection_content_hash"], timestamps=timestamps)
            base[method_id] = (alarms, None if trace is None else dict(trace))
        if panel_id == h23:
            entry = dispatch.lookup(panel_id, "V2A_RULE_ONLY_REFERENCE")
            alarms, trace = execute_normal_method_v4(executor=executor, entry=entry,
                feature_order=feature_order, matrix=matrix, file_id=source["file_id"],
                projection_hash=projection["projection_content_hash"], timestamps=timestamps)
            base["V2A_RULE_ONLY_REFERENCE"] = (alarms, dict(trace or {}))
        outputs = dict(base)
        fusion_map = {
            "M3_PCA_PLUS_T0": ("M0_PCA_SPE", "M1_T0_RULE_ONLY"),
            "M4_PCA_PLUS_T2": ("M0_PCA_SPE", "M2_T2_RULE_ONLY"),
            "ISOLATION_FOREST_PLUS_T2": ("ISOLATION_FOREST", "M2_T2_RULE_ONLY"),
        }
        if panel_id == h23:
            fusion_map["HISTORICAL_PCA_PLUS_V2A_CONTINUITY"] = ("M0_PCA_SPE", "V2A_RULE_ONLY_REFERENCE")
        for method_id, (detector_id, rule_id) in fusion_map.items():
            outputs[method_id] = _fuse(base[detector_id][0], base[rule_id][0], dict(base[rule_id][1] or {}))
        expected = {entry.method_id for entry in dispatch.entries if entry.panel_id == panel_id}
        if set(outputs) != expected:
            raise RuntimeError("NORMAL_METHOD_CENSUS_MISMATCH")
        for method_id in sorted(outputs):
            alarms, trace = outputs[method_id]
            entry = dispatch.lookup(panel_id, method_id)
            component_id = digest_v1([panel_id, source["file_id"], method_id, projection["self_hash"]])
            configured = None if trace is None else trace["configured_rule_sources"]
            bundle = build_normal_source_bundle_v2(
                component_id=component_id, panel_id=panel_id, dataset_version=version,
                method_id=method_id, file_id=source["file_id"],
                component_role=source["component_role"], authority_class=source["authority_class"],
                method_authority_hash=digest_v1(entry.document()),
                physical_file_authority_hash=source["source_hash"],
                projection_authority_hash=projection["self_hash"],
                timestamps=timestamps, alarms=alarms,
                configured_rule_sources=configured, runtime_trace=trace,
                source_commit=source_commit,
            )
            path = staging_root / "bundles" / f"{component_id}.json"
            receipt = persist_normal_source_bundle_v2(path, bundle)
            receipts.append(receipt); component_paths[component_id] = path
            metadata.append({
                "component_id": component_id, "panel_id": panel_id,
                "dataset_version": version, "method_id": method_id,
                "file_id": source["file_id"], "component_role": source["component_role"],
                "authority_class": source["authority_class"],
                "method_authority_hash": bundle["method_authority_hash"],
                "physical_file_authority_hash": source["source_hash"],
                "projection_authority_hash": projection["self_hash"],
                "timeline_authority_hash": bundle["timeline_authority"]["self_hash"],
            })
            final_path = private_root / "bundles" / f"{component_id}.json"
            private_records.append({"component_id": component_id, "path": str(final_path.resolve()),
                                    "artifact_byte_hash": receipt["artifact_byte_hash"],
                                    "document_self_hash": receipt["document_self_hash"]})

    registry = build_normal_source_registry_v2(component_receipts=receipts,
        component_metadata=metadata, dec031_binding_hash=decision["self_hash"],
        required_components=expected_roster, source_commit=source_commit)
    replay = replay_normal_source_registry_v2(registry=registry, component_paths=component_paths,
                                               expected_dec031_binding_hash=decision["self_hash"])
    historical_comparison = _historical_detector_replay(replay)
    private_manifest = self_hashed_v1({
        "schema": "dg05_normal_source_private_manifest_v1", "status": "COMPLETE",
        "registry_hash": registry["self_hash"], "records": private_records,
        "record_count": len(private_records), "backup_status": "SINGLE_COPY_LOCAL_ONLY",
        "attack_test_accesses": 0, "label_scenario_accesses": 0,
        "excluded_normal_label_values_parsed": 0, "source_commit": source_commit,
    })
    _publish(staging_root / "TASK_PRIVATE_VAULT_MANIFEST_V1.json", private_manifest)
    _publish(staging_root / "NORMAL_BURDEN_REPLAY_PRIVATE_V2.json", replay)
    os.rename(staging_root, private_root)
    final_component_paths = {
        component_id: private_root / "bundles" / f"{component_id}.json"
        for component_id in component_paths
    }
    restored_replay = replay_normal_source_registry_v2(
        registry=registry,
        component_paths=final_component_paths,
        expected_dec031_binding_hash=decision["self_hash"],
    )
    if restored_replay != replay:
        raise RuntimeError("PRIVATE_RESTORE_REPLAY_MISMATCH")
    projection_bundle = self_hashed_v1({
        "schema": "normal_runtime_projection_authority_bundle_v1",
        "authorities": projection_authorities,
        "authority_count": len(projection_authorities),
        "positive_allowlist_only": True, "normal_label_values_parsed": 0,
        "source_commit": source_commit,
    })
    closure = self_hashed_v1({
        "schema": "normal_source_closure_receipt_v1", "status": "PASS",
        "discovery_hash": discovery["self_hash"], "projection_bundle_hash": projection_bundle["self_hash"],
        "registry_hash": registry["self_hash"], "independent_replay_hash": replay["self_hash"],
        "historical_comparison_hash": historical_comparison["self_hash"],
        "method_bundle_count": 23, "physical_component_count": len(private_records),
        "private_manifest_hash": private_manifest["self_hash"],
        "private_paths_published": False, "new_fitting": 0, "provider_calls": 0,
        "gdn_runs": 0, "attack_test_accesses": 0, "label_scenario_accesses": 0,
        "excluded_normal_label_values_parsed": 0, "source_commit": source_commit,
    })
    _publish(OUT / "NORMAL_SOURCE_DISCOVERY_CENSUS_V1.json", discovery)
    _publish(OUT / "NORMAL_RUNTIME_PROJECTION_AUTHORITIES_V1.json", projection_bundle)
    _publish(OUT / "NORMAL_BURDEN_SOURCE_REGISTRY_V2.json", registry)
    _publish(OUT / "NORMAL_BURDEN_HISTORICAL_COMPARISON_V1.json", historical_comparison)
    _publish(OUT / "NORMAL_SOURCE_CLOSURE_RECEIPT_V1.json", closure)
    print(json.dumps({"status": "PASS", "registry_hash": registry["self_hash"],
                      "replay_hash": replay["self_hash"], "components": len(private_records),
                      "method_bundles": 23}, sort_keys=True))


if __name__ == "__main__":
    main()
