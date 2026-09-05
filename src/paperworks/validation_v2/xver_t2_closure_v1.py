"""Capability-gated SCI-02B binding for frozen external T2 outputs."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from .exp03b_contract_v1 import digest, require
from .exp03b_custody_v1 import publish, seal
from .exp03b_execution_v2 import VerifiedAdmission
from .exp03b_binder_v2 import FIXED_ALIAS, POLICY, fixed_roles, validate_roles
from .exp03b_numeric_v1 import pooled_roles, roles_from_summary
from .exp03b_evaluation import GuardRuleInput


_ISSUER = object()


class ExternalT2PostInductionCapabilityV1:
    __slots__ = ("files", "reference_hash", "members", "admission_hashes", "version")

    def __init__(self, token, *, files, reference_hash, members, admission_hashes, version):
        require(token is _ISSUER, "T2_CLOSURE_FACTORY_REQUIRED")
        self.files = tuple(files)
        self.reference_hash = reference_hash
        self.members = frozenset(members)
        self.admission_hashes = frozenset(admission_hashes)
        self.version = version

    def replay(self) -> None:
        require(all(sha256(path.read_bytes()).hexdigest() == expected for path, expected in self.files), "T2_CLOSURE_BYTES_CHANGED")


def authorize_t2_binding(
    runroot: Path,
    version_directory: Path,
    *,
    version: str,
    candidate_ids: tuple[str, ...],
    execution_hash: str,
    reference: dict,
    evaluation: dict,
    read_document,
) -> ExternalT2PostInductionCapabilityV1:
    """Require global provider closure and frozen semantic evaluation."""
    require(version in ("22.04", "21.03") and len(candidate_ids) == len(set(candidate_ids)) > 0, "T2_COHORT")
    files = []

    def read(path: Path) -> dict:
        value = read_document(path)
        files.append((path, sha256(path.read_bytes()).hexdigest()))
        return value

    closed = read(runroot / "PROVIDER_PHASE_CLOSED.json")
    combined = read(runroot / "ALL_XVER_PROVIDER_OUTPUTS_FROZEN.json")
    bundle = read(version_directory / "PROVIDER_OUTPUTS_FROZEN.json")
    require(
        closed["provider_calls_allowed"] is False
        and closed["output_bundle_hash"] == combined["self_hash"]
        and closed["execution_freeze_hash"] == execution_hash
        and combined["version_bundles"][version] == bundle["self_hash"],
        "CLOSED_PROVIDER_PHASE_BINDING",
    )
    require(
        bundle["candidate_ids"] == list(candidate_ids)
        and bundle["candidate_count"] == len(candidate_ids)
        and bundle["train2_admissions_frozen"] is True,
        "T2_SLOT_CLOSURE",
    )
    rows = []
    for candidate_id in candidate_ids:
        row = read(version_directory / "outputs" / f"{candidate_id}.json")
        require(row["version"] == version and row["candidate_id"] == candidate_id, "OUTPUT_VERSION_IDENTITY")
        rows.append(row)
    require([row["self_hash"] for row in rows] == bundle["terminal_hashes"], "T2_TERMINAL_HASH_CLOSURE")
    require(
        evaluation["version"] == version
        and evaluation["execution_hash"] == execution_hash
        and evaluation["provider_bundle_hash"] == bundle["self_hash"]
        and evaluation["reference_hash"] == reference["self_hash"],
        "T2_EVALUATION_BINDING",
    )
    files.append((version_directory / "SEMANTIC_EVALUATION_FROZEN.json", sha256((version_directory / "SEMANTIC_EVALUATION_FROZEN.json").read_bytes()).hexdigest()))
    reference_records = {row["candidate_id"]: row["relations"] for row in reference["records"]}
    require(set(reference_records) == set(candidate_ids), "REFERENCE_COHORT_BINDING")
    members = (
        (candidate_id, relation["source_direction"], relation["target_direction"], relation["horizon_seconds"])
        for candidate_id, relations in reference_records.items() for relation in relations
    )
    admission_hashes = [row["admission_hash"] for row in rows if row["admission_hash"] is not None]
    capability = ExternalT2PostInductionCapabilityV1(
        _ISSUER, files=files, reference_hash=reference["self_hash"], members=members,
        admission_hashes=admission_hashes, version=version,
    )
    capability.replay()
    publish(version_directory / "NUMERIC_BINDING_STARTED.json", seal({
        "version": version, "policy": POLICY, "provider_bundle_hash": bundle["self_hash"],
        "semantic_evaluation_hash": evaluation["self_hash"], "provider_calls_allowed": False,
    }))
    return capability


def bind_t2_rule(
    capability: ExternalT2PostInductionCapabilityV1,
    admission: VerifiedAdmission,
    index: int,
    *,
    pair: tuple[str, str],
    train1_summary: tuple[dict, dict],
    train2_summary: tuple[dict, dict],
) -> GuardRuleInput:
    require(type(capability) is ExternalT2PostInductionCapabilityV1, "POST_SEMANTIC_EVALUATION_REQUIRED")
    capability.replay()
    require(type(admission) is VerifiedAdmission, "VERIFIED_ADMISSION_REQUIRED")
    admission.replay()
    require(admission.receipt["self_hash"] in capability.admission_hashes, "T2_ADMISSION_CLOSURE")
    require(admission.candidate_id == "EXP03B-CAND-" + digest({"source": pair[0], "target": pair[1]})[:20], "PAIR_BINDING")
    semantic = admission.proposal.rules[index].semantic
    require(
        (admission.candidate_id, semantic.source_direction, semantic.target_direction, semantic.horizon_seconds)
        in capability.members,
        "NORMAL_CONFIRMATION_REQUIRED",
    )
    tables = []
    for source_summary, target_summary in (train1_summary, train2_summary):
        selected = fixed_roles(source_summary, target_summary, semantic.source_direction)
        common = roles_from_summary(source_summary, target_summary, semantic.source_direction, "NUM-000")
        validate_roles(common)
        tables.append((selected, common))
    selected = pooled_roles(tables[0][0], tables[1][0], train2_status="ACCEPTED")
    common = pooled_roles(tables[0][1], tables[1][1], train2_status="ACCEPTED")
    return GuardRuleInput(
        admission.candidate_id, *pair, semantic, FIXED_ALIAS,
        tuple(sorted(selected.items())), tuple(sorted(common.items())),
        admission.receipt["self_hash"], capability.reference_hash,
        digest(tables[0]), digest(tables[1]),
    )
