"""Run the bounded TASK-039BR0 source diagnosis without pair evaluation."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from paperworks.feasibility.hai_source_diagnosis_v1 import (
    CONTINUOUS_SOURCE_ROLES,
    SOURCE_EXCLUSION_CATEGORIES,
    HAIContinuousSourceMorphologyV1,
    HAIEndRouteReadinessV1,
    HAISourceDiagnosisError,
    HAISourceExclusionRecordV1,
    HAISourceExclusionSummaryV1,
    RuleV1CompatibilityRecordV1,
    TASK039BR0DataAccessLedger,
    build_continuous_route_readiness,
    classify_source_exclusion,
    decide_relation_family_route,
    diagnose_continuous_source_morphology,
)
from paperworks.v6.common import canonical_json_v1, stable_hash_v1


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPOSITORY_ROOT / "configs/v6/task039br0_source_eligibility_diagnosis.json"
PUBLIC_ROOT = REPOSITORY_ROOT / "docs/task_reports"
MANIFEST_PATH = REPOSITORY_ROOT / "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"
BLOCKED_COMMIT = "6543ca5b88779262d01c5e0c24e51216dd0835e9"
BLOCKED_METADATA_PATH = "docs/task_reports/TASK-039B_VARIABLE_METADATA.json"
BLOCKED_SELECTION_PATH = "docs/task_reports/TASK-039B_PROCESS_SELECTION.json"
SNAPSHOT_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"
HAIEND_DIRECTORY = "haiend-23.05"


def _run_git(repository: Path, *arguments: str, safe: bool = False) -> str:
    command = ["git"]
    if safe:
        command.extend(["-c", f"safe.directory={repository.as_posix()}"])
    command.extend(["-C", str(repository), *arguments])
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise HAISourceDiagnosisError("required Git object is unavailable")
    return result.stdout


def _load_self_hashed_config() -> dict[str, Any]:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    observed = payload.pop("config_hash", None)
    expected = stable_hash_v1(payload)
    if observed != expected:
        raise HAISourceDiagnosisError("TASK-039BR0 config self-hash mismatch")
    payload["config_hash"] = observed
    return payload


def _load_blocked_payload(relative_path: str) -> dict[str, Any]:
    text = _run_git(REPOSITORY_ROOT, "show", f"{BLOCKED_COMMIT}:{relative_path}")
    return json.loads(text)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    _assert_public_boundary(encoded)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded, encoding="utf-8")


def _write_private_json(path: Path, payload: Mapping[str, Any]) -> str:
    body = dict(payload)
    body["artifact_hash"] = stable_hash_v1(body)
    encoded = json.dumps(body, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded, encoding="utf-8")
    return body["artifact_hash"]


def _assert_public_boundary(text: str) -> None:
    lowered = text.lower()
    prohibited = (
        "attack_start",
        "attack_end",
        "attack_target",
        "target_controller",
        "raw_window",
        "raw_sequence",
        "c:\\users\\",
        "/home/",
        "signed_url",
        "authorization_header",
        "credential_path",
    )
    if any(item in lowered for item in prohibited):
        raise HAISourceDiagnosisError("public output boundary rejected content")


def _diagnostic_projection_hash(metadata: Mapping[str, Any]) -> str:
    return stable_hash_v1(
        {
            "artifact_type": "task039b_aggregate_domain_diagnostic_projection",
            "metadata_artifact_hash": metadata["artifact_hash"],
            "observed_domain": metadata["observed_value_domain"],
            "data_domain_evidence": metadata["data_domain_evidence"],
        }
    )


def _build_source_records(
    metadata: Sequence[Mapping[str, Any]],
) -> tuple[HAISourceExclusionRecordV1, ...]:
    records = []
    for item in metadata:
        primary = classify_source_exclusion(item)
        secondary = tuple(
            reason
            for reason in item.get("exclusion_reasons", ())
            if reason not in {primary, "continuous_actuator_outside_first_mvp"}
        )
        records.append(
            HAISourceExclusionRecordV1(
                variable_name=str(item["variable_name"]),
                process_id=str(item["process_id"]),
                documented_semantic_role=str(item["semantic_role"]),
                observed_domain=str(item["observed_value_domain"]),
                task039b_source_eligibility=bool(item["source_eligibility"]),
                primary_exclusion_reason=primary,
                secondary_exclusion_reasons=secondary,
                manual_reference=tuple(int(page) for page in item["manual_reference"]),
                official_graph_references=tuple(item["official_graph_references"]),
                aggregate_domain_diagnostic_ref=_diagnostic_projection_hash(item),
                review_status=str(item["review_status"]),
                metadata_confidence=str(item["metadata_confidence"]),
            )
        )
    return tuple(records)


def _summary_counts(records: Sequence[HAISourceExclusionRecordV1]) -> tuple[dict[str, Any], ...]:
    results = []
    for process_id in ("P1", "P3"):
        scoped = [item for item in records if item.process_id == process_id]
        counts = {
            category: sum(item.primary_exclusion_reason == category for item in scoped)
            for category in SOURCE_EXCLUSION_CATEGORIES
        }
        results.append(
            {
                "process_id": process_id,
                "variable_count": len(scoped),
                "primary_exclusion_counts": counts,
                "documented_control_variables_exist": any(
                    item.documented_semantic_role in CONTINUOUS_SOURCE_ROLES
                    and item.review_status == "reviewed"
                    for item in scoped
                ),
                "documented_continuous_controls_exist": any(
                    item.primary_exclusion_reason
                    in {
                        "documented_continuous_control_command",
                        "documented_continuous_actuator_feedback",
                    }
                    for item in scoped
                ),
                "discrete_variables_without_control_semantics": counts[
                    "discrete_but_not_control_semantics"
                ],
                "control_variables_constant_or_insufficient": (
                    counts["control_semantics_but_constant"]
                    + counts["control_semantics_but_insufficient_changes"]
                ),
                "semantic_role_unresolved_count": counts["semantic_role_unresolved"],
            }
        )
    return tuple(results)


def _read_pointer_inventory(official_root: Path) -> tuple[dict[str, Any], ...]:
    listing = _run_git(
        official_root,
        "ls-tree",
        "-r",
        "--long",
        SNAPSHOT_COMMIT,
        "--",
        HAIEND_DIRECTORY,
        safe=True,
    )
    records = []
    pattern = re.compile(r"^100644 blob ([a-f0-9]{40})\s+\d+\t(.+)$")
    for line in listing.splitlines():
        match = pattern.match(line)
        if match is None:
            raise HAISourceDiagnosisError("unexpected HAIEnd Git tree entry")
        blob_sha, relative_path = match.groups()
        pointer = _run_git(
            official_root,
            "show",
            f"{SNAPSHOT_COMMIT}:{relative_path}",
            safe=True,
        ).splitlines()
        if len(pointer) != 3 or not pointer[1].startswith("oid sha256:"):
            raise HAISourceDiagnosisError("HAIEnd entry is not a Git-LFS pointer")
        oid = pointer[1].removeprefix("oid sha256:")
        size = int(pointer[2].removeprefix("size "))
        records.append(
            {
                "relative_path": relative_path,
                "git_blob_sha": blob_sha,
                "lfs_oid_sha256": oid,
                "lfs_size_bytes": size,
                "payload_materialized_or_opened": False,
            }
        )
    return tuple(sorted(records, key=lambda item: item["relative_path"]))


def _build_haiend_readiness(official_root: Path) -> HAIEndRouteReadinessV1:
    if _run_git(official_root, "rev-parse", "HEAD", safe=True).strip() != SNAPSHOT_COMMIT:
        raise HAISourceDiagnosisError("official HAI checkout is not pinned")
    inventory = _read_pointer_inventory(official_root)
    paths = tuple(item["relative_path"] for item in inventory)
    train_count = sum("end-train" in item for item in paths)
    test_count = sum("end-test" in item and "label-" not in item for item in paths)
    expected_names = {
        *(f"{HAIEND_DIRECTORY}/end-train{index}.csv" for index in range(1, 5)),
        *(f"{HAIEND_DIRECTORY}/end-test{index}.csv" for index in range(1, 3)),
        *(f"{HAIEND_DIRECTORY}/label-test{index}.csv" for index in range(1, 3)),
        *(f"{HAIEND_DIRECTORY}/summary_label{index}.txt" for index in range(1, 3)),
    }
    complete = set(paths) == expected_names and train_count == 4 and test_count == 2
    return HAIEndRouteReadinessV1(
        official_repository="https://github.com/icsdataset/hai",
        snapshot_commit=SNAPSHOT_COMMIT,
        official_directory=HAIEND_DIRECTORY,
        pointer_inventory=inventory,
        file_count=len(inventory),
        expected_point_count=225,
        train_file_count=train_count,
        test_file_count=test_count,
        normal_data_availability_documented=train_count == 4,
        same_experiment_version_context_documented=True,
        boiler_internal_control_logic_documented=True,
        technical_manual_per_point_coverage_verified=False,
        official_graph_relevance="P1_Boiler_reference_only_not_candidate_truth",
        license_and_citation_compatible=True,
        payload_downloaded_or_opened=False,
        binary_or_discrete_claim_made=False,
        row_synchronization_claim_made=False,
        complete_auditable_p1_candidate_route=complete,
        route_status="haiend_route_requires_separate_provenance_and_feasibility",
    )


def _file_sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _verify_authorized_training_files(
    data_root: Path, config: Mapping[str, Any]
) -> None:
    if data_root.name != "hai-23.05" or not data_root.is_dir():
        raise HAISourceDiagnosisError("data root must be the verified hai-23.05 root")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("artifact_hash") != config["source_manifest_id"]:
        raise HAISourceDiagnosisError("TASK-039A manifest identity mismatch")
    records = {item["relative_local_path"]: item for item in manifest["files"]}
    for relative_path in config["authorized_train_files"]:
        expected = records.get(relative_path)
        if expected is None or expected.get("provenance_status") != "verified":
            raise HAISourceDiagnosisError("authorized train file lacks verified provenance")
        path = data_root / PurePosixPath(relative_path).name
        if (
            not path.is_file()
            or path.stat().st_size != expected["byte_size"]
            or _file_sha(path) != expected["sha256"]
        ):
            raise HAISourceDiagnosisError("authorized train file hash or size mismatch")


def _build_rule_compatibility() -> RuleV1CompatibilityRecordV1:
    schema_path = REPOSITORY_ROOT / "schemas/rule_dsl_schema.json"
    parser_path = REPOSITORY_ROOT / "src/paperworks/contracts/rule_v1.py"
    verifier_path = REPOSITORY_ROOT / "src/paperworks/contracts/verifier_v1.py"
    runtime_path = REPOSITORY_ROOT / "src/paperworks/contracts/runtime_v1.py"
    parser = parser_path.read_text(encoding="utf-8")
    verifier = verifier_path.read_text(encoding="utf-8")
    runtime = runtime_path.read_text(encoding="utf-8")
    checks = {
        "exactly_one_source": "len(rule.source_variables) != 1" in parser,
        "exactly_one_target": "len(rule.target_variables) != 1" in parser,
        "delayed_response_only": 'rule.relation_type != "delayed_response"' in parser,
        "state_changes_to_only": 'rule.trigger.trigger_type != "state_changes_to"' in parser,
        "literal_state_value_required": "rule.trigger.state_value is None" in parser,
        "trigger_threshold_references_rejected": "rule.trigger.threshold_parameter_ref" in parser,
        "trigger_range_references_rejected": "rule.trigger.range_parameter_ref" in parser,
        "trigger_duration_references_rejected": "rule.trigger.duration_parameter_ref" in parser,
        "increase_only": 'rule.expected_effect.direction != "increase"' in parser,
        "missing_expected_response_only": (
            'rule.output_semantics.violation_direction != "missing_expected_response"'
            in parser
        ),
        "verifier_runtime_bound_to_semantics": (
            "delayed_response_rule_to_dict" in verifier
            and 'validate_artifact("rule_dsl"' in verifier
            and "missing_expected_response" in verifier
            and "rule.trigger.state_value" in runtime
            and "window.source_values" in runtime
        ),
    }
    return RuleV1CompatibilityRecordV1(
        rule_schema_sha256=_file_sha(schema_path),
        rule_parser_sha256=_file_sha(parser_path),
        verifier_sha256=_file_sha(verifier_path),
        runtime_sha256=_file_sha(runtime_path),
        continuous_source_route_classification="requires_versioned_rule_semantics",
        **checks,
    )


def _process_morphology_public(
    records: Sequence[HAIContinuousSourceMorphologyV1],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "artifact_type": "task039br0_continuous_source_readiness_report",
        "morphology_records": [item.to_dict() for item in records],
        "large_change_diagnostic_authoritative": False,
        "source_target_pairs_evaluated": False,
    }


def _render_report(
    *,
    source_summary: HAISourceExclusionSummaryV1,
    continuous: Mapping[str, Any],
    haiend: HAIEndRouteReadinessV1,
    rule_v1: RuleV1CompatibilityRecordV1,
    decision: Mapping[str, Any],
    access: Mapping[str, Any],
) -> str:
    rows = {item["process_id"]: item for item in continuous["process_records"]}
    return f"""# TASK-039BR0 Report

