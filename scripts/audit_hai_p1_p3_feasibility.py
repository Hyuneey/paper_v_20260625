"""Run the TASK-039B normal-only P1/P3 delayed-response feasibility audit."""

from __future__ import annotations

import argparse
import gc
import json
import subprocess
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from statistics import median
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from paperworks.data.contracts_v2 import CreationMetadataV2  # noqa: E402
from paperworks.feasibility.hai_process_io_v1 import (  # noqa: E402
    extract_manual_pages,
    extract_manual_variable_entries,
    load_process_values,
    load_verified_task039a_manifest,
    official_graph_available_for_process,
    official_graph_references_by_variable,
    private_ledger_hash_and_write,
    process_feature_names,
    verify_training_files,
)
from paperworks.feasibility.hai_process_v1 import (  # noqa: E402
    APPROVED_TRAIN_FILES,
    HAIGDNViewReadinessV1,
    HAIFeasibilityError,
    HAIMetadataEvidenceRecordV1,
    HAIProcessFreezeV1,
    TASK039BDataAccessLedger,
    build_domain_diagnostic,
    build_process_feasibility,
    build_variable_metadata,
    canonical_json,
    canonical_self_hash,
    create_process_split_manifests,
    create_process_views,
    isolated_transition_indices,
    public_payload_has_prohibited_content,
    screen_delayed_response_pair,
    select_process,
    transition_indices,
)


CONFIG_PATH = REPOSITORY_ROOT / "configs/v6/task039b_hai_p1_p3_feasibility.json"
MANIFEST_PATH = REPOSITORY_ROOT / "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"
REFERENCE_REPORT_PATH = REPOSITORY_ROOT / "docs/task_reports/TASK-039A_REFERENCE_INVENTORY.json"
DEFAULT_PUBLIC_ROOT = REPOSITORY_ROOT / "docs/task_reports"


def _git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise HAIFeasibilityError("Git execution preflight failed")
    return result.stdout.strip()


def _load_self_hashed(path: Path, field: str) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get(field) != canonical_self_hash(document, field):
        raise HAIFeasibilityError(f"self-hash mismatch: {path.name}")
    return document


def _assert_external_root(path: Path, field: str) -> Path:
    resolved = path.resolve()
    repository = REPOSITORY_ROOT.resolve()
    if resolved == repository or repository in resolved.parents or not resolved.is_dir():
        raise HAIFeasibilityError(f"{field} must be an existing directory outside repository")
    return resolved


def _artifact_wrapper(artifact_type: str, **fields: Any) -> dict[str, Any]:
    document = {"schema_version": "1.0.0", "artifact_type": artifact_type, **fields}
    document["artifact_hash"] = canonical_self_hash(document)
    return document


def _write_public(path: Path, document: Mapping[str, Any]) -> None:
    payload = json.loads(canonical_json(document))
    if public_payload_has_prohibited_content(payload):
        raise HAIFeasibilityError("public output boundary rejected sensitive content")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _verify_execution_preflight(execution_code_commit: str) -> None:
    if _git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        raise HAIFeasibilityError("real audit must run from main")
    if _git("rev-parse", "HEAD") != execution_code_commit:
        raise HAIFeasibilityError("execution commit does not match HEAD")
    if _git("status", "--short"):
        raise HAIFeasibilityError("real audit requires a clean implementation commit")


def _page_summary(extraction: Any, process_id: str) -> tuple[int, ...]:
    pages = []
    marker = process_id.lower()
    process_name = "boiler" if process_id == "P1" else "water treatment"
    for number, text in enumerate(extraction.page_texts, start=1):
        lowered = text.lower()
        if marker in lowered or process_name in lowered:
            pages.append(number)
    return tuple(pages)


