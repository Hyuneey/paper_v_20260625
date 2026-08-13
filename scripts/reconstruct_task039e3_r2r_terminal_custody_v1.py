#!/usr/bin/env python3
"""Reconstruct the omitted historical proposal-envelope custody exactly once.

Run this script with PYTHONPATH pointing only at the exact historical
execution checkout. It never contacts a provider and writes one create-new
private supplemental artifact outside Git.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import stat
import subprocess
from typing import Any, Mapping, Sequence

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    canonical_proposal_hash_v1,
)
from paperworks.v6.task039e2_execution_configuration_v1 import (
    ProviderProposalCoreV1,
    RuleProposalEnvelopeV1,
    WINDOW_NUMERIC_ROLES,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    E0_BUDGET_POLICY_HASH,
    EXECUTION_SCHEDULE_HASH,
    PROVIDER_MODEL_RECEIPT_HASH,
    build_main_request_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    T0_TEMPLATE_HASH,
    _envelope_to_dict,
    _project_proposal_document,
    _provenance,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    PUBLIC_COHORT_FILE,
    SCHEDULE_FILE,
    _load_json,
    _verify_self_hash,
    load_real_evidence_schedule_v1,
)


HISTORICAL_EXECUTION_COMMIT = "5dca2d0431d60ef2f2bdfc907ebfe3fe18521f16"
SUCCESS_RECEIPT_HASH = "d164f00da3121e345907fe9076e62f4697493f26dde7448cc8527b895cbffa6e"
ORIGINAL_PROPOSAL_LEDGER_HASH = (
    "1d573ae83a147edf4aacb2a806016d7cfaf23b90d17e11e4e7b3c885c30e0e93"
)
SUPPLEMENT_FILE = (
    "TASK039E3_R2R_PROPOSAL_RECORD_HASH_PREIMAGE_SUPPLEMENT_V1.json"
)


class HistoricalCustodyReconstructionError(RuntimeError):
    """Historical proposal custody cannot be reconstructed without inference."""


def _resolve_nonlink(path: Path, label: str) -> Path:
    resolved = path.resolve(strict=True)
    metadata = path.lstat()
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(metadata, "st_file_attributes", 0)
    if path.is_symlink() or (reparse and attributes & reparse):
        raise HistoricalCustodyReconstructionError(f"{label} cannot be a link")
    return resolved


def _is_nested(left: Path, right: Path) -> bool:
    try:
        left.relative_to(right)
    except ValueError:
        return False
    return True


def _prepare_output_root(
    requested: Path, *, repository_root: Path, protected_roots: Sequence[Path]
) -> Path:
    if not requested.is_absolute() or requested.exists():
        raise HistoricalCustodyReconstructionError(
            "supplemental private root must be absolute and new"
        )
    parent = _resolve_nonlink(requested.parent, "supplement parent")
    root = parent / requested.name
    repository = _resolve_nonlink(repository_root, "historical repository")
    protected = tuple(_resolve_nonlink(path, "protected root") for path in protected_roots)
    for boundary in (repository, *protected):
        if _is_nested(root, boundary) or _is_nested(boundary, root):
            raise HistoricalCustodyReconstructionError(
                "supplemental root must be distinct and unnested"
            )
    root.mkdir()
    return _resolve_nonlink(root, "supplemental private root")


def _core_from_project(project: Mapping[str, Any]) -> ProviderProposalCoreV1:
    references = project.get("preregistered_window_constant_references")
    variables = project.get("variables")
    if not isinstance(references, list) or len(references) != len(WINDOW_NUMERIC_ROLES):
        raise HistoricalCustodyReconstructionError("window reference projection differs")
    if not isinstance(variables, list):
        raise HistoricalCustodyReconstructionError("proposal variables differ")
    try:
        return ProviderProposalCoreV1(
            dsl_family=project["dsl_family"],
            relation_identity=project["relation_identity"],
            source=project["source"],
            source_step_direction=project["source_step_direction"],
            target=project["target"],
            target_response_direction=project["target_response_direction"],
            selected_delay_horizon_seconds=project[
                "selected_delay_horizon_seconds"
            ],
            source_threshold_reference=project["source_threshold_reference"],
            source_stability_reference=project["source_stability_reference"],
            target_scale_reference=project["target_scale_reference"],
            window_constant_references=dict(zip(WINDOW_NUMERIC_ROLES, references)),
            variables=tuple(variables),
            runtime_logic_family=project["runtime_logic"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HistoricalCustodyReconstructionError(
            "persisted proposal core cannot be reconstructed"
        ) from exc


def reconstruct_supplement_v1(
    *, repository_root: Path, e1_private_ledger: Path,
    original_proposal_ledger: Path, original_provider_ledger: Path,
    success_receipt: Path,
) -> dict[str, Any]:
    """Return the complete private supplement without writing it."""

    repository = _resolve_nonlink(repository_root, "historical repository")
    head = subprocess.run(
        ["git", "-c", f"safe.directory={repository}", "rev-parse", "HEAD"],
        cwd=repository, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if head != HISTORICAL_EXECUTION_COMMIT:
        raise HistoricalCustodyReconstructionError("historical execution commit differs")

    preflight_cohort = _load_json(repository / PUBLIC_COHORT_FILE)
    schedule = _load_json(repository / SCHEDULE_FILE)
    relation_identities = schedule.get("relation_identities")
    if not isinstance(relation_identities, list) or len(relation_identities) != 42:
        raise HistoricalCustodyReconstructionError("historical relation schedule differs")
    evidences = load_real_evidence_schedule_v1(
        private_ledger_path=_resolve_nonlink(e1_private_ledger, "E1 ledger"),
        public_cohort=preflight_cohort,
        relation_identities=relation_identities,
    )
    evidence_by_identity = {
        item.relation.relation_identity: item for item in evidences
    }

    proposal_ledger = _load_json(
        _resolve_nonlink(original_proposal_ledger, "proposal ledger")
    )
    _verify_self_hash(proposal_ledger, ORIGINAL_PROPOSAL_LEDGER_HASH)
    proposal_records = proposal_ledger.get("records")
    if proposal_ledger.get("record_count") != 251 or not isinstance(
        proposal_records, list
    ):
        raise HistoricalCustodyReconstructionError("proposal ledger count differs")
    provider_ledger = _load_json(
        _resolve_nonlink(original_provider_ledger, "provider ledger")
    )
    _verify_self_hash(provider_ledger)
    provider_records = provider_ledger.get("records")
    if provider_ledger.get("record_count") != 252 or not isinstance(
        provider_records, list
    ):
        raise HistoricalCustodyReconstructionError("provider ledger count differs")
    receipt = _load_json(_resolve_nonlink(success_receipt, "success receipt"))
    _verify_self_hash(receipt, SUCCESS_RECEIPT_HASH)

    invalid = [record for record in provider_records if record.get("parse_status") != "valid_structured"]
    if len(invalid) != 1:
        raise HistoricalCustodyReconstructionError("missing proposal cause differs")
    missing_slot = invalid[0].get("slot")
    if not isinstance(missing_slot, Mapping) or (
        missing_slot.get("arm"), missing_slot.get("relation_schedule_index"),
        missing_slot.get("arm_local_call_number"), invalid[0].get("parse_status")
    ) != ("T1-B", 19, 2, "schema_parse_failure"):
        raise HistoricalCustodyReconstructionError("missing proposal slot differs")
    missing_identity = relation_identities[19]
    if any(
        (record.get("relation_identity"), record.get("arm"), record.get("call_number"))
        == (missing_identity, "T1-B", 2)
        for record in proposal_records
    ):
        raise HistoricalCustodyReconstructionError(
            "schema-failure proposal was unexpectedly materialized"
        )

    supplements: list[dict[str, Any]] = []
    for record in proposal_records:
        identity = record.get("relation_identity")
        arm = record.get("arm")
        call_number = record.get("call_number")
        evidence = evidence_by_identity.get(identity)
        project = record.get("project_proposal")
        validity = record.get("validity_result")
        if (
            evidence is None or arm not in {"T0", "T1", "T1-B", "T2"}
            or isinstance(call_number, bool) or not isinstance(call_number, int)
            or not isinstance(project, Mapping) or not isinstance(validity, Mapping)
        ):
            raise HistoricalCustodyReconstructionError("proposal binding differs")
        if arm == "T2" and call_number != 1:
            raise HistoricalCustodyReconstructionError(
                "historical T2 follow-up preimage is not authorized here"
            )
        core = _core_from_project(project)
        provenance = _provenance(
            evidence=evidence,
            arm=arm,
            prompt_version=(
                "T0_TEMPLATE_V1" if arm == "T0" else "MAIN_INITIAL_PROMPT_V1"
            ),
        )
        reproduced = _project_proposal_document(
            core=core, evidence=evidence, provenance=provenance
        )
        if reproduced != dict(project):
            raise HistoricalCustodyReconstructionError(
                "historical project proposal does not reproduce exactly"
            )
        proposal_hash = record.get("proposal_hash")
        validity_hash = record.get("validity_hash")
        if (
            proposal_hash != project.get("proposal_hash")
            or canonical_proposal_hash_v1(project) != proposal_hash
            or validity.get("proposal_hash") != proposal_hash
            or stable_hash_v1({
                key: value for key, value in validity.items() if key != "artifact_hash"
            }) != validity_hash
            or validity.get("artifact_hash") != validity_hash
        ):
            raise HistoricalCustodyReconstructionError(
                "proposal or validity hash differs"
            )
        view = evidence.render_view()
        prompt_hash = (
            T0_TEMPLATE_HASH
            if arm == "T0"
            else build_main_request_v1(view).model_visible_content_hash
        )
        envelope = RuleProposalEnvelopeV1(
            proposal_core=core,
            construction_arm=arm,
            local_call_number=call_number,
            budget_policy_hash=E0_BUDGET_POLICY_HASH,
            evidence_hash=view.evidence_hash,
            prompt_hash=prompt_hash,
            provider_model_receipt_hash=(
                None if arm == "T0" else PROVIDER_MODEL_RECEIPT_HASH
            ),
            execution_schedule_hash=EXECUTION_SCHEDULE_HASH,
        )
        envelope_document = _envelope_to_dict(envelope)
        preimage = {
            "relation_identity": identity,
            "arm": arm,
            "call_number": call_number,
            "proposal_envelope": envelope_document,
            "proposal_hash": proposal_hash,
            "validity_hash": validity_hash,
        }
        recomputed = stable_hash_v1(preimage)
        if recomputed != record.get("record_hash"):
            raise HistoricalCustodyReconstructionError(
                "historical proposal record hash differs"
            )
        supplemental = {
            **preimage,
            "original_record_hash": record["record_hash"],
            "recomputed_record_hash": recomputed,
        }
        supplemental["supplement_record_hash"] = stable_hash_v1(supplemental)
        supplements.append(supplemental)

    counts = Counter(record["arm"] for record in supplements)
    if counts != {"T0": 42, "T1": 42, "T1-B": 125, "T2": 42}:
        raise HistoricalCustodyReconstructionError("proposal arm counts differ")
    document = {
        "schema_version": "1.0.0",
        "artifact_type": (
            "task039e3_r2r_proposal_record_hash_preimage_supplement_v1"
        ),
        "task_id": "TASK-039E3-R2R-TERMINAL-CUSTODY-REMEDIATION",
        "classification": "PRIVATE_SUPPLEMENTAL_CUSTODY",
        "historical_execution_commit": HISTORICAL_EXECUTION_COMMIT,
        "historical_execution_receipt_hash": SUCCESS_RECEIPT_HASH,
        "original_proposal_ledger_hash": ORIGINAL_PROPOSAL_LEDGER_HASH,
        "reconstruction_source_authority": "exact_historical_git_bytes",
        "proposal_record_count": 251,
        "proposal_arm_counts": dict(sorted(counts.items())),
        "record_hash_preimages_reconstructed": 251,
        "record_hash_exact_matches": 251,
        "record_hash_mismatches": 0,
        "t2_all_local_call_one": True,
        "missing_schema_failure_proposal_materialized": False,
        "numeric_values_included": False,
        "raw_time_series_included": False,
        "provider_raw_responses_included": False,
        "credential_included": False,
        "authorization_header_included": False,
        "chain_of_thought_included": False,
        "records": supplements,
    }
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def _write_create_new(path: Path, document: Mapping[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(
            document, handle, ensure_ascii=True, allow_nan=False,
            sort_keys=True, separators=(",", ":"),
        )
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    observed = _load_json(path)
    _verify_self_hash(observed, str(document["artifact_hash"]))
    if observed != document:
        raise HistoricalCustodyReconstructionError(
            "durable supplement differs after re-read"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-repository-root", type=Path, required=True)
    parser.add_argument("--e1-private-ledger", type=Path, required=True)
    parser.add_argument("--original-proposal-ledger", type=Path, required=True)
    parser.add_argument("--original-provider-ledger", type=Path, required=True)
    parser.add_argument("--success-receipt", type=Path, required=True)
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument("--output-private-root", type=Path)
    destination.add_argument("--verify-existing-supplement", type=Path)
    parser.add_argument("--protected-root", type=Path, action="append", default=[])
    arguments = parser.parse_args()
    document = reconstruct_supplement_v1(
        repository_root=arguments.historical_repository_root,
        e1_private_ledger=arguments.e1_private_ledger,
        original_proposal_ledger=arguments.original_proposal_ledger,
        original_provider_ledger=arguments.original_provider_ledger,
        success_receipt=arguments.success_receipt,
    )
    if arguments.verify_existing_supplement is not None:
        observed = _load_json(
            _resolve_nonlink(
                arguments.verify_existing_supplement, "existing supplement"
            )
        )
        _verify_self_hash(observed, str(document["artifact_hash"]))
        if observed != document:
            raise HistoricalCustodyReconstructionError(
                "existing supplement differs from exact reconstruction"
            )
    else:
        root = _prepare_output_root(
            arguments.output_private_root,
            repository_root=arguments.historical_repository_root,
            protected_roots=arguments.protected_root,
        )
        _write_create_new(root / SUPPLEMENT_FILE, document)
    print(json.dumps({
        "status": "passed_private_supplement_materialization",
        "artifact_hash": document["artifact_hash"],
        "records": document["proposal_record_count"],
        "exact_matches": document["record_hash_exact_matches"],
        "mismatches": document["record_hash_mismatches"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