## Status

`passed_source_eligibility_root_cause_audit`

Recommended route:
`{decision['recommended_route']}`

Next task:
`{decision['next_task']}`

## Frozen TASK-039B Result

TASK-039B remains `blocked_no_feasible_delayed_response_process`. P1 retained
37 variables, zero eligible discrete control sources, 12 continuous targets,
and zero screened pairs. P3 retained 7 variables, zero eligible discrete
control sources, 3 continuous targets, and zero screened pairs. No process was
selected and no TASK-039B gate was changed.

## Root Cause

The detailed source ledger classifies each of the 44 P1/P3 variables exactly
once. Its private artifact hash is `{source_summary.private_detail_ledger_hash}`.
The public summary distinguishes documented continuous controls, constant
control signals, setpoints, sensors, non-control discrete fields, and unresolved
semantics. The dominant source-space mismatch is that documented control and
actuator fields are represented continuously, while several discrete controls
are constant and the one observed binary P1 command lacks reviewed manual
binding.

## Continuous Source Morphology

| Process | Documented continuous candidates | Nonconstant train1/train2/train3 | Repeated in all files | Route status |
|---|---:|---:|---:|---|
| P1 | {rows['P1']['documented_continuous_control_feedback_candidates']} | {rows['P1']['nonconstant_candidates_train1']}/{rows['P1']['nonconstant_candidates_train2']}/{rows['P1']['nonconstant_candidates_train3']} | {rows['P1']['candidates_with_repeated_bounded_changes_all_files']} | `{rows['P1']['route_status']}` |
| P3 | {rows['P3']['documented_continuous_control_feedback_candidates']} | {rows['P3']['nonconstant_candidates_train1']}/{rows['P3']['nonconstant_candidates_train2']}/{rows['P3']['nonconstant_candidates_train3']} | {rows['P3']['candidates_with_repeated_bounded_changes_all_files']} | `{rows['P3']['route_status']}` |