def _screen_process(
    *,
    process_id: str,
    data_root: Path,
    official_root: Path,
    verified_files: Any,
    extraction: Any,
    graph_inventory: Mapping[str, Any],
    ledger: TASK039BDataAccessLedger,
    private_root: Path,
    dataset_manifest_id: str,
    creation: CreationMetadataV2,
) -> dict[str, Any]:
    feature_names = process_feature_names(verified_files[0].header, process_id)
    values = load_process_values(
        data_root=data_root,
        verified_files=verified_files,
        process_id=process_id,
        ledger=ledger,
    )
    manual_entries = extract_manual_variable_entries(
        page_texts=extraction.page_texts, variable_names=feature_names
    )
    graph_refs = official_graph_references_by_variable(
        official_root=official_root,
        public_reference_inventory=graph_inventory,
        variable_names=feature_names,
    )
    computations: dict[str, Any] = {}
    diagnostics = []
    metadata = []
    metadata_evidence = []
    for name in feature_names:
        computation = build_domain_diagnostic(
            variable_name=name,
            process_id=process_id,
            values_by_file={file_name: columns[name] for file_name, columns in values.items()},
            candidate_fit_files=APPROVED_TRAIN_FILES[:2],
        )
        computations[name] = computation
        diagnostics.append(computation.diagnostic)
        entry = manual_entries[name]
        evidence_refs: tuple[str, ...] = ()
        if entry.page_references:
            evidence_id = sha256(
                canonical_json(
                    {
                        "variable_name": name,
                        "manual_pages": list(entry.page_references),
                        "excerpt_hash": entry.excerpt_hash,
                    }
                ).encode()
            ).hexdigest()
            evidence = HAIMetadataEvidenceRecordV1(
                evidence_id=evidence_id,
                evidence_type="official_technical_manual_exact_tag_reference",
                source_reference="hai_dataset_technical_details.pdf@2a814cebc9a66b06c9e5cd545e2d72e65d383737",
                page_references=entry.page_references,
                excerpt_hash=entry.excerpt_hash,
                supports_semantic_role=True,
                supports_unit_or_quantity=entry.unit != "unverified",
                claim_boundary="metadata_only_not_causal_evidence",
            )
            metadata_evidence.append(evidence)
            evidence_refs = (evidence.artifact_hash,)
        metadata.append(
            build_variable_metadata(
                variable_name=name,
                process_id=process_id,
                description=entry.description,
                unit=entry.unit,
                subsystem_or_stage=(
                    "Boiler" if process_id == "P1" else "Water Treatment"
                ),
                manual_pages=entry.page_references,
                official_graph_references=graph_refs[name],
                domain=computation.diagnostic,
                evidence_record_refs=evidence_refs,
            )
        )
    eligible_sources = [item for item in metadata if item.source_eligibility]
    eligible_targets = [item for item in metadata if item.target_eligibility]
    source_values_by_file = {
        file_name: {item.variable_name: columns[item.variable_name] for item in eligible_sources}
        for file_name, columns in values.items()
    }
    trigger_cache: dict[tuple[str, float], dict[str, tuple[int, ...]]] = {}
    total_cache: dict[tuple[str, float], dict[str, int]] = {}
    screenings = []
    private_pair_records = []
    for source in eligible_sources:
        domain_values = computations[source.variable_name].distinct_values
        if not domain_values:
            continue
        for destination_state in domain_values:
            key = (source.variable_name, destination_state)
            trigger_cache[key] = {
                file_name: isolated_transition_indices(
                    source_variable=source.variable_name,
                    source_values=source_values_by_file[file_name],
                    destination_state=destination_state,
                    radius_seconds=2,
                )
                for file_name in values
            }
            total_cache[key] = {
                file_name: len(
                    transition_indices(
                        source_values_by_file[file_name][source.variable_name], destination_state
                    )
                )
                for file_name in values
            }
            for target in eligible_targets:
                scale = computations[target.variable_name].diagnostic.one_step_robust_variation_scale
                if scale is None:
                    continue
                record, private = screen_delayed_response_pair(
                    process_id=process_id,
                    source_variable=source.variable_name,
                    target_variable=target.variable_name,
                    destination_state=destination_state,
                    source_values_by_file=source_values_by_file,
                    target_values_by_file={
                        file_name: columns[target.variable_name]
                        for file_name, columns in values.items()
                    },
                    noise_scale=scale,
                    fit_files=APPROVED_TRAIN_FILES[:2],
                    calibration_file=APPROVED_TRAIN_FILES[2],
                    isolated_indices_by_file=trigger_cache[key],
                    total_trigger_counts_by_file=total_cache[key],
                )
                screenings.append(record)
                private_pair_records.append(private)
    canonical_view, candidate_view = create_process_views(
        dataset_manifest_id=dataset_manifest_id,
        process_id=process_id,
        feature_names=feature_names,
        creation_metadata=creation,
    )
    row_counts = {item.relative_path: item.row_count for item in verified_files}
    splits = create_process_split_manifests(
        dataset_manifest_id=dataset_manifest_id,
        data_view_id=canonical_view.view_id,
        process_id=process_id,
        row_counts=row_counts,
        creation_metadata=creation,
    )
    private_document = {
        "schema_version": "1.0.0",
        "artifact_type": "task039b_private_screening_ledger_v1",
        "process_id": process_id,
        "screening_records": private_pair_records,
        "comparison_views": [canonical_view.to_dict(), candidate_view.to_dict()],
        "comparison_splits": [item.to_dict() for item in splits],
        "raw_values_included": False,
        "transition_timestamps_included": False,
        "authoritative_candidate_universe": False,
    }
    private_hash = private_ledger_hash_and_write(
        private_root / f"task039b_{process_id.lower()}_screening_ledger.json",
        private_document,
    )
    feasibility = build_process_feasibility(
        process_id=process_id,
        metadata=metadata,
        diagnostics=diagnostics,
        screenings=screenings,
        private_screening_ledger_hash=private_hash,
        official_graph_reference_available=official_graph_available_for_process(
            graph_inventory, process_id
        ),
    )
    result = {
        "feature_names": feature_names,
        "metadata": tuple(metadata),
        "metadata_evidence": tuple(metadata_evidence),
        "diagnostics": tuple(diagnostics),
        "feasibility": feasibility,
        "canonical_view": canonical_view,
        "candidate_view": candidate_view,
        "splits": splits,
        "screening_count": len(screenings),
        "private_screening_ledger_hash": private_hash,
    }
    del values, computations, trigger_cache, total_cache, screenings, private_pair_records
    gc.collect()
    return result


