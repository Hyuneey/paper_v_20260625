"""Non-interactive official HAI 23.05 provenance and custody audit."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from paperworks.data.contracts_v2 import CreationMetadataV2  # noqa: E402
from paperworks.data.hai_provenance_v1 import (  # noqa: E402
    HAIGraphInventoryRecordV1,
    HAIProvenanceAuditResultV1,
    HAIProvenanceError,
    HAIReferenceFileRecordV1,
    HAIRepositorySnapshotV1,
    assert_external_audit_roots,
    assert_public_artifact_has_no_sensitive_content,
    audit_csv_structure,
    audit_label_custody_pair,
    build_hai_dataset_manifest_v2,
    canonical_self_hash,
    git_blob_sha,
    git_blob_text,
    inventory_graph_file,
    inventory_pdf_reference,
    run_git,
    streaming_sha256,
    validate_lfs_materialization,
    write_public_json,
    _read_header,
)


CONFIG_PATH = REPOSITORY_ROOT / "configs/data/hai_2305_official_provenance.json"
REPORT_ROOT = REPOSITORY_ROOT / "docs/task_reports"


def _load_config(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("config_hash") != canonical_self_hash(document, "config_hash"):
        raise HAIProvenanceError("configuration self-hash mismatch")
    return document


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def _git_check(repository: Path, *arguments: str) -> bool:
    return _run(["git", *arguments], cwd=repository).returncode == 0


def _write_report(path: Path, document: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(document)
    payload["report_hash"] = canonical_self_hash(payload, "report_hash")
    write_public_json(path, payload)
    return payload


def _citation_hash(readme: str) -> str:
    lower = readme.lower()
    start = lower.find("citation")
    section = readme[start:] if start >= 0 else readme
    return sha256(section.encode("utf-8")).hexdigest()


def _readme_warning_codes(readme: str) -> tuple[str, ...]:
    lower = readme.lower()
    cross_label_pattern = bool(
        re.search(
            r"\[hai\s*23\.05\]\([^)]*haiend-23\.05|"
            r"\[haiend\s*23\.05\]\([^)]*hai-23\.05",
            lower,
        )
    )
    return (
        ("README_HAI_HAIEND_LINK_LABEL_AMBIGUITY",)
        if cross_label_pattern
        else ()
    )


def _normalize_git_remote(value: str) -> str:
    return value[:-4] if value.endswith(".git") else value


def _readme_supports_normal_train_status(readme: str) -> bool:
    lower = " ".join(readme.lower().split())
    return bool(
        re.search(r"(?:train|training).{0,180}normal", lower)
        or re.search(r"normal.{0,180}(?:train|training)", lower)
    )


def _repository_snapshot(
    official_root: Path, config: Mapping[str, Any]
) -> tuple[HAIRepositorySnapshotV1, str, str, str]:
    snapshot_commit = str(config["snapshot_commit"])
    introduction_commit = str(config["introduction_commit"])
    observed_head = run_git(official_root, "rev-parse", "HEAD")
    tree_sha = run_git(official_root, "rev-parse", "HEAD^{tree}")
    origin = run_git(official_root, "remote", "get-url", "origin")
    branch = run_git(official_root, "branch", "--show-current")
    clean = run_git(official_root, "status", "--short") == ""
    git_fsck = _git_check(official_root, "fsck", "--full")
    lfs_version = _run(["git", "lfs", "version"], cwd=official_root)
    lfs_available = lfs_version.returncode == 0
    lfs_fsck = lfs_available and _git_check(official_root, "lfs", "fsck")
    if not _git_check(official_root, "cat-file", "-e", f"{introduction_commit}^{{commit}}"):
        raise HAIProvenanceError("HAI 23.05 introduction commit is unavailable")
    readme_blob = git_blob_sha(official_root, snapshot_commit, "README.md")
    manual_path = str(config["technical_manual_path"])
    manual_blob = git_blob_sha(official_root, snapshot_commit, manual_path)
    readme = git_blob_text(official_root, snapshot_commit, "README.md")
    tree_paths = set(
        run_git(official_root, "ls-tree", "-r", "--name-only", snapshot_commit).splitlines()
    )
    license_present = "LICENSE" in tree_paths
    snapshot = HAIRepositorySnapshotV1(
        repository_url=str(config["official_repository"]),
        snapshot_commit=snapshot_commit,
        introduction_commit=introduction_commit,
        observed_head=observed_head,
        tree_sha=tree_sha,
        observed_origin_url=origin,
        detached_head=(branch == ""),
        checkout_clean=clean,
        git_fsck_passed=git_fsck,
        git_lfs_fsck_passed=lfs_fsck,
        lfs_available=lfs_available,
        readme_blob_sha=readme_blob,
        technical_manual_blob_sha=manual_blob,
        standalone_license_present=license_present,
        license_source="README License section at pinned snapshot",
        license_statement="CC BY-SA 4.0",
        warning_codes=_readme_warning_codes(readme),
    )
    return snapshot, readme, streaming_sha256(official_root / "README.md"), _citation_hash(readme)


def _inventory_references(
    official_root: Path,
    snapshot_commit: str,
    config: Mapping[str, Any],
    readme_sha256: str,
    citation_sha256: str,
) -> tuple[dict[str, Any], HAIReferenceFileRecordV1, tuple[HAIGraphInventoryRecordV1, ...]]:
    manual_relative = str(config["technical_manual_path"])
    manual = inventory_pdf_reference(
        official_root / manual_relative,
        relative_path=manual_relative,
        git_blob_sha=git_blob_sha(official_root, snapshot_commit, manual_relative),
    )
    graph_paths = tuple(
        line
        for line in run_git(
            official_root,
            "ls-tree",
            "-r",
            "--name-only",
            snapshot_commit,
            "--",
            "graph",
        ).splitlines()
        if line
    )
    graphs = tuple(
        inventory_graph_file(
            official_root / relative,
            relative_path=relative,
            git_blob_sha=git_blob_sha(official_root, snapshot_commit, relative),
        )
        for relative in graph_paths
    )
    readme_record = {
        "relative_path": "README.md",
        "git_blob_sha": git_blob_sha(official_root, snapshot_commit, "README.md"),
        "content_sha256": readme_sha256,
        "license_source": "README License section",
        "license_statement": "CC BY-SA 4.0",
        "citation_sha256": citation_sha256,
    }
    return readme_record, manual, graphs


def _markdown_reports(
    *,
    snapshot: HAIRepositorySnapshotV1,
    csv_records: list[Any],
    labels: list[Any],
    graphs: tuple[HAIGraphInventoryRecordV1, ...],
    dataset_manifest_id: str,
    status: str,
) -> dict[Path, str]:
    source = f"""# HAI 23.05 Source Provenance