The five-times-MAD change diagnostic is non-authoritative. No trigger threshold
was calibrated, no source-target pair was evaluated, and no process was
selected.

## Contract And Alternative Routes

Rule v1 remains unchanged. It supports one source, one target, a literal
`state_changes_to` trigger, increase-only delayed response, and
`missing_expected_response`. A continuous source therefore
`{rule_v1.continuous_source_route_classification}`.

The pinned HAIEnd tree contains {haiend.file_count} Git-LFS pointer records,
including {haiend.train_file_count} documented normal train files. Official
documentation identifies additional Boiler DCS internal-control points and the
same experiment/version context. No HAIEnd payload was downloaded or opened,
and no binary, discrete, usefulness, or row-level synchronization claim is
made. Its status remains `{haiend.route_status}`.

## Data Boundary

- test file access count: {access['test_file_access_count']}
- label file access count: {access['label_file_access_count']}
- attack summary access count: {access['attack_summary_access_count']}
- private custody access count: {access['private_custody_access_count']}
- normal-guard feature values accessed: {str(access['normal_guard_feature_values_accessed']).lower()}
- P2/P4 feature values accessed: {str(access['p2_p4_feature_values_accessed']).lower()}

TASK-039C remains unauthorized.

TASK-039BR0 explains why the original binary/discrete delayed-response MVP
failed on HAI P1 and P3 and identifies the next defensible research route.