def run(args: argparse.Namespace) -> int:
    _verify_execution_preflight(args.execution_code_commit)
    official_root = _assert_external_root(args.official_root, "official_root")
    data_root = (official_root / "hai-23.05").resolve()
    if data_root != args.data_root.resolve() or not data_root.is_dir():
        raise HAIFeasibilityError("data root must be the official hai-23.05 directory")
    private_root = _assert_external_root(args.private_root, "private_root")
    public_root = args.public_output_root.resolve()
    if public_root != DEFAULT_PUBLIC_ROOT.resolve():
        raise HAIFeasibilityError("public output root must be docs/task_reports")
    config = _load_self_hashed(CONFIG_PATH, "config_hash")
    manifest = load_verified_task039a_manifest(MANIFEST_PATH)
    ledger = TASK039BDataAccessLedger()
    verified = verify_training_files(data_root=data_root, manifest=manifest, ledger=ledger)
    manual_path = official_root / "hai_dataset_technical_details.pdf"
    extraction = extract_manual_pages(manual_path)
    if extraction.page_count <= 0:
        raise HAIFeasibilityError("blocked_hai_metadata_evidence_insufficient")
    reference_inventory = _load_self_hashed(REFERENCE_REPORT_PATH, "artifact_hash")
    graph_inventory = reference_inventory
    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    creation = CreationMetadataV2(
        created_at=created_at,
        created_by="TASK-039B HAI P1/P3 normal-only feasibility audit",
        code_commit=args.execution_code_commit,
        config_hash=config["config_hash"],
    )
    results = {
        process_id: _screen_process(
            process_id=process_id,
            data_root=data_root,
            official_root=official_root,
            verified_files=verified,
            extraction=extraction,
            graph_inventory=graph_inventory,
            ledger=ledger,
            private_root=private_root,
            dataset_manifest_id=manifest.manifest_id,
            creation=creation,
        )
        for process_id in ("P1", "P3")
    }
    selection = select_process(
        p1=results["P1"]["feasibility"],
        p3=results["P3"]["feasibility"],
        selection_policy_id=config["selection_policy"]["policy_id"],
        selection_policy_hash=sha256(
            canonical_json(config["selection_policy"]).encode()
        ).hexdigest(),
    )
    access_audit = ledger.freeze()
    metadata_registry = _artifact_wrapper(
        "task039b_variable_metadata_registry_v1",
        records=[
            item.to_dict() for process_id in ("P1", "P3") for item in results[process_id]["metadata"]
        ],
        evidence_records=[
            item.to_dict()
            for process_id in ("P1", "P3")
            for item in results[process_id]["metadata_evidence"]
        ],
        raw_values_included=False,
    )
    _write_public(public_root / "TASK-039B_VARIABLE_METADATA.json", metadata_registry)
    _write_public(public_root / "TASK-039B_P1_FEASIBILITY.json", results["P1"]["feasibility"].to_dict())
    _write_public(public_root / "TASK-039B_P3_FEASIBILITY.json", results["P3"]["feasibility"].to_dict())
    _write_public(public_root / "TASK-039B_PROCESS_SELECTION.json", selection.to_dict())
    _write_public(public_root / "TASK-039B_DATA_ACCESS_AUDIT.json", access_audit.to_dict())
    if selection.selection_status != "selected" or selection.selected_process_id is None:
        return 2
    selected_id = selection.selected_process_id
    excluded_id = selection.excluded_process_id
    selected = results[selected_id]
    splits = selected["splits"]
    process_freeze = HAIProcessFreezeV1(
        dataset_manifest_id=manifest.manifest_id,
        selected_process_id=selected_id,
        selected_process_name="Boiler" if selected_id == "P1" else "Water Treatment",
        excluded_process_id=str(excluded_id),
        selection_policy_id=config["selection_policy"]["policy_id"],
        selection_policy_hash=selection.selection_policy_hash,
        selected_process_feasibility_report_hash=selected["feasibility"].artifact_hash,
        excluded_process_feasibility_report_hash=results[str(excluded_id)]["feasibility"].artifact_hash,
        metadata_registry_hash=metadata_registry["artifact_hash"],
        private_screening_ledger_hash=selected["private_screening_ledger_hash"],
        normal_candidate_fit_split_id=splits[0].split_id,
        normal_relation_calibration_split_id=splits[1].split_id,
        normal_guard_split_id=splits[2].split_id,
        canonical_rule_view_id=selected["canonical_view"].view_id,
        candidate_learning_view_id=selected["candidate_view"].view_id,
        gdn_view_status="pending_production_backend",
        selection_status="passed_hai_2305_single_process_freeze",
        claim_boundary="single_process_feasibility_freeze_not_performance_evidence",
        creation_metadata=creation,
    )
    gdn = HAIGDNViewReadinessV1(
        selected_process_id=selected_id,
        production_backend="unresolved",
        downsampling="not_approved",
        model_training="not_authorized",
        candidate_mask="required_in_future",
        authoritative_gdn_view_created=False,
        claim_boundary="readiness_plan_only_not_model_evidence",
    )
    split_report = _artifact_wrapper(
        "task039b_selected_split_manifests_v2",
        selected_process_id=selected_id,
        split_manifests=[item.to_dict() for item in splits],
    )
    _write_public(public_root / "TASK-039B_PROCESS_FREEZE.json", process_freeze.to_dict())
    _write_public(public_root / "TASK-039B_CANONICAL_RULE_VIEW_V2.json", selected["canonical_view"].to_dict())
    _write_public(public_root / "TASK-039B_CANDIDATE_LEARNING_VIEW_V2.json", selected["candidate_view"].to_dict())
    _write_public(public_root / "TASK-039B_SPLIT_MANIFESTS_V2.json", split_report)
    _write_public(public_root / "TASK-039B_GDN_VIEW_READINESS.json", gdn.to_dict())
    execution_summary = _artifact_wrapper(
        "task039b_execution_summary_v1",
        status="passed_hai_2305_single_process_freeze",
        execution_code_commit=args.execution_code_commit,
        selected_process_id=selected_id,
        manual_extraction={
            "extractor": extraction.extractor,
            "extractor_version": extraction.extractor_version,
            "page_count": extraction.page_count,
            "title": extraction.title,
            "p1_reference_pages": list(_page_summary(extraction, "P1")),
            "p3_reference_pages": list(_page_summary(extraction, "P3")),
            "full_text_persisted": False,
        },
        normal_guard_feature_values_accessed=False,
        attack_information_accessed=False,
        scientific_performance_computed=False,
        process_freeze_hash=process_freeze.artifact_hash,
    )
    _write_public(public_root / "TASK-039B_EXECUTION_SUMMARY.json", execution_summary)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--public-output-root", type=Path, default=DEFAULT_PUBLIC_ROOT)
    parser.add_argument("--execution-code-commit", required=True)
    return parser


def main() -> int:
    try:
        return run(build_parser().parse_args())
    except (HAIFeasibilityError, OSError, ValueError) as exc:
        print(f"TASK-039B failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