The official `icsdataset/hai` source is pinned at
`{snapshot.snapshot_commit}`. Git and Git-LFS identity, materialization, file
integrity, and checkout cleanliness were audited. Local absolute paths and raw
data are excluded from this public record.

Status: `{status}`
Dataset manifest: `{dataset_manifest_id}`
"""
    files = "# HAI 23.05 File Inventory\n\n" + "\n".join(
        f"- `{item.relative_path}`: {item.byte_size} bytes, {item.row_count} rows"
        for item in csv_records
    ) + "\n"
    custody = "# HAI 23.05 Label Custody\n\n" + "\n".join(
        f"- `{item.label_relative_path}`: alignment `{item.timestamp_alignment_status}`, "
        f"domain valid `{str(item.label_domain_valid).lower()}`, events `{item.event_record_count}`"
        for item in labels
    ) + "\n\nAttack intervals, targets, descriptions, and positive-point counts are not public.\n"
    references = f"""# HAI 23.05 Reference Inventory

- Technical manual integrity and parse availability were audited.
- Official graph files inventoried: {len(graphs)}.
- Graphs are treated as weak relation references, not causal truth or an RQ1 answer key.
"""
    schema = f"""# HAI 23.05 Schema Audit

Six time-series files were streamed with bounded memory. Ordered headers,
timestamp continuity, row shape, UTF-8 encoding, and the 86-point reconciliation
were checked. Test files received structural inspection only; no feature-value
statistics were calculated.