It does not lower the TASK-039B gate, select a process, establish continuous
delayed-response feasibility, modify Rule v1, create Rule v2, download HAIEnd,
inspect attack data, construct candidate pairs, train a model, generate a rule,
run a detector, or establish anomaly-detection performance.
"""


def run(args: argparse.Namespace) -> int:
    config = _load_self_hashed_config()
    if config["authoritative_main_commit"] != "2450e2c9d3a3f3722581e2c1594435451493bf00":
        raise HAISourceDiagnosisError("authoritative main identity mismatch")
    if _run_git(REPOSITORY_ROOT, "rev-parse", "main").strip() != config[
        "authoritative_main_commit"
    ] or _run_git(REPOSITORY_ROOT, "rev-parse", "origin/main").strip() != config[
        "authoritative_main_commit"
    ]:
        raise HAISourceDiagnosisError("authoritative main ref mismatch")
    if _run_git(REPOSITORY_ROOT, "rev-parse", "task-039b-blocked-no-feasible").strip() != BLOCKED_COMMIT:
        raise HAISourceDiagnosisError("blocked TASK-039B branch identity mismatch")
    private_root = args.private_root.resolve()
    try:
        private_root.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise HAISourceDiagnosisError("private output root must remain outside repository")
    _verify_authorized_training_files(args.data_root, config)
    metadata_payload = _load_blocked_payload(BLOCKED_METADATA_PATH)
    selection_payload = _load_blocked_payload(BLOCKED_SELECTION_PATH)
    if selection_payload["artifact_hash"] != config["task039b_selection_hash"]:
        raise HAISourceDiagnosisError("TASK-039B selection artifact mismatch")
    metadata = tuple(metadata_payload["records"])
    if len(metadata) != 44:
        raise HAISourceDiagnosisError("TASK-039B variable population mismatch")

    source_records = _build_source_records(metadata)
    private_ledger_hash = _write_private_json(
        args.private_root / "task039br0_source_exclusion_ledger.json",
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039br0_private_source_exclusion_ledger_v1",
            "task039b_result_commit": BLOCKED_COMMIT,
            "records": [item.to_dict() for item in source_records],
            "raw_values_included": False,
        },
    )
    source_summary = HAISourceExclusionSummaryV1(
        task039b_result_commit=BLOCKED_COMMIT,
        task039b_selection_hash=selection_payload["artifact_hash"],
        frozen_status=selection_payload["selection_status"],
        frozen_metrics=(
            {
                "process_id": "P1",
                "total_variables": 37,
                "eligible_discrete_control_sources": 0,
                "eligible_continuous_sensor_targets": 12,
                "screened_pairs": 0,
                "feasibility_gate": "failed",
            },
            {
                "process_id": "P3",
                "total_variables": 7,
                "eligible_discrete_control_sources": 0,
                "eligible_continuous_sensor_targets": 3,
                "screened_pairs": 0,
                "feasibility_gate": "failed",
            },
        ),
        counts_by_process=_summary_counts(source_records),
        private_detail_ledger_hash=private_ledger_hash,
    )

    ledger = TASK039BR0DataAccessLedger()
    morphology = tuple(
        item
        for process_id in ("P1", "P3")
        for item in diagnose_continuous_source_morphology(
            data_root=args.data_root,
            process_id=process_id,
            metadata_records=metadata,
            ledger=ledger,
            distinct_cap=int(config["continuous_morphology"]["distinct_count_cap"]),
            numeric_epsilon=float(config["continuous_morphology"]["numeric_epsilon"]),
            minimum_repeated_changes=int(
                config["continuous_morphology"]["minimum_repeated_changes_per_file"]
            ),
        )
    )
    private_morphology_hash = _write_private_json(
        args.private_root / "task039br0_continuous_source_morphology_ledger.json",
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039br0_private_continuous_source_morphology_ledger_v1",
            "records": [item.to_dict() for item in morphology],
            "source_target_pairs_evaluated": False,
            "raw_values_included": False,
            "transition_timestamps_included": False,
        },
    )
    continuous = build_continuous_route_readiness(
        morphology,
        private_morphology_ledger_hash=private_morphology_hash,
    )
    continuous_payload = continuous.to_dict()
    haiend = _build_haiend_readiness(args.official_root)
    rule_v1 = _build_rule_compatibility()
    decision = decide_relation_family_route(
        continuous=continuous,
        haiend=haiend,
        rule_v1=rule_v1,
        source_summary=source_summary,
    )
    access = ledger.freeze()

    public_root = args.public_output_root.resolve()
    if public_root != PUBLIC_ROOT.resolve():
        raise HAISourceDiagnosisError("public output root must be docs/task_reports")
    _write_json(public_root / "TASK-039BR0_SOURCE_EXCLUSION_SUMMARY.json", source_summary.to_dict())
    _write_json(public_root / "TASK-039BR0_CONTINUOUS_SOURCE_READINESS.json", continuous_payload)
    _write_json(public_root / "TASK-039BR0_HAIEND_ROUTE_READINESS.json", haiend.to_dict())
    _write_json(public_root / "TASK-039BR0_RULE_V1_COMPATIBILITY.json", rule_v1.to_dict())
    _write_json(public_root / "TASK-039BR0_RELATION_FAMILY_DECISION.json", decision.to_dict())
    _write_json(public_root / "TASK-039BR0_DATA_ACCESS_AUDIT.json", access.to_dict())
    report = _render_report(
        source_summary=source_summary,
        continuous=continuous_payload,
        haiend=haiend,
        rule_v1=rule_v1,
        decision=decision.to_dict(),
        access=access.to_dict(),
    )
    _assert_public_boundary(report)
    (public_root / "TASK-039BR0_REPORT.md").write_text(report, encoding="utf-8")
    print(decision.recommended_route)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--public-output-root", type=Path, default=PUBLIC_ROOT)
    return parser


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
