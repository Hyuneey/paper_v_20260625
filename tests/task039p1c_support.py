"""Synthetic canonical-context factories for TASK-039P1C tests."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from paperworks.contracts.artifact_hashing import with_computed_artifact_hash
from paperworks.contracts.canonical_collection_v1 import (
    CanonicalBindingPolicyV1,
    CanonicalContextBuildResultV1,
    CanonicalContextMappingsV1,
    build_canonical_delayed_response_context_v1,
    canonical_graph_edge_sha256_v1,
)
from paperworks.contracts.graph_v1 import (
    CandidateGraphV1,
    load_candidate_graph,
)
from paperworks.contracts.normal_evidence_binding_v1 import (
    derive_normal_reference_id_v1,
)
from paperworks.contracts.parameter_v1 import (
    CalibrationParameterV1,
    parse_calibration_parameter,
)
from paperworks.contracts.rule_v1 import (
    DelayedResponseRuleV1,
    parse_delayed_response_rule,
)
from paperworks.contracts.verifier_v1 import (
    DelayedResponseVerifierPolicyV1,
    RuleVerificationOutcomeV1,
    verify_delayed_response_rule,
)
from paperworks.data.contracts_v2 import (
    DataViewManifestV2,
    DatasetManifestV2,
    SplitManifestV2,
    SplitRoleV2,
)
from paperworks.v6.normal_evidence_v1 import (
    CalibrationParameterReferenceV1,
    CalibrationParameterRoleV1,
    DistributionSummaryV1,
    NormalRelationEvidenceV1,
)

from task039p1a_support import (
    data_view_manifest_v2,
    dataset_manifest_v2,
    split_manifest_v2,
)
from task039p1b_support import (
    creation_metadata,
    digest,
    supported_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "fixtures/task032c/graph_delayed_response.json"
RULE_PATH = ROOT / "fixtures/task032d/rule_candidate.json"
POLICY_PATH = ROOT / "fixtures/task032d/verifier_policy.json"
PARAMETER_PATHS = (
    ROOT / "fixtures/task032d/parameter_lag.json",
    ROOT / "fixtures/task032d/parameter_tolerance.json",
    ROOT / "fixtures/task032d/parameter_duration.json",
    ROOT / "fixtures/task032d/parameter_support.json",
    ROOT / "fixtures/task032d/parameter_severity.json",
)
PROCESS_SCOPE = ("P1",)
SUBSYSTEM = "synthetic_subsystem"
REGIME = "REGIME-SYNTHETIC-032C"
CONDITION_ID = "COND-SYNTHETIC-032D"
EDGE_ID = "EDGE-ACTUATORA-SENSORB"


@dataclass(frozen=True)
class CanonicalFixtureV1:
    dataset: DatasetManifestV2
    view: DataViewManifestV2
    split: SplitManifestV2
    graph: CandidateGraphV1
    normal_evidence: NormalRelationEvidenceV1
    parameters: tuple[CalibrationParameterV1, ...]
    mappings: CanonicalContextMappingsV1
    build_result: CanonicalContextBuildResultV1
    candidate_rule: DelayedResponseRuleV1
    policy: DelayedResponseVerifierPolicyV1

    @property
    def collection(self):
        assert self.build_result.collection is not None
        return self.build_result.collection


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _dataset_context(
    graph: CandidateGraphV1,
) -> tuple[DatasetManifestV2, DataViewManifestV2, SplitManifestV2]:
    base_dataset = dataset_manifest_v2()
    dataset = replace(
        base_dataset,
        dataset_version_or_edition=graph.dataset_version,
        available_process_ids=PROCESS_SCOPE,
        files=tuple(
            replace(
                item,
                process_ids=(
                    PROCESS_SCOPE if item.process_ids is not None else None
                ),
            )
            for item in base_dataset.files
        ),
    )
    view = replace(
        data_view_manifest_v2(process_scope=PROCESS_SCOPE),
        source_dataset_manifest_id=dataset.manifest_id,
    )
    split = replace(
        split_manifest_v2(SplitRoleV2.NORMAL_RELATION_CALIBRATION),
        dataset_manifest_id=dataset.manifest_id,
        data_view_id=view.view_id,
        process_scope=PROCESS_SCOPE,
    )
    return dataset, view, split


def _normal_reference_id(
    dataset: DatasetManifestV2,
    view: DataViewManifestV2,
    split: SplitManifestV2,
) -> str:
    return derive_normal_reference_id_v1(
        source_normal_reference_hashes=(digest("matched-normal-v6"),),
        dataset_manifest_id=dataset.manifest_id,
        data_view_id=view.view_id,
        split_manifest_id=split.split_id,
        dataset_version=dataset.dataset_version_or_edition,
        process_scope=PROCESS_SCOPE,
        subsystem=SUBSYSTEM,
        operating_regime_id=REGIME,
        matching_policy_id="MATCH-V6-SYNTHETIC",
        matching_policy_version="1.0.0",
        matching_method="exact_regime_then_lexicographic",
    )


def _parameters(normal_reference_id: str) -> tuple[CalibrationParameterV1, ...]:
    result: list[CalibrationParameterV1] = []
    for path in PARAMETER_PATHS:
        document = _read_json(path)
        document["normal_reference_refs"] = [normal_reference_id]
        document = with_computed_artifact_hash(document)
        result.append(parse_calibration_parameter(document))
    return tuple(result)


def build_canonical_fixture() -> CanonicalFixtureV1:
    graph = load_candidate_graph(GRAPH_PATH)
    dataset, view, split = _dataset_context(graph)
    normal_reference_id = _normal_reference_id(dataset, view, split)
    parameters = _parameters(normal_reference_id)
    parameters_by_role = {
        item.parameter_role: item for item in parameters
    }
    edge_hash = canonical_graph_edge_sha256_v1(graph, EDGE_ID)
    condition_hash = digest("regime-condition-v6")
    normal_evidence = supported_evidence(
        dataset_manifest_id=dataset.manifest_id,
        data_view_id=view.view_id,
        split_manifest_id=split.split_id,
        process_scope=PROCESS_SCOPE,
        source_variable="ActuatorA",
        target_variable="SensorB",
        source_metadata_ref=graph.nodes[0].metadata_provenance.artifact_hash,
        target_metadata_ref=graph.nodes[1].metadata_provenance.artifact_hash,
        candidate_universe_ref=digest("candidate-universe-v6"),
        candidate_edge_refs=(edge_hash,),
        operating_regime_id=REGIME,
        operating_regime_condition_refs=(condition_hash,),
        lag_summary=DistributionSummaryV1(
            count=3,
            minimum=1.0,
            p50=2.0,
            p95=4.8,
            maximum=5.0,
            unit="seconds",
            method="synthetic_quantiles",
            value_semantics="lag",
        ),
        matched_normal_reference_refs=(digest("matched-normal-v6"),),
        calibration_parameter_refs=(
            CalibrationParameterReferenceV1(
                CalibrationParameterRoleV1.LAG,
                parameters_by_role["lag_maximum"].artifact_hash,
            ),
            CalibrationParameterReferenceV1(
                CalibrationParameterRoleV1.TOLERANCE,
                parameters_by_role["tolerance"].artifact_hash,
            ),
        ),
    )
    mappings = CanonicalContextMappingsV1(
        edge_ids_by_source_hash={edge_hash: EDGE_ID},
        condition_ids_by_source_hash={condition_hash: CONDITION_ID},
        condition_artifact_hashes_by_id={CONDITION_ID: condition_hash},
        parameter_ids_by_source_hash={
            parameters_by_role["lag_maximum"].artifact_hash: (
                parameters_by_role["lag_maximum"].parameter_id
            ),
            parameters_by_role["tolerance"].artifact_hash: (
                parameters_by_role["tolerance"].parameter_id
            ),
        },
        required_parameter_ids_by_role={
            "persistence_duration": (
                parameters_by_role["persistence_duration"].parameter_id
            ),
            "minimum_support": (
                parameters_by_role["minimum_support"].parameter_id
            ),
            "severity_boundary": (
                parameters_by_role["severity_boundary"].parameter_id
            ),
        },
    )
    build_result = build_canonical_delayed_response_context_v1(
        dataset_manifest=dataset,
        data_view=view,
        split_manifest=split,
        normal_evidence=normal_evidence,
        graph=graph,
        parameters=parameters,
        mappings=mappings,
        subsystem=SUBSYSTEM,
        binding_policy=CanonicalBindingPolicyV1(
            matching_policy_id="MATCH-V6-SYNTHETIC",
            matching_policy_version="1.0.0",
            matching_method="exact_regime_then_lexicographic",
            deterministic_tie_breaking=True,
            selection_policy_id="SELECT-V6-SYNTHETIC",
            selection_policy_version="1.0.0",
            selection_pre_registered=True,
        ),
        creation_metadata=creation_metadata(),
    )
    if build_result.status != "created":
        raise AssertionError(
            f"synthetic canonical context failed: {build_result.to_dict()}"
        )
    collection = build_result.collection
    assert collection is not None
    candidate_document = _read_json(RULE_PATH)
    candidate_document["normal_reference_refs"] = [
        collection.normal_reference_binding.normal_reference_id
    ]
    candidate_document["evidence_refs"] = [
        collection.evidence.evidence_id
    ]
    candidate_rule = parse_delayed_response_rule(candidate_document)
    policy = DelayedResponseVerifierPolicyV1.from_dict(
        _read_json(POLICY_PATH)
    )
    return CanonicalFixtureV1(
        dataset=dataset,
        view=view,
        split=split,
        graph=graph,
        normal_evidence=normal_evidence,
        parameters=parameters,
        mappings=mappings,
        build_result=build_result,
        candidate_rule=candidate_rule,
        policy=policy,
    )


def verify_canonical_fixture(
    fixture: CanonicalFixtureV1 | None = None,
) -> tuple[CanonicalFixtureV1, RuleVerificationOutcomeV1]:
    current = fixture or build_canonical_fixture()
    outcome = verify_delayed_response_rule(
        current.candidate_rule,
        current.collection,
        policy=current.policy,
    )
    return current, outcome