Status: `{status}`
"""
    return {
        REPOSITORY_ROOT / "docs/v6/HAI_2305_SOURCE_PROVENANCE.md": source,
        REPOSITORY_ROOT / "docs/v6/HAI_2305_FILE_INVENTORY.md": files,
        REPOSITORY_ROOT / "docs/v6/HAI_2305_LABEL_CUSTODY.md": custody,
        REPOSITORY_ROOT / "docs/v6/HAI_2305_REFERENCE_INVENTORY.md": references,
        REPOSITORY_ROOT / "docs/v6/HAI_2305_SCHEMA_AUDIT.md": schema,
    }


def run_audit(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    official_root = args.official_root.resolve()
    private_root = args.private_root.resolve()
    paper_root = args.paper_root.resolve()
    assert_external_audit_roots(
        paper_repository_root=paper_root,
        official_root=official_root,
        private_root=private_root,
    )
    if args.data_root.resolve() != (official_root / config["dataset_directory"]).resolve():
        raise HAIProvenanceError("HAI_DATA_ROOT must equal HAI_OFFICIAL_ROOT/hai-23.05")
    if args.public_output_root.resolve() != REPORT_ROOT.resolve():
        raise HAIProvenanceError("public output root must be docs/task_reports")

    snapshot, readme, readme_sha256, citation_sha256 = _repository_snapshot(
        official_root, config
    )
    snapshot_gate = (
        snapshot.observed_head == config["snapshot_commit"]
        and _normalize_git_remote(snapshot.observed_origin_url)
        == _normalize_git_remote(str(config["official_repository"]))
        and snapshot.detached_head
        and snapshot.checkout_clean
        and snapshot.readme_blob_sha == config["expected_readme_blob_sha"]
        and snapshot.technical_manual_blob_sha
        == config["expected_technical_manual_blob_sha"]
        and not snapshot.standalone_license_present
        and "cc by-sa 4.0" in readme.lower()
    )

    expected_lfs = tuple(config["expected_lfs_files"])
    tree_files = set(
        run_git(
            official_root,
            "ls-tree",
            "-r",
            "--name-only",
            str(config["snapshot_commit"]),
            "--",
            str(config["dataset_directory"]),
        ).splitlines()
    )
    expected_paths = {str(item["relative_path"]) for item in expected_lfs}
    if tree_files != expected_paths:
        raise HAIProvenanceError("HAI 23.05 source file population differs from freeze")
    lfs_records = []
    for item in expected_lfs:
        relative = str(item["relative_path"])
        pointer_text = git_blob_text(
            official_root, str(config["snapshot_commit"]), relative
        )

    lfs_listed_paths = set(
        run_git(official_root, "lfs", "ls-files", "-n").splitlines()
    )
    if not expected_paths.issubset(lfs_listed_paths):
        raise HAIProvenanceError("expected HAI files are absent from Git-LFS inventory")
        lfs_records.append(
            validate_lfs_materialization(
                relative_path=relative,
                pointer_text=pointer_text,
                materialized_path=official_root / relative,
                expected_oid_sha256=str(item["oid_sha256"]),
                expected_size_bytes=int(item["byte_size"]),
            )
        )

    time_series_paths = (
        "hai-23.05/hai-train1.csv",
        "hai-23.05/hai-train2.csv",
        "hai-23.05/hai-train3.csv",
        "hai-23.05/hai-train4.csv",
        "hai-23.05/hai-test1.csv",
        "hai-23.05/hai-test2.csv",
    )
    _, canonical_header, _ = _read_header(official_root / time_series_paths[0])
    csv_records = []
    for relative in time_series_paths:
        is_test = "hai-test" in relative
        csv_records.append(
            audit_csv_structure(
                official_root / relative,
                relative_path=relative,
                expected_point_count=int(config["expected_primary_point_count"]),
                canonical_header=canonical_header,
                official_train_normal_description_verified=(
                    not is_test and _readme_supports_normal_train_status(readme)
                ),
                test_file_structural_only=is_test,
            )
        )
    timestamp_index = next(
        index for index, value in enumerate(canonical_header)
        if value.strip().lower() in {"timestamp", "time", "datetime", "date_time"}
    )
    feature_names = [
        value
        for index, value in enumerate(canonical_header)
        if index != timestamp_index
        and value.strip().lower() not in {"label", "attack", "anomaly", "is_attack"}
    ]
    feature_names_hash = sha256(
        json.dumps(feature_names, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    _, label_header, _ = _read_header(official_root / "hai-23.05/label-test1.csv")
    label_fields = [
        value
        for value in label_header
        if value.strip().lower() not in {"timestamp", "time", "datetime", "date_time"}
    ]
    if len(label_fields) != 1:
        raise HAIProvenanceError("external label field cannot be discovered uniquely")

    labels = []
    for number in (1, 2):
        labels.append(
            audit_label_custody_pair(
                test_path=official_root / f"hai-23.05/hai-test{number}.csv",
                test_relative_path=f"hai-23.05/hai-test{number}.csv",
                label_path=official_root / f"hai-23.05/label-test{number}.csv",
                label_relative_path=f"hai-23.05/label-test{number}.csv",
                summary_path=official_root / f"hai-23.05/summary_label{number}.txt",
                summary_relative_path=f"hai-23.05/summary_label{number}.txt",
                expected_event_count=int(
                    config["expected_summary_event_counts"][f"summary_label{number}.txt"]
                ),
                private_output_path=private_root / f"label_custody_{number}.json",
            )
        )

    readme_record, manual, graphs = _inventory_references(
        official_root,
        str(config["snapshot_commit"]),
        config,
        readme_sha256,
        citation_sha256,
    )
    reference_inventory = {
        "schema_version": "1.0.0",
        "artifact_type": "hai_reference_inventory",
        "task_id": "TASK-039A",
        "snapshot_commit": str(config["snapshot_commit"]),
        "readme": readme_record,
        "technical_manual": manual.to_dict(),
        "graphs": [item.to_dict() for item in graphs],
        "official_graph_claim_boundary": "weak_relation_reference_not_causal_truth",
    }
    reference_inventory["artifact_hash"] = canonical_self_hash(
        reference_inventory, "artifact_hash"
    )

    creation = CreationMetadataV2(
        created_at=args.created_at,
        created_by="TASK-039A official provenance audit",
        code_commit=args.execution_code_commit,
        config_hash=str(config["config_hash"]),
    )
    manifest = build_hai_dataset_manifest_v2(
        csv_records=csv_records,
        label_records=labels,
        lfs_records=lfs_records,
        metadata_artifact_references=(
            snapshot.artifact_hash,
            manual.artifact_hash,
            reference_inventory["artifact_hash"],
        ),
        source_repository=str(config["official_repository"]),
        snapshot_commit=str(config["snapshot_commit"]),
        feature_names_hash=feature_names_hash,
        label_field_name=label_fields[0],
        license_reference=(
            f"README.md License section@{config['snapshot_commit']}"
        ),
        citation_reference=f"sha256:{citation_sha256}",
        creation_metadata=creation,
        expected_point_count=int(config["expected_primary_point_count"]),
        expected_process_ids=tuple(str(item) for item in config["expected_process_ids"]),
    )

    csv_gate = all(
        item.timestamps_strictly_increasing
        and item.malformed_row_count == 0
        and item.inconsistent_field_count_rows == 0
        and item.ordered_header_matches_canonical
        and item.expected_point_count_reconciled
        and len(item.distinct_timestamp_delta_seconds) == 1
        and not item.timestamp_delta_summary_truncated
        for item in csv_records
    )
    gates = {
        "official_repository_remote_matches": _normalize_git_remote(
            snapshot.observed_origin_url
        )
        == _normalize_git_remote(str(config["official_repository"])),
        "source_head_matches_pinned_commit": snapshot.observed_head
        == config["snapshot_commit"],
        "source_checkout_clean": snapshot.checkout_clean,
        "source_snapshot_identity_verified": snapshot_gate,
        "git_fsck_passed": snapshot.git_fsck_passed,
        "git_lfs_available": snapshot.lfs_available,
        "git_lfs_fsck_passed": snapshot.git_lfs_fsck_passed,
        "exact_lfs_file_population": tree_files == expected_paths,
        "expected_files_registered_in_git_lfs": expected_paths.issubset(lfs_listed_paths),
        "all_lfs_pointers_match": all(item.pointer_matches_expected for item in lfs_records),
        "all_lfs_files_materialized": all(item.materialized for item in lfs_records),
        "csv_schema_and_continuity_valid": csv_gate,
        "train_files_normal_only": all(
            item.normal_file_status == "normal_only_verified"
            for item in csv_records if "hai-train" in item.relative_path
        ),
        "labels_aligned_and_custodied": all(item.custody_status == "verified" for item in labels),
        "event_counts_match": sum(item.event_record_count for item in labels)
        == int(config["expected_summary_event_counts"]["total"]),
        "manual_verified": manual.file_type_valid,
        "reference_inventory_complete": len(graphs) > 0,
        "license_and_citation_recorded": bool(citation_sha256) and "cc by-sa 4.0" in readme.lower(),
        "haiend_excluded": all(
            not item.relative_path.lower().startswith("haiend-") for item in lfs_records
        ),
        "raw_private_boundary_passed": True,
        "scientific_analysis_performed": False,
    }
    # The final boundary gate is expressed positively for all-gates evaluation.
    gates["no_scientific_analysis_performed"] = not gates.pop(
        "scientific_analysis_performed"
    )
    status = (
        "passed_hai_2305_official_provenance_audit"
        if all(gates.values())
        else "failed_regression_check"
    )
    boundary = {
        "label_content_accessed_for_provenance_only": True,
        "label_content_used_for_scientific_selection": False,
        "attack_event_details_publicly_exposed": False,
        "test_file_feature_statistics_computed": False,
        "process_selected": False,
        "scientific_split_created": False,
        "detector_executed": False,
        "rule_constructed_or_executed": False,
        "outer_or_sealed_scientific_access": False,
        "absolute_local_paths_public": False,
    }
    result = HAIProvenanceAuditResultV1(
        task_id="TASK-039A",
        status=status,
        execution_code_commit=args.execution_code_commit,
        repository_snapshot=snapshot,
        lfs_records=tuple(lfs_records),
        csv_records=tuple(csv_records),
        label_custody_records=tuple(labels),
        reference_records=(manual,),
        graph_records=graphs,
        dataset_manifest_id=manifest.manifest_id,
        mandatory_gates=gates,
        boundary=boundary,
        created_at=args.created_at,
    )

    write_public_json(REPORT_ROOT / "TASK-039A_DATASET_MANIFEST_V2.json", manifest.to_dict())
    _write_report(
        REPORT_ROOT / "TASK-039A_SOURCE_RECEIPT.json",
        {
            "schema_version": "1.0",
            "artifact_type": "task039a_source_receipt",
            "task_id": "TASK-039A",
            "status": status,
            "execution_code_commit": args.execution_code_commit,
            "repository_snapshot": snapshot.to_dict(),
            "lfs_records": [item.to_dict() for item in lfs_records],
            "readme_content_sha256": readme_sha256,
            "citation_sha256": citation_sha256,
        },
    )
    _write_report(
        REPORT_ROOT / "TASK-039A_CSV_STRUCTURE_REPORT.json",
        {
            "schema_version": "1.0",
            "artifact_type": "task039a_csv_structure_report",
            "task_id": "TASK-039A",
            "status": status,
            "records": [item.to_dict() for item in csv_records],
            "all_headers_aligned": all(item.ordered_header_matches_canonical for item in csv_records),
            "feature_names_hash": feature_names_hash,
            "feature_count": int(config["expected_primary_point_count"]),
            "test_files_structural_only": True,
        },
    )
    _write_report(
        REPORT_ROOT / "TASK-039A_LABEL_CUSTODY_PUBLIC_REPORT.json",
        {
            "schema_version": "1.0",
            "artifact_type": "task039a_label_custody_public_report",
            "task_id": "TASK-039A",
            "status": status,
            "records": [item.to_dict() for item in labels],
            "total_expected_event_count": int(config["expected_summary_event_counts"]["total"]),
            "label_content_accessed_for_provenance_only": True,
            "label_content_used_for_scientific_selection": False,
            "attack_event_details_publicly_exposed": False,
        },
    )
    write_public_json(
        REPORT_ROOT / "TASK-039A_REFERENCE_INVENTORY.json", reference_inventory
    )
    write_public_json(
        REPORT_ROOT / "TASK-039A_PROVENANCE_REPORT.json", result.to_dict()
    )
    for path, text in _markdown_reports(
        snapshot=snapshot,
        csv_records=csv_records,
        labels=labels,
        graphs=graphs,
        dataset_manifest_id=manifest.manifest_id,
        status=status,
    ).items():
        path.write_text(text, encoding="utf-8")
    report = f"""# TASK-039A Report

