"""Authorized TASK-039E3 construction-only scientific execution.

All construction semantics are imported from the frozen PREP orchestration.
This additive module supplies real E1 evidence projection, durable private
custody, live-run invariants, and sanitized public result construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import statistics
import subprocess
from typing import Any, Mapping, Sequence

from paperworks.v6.common import stable_hash_v1, thaw_json
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    ApprovedNumericEvidenceBundleV1,
    ConfirmedRelationPrimitiveV1,
)
from paperworks.v6.task039e2_execution_configuration_v1 import (
    CALIBRATED_NUMERIC_ROLES,
    ProviderProposalCoreV1,
    WINDOW_NUMERIC_ROLES,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    E0_PROTOCOL_BUNDLE_HASH,
    E1_CONSTRUCTION_EVIDENCE_COHORT_HASH,
    E1_MATERIALIZATION_RESULT_HASH,
    E1_PRIVATE_LEDGER_HASH,
    E2_PROTOCOL_BUNDLE_HASH,
    E3_AUTHORIZATION_HASH,
    EXACT_MODEL,
    EXECUTION_SCHEDULE_HASH,
    ConstructionInputViewV1,
    ConstructionNumericBindingV1,
    ProviderCallLedgerV1,
    ProviderCallSlotV1,
    ScientificRunAbortV1,
    TASK039E3PreparationError,
    build_capability_probe_request_v1,
    execute_mock_provider_slot_v1,
    validate_e3_authorization_v1,
)
from paperworks.v6.task039e3_live_transport_v1 import (
    LiveOpenAIChatCompletionsTransportV1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    T0_TEMPLATE_HASH,
    ConstructionOutcomeLedgerV1,
    ConstructionOutcomeRecordV1,
    ConstructionProposalLedgerV1,
    ConstructionProposalRecordV1,
    DirectNumberOutcomeV1,
    PublicConstructionMetricsV1,
    aggregate_construction_metrics_v1,
    aggregate_direct_number_metrics_v1,
    run_direct_number_v1,
    run_t1_v1,
    run_t1b_v1,
    run_t2_v1,
    wrap_and_verify_core_v1,
)


TASK_ID = "TASK-039E3"
STATUS = "passed_task039e3_rule_construction_scientific_execution"
BRANCH = "task-039e3-scientific-execution"
PREP_COMMIT = "aee1fc6e22bcb45572fe3bab5c9bb605de09d721"
RELATION_COUNT = 42
PRIVATE_LEDGER_FILE = "TASK039E1_PRIVATE_CONSTRUCTION_EVIDENCE_LEDGER.json"
PUBLIC_COHORT_FILE = "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_COHORT.json"
AUTHORIZATION_FILE = "docs/task_reports/TASK-039E3_AUTHORIZATION.json"
E2_BUNDLE_FILE = "docs/task_reports/TASK-039E2_PROTOCOL_BUNDLE.json"
SCHEDULE_FILE = "docs/task_reports/TASK-039E2_EXECUTION_SCHEDULE.json"

SCIENTIFIC_SOURCE_PATHS = (
    "src/paperworks/v6/task039e3_execution_prep_v1.py",
    "src/paperworks/v6/task039e3_orchestration_v1.py",
    "src/paperworks/v6/task039e0_rule_construction_protocol_v1.py",
    "src/paperworks/v6/task039e3_live_transport_v1.py",
    "src/paperworks/v6/task039e3_scientific_execution_v1.py",
)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TASK039E3PreparationError(f"JSON object required: {path.name}")
    return value


def _verify_self_hash(document: Mapping[str, Any], expected: str | None = None) -> str:
    observed = document.get("artifact_hash")
    if not isinstance(observed, str) or len(observed) != 64:
        raise TASK039E3PreparationError("artifact hash is missing")
    content = {key: value for key, value in document.items() if key != "artifact_hash"}
    if stable_hash_v1(content) != observed or (expected is not None and observed != expected):
        raise TASK039E3PreparationError("artifact self-hash differs")
    return observed


def _with_hash(content: Mapping[str, Any]) -> dict[str, Any]:
    document = dict(content)
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def validate_public_preflight_v1(repository_root: Path) -> dict[str, Any]:
    authorization = _load_json(repository_root / AUTHORIZATION_FILE)
    validate_e3_authorization_v1(authorization)
    bundle = _load_json(repository_root / E2_BUNDLE_FILE)
    _verify_self_hash(bundle, E2_PROTOCOL_BUNDLE_HASH)
    cohort = _load_json(repository_root / PUBLIC_COHORT_FILE)
    _verify_self_hash(cohort, E1_CONSTRUCTION_EVIDENCE_COHORT_HASH)
    schedule = _load_json(repository_root / SCHEDULE_FILE)
    _verify_self_hash(schedule, EXECUTION_SCHEDULE_HASH)
    identities = schedule.get("relation_identities")
    if not isinstance(identities, list) or len(identities) != 42 or len(set(identities)) != 42:
        raise TASK039E3PreparationError("E2 relation schedule differs")
    if cohort.get("relation_count") != 42 or cohort.get("numeric_binding_count") != 462:
        raise TASK039E3PreparationError("E1 public cohort count differs")
    return {"authorization": authorization, "bundle": bundle, "cohort": cohort, "schedule": schedule}


def validate_git_execution_state_v1(
    repository_root: Path, *, expected_execution_commit: str
) -> str:
    def run(*arguments: str) -> str:
        completed = subprocess.run(
            ["git", *arguments], cwd=repository_root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        return completed.stdout.strip()

    head = run("rev-parse", "HEAD")
    branch = run("branch", "--show-current")
    if head != expected_execution_commit or branch != BRANCH:
        raise TASK039E3PreparationError("execution branch/commit validation failed")
    if run("status", "--porcelain"):
        raise TASK039E3PreparationError("execution worktree must be clean")
    if run("merge-base", "--is-ancestor", PREP_COMMIT, head) != "":
        raise TASK039E3PreparationError("PREP ancestry check produced output")
    return head


def validate_private_roots_v1(
    *, repository_root: Path, e1_private_value: str, e3_private_value: str
) -> tuple[Path, Path]:
    values = (e1_private_value, e3_private_value)
    if any(not value or not Path(value).is_absolute() or ".." in Path(value).parts for value in values):
        raise TASK039E3PreparationError("private roots must be absolute and traversal-free")
    repository = repository_root.resolve(strict=True)
    e1_root = Path(e1_private_value).resolve(strict=True)
    e3_requested = Path(e3_private_value)
    e3_requested.mkdir(parents=True, exist_ok=True)
    e3_root = e3_requested.resolve(strict=True)
    if str(e1_root).casefold() == str(e3_root).casefold():
        raise TASK039E3PreparationError("E1 and E3 private roots must differ")
    for root in (e1_root, e3_root):
        try:
            root.relative_to(repository)
        except ValueError:
            pass
        else:
            raise TASK039E3PreparationError("private root must remain outside Git")
    if any(e3_root.iterdir()):
        raise TASK039E3PreparationError("TASK039E3_PRIVATE_ROOT must be new and empty")
    return e1_root, e3_root


def compute_scientific_source_hashes_v1(repository_root: Path) -> dict[str, str]:
    return {
        relative: sha256((repository_root / relative).read_bytes()).hexdigest()
        for relative in SCIENTIFIC_SOURCE_PATHS
    }


@dataclass(frozen=True)
class RealConstructionEvidenceV1:
    relation: ConfirmedRelationPrimitiveV1
    numeric_evidence: ApprovedNumericEvidenceBundleV1
    numeric_bindings: tuple[ConstructionNumericBindingV1, ...]
    approved_evidence_identities: tuple[str, ...]
    private_record_hash: str

    def render_view(self) -> ConstructionInputViewV1:
        return ConstructionInputViewV1(
            relation_identity=self.relation.relation_identity,
            source=self.relation.source,
            source_step_direction=self.relation.source_step_direction,
            target=self.relation.target,
            target_response_direction=self.relation.target_response_direction,
            selected_delay_horizon_seconds=self.relation.selected_delay_horizon_seconds,
            numeric_bindings=self.numeric_bindings,
            approved_evidence_identities=self.approved_evidence_identities,
            semantic_process_metadata={
                "process_identity": "P1",
                "relation_family": "continuous_step_delayed_response_v1",
                "construction_evidence_status": "approved",
            },
        )


def run_real_t0_v1(
    *, evidence: RealConstructionEvidenceV1,
    proposal_ledger: ConstructionProposalLedgerV1,
    outcome_ledger: ConstructionOutcomeLedgerV1,
) -> ConstructionOutcomeRecordV1:
    """Authorized real adapter for the E2 synthetic-locked T0 template."""

    view = evidence.render_view()
    references = view.numeric_references
    core = ProviderProposalCoreV1(
        dsl_family="canonical_delayed_response_rule_v1_candidate",
        relation_identity=view.relation_identity,
        source=view.source,
        source_step_direction=view.source_step_direction,
        target=view.target,
        target_response_direction=view.target_response_direction,
        selected_delay_horizon_seconds=view.selected_delay_horizon_seconds,
        source_threshold_reference=references["source_step_threshold"],
        source_stability_reference=references["source_stability_tolerance"],
        target_scale_reference=references["target_noise_scale"],
        window_constant_references={role: references[role] for role in WINDOW_NUMERIC_ROLES},
        variables=(view.source, view.target),
        runtime_logic_family="missing_expected_delayed_response",
    )
    proposal = wrap_and_verify_core_v1(
        core=core,
        evidence=evidence,
        arm="T0",
        call_number=0,
        prompt_hash=T0_TEMPLATE_HASH,
    )
    proposal_ledger.append(proposal)
    admissible = proposal.validity_result.status == "admissible"
    outcome = ConstructionOutcomeRecordV1(
        relation_identity=evidence.relation.relation_identity,
        arm="T0",
        outcome="accepted_proposal" if admissible else "no_rule",
        accepted_call_index=0 if admissible else None,
        generation_calls_consumed=0,
        verifier_invocations=1,
        verifier_rejected_proposal_count=0 if admissible else 1,
        first_call_admissible=admissible,
        no_rule_reason=None if admissible else "t0_verifier_rejection",
    )
    outcome_ledger.append(outcome)
    return outcome


def project_real_evidence_v1(
    *, private_record: Mapping[str, Any], public_primitive: Mapping[str, Any],
    public_bundle: Mapping[str, Any], public_manifest: Mapping[str, Any],
) -> RealConstructionEvidenceV1:
    private_hash = _verify_self_hash(private_record)
    if public_manifest.get("private_evidence_record_hash") != private_hash:
        raise TASK039E3PreparationError("public/private E1 evidence binding differs")
    bindings_raw = private_record.get("numeric_bindings")
    if not isinstance(bindings_raw, list) or len(bindings_raw) != 11:
        raise TASK039E3PreparationError("E1 private numeric bindings differ")
    bindings = tuple(
        ConstructionNumericBindingV1(
            numeric_role=str(item["numeric_role"]),
            value=item["numeric_value"],
            reference=str(item["numeric_reference"]),
            evidence_identity=str(item["numeric_reference"]),
        )
        for item in bindings_raw
        if item["numeric_role"] != "selected_delay_horizon_seconds"
    )
    if len(bindings) != 10:
        raise TASK039E3PreparationError("E3 construction numeric-role projection differs")
    references = {item.numeric_role: item.reference for item in bindings}
    relation = ConfirmedRelationPrimitiveV1(
        relation_identity=str(private_record["relation_identity"]),
        source=str(private_record["source"]),
        source_step_direction=str(private_record["source_step_direction"]),
        target=str(private_record["target"]),
        target_response_direction=str(private_record["target_response_direction"]),
        selected_delay_horizon_seconds=int(private_record["selected_horizon_seconds"]),
        approved_source_threshold_reference=references["source_step_threshold"],
        approved_source_stability_reference=references["source_stability_tolerance"],
        approved_target_scale_reference=references["target_noise_scale"],
        fit_evidence_reference=str(private_record["d1_fit_evidence_hash"]),
        confirmation_evidence_reference=str(private_record["d2_confirmation_evidence_hash"]),
    )
    if relation.binding_hash != private_record.get("relation_binding_hash"):
        raise TASK039E3PreparationError("private relation binding differs")
    if public_primitive.get("binding_hash") != relation.binding_hash:
        raise TASK039E3PreparationError("public relation primitive differs")
    numeric = ApprovedNumericEvidenceBundleV1(
        relation_binding_hash=relation.binding_hash,
        source_threshold_reference=references["source_step_threshold"],
        source_stability_reference=references["source_stability_tolerance"],
        target_scale_reference=references["target_noise_scale"],
        fit_evidence_reference=relation.fit_evidence_reference,
        confirmation_evidence_reference=relation.confirmation_evidence_reference,
        preregistered_window_constant_references=tuple(
            references[role] for role in WINDOW_NUMERIC_ROLES
        ),
    )
    numeric.assert_matches(relation)
    if public_bundle.get("artifact_hash") != numeric.artifact_hash:
        raise TASK039E3PreparationError("public numeric bundle differs")
    return RealConstructionEvidenceV1(
        relation=relation,
        numeric_evidence=numeric,
        numeric_bindings=bindings,
        approved_evidence_identities=tuple(item.reference for item in bindings),
        private_record_hash=private_hash,
    )


def load_real_evidence_schedule_v1(
    *, private_ledger_path: Path, public_cohort: Mapping[str, Any],
    relation_identities: Sequence[str],
) -> tuple[RealConstructionEvidenceV1, ...]:
    ledger = _load_json(private_ledger_path)
    _verify_self_hash(ledger, E1_PRIVATE_LEDGER_HASH)
    records = ledger.get("records")
    if ledger.get("record_count") != 42 or ledger.get("numeric_binding_count") != 462 or not isinstance(records, list):
        raise TASK039E3PreparationError("E1 private ledger counts differ")
    for record in records:
        _verify_self_hash(record)
    private_by_identity = {record["relation_identity"]: record for record in records}
    primitives = {item["relation_identity"]: item for item in public_cohort["confirmed_relation_primitives"]}
    bundles = {item["relation_binding_hash"]: item for item in public_cohort["approved_numeric_evidence_bundles"]}
    manifests = {item["relation_identity"]: item for item in public_cohort["public_manifest_entries"]}
    projected: list[RealConstructionEvidenceV1] = []
    for identity in relation_identities:
        private = private_by_identity.get(identity)
        primitive = primitives.get(identity)
        manifest = manifests.get(identity)
        if private is None or primitive is None or manifest is None:
            raise TASK039E3PreparationError("E1 relation schedule projection differs")
        bundle = bundles.get(private["relation_binding_hash"])
        if bundle is None:
            raise TASK039E3PreparationError("E1 numeric bundle projection differs")
        projected.append(project_real_evidence_v1(
            private_record=private, public_primitive=primitive,
            public_bundle=bundle, public_manifest=manifest,
        ))
    if len(projected) != 42 or len({item.relation.relation_identity for item in projected}) != 42:
        raise TASK039E3PreparationError("real evidence projection count differs")
    return tuple(projected)


class _DurableJsonl:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._handle = path.open("x", encoding="utf-8", newline="\n")

    def persist(self, document: Mapping[str, Any]) -> None:
        json.dump(document, self._handle, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":"))
        self._handle.write("\n")
        self._handle.flush()
        os.fsync(self._handle.fileno())

    def close(self) -> None:
        self._handle.close()


class DurableProviderCallLedgerV1(ProviderCallLedgerV1):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self._custody = _DurableJsonl(path)

    def append(self, **kwargs: Any) -> Any:
        record = super().append(**kwargs)
        self._custody.persist(record.to_dict())
        return record

    def close(self) -> None:
        self._custody.close()


def _proposal_document(record: ConstructionProposalRecordV1) -> dict[str, Any]:
    validity = record.validity_result
    return {
        "relation_identity": record.relation_identity,
        "arm": record.arm,
        "call_number": record.call_number,
        "project_proposal": thaw_json(record.project_proposal),
        "validity_result": validity.to_dict(),
        "proposal_hash": record.proposal_hash,
        "validity_hash": record.validity_hash,
        "record_hash": record.record_hash,
    }


class DurableConstructionProposalLedgerV1(ConstructionProposalLedgerV1):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self._custody = _DurableJsonl(path)

    def append(self, record: ConstructionProposalRecordV1) -> None:
        super().append(record)
        self._custody.persist(_proposal_document(record))

    def close(self) -> None:
        self._custody.close()


class DurableConstructionOutcomeLedgerV1(ConstructionOutcomeLedgerV1):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self._custody = _DurableJsonl(path)

    def append(self, record: ConstructionOutcomeRecordV1) -> None:
        super().append(record)
        document = record.to_dict()
        document["artifact_hash"] = record.artifact_hash
        self._custody.persist(document)

    def close(self) -> None:
        self._custody.close()


class DurableDirectNumberLedgerV1:
    def __init__(self, path: Path) -> None:
        self.records: list[DirectNumberOutcomeV1] = []
        self._custody = _DurableJsonl(path)

    def append(self, record: DirectNumberOutcomeV1) -> None:
        if any(item.relation_identity == record.relation_identity for item in self.records):
            raise TASK039E3PreparationError("duplicate direct-number relation")
        document = {
            "relation_identity": record.relation_identity,
            "parse_status": record.parse_status,
            "normalized_absolute_errors": thaw_json(record.normalized_absolute_errors),
            "missing_number": record.missing_number,
            "nonfinite_or_parse_failure": record.nonfinite_or_parse_failure,
            "sign_domain_violation_roles": list(record.sign_domain_violation_roles),
            "generation_calls_consumed": record.generation_calls_consumed,
            "validity_authority": record.validity_authority,
            "runtime_authority": record.runtime_authority,
        }
        document["record_hash"] = stable_hash_v1(document)
        self.records.append(record)
        self._custody.persist(document)

    @property
    def ledger_hash(self) -> str:
        return stable_hash_v1({
            "artifact_type": "task039e3_direct_number_ledger_v1",
            "relation_identities": [item.relation_identity for item in self.records],
            "record_count": len(self.records),
        })

    def close(self) -> None:
        self._custody.close()


def _final_private_ledger(path: Path, *, artifact_type: str, records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    content = {
        "schema_version": "1.0.0",
        "artifact_type": artifact_type,
        "task_id": TASK_ID,
        "record_count": len(records),
        "records": list(records),
        "storage_boundary": "outside_git",
        "raw_hai_included": False,
        "credential_included": False,
        "chain_of_thought_included": False,
        "runtime_authority": False,
    }
    document = _with_hash(content)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return document


def _direct_summary(
    raw: Mapping[str, Any], outcomes: Sequence[DirectNumberOutcomeV1]
) -> dict[str, Any]:
    role_values = raw["normalized_absolute_error_by_role"]
    by_role: dict[str, Any] = {}
    for role in CALIBRATED_NUMERIC_ROLES:
        values = [float(value) for value in role_values[role]]
        by_role[role] = {
            "count": len(values),
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
            "mean": statistics.fmean(values) if values else None,
            "median": statistics.median(values) if values else None,
            "missing_number_count": sum(item.missing_number for item in outcomes),
            "missing_number_rate": sum(item.missing_number for item in outcomes) / 42,
            "nonfinite_or_parse_failure_count": sum(
                item.nonfinite_or_parse_failure for item in outcomes
            ),
            "nonfinite_or_parse_failure_rate": sum(
                item.nonfinite_or_parse_failure for item in outcomes
            ) / 42,
            "sign_domain_violation_count": sum(
                role in item.sign_domain_violation_roles for item in outcomes
            ),
            "sign_domain_violation_rate": sum(
                role in item.sign_domain_violation_roles for item in outcomes
            ) / 42,
        }
    return {
        "normalized_absolute_error_summary_by_role": by_role,
        "missing_number_rate": raw["missing_number_rate"],
        "nonfinite_or_parse_failure_rate": raw["nonfinite_or_parse_failure_rate"],
        "sign_domain_violation_rate": raw["sign_domain_violation_rate"],
        "validity_authority": False,
        "runtime_authority": False,
    }


def run_authorized_scientific_execution_v1(
    *, repository_root: Path, execution_commit: str, e1_private_root: Path,
    e3_private_root: Path, transport: LiveOpenAIChatCompletionsTransportV1,
    preflight: Mapping[str, Any], source_hashes: Mapping[str, str],
    progress: Any = print,
) -> dict[str, dict[str, Any]]:
    provider_ledger = DurableProviderCallLedgerV1(e3_private_root / "provider_calls.jsonl")
    proposal_ledger = DurableConstructionProposalLedgerV1(e3_private_root / "proposals_validity.jsonl")
    outcome_ledger = DurableConstructionOutcomeLedgerV1(e3_private_root / "construction_outcomes.jsonl")
    direct_ledger = DurableDirectNumberLedgerV1(e3_private_root / "direct_number.jsonl")
    capability_slot = ProviderCallSlotV1(
        None, stable_hash_v1({"fixture": "SYNTHETIC_CAPABILITY_CHECK"}),
        "CAPABILITY", 1, False,
    )
    try:
        capability_result = execute_mock_provider_slot_v1(
            slot=capability_slot,
            request=build_capability_probe_request_v1(),
            transport=transport,
            ledger=provider_ledger,
            parse_kind="capability",
        )
        parsed_capability = capability_result.parsed_capability
        if parsed_capability is None or parsed_capability.status != "pass":
            capability = _with_hash({
                "schema_version": "1.0.0", "artifact_type": "task039e3_capability_gate_receipt_v1",
                "task_id": TASK_ID, "status": "blocked_task039e3_capability_gate",
                "execution_code_commit": execution_commit, "exact_model": EXACT_MODEL,
                "response_id": capability_result.record.provider_response_metadata.get("response_id"),
                "returned_model": capability_result.record.provider_response_metadata.get("model"),
                "finish_reason": capability_result.record.provider_response_metadata.get("finish_reason"),
                "structured_parse_status": parsed_capability.status if parsed_capability else "missing",
                "transport_attempts": len(capability_result.record.transport_attempts),
                "usage": capability_result.record.provider_response_metadata.get("token_usage"),
                "system_fingerprint": transport.attempt_custody[-1].system_fingerprint if transport.attempt_custody else None,
                "passed": False, "scientific_calls": 0,
                "configuration_modified_after_probe": False,
            })
            return {"capability": capability, "blocked": {"status": "blocked_task039e3_capability_gate"}}
        capability = _with_hash({
            "schema_version": "1.0.0", "artifact_type": "task039e3_capability_gate_receipt_v1",
            "task_id": TASK_ID, "status": "passed_task039e3_capability_gate",
            "execution_code_commit": execution_commit, "exact_model": EXACT_MODEL,
            "response_id": capability_result.record.provider_response_metadata.get("response_id"),
            "returned_model": capability_result.record.provider_response_metadata.get("model"),
            "finish_reason": capability_result.record.provider_response_metadata.get("finish_reason"),
            "structured_parse_status": parsed_capability.status,
            "transport_attempts": len(capability_result.record.transport_attempts),
            "usage": capability_result.record.provider_response_metadata.get("token_usage"),
            "system_fingerprint": transport.attempt_custody[-1].system_fingerprint if transport.attempt_custody else None,
            "passed": True, "scientific_calls_before_probe": 0,
            "configuration_modified_after_probe": False,
        })
        progress("capability completed passed")
        schedule = preflight["schedule"]["relation_identities"]
        evidence_records = load_real_evidence_schedule_v1(
            private_ledger_path=e1_private_root / PRIVATE_LEDGER_FILE,
            public_cohort=preflight["cohort"], relation_identities=schedule,
        )
        for index, evidence in enumerate(evidence_records):
            run_real_t0_v1(evidence=evidence, proposal_ledger=proposal_ledger, outcome_ledger=outcome_ledger)
            run_t1_v1(
                relation_schedule_index=index, evidence=evidence, transport=transport,
                call_ledger=provider_ledger, proposal_ledger=proposal_ledger,
                outcome_ledger=outcome_ledger,
            )
            run_t1b_v1(
                relation_schedule_index=index, evidence=evidence, transport=transport,
                call_ledger=provider_ledger, proposal_ledger=proposal_ledger,
                outcome_ledger=outcome_ledger,
            )
            run_t2_v1(
                relation_schedule_index=index, evidence=evidence, transport=transport,
                call_ledger=provider_ledger, proposal_ledger=proposal_ledger,
                outcome_ledger=outcome_ledger,
                retrieval_identity=evidence.approved_evidence_identities[0],
            )
            direct_ledger.append(run_direct_number_v1(
                relation_schedule_index=index, evidence=evidence,
                transport=transport, call_ledger=provider_ledger,
            ))
            progress(f"relation {index + 1:02d}/42 completed scientific calls {sum(item.slot.scientific for item in provider_ledger.records)}")
        outcome_ledger.assert_complete_future_cohort(schedule)
        if len(direct_ledger.records) != 42:
            raise TASK039E3PreparationError("direct-number relation count differs")
        scientific_records = [item for item in provider_ledger.records if item.slot.scientific]
        counts = {
            arm: sum(item.slot.arm == arm for item in scientific_records)
            for arm in ("T1", "T1-B", "T2", "T1-DIRECT-NUMBER")
        }
        if counts["T1"] != 42 or counts["T1-B"] != 126 or counts["T1-DIRECT-NUMBER"] != 42 or not 42 <= counts["T2"] <= 126:
            raise TASK039E3PreparationError("scientific call accounting differs")
        if len(scientific_records) != 210 + counts["T2"]:
            raise TASK039E3PreparationError("total scientific call accounting differs")
        if compute_scientific_source_hashes_v1(repository_root) != dict(source_hashes):
            raise TASK039E3PreparationError("scientific source changed after provider contact")

        provider_records = [item.to_dict() for item in provider_ledger.records]
        proposal_records = [_proposal_document(item) for item in proposal_ledger.records]
        outcome_records = [dict(item.to_dict(), artifact_hash=item.artifact_hash) for item in outcome_ledger.records]
        direct_records = []
        for item in direct_ledger.records:
            content = {
                "relation_identity": item.relation_identity, "parse_status": item.parse_status,
                "normalized_absolute_errors": thaw_json(item.normalized_absolute_errors),
                "missing_number": item.missing_number,
                "nonfinite_or_parse_failure": item.nonfinite_or_parse_failure,
                "sign_domain_violation_roles": list(item.sign_domain_violation_roles),
            }
            direct_records.append(dict(content, record_hash=stable_hash_v1(content)))
        provider_private = _final_private_ledger(
            e3_private_root / "TASK039E3_PROVIDER_CALL_LEDGER.json",
            artifact_type="task039e3_provider_call_ledger_v1", records=provider_records,
        )
        proposal_private = _final_private_ledger(
            e3_private_root / "TASK039E3_PROPOSAL_VALIDITY_LEDGER.json",
            artifact_type="task039e3_proposal_validity_ledger_v1", records=proposal_records,
        )
        outcome_private = _final_private_ledger(
            e3_private_root / "TASK039E3_CONSTRUCTION_OUTCOME_LEDGER.json",
            artifact_type="task039e3_construction_outcome_ledger_v1", records=outcome_records,
        )
        direct_private = _final_private_ledger(
            e3_private_root / "TASK039E3_DIRECT_NUMBER_LEDGER.json",
            artifact_type="task039e3_direct_number_ledger_v1", records=direct_records,
        )
        main_metrics = aggregate_construction_metrics_v1(outcome_ledger.records)
        direct_raw = aggregate_direct_number_metrics_v1(direct_ledger.records)
        direct_metrics_content = {
            "schema_version": "1.0.0", "artifact_type": "task039e3_direct_number_metrics_v1",
            "task_id": TASK_ID, "relation_count": 42,
            **_direct_summary(direct_raw, direct_ledger.records),
            "labels_used": False, "winner_selected": False,
        }
        direct_metrics = _with_hash(direct_metrics_content)
        metrics_core = PublicConstructionMetricsV1(
            provider_call_ledger_hash=provider_private["artifact_hash"],
            proposal_ledger_hash=proposal_private["artifact_hash"],
            outcome_ledger_hash=outcome_private["artifact_hash"],
            main_metrics=main_metrics,
            direct_number_metrics=_direct_summary(direct_raw, direct_ledger.records),
            scientific_slot_count=len(scientific_records),
        ).to_dict()
        construction_metrics = _with_hash({
            "schema_version": "1.0.0", "artifact_type": "task039e3_construction_metrics_v1",
            "task_id": TASK_ID, "status": STATUS,
            "main_metrics": main_metrics,
            "provider_call_ledger_hash": provider_private["artifact_hash"],
            "proposal_validity_ledger_hash": proposal_private["artifact_hash"],
            "outcome_ledger_hash": outcome_private["artifact_hash"],
            "scientific_slot_count": len(scientific_records),
            "frozen_metrics_contract_hash": metrics_core["artifact_hash"],
            "winner_selected": False,
        })
        transport_attempts = len(transport.attempt_custody)
        transport_retries = transport_attempts - len(provider_ledger.records)
        custody = _with_hash({
            "schema_version": "1.0.0", "artifact_type": "task039e3_provider_custody_binding_v1",
            "task_id": TASK_ID, "provider": "openai", "model": EXACT_MODEL,
            "provider_call_ledger_hash": provider_private["artifact_hash"],
            "record_count": len(provider_records), "scientific_record_count": len(scientific_records),
            "transport_attempt_count": transport_attempts, "transport_retry_count": transport_retries,
            "hash_chain_verified": all(
                record["previous_record_hash"] == (provider_records[i - 1]["record_hash"] if i else None)
                for i, record in enumerate(provider_records)
            ),
            "private_storage": "outside_git", "individual_proposals_public": False,
        })
        private_bindings = _with_hash({
            "schema_version": "1.0.0", "artifact_type": "task039e3_private_ledger_bindings_v1",
            "task_id": TASK_ID,
            "provider_call_ledger_hash": provider_private["artifact_hash"],
            "proposal_validity_ledger_hash": proposal_private["artifact_hash"],
            "outcome_ledger_hash": outcome_private["artifact_hash"],
            "direct_number_ledger_hash": direct_private["artifact_hash"],
            "provider_records": len(provider_records), "proposal_records": len(proposal_records),
            "outcome_records": len(outcome_records), "direct_number_records": len(direct_records),
            "private_contents_public": False, "storage_boundary": "outside_git",
        })
        access = _with_hash({
            "schema_version": "1.0.0", "artifact_type": "task039e3_data_access_audit_v1",
            "task_id": TASK_ID, "e1_private_ledger_accessed": True,
            "e1_private_ledger_modified": False, "hai_accessed": False,
            "train1_train2_train3_train4_accessed": False,
            "test_labels_attacks_accessed": False,
            "provider_contacted": True, "credential_read_by_live_runner": True,
            "credential_persisted": False, "individual_proposals_public": False,
            "raw_private_evidence_public": False, "prohibited_access_count": 0,
            "rule_v2_authorized": False, "runtime_authority": False,
        })
        summary = _with_hash({
            "schema_version": "1.0.0", "artifact_type": "task039e3_execution_summary_v1",
            "task_id": TASK_ID, "status": STATUS, "execution_code_commit": execution_commit,
            "relations_completed": 42, "relations_skipped": 0,
            "t0_outcomes": 42, "t1_outcomes": 42, "t1b_outcomes": 42, "t2_outcomes": 42,
            "direct_number_results": 42, "scientific_calls": len(scientific_records),
            "scientific_call_counts": counts, "transport_attempts": transport_attempts,
            "transport_retries": transport_retries, "scientific_retries": 0,
            "cross_arm_leakage": False, "winner_selected": False,
            "rule_v2_authorized": False, "runtime_authority": False,
        })
        receipt = _with_hash({
            "schema_version": "1.0.0", "artifact_type": "task039e3_execution_receipt_v1",
            "task_id": TASK_ID, "status": STATUS, "execution_code_commit": execution_commit,
            "e3_authorization_hash": E3_AUTHORIZATION_HASH,
            "e0_protocol_bundle_hash": E0_PROTOCOL_BUNDLE_HASH,
            "e1_materialization_result_hash": E1_MATERIALIZATION_RESULT_HASH,
            "e1_construction_cohort_hash": E1_CONSTRUCTION_EVIDENCE_COHORT_HASH,
            "e1_private_ledger_hash": E1_PRIVATE_LEDGER_HASH,
            "e2_protocol_bundle_hash": E2_PROTOCOL_BUNDLE_HASH,
            "execution_schedule_hash": EXECUTION_SCHEDULE_HASH,
            "capability_receipt_hash": capability["artifact_hash"],
            "provider_custody_binding_hash": custody["artifact_hash"],
            "private_ledger_bindings_hash": private_bindings["artifact_hash"],
            "construction_metrics_hash": construction_metrics["artifact_hash"],
            "direct_number_metrics_hash": direct_metrics["artifact_hash"],
            "execution_summary_hash": summary["artifact_hash"],
            "data_access_audit_hash": access["artifact_hash"],
            "scientific_source_hashes": dict(source_hashes),
            "configuration_changed_after_capability_probe": False,
            "scientific_source_changed_after_provider_contact": False,
            "individual_proposals_public": False, "rule_v2_authorized": False,
            "runtime_authority": False, "utility_evaluation_authorized": False,
        })
        return {
            "capability": capability, "custody": custody, "private_bindings": private_bindings,
            "construction_metrics": construction_metrics, "direct_metrics": direct_metrics,
            "summary": summary, "access": access, "receipt": receipt,
        }
    except ScientificRunAbortV1 as exc:
        failure = _with_hash({
            "schema_version": "1.0.0", "artifact_type": "task039e3_execution_failure_receipt_v1",
            "task_id": TASK_ID, "status": "failed_task039e3_scientific_execution",
            "execution_code_commit": execution_commit,
            "capability_state": "passed" if len(provider_ledger.records) > 1 else "not_passed",
            "completed_scientific_slot_count": sum(item.slot.scientific for item in provider_ledger.records),
            "provider_call_ledger_head_hash": provider_ledger.records[-1].record_hash if provider_ledger.records else None,
            "last_completed_slot": provider_ledger.records[-1].slot.to_dict() if provider_ledger.records else None,
            "failure_classification": (
                "failed_task039e3_model_identity_integrity"
                if transport.attempt_custody and transport.attempt_custody[-1].outcome == "model_identity_integrity"
                else "failed_task039e3_scientific_execution"
            ),
            "underlying_failure_receipt_hash": exc.receipt.artifact_hash,
            "configuration_unchanged": True, "automatic_resume_authorized": False,
        })
        return {"failure": failure}
    finally:
        provider_ledger.close()
        proposal_ledger.close()
        outcome_ledger.close()
        direct_ledger.close()


def write_public_artifacts_v1(repository_root: Path, artifacts: Mapping[str, Mapping[str, Any]]) -> None:
    names = {
        "capability": "TASK-039E3_CAPABILITY_GATE.json",
        "custody": "TASK-039E3_PROVIDER_CUSTODY_BINDING.json",
        "private_bindings": "TASK-039E3_PRIVATE_LEDGER_BINDINGS.json",
        "construction_metrics": "TASK-039E3_CONSTRUCTION_METRICS.json",
        "direct_metrics": "TASK-039E3_DIRECT_NUMBER_METRICS.json",
        "summary": "TASK-039E3_EXECUTION_SUMMARY.json",
        "access": "TASK-039E3_DATA_ACCESS_AUDIT.json",
        "receipt": "TASK-039E3_EXECUTION_RECEIPT.json",
        "failure": "TASK-039E3_EXECUTION_FAILURE.json",
    }
    report_root = repository_root / "docs" / "task_reports"
    for key, document in artifacts.items():
        if key in {"blocked"}:
            continue
        filename = names.get(key)
        if filename is None:
            continue
        with (report_root / filename).open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, ensure_ascii=True, allow_nan=False, indent=2, sort_keys=True)
            handle.write("\n")


__all__ = [
    "BRANCH", "PREP_COMMIT", "RealConstructionEvidenceV1",
    "compute_scientific_source_hashes_v1", "load_real_evidence_schedule_v1",
    "project_real_evidence_v1", "run_authorized_scientific_execution_v1",
    "run_real_t0_v1",
    "validate_git_execution_state_v1", "validate_private_roots_v1",
    "validate_public_preflight_v1", "write_public_artifacts_v1",
]