Status: `{status}`

Execution code commit: `{args.execution_code_commit}`

TASK-039A verifies the official HAI 23.05 source, Git-LFS materialization,
file integrity, structural schema, label custody, and public provenance
manifest.

It does not select a process, validate delayed-response feasibility, type
scientific variables, construct candidate relations, train a graph model,
generate a rule, run a detector, access a scientific outer/sealed evaluation,
or establish thesis performance.

Next task: `TASK-039B`.
"""
    (REPORT_ROOT / "TASK-039A_REPORT.md").write_text(report, encoding="utf-8")
    return 0 if status == "passed_hai_2305_official_provenance_audit" else 1


def _path_argument(value: str | None, environment_name: str) -> Path:
    selected = value or os.environ.get(environment_name)
    if not selected:
        raise HAIProvenanceError(f"{environment_name} is required")
    return Path(selected)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--official-root")
    parser.add_argument("--data-root")
    parser.add_argument("--private-root")
    parser.add_argument("--public-output-root", type=Path, default=REPORT_ROOT)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--execution-code-commit", required=True)
    parser.add_argument(
        "--created-at",
        default=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    return parser


def main() -> int:
    parser = build_parser()
    arguments = parser.parse_args()
    try:
        arguments.official_root = _path_argument(
            arguments.official_root, "HAI_OFFICIAL_ROOT"
        )
        arguments.data_root = _path_argument(arguments.data_root, "HAI_DATA_ROOT")
        arguments.private_root = _path_argument(
            arguments.private_root, "HAI_PRIVATE_AUDIT_ROOT"
        )
        return run_audit(arguments)
    except (HAIProvenanceError, OSError, json.JSONDecodeError) as exc:
        # Deliberately omit exception text because it may contain an absolute path.
        print(f"TASK-039A audit failed: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
