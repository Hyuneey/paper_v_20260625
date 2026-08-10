"""Deterministic metadata-only discovery for the TASK-039C META arm.

This module consumes only the frozen C0 identity universe, a reviewed
metadata-evidence declaration, the pinned official HAI technical manual
identity, and the pinned official P1 physical graph.  It has no API that
accepts time-series feature values.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha1, sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from paperworks.v6.candidate_discovery_protocol_v1 import (
    CandidateDiscoveryProtocolBundleV1,
    MetadataRankInputV1,
    derive_candidate_budget_views_v1,
    eligible_pair_records_v1,
    rank_metadata_candidates_v1,
)
from paperworks.v6.common import (
    canonical_json_v1,
    parse_iso_datetime,
    reject_unknown_fields,
    require_sha256,
    stable_hash_v1,
)


TASK_ID = "TASK-039C-META"
ARM_ID = "META"
PASSING_STATUS = "passed_task039c_metadata_candidate_discovery"
SCHEMA_VERSION = "1.0.0"

C0_PROTOCOL_BUNDLE_HASH = (
    "41aab751d6bbbaadc72a95ef3289ea6440c26659fb38f640bf17fb0688836dff"
)
METADATA_POLICY_HASH = (
    "5fc43a043f0e75a56cab855a466a97a394fc1a6fdb67461b17696034547e4af3"
)
SOURCE_IDENTITY_LIST_HASH = (
    "0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234"
)
TARGET_IDENTITY_LIST_HASH = (
    "063037980aae4f0eaf45fbebb59f2aa0a924fbad583f3818107a793dfe7248e7"
)
PAIR_UNIVERSE_HASH = (
    "fc072d3e18ce4623972c2cb64f6266727092ecae03fdb0f0dd929d705e1d8557"
)
OFFICIAL_SNAPSHOT_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"
OFFICIAL_MANUAL_SHA256 = (
    "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556"
)
OFFICIAL_MANUAL_GIT_BLOB = "18cb88514176e1c641f584cf24ac8e9559432b38"
OFFICIAL_GRAPH_SHA256 = (
    "eca648d73c0444a35294608c2a1067256d7b32547257153226fece2de3febd07"
)
OFFICIAL_GRAPH_GIT_BLOB = "c47dc78fdef88ec1f5973280e179707cca36231b"
OFFICIAL_GRAPH_CLAIM_BOUNDARY = "weak_relation_reference_not_causal_truth"

EVIDENCE_TIERS = (
    "M1_EXPLICIT",
    "M2_GRAPH_ADJACENT",
    "M3_SUBSYSTEM_SUPPORTED",
    "UNSUPPORTED",
)
SUMMARY_VOCABULARY = frozenset(
    {
        "manual_explicit_control_chain",
        "manual_explicit_control_chain_and_graph_adjacent",
        "graph_adjacent_with_reviewed_semantic_mapping",
        "reviewed_same_control_subsystem_no_direct_graph_edge",
        "no_approved_prioritization_evidence",
    }
)
INDEPENDENT_SOURCE_IDS = frozenset(
    {"official_HAI_technical_manual", "official_P1_process_physical_graph"}
)

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_GIT_BLOB = re.compile(r"^[0-9a-f]{40}$")
_LOCAL_PATH = re.compile(r"[A-Za-z]:[\\/](?:Users|Documents|Desktop)[\\/]", re.I)
_PROHIBITED_PUBLIC_TOKENS = (
    "hai-train",
    "hai-test",
    "label-test",
    "summary_label",
    "br2_private",
    "directional_fit",
    "confirmation_record",
    "confirmed_pair",
    "selected_horizon",
    "effect_ratio",
    ".csv",
)


class MetadataCandidateDiscoveryError(ValueError):
    """Raised when META evidence, identity, or boundary checks fail closed."""


def _require_identifier(value: str, field_name: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise MetadataCandidateDiscoveryError(f"{field_name} is not a safe identifier")
    return value


def _require_git_blob(value: str, field_name: str) -> str:
    if not isinstance(value, str) or _GIT_BLOB.fullmatch(value) is None:
        raise MetadataCandidateDiscoveryError(f"{field_name} is not a Git blob SHA")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise MetadataCandidateDiscoveryError(f"{field_name} must be boolean")
    return value


def _require_string_tuple(
    values: object, field_name: str, *, allow_empty: bool = True
) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise MetadataCandidateDiscoveryError(f"{field_name} must be an array")
    result = tuple(str(item) for item in values)
    if not allow_empty and not result:
        raise MetadataCandidateDiscoveryError(f"{field_name} must not be empty")
    if any(not item for item in result) or len(result) != len(set(result)):
        raise MetadataCandidateDiscoveryError(
            f"{field_name} must contain unique non-empty strings"
        )
    return result


def _verify_supplied_self_hash(
    payload: Mapping[str, Any], field_name: str, artifact_type: str
) -> str:
    supplied = payload.get(field_name)
    try:
        require_sha256(str(supplied), field_name)
    except ValueError as exc:
        raise MetadataCandidateDiscoveryError(str(exc)) from exc
    content = dict(payload)
    content.pop(field_name, None)
    observed = stable_hash_v1(content)
    if supplied != observed:
        raise MetadataCandidateDiscoveryError(
            f"{artifact_type} {field_name} self-hash mismatch"
        )
    return str(supplied)


@dataclass(frozen=True)
class FrozenUniverseBindingV1:
    """Identity-only view of the exact C0 P1 candidate universe."""

    source_variables: tuple[str, ...]
    target_variables: tuple[str, ...]
    source_identity_list_hash: str
    target_identity_list_hash: str
    pair_universe_hash: str

    def __post_init__(self) -> None:
        if tuple(sorted(set(self.source_variables))) != self.source_variables:
            raise MetadataCandidateDiscoveryError("sources are not canonical and unique")
        if tuple(sorted(set(self.target_variables))) != self.target_variables:
            raise MetadataCandidateDiscoveryError("targets are not canonical and unique")
        if len(self.source_variables) != 12 or len(self.target_variables) != 12:
            raise MetadataCandidateDiscoveryError("frozen source/target count changed")
        if len(self.pairs) != 144:
            raise MetadataCandidateDiscoveryError("frozen pair count changed")
        if self.source_identity_list_hash != SOURCE_IDENTITY_LIST_HASH:
            raise MetadataCandidateDiscoveryError("source identity hash mismatch")
        if self.target_identity_list_hash != TARGET_IDENTITY_LIST_HASH:
            raise MetadataCandidateDiscoveryError("target identity hash mismatch")
        if self.pair_universe_hash != PAIR_UNIVERSE_HASH:
            raise MetadataCandidateDiscoveryError("pair-universe hash mismatch")

    @property
    def pairs(self) -> tuple[tuple[str, str], ...]:
        return eligible_pair_records_v1(self.source_variables, self.target_variables)

    @property
    def pair_set(self) -> frozenset[tuple[str, str]]:
        return frozenset(self.pairs)


def load_frozen_c0_universe_v1(
    *, config_payload: Mapping[str, Any], bundle_payload: Mapping[str, Any]
) -> FrozenUniverseBindingV1:
    """Validate the public C0 config/bundle and return its identity-only universe."""

    config_content = dict(config_payload)
    supplied_config_hash = config_content.pop("config_hash", None)
    if supplied_config_hash != stable_hash_v1(config_content):
        raise MetadataCandidateDiscoveryError("C0 config self-hash mismatch")
    try:
        bundle = CandidateDiscoveryProtocolBundleV1.from_dict(bundle_payload)
    except ValueError as exc:
        raise MetadataCandidateDiscoveryError(str(exc)) from exc
    if bundle.artifact_hash != C0_PROTOCOL_BUNDLE_HASH:
        raise MetadataCandidateDiscoveryError("C0 protocol bundle hash mismatch")
    if bundle.metadata_policy.artifact_hash != METADATA_POLICY_HASH:
        raise MetadataCandidateDiscoveryError("C0 META policy hash mismatch")
    universe = bundle.universe_policy
    if universe.selected_process_id != "P1" or universe.selected_process_name != "Boiler":
        raise MetadataCandidateDiscoveryError("selected process is not P1 Boiler")
    return FrozenUniverseBindingV1(
        source_variables=universe.source_variables,
        target_variables=universe.target_variables,
        source_identity_list_hash=universe.source_identity_list_hash,
        target_identity_list_hash=universe.target_identity_list_hash,
        pair_universe_hash=universe.eligible_pair_universe_hash,
    )


@dataclass(frozen=True)
class OfficialReferenceV1:
    reference_id: str
    independent_source_id: str
    locator: str
    content_sha256: str
    git_blob_sha: str

    def __post_init__(self) -> None:
        _require_identifier(self.reference_id, "reference_id")
        if self.independent_source_id not in INDEPENDENT_SOURCE_IDS:
            raise MetadataCandidateDiscoveryError("unapproved independent evidence source")
        _require_identifier(self.locator, "reference locator")
        try:
            require_sha256(self.content_sha256, "reference content_sha256")
        except ValueError as exc:
            raise MetadataCandidateDiscoveryError(str(exc)) from exc
        _require_git_blob(self.git_blob_sha, "reference git_blob_sha")
        expected = {
            "official_HAI_technical_manual": (
                OFFICIAL_MANUAL_SHA256,
                OFFICIAL_MANUAL_GIT_BLOB,
            ),
            "official_P1_process_physical_graph": (
                OFFICIAL_GRAPH_SHA256,
                OFFICIAL_GRAPH_GIT_BLOB,
            ),
        }[self.independent_source_id]
        if (self.content_sha256, self.git_blob_sha) != expected:
            raise MetadataCandidateDiscoveryError("official reference identity mismatch")

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_sha256": self.content_sha256,
            "git_blob_sha": self.git_blob_sha,
            "independent_source_id": self.independent_source_id,
            "locator": self.locator,
            "reference_id": self.reference_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OfficialReferenceV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "reference_id",
                    "independent_source_id",
                    "locator",
                    "content_sha256",
                    "git_blob_sha",
                }
            ),
            "official_metadata_reference_v1",
        )
        return cls(
            reference_id=str(data["reference_id"]),
            independent_source_id=str(data["independent_source_id"]),
            locator=str(data["locator"]),
            content_sha256=str(data["content_sha256"]),
            git_blob_sha=str(data["git_blob_sha"]),
        )


@dataclass(frozen=True)
class VariableGraphBindingV1:
    variable: str
    graph_node_id: str | None
    reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.variable, "graph binding variable")
        if self.graph_node_id is not None:
            _require_identifier(self.graph_node_id, "graph_node_id")
        if tuple(sorted(set(self.reference_ids))) != self.reference_ids:
            raise MetadataCandidateDiscoveryError("graph binding refs are not canonical")

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_node_id": self.graph_node_id,
            "reference_ids": list(self.reference_ids),
            "variable": self.variable,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VariableGraphBindingV1":
        reject_unknown_fields(
            data,
            frozenset({"variable", "graph_node_id", "reference_ids"}),
            "metadata_variable_graph_binding_v1",
        )
        node = data["graph_node_id"]
        if node is not None and not isinstance(node, str):
            raise MetadataCandidateDiscoveryError("graph_node_id must be string or null")
        return cls(
            variable=str(data["variable"]),
            graph_node_id=node,
            reference_ids=tuple(sorted(_require_string_tuple(data["reference_ids"], "reference_ids"))),
        )


@dataclass(frozen=True)
class VariableSubsystemBindingV1:
    variable: str
    subsystem_ids: tuple[str, ...]
    reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.variable, "subsystem binding variable")
        if tuple(sorted(set(self.subsystem_ids))) != self.subsystem_ids:
            raise MetadataCandidateDiscoveryError("subsystem ids are not canonical")
        for subsystem_id in self.subsystem_ids:
            _require_identifier(subsystem_id, "subsystem_id")
        if tuple(sorted(set(self.reference_ids))) != self.reference_ids:
            raise MetadataCandidateDiscoveryError("subsystem refs are not canonical")
        if bool(self.subsystem_ids) != bool(self.reference_ids):
            raise MetadataCandidateDiscoveryError(
                "subsystem membership and its references must both be present or absent"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_ids": list(self.reference_ids),
            "subsystem_ids": list(self.subsystem_ids),
            "variable": self.variable,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VariableSubsystemBindingV1":
        reject_unknown_fields(
            data,
            frozenset({"variable", "subsystem_ids", "reference_ids"}),
            "metadata_variable_subsystem_binding_v1",
        )
        return cls(
            variable=str(data["variable"]),
            subsystem_ids=tuple(sorted(_require_string_tuple(data["subsystem_ids"], "subsystem_ids"))),
            reference_ids=tuple(sorted(_require_string_tuple(data["reference_ids"], "reference_ids"))),
        )


@dataclass(frozen=True)
class ManualExplicitPairV1:
    source_identity: str
    target_identity: str
    reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.source_identity, "explicit source_identity")
        _require_identifier(self.target_identity, "explicit target_identity")
        if not self.reference_ids or tuple(sorted(set(self.reference_ids))) != self.reference_ids:
            raise MetadataCandidateDiscoveryError("explicit pair refs are not canonical")

    @property
    def identity(self) -> tuple[str, str]:
        return (self.source_identity, self.target_identity)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_ids": list(self.reference_ids),
            "source_identity": self.source_identity,
            "target_identity": self.target_identity,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ManualExplicitPairV1":
        reject_unknown_fields(
            data,
            frozenset({"source_identity", "target_identity", "reference_ids"}),
            "metadata_manual_explicit_pair_v1",
        )
        return cls(
            source_identity=str(data["source_identity"]),
            target_identity=str(data["target_identity"]),
            reference_ids=tuple(sorted(_require_string_tuple(data["reference_ids"], "reference_ids", allow_empty=False))),
        )


@dataclass(frozen=True)
class ReviewedMetadataEvidenceInputV1:
    """Reviewed declaration that contains metadata identities, never values."""

    snapshot_commit: str
    graph_reference_id: str
    reference_catalog: tuple[OfficialReferenceV1, ...]
    source_graph_bindings: tuple[VariableGraphBindingV1, ...]
    target_graph_bindings: tuple[VariableGraphBindingV1, ...]
    source_subsystem_bindings: tuple[VariableSubsystemBindingV1, ...]
    target_subsystem_bindings: tuple[VariableSubsystemBindingV1, ...]
    manual_explicit_pairs: tuple[ManualExplicitPairV1, ...]
    evidence_input_hash: str

    def __post_init__(self) -> None:
        if self.snapshot_commit != OFFICIAL_SNAPSHOT_COMMIT:
            raise MetadataCandidateDiscoveryError("official snapshot commit mismatch")
        _require_identifier(self.graph_reference_id, "graph_reference_id")
        try:
            require_sha256(self.evidence_input_hash, "evidence_input_hash")
        except ValueError as exc:
            raise MetadataCandidateDiscoveryError(str(exc)) from exc
        reference_ids = tuple(item.reference_id for item in self.reference_catalog)
        if tuple(sorted(set(reference_ids))) != reference_ids:
            raise MetadataCandidateDiscoveryError("reference catalog is not canonical")
        catalog = {item.reference_id: item for item in self.reference_catalog}
        graph_ref = catalog.get(self.graph_reference_id)
        if (
            graph_ref is None
            or graph_ref.independent_source_id
            != "official_P1_process_physical_graph"
        ):
            raise MetadataCandidateDiscoveryError("graph reference is unavailable")
        used_refs: set[str] = {self.graph_reference_id}
        for binding in (
            *self.source_graph_bindings,
            *self.target_graph_bindings,
            *self.source_subsystem_bindings,
            *self.target_subsystem_bindings,
            *self.manual_explicit_pairs,
        ):
            used_refs.update(binding.reference_ids)
        unknown_refs = sorted(used_refs - set(catalog))
        if unknown_refs:
            raise MetadataCandidateDiscoveryError(
                f"evidence uses unknown references: {', '.join(unknown_refs)}"
            )
        for pair in self.manual_explicit_pairs:
            if any(
                catalog[ref].independent_source_id
                != "official_HAI_technical_manual"
                for ref in pair.reference_ids
            ):
                raise MetadataCandidateDiscoveryError(
                    "M1 declarations require official manual references"
                )
        observed_hash = stable_hash_v1(self.to_content_dict())
        if observed_hash != self.evidence_input_hash:
            raise MetadataCandidateDiscoveryError("evidence input self-hash mismatch")

    @property
    def reference_by_id(self) -> Mapping[str, OfficialReferenceV1]:
        return MappingProxyType({item.reference_id: item for item in self.reference_catalog})

    def to_content_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039c_meta_reviewed_metadata_evidence_input_v1",
            "graph_reference_id": self.graph_reference_id,
            "manual_explicit_pairs": [item.to_dict() for item in self.manual_explicit_pairs],
            "reference_catalog": [item.to_dict() for item in self.reference_catalog],
            "schema_version": SCHEMA_VERSION,
            "snapshot_commit": self.snapshot_commit,
            "source_graph_bindings": [item.to_dict() for item in self.source_graph_bindings],
            "source_subsystem_bindings": [item.to_dict() for item in self.source_subsystem_bindings],
            "target_graph_bindings": [item.to_dict() for item in self.target_graph_bindings],
            "target_subsystem_bindings": [item.to_dict() for item in self.target_subsystem_bindings],
            "task_id": TASK_ID,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.to_content_dict()
        payload["evidence_input_hash"] = self.evidence_input_hash
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReviewedMetadataEvidenceInputV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "artifact_type",
                    "schema_version",
                    "task_id",
                    "snapshot_commit",
                    "graph_reference_id",
                    "reference_catalog",
                    "source_graph_bindings",
                    "target_graph_bindings",
                    "source_subsystem_bindings",
                    "target_subsystem_bindings",
                    "manual_explicit_pairs",
                    "evidence_input_hash",
                }
            ),
            "task039c_meta_reviewed_metadata_evidence_input_v1",
        )
        if data["artifact_type"] != "task039c_meta_reviewed_metadata_evidence_input_v1":
            raise MetadataCandidateDiscoveryError("evidence input artifact_type mismatch")
        if data["schema_version"] != SCHEMA_VERSION or data["task_id"] != TASK_ID:
            raise MetadataCandidateDiscoveryError("evidence input identity mismatch")
        sequence_fields = (
            "reference_catalog",
            "source_graph_bindings",
            "target_graph_bindings",
            "source_subsystem_bindings",
            "target_subsystem_bindings",
            "manual_explicit_pairs",
        )
        if any(not isinstance(data[field], list) for field in sequence_fields):
            raise MetadataCandidateDiscoveryError("evidence input arrays are invalid")
        return cls(
            snapshot_commit=str(data["snapshot_commit"]),
            graph_reference_id=str(data["graph_reference_id"]),
            reference_catalog=tuple(
                OfficialReferenceV1.from_dict(item) for item in data["reference_catalog"]
            ),
            source_graph_bindings=tuple(
                VariableGraphBindingV1.from_dict(item) for item in data["source_graph_bindings"]
            ),
            target_graph_bindings=tuple(
                VariableGraphBindingV1.from_dict(item) for item in data["target_graph_bindings"]
            ),
            source_subsystem_bindings=tuple(
                VariableSubsystemBindingV1.from_dict(item)
                for item in data["source_subsystem_bindings"]
            ),
            target_subsystem_bindings=tuple(
                VariableSubsystemBindingV1.from_dict(item)
                for item in data["target_subsystem_bindings"]
            ),
            manual_explicit_pairs=tuple(
                ManualExplicitPairV1.from_dict(item) for item in data["manual_explicit_pairs"]
            ),
            evidence_input_hash=str(data["evidence_input_hash"]),
        )


def validate_evidence_against_universe_v1(
    universe: FrozenUniverseBindingV1, evidence: ReviewedMetadataEvidenceInputV1
) -> None:
    """Require exact coverage and reject every out-of-universe declaration."""

    binding_groups = (
        (evidence.source_graph_bindings, universe.source_variables, "source graph"),
        (evidence.target_graph_bindings, universe.target_variables, "target graph"),
        (evidence.source_subsystem_bindings, universe.source_variables, "source subsystem"),
        (evidence.target_subsystem_bindings, universe.target_variables, "target subsystem"),
    )
    for bindings, expected, label in binding_groups:
        variables = tuple(item.variable for item in bindings)
        if variables != expected:
            raise MetadataCandidateDiscoveryError(f"{label} bindings changed the universe")
    explicit_identities = tuple(item.identity for item in evidence.manual_explicit_pairs)
    if tuple(sorted(set(explicit_identities))) != explicit_identities:
        raise MetadataCandidateDiscoveryError("manual explicit pairs are not canonical")
    outside = sorted(set(explicit_identities) - universe.pair_set)
    if outside:
        raise MetadataCandidateDiscoveryError("manual evidence contains out-of-universe pair")


@dataclass(frozen=True)
class OfficialPhysicalGraphV1:
    node_ids: frozenset[str]
    directed_edges: frozenset[tuple[str, str]]


def authorize_metadata_reference_path_v1(path: Path, reference_kind: str) -> None:
    """Authorize only the exact official manual or physical-graph filename."""

    expected_names = {
        "technical_manual": "hai_dataset_technical_details.pdf",
        "physical_graph": "phy_boiler.json",
    }
    expected = expected_names.get(reference_kind)
    if expected is None or path.name != expected:
        raise MetadataCandidateDiscoveryError("metadata reference path is not authorized")
    lowered = str(path).lower()
    forbidden = (
        "hai-train",
        "hai-test",
        "label-test",
        "summary_label",
        "br2",
        "stat",
        "gdn",
        ".csv",
    )
    if any(token in lowered for token in forbidden):
        raise MetadataCandidateDiscoveryError("prohibited data path requested")


def _file_hashes(path: Path) -> tuple[str, str]:
    digest = sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    blob = sha1()
    blob.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            blob.update(chunk)
    return digest.hexdigest(), blob.hexdigest()


def verify_official_reference_file_v1(
    *, path: Path, reference_kind: str
) -> tuple[str, str]:
    authorize_metadata_reference_path_v1(path, reference_kind)
    if not path.is_file():
        raise MetadataCandidateDiscoveryError("official metadata reference is unavailable")
    observed = _file_hashes(path)
    expected = {
        "technical_manual": (OFFICIAL_MANUAL_SHA256, OFFICIAL_MANUAL_GIT_BLOB),
        "physical_graph": (OFFICIAL_GRAPH_SHA256, OFFICIAL_GRAPH_GIT_BLOB),
    }[reference_kind]
    if observed != expected:
        raise MetadataCandidateDiscoveryError("official metadata reference hash mismatch")
    return observed


def load_official_physical_graph_v1(path: Path) -> OfficialPhysicalGraphV1:
    verify_official_reference_file_v1(path=path, reference_kind="physical_graph")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("directed") is not True
        or payload.get("multigraph") is not False
        or not isinstance(payload.get("nodes"), list)
        or not isinstance(payload.get("links"), list)
    ):
        raise MetadataCandidateDiscoveryError("official graph structure is invalid")
    node_ids = frozenset(str(item.get("id")) for item in payload["nodes"])
    if "None" in node_ids or len(node_ids) != len(payload["nodes"]):
        raise MetadataCandidateDiscoveryError("official graph node identities are invalid")
    edges = frozenset(
        (str(item.get("source")), str(item.get("target")))
        for item in payload["links"]
    )
    if any(source not in node_ids or target not in node_ids for source, target in edges):
        raise MetadataCandidateDiscoveryError("official graph edge is unbound")
    return OfficialPhysicalGraphV1(node_ids=node_ids, directed_edges=edges)


@dataclass(frozen=True)
class MetadataPairEvidenceRecordV1:
    source_identity: str
    target_identity: str
    evidence_tier: str
    independent_official_reference_count: int
    reference_identifiers: tuple[str, ...]
    graph_evidence_present: bool
    subsystem_evidence_present: bool
    manual_semantic_evidence_present: bool
    evidence_summary: str
    supported_status: bool

    def __post_init__(self) -> None:
        if self.evidence_tier not in EVIDENCE_TIERS:
            raise MetadataCandidateDiscoveryError("unknown evidence tier")
        if self.independent_official_reference_count < 0:
            raise MetadataCandidateDiscoveryError("negative reference count")
        if tuple(sorted(set(self.reference_identifiers))) != self.reference_identifiers:
            raise MetadataCandidateDiscoveryError("pair references are not canonical")
        if self.evidence_summary not in SUMMARY_VOCABULARY:
            raise MetadataCandidateDiscoveryError("evidence summary is outside vocabulary")
        supported = self.evidence_tier != "UNSUPPORTED"
        if self.supported_status != supported:
            raise MetadataCandidateDiscoveryError("supported status disagrees with tier")
        if self.evidence_tier == "M1_EXPLICIT" and not self.manual_semantic_evidence_present:
            raise MetadataCandidateDiscoveryError("M1 requires manual semantic evidence")
        if self.evidence_tier == "M2_GRAPH_ADJACENT" and not self.graph_evidence_present:
            raise MetadataCandidateDiscoveryError("M2 requires graph adjacency")
        if self.evidence_tier == "M3_SUBSYSTEM_SUPPORTED":
            if not self.subsystem_evidence_present or self.graph_evidence_present:
                raise MetadataCandidateDiscoveryError("M3 boundary is invalid")
        if self.evidence_tier == "UNSUPPORTED" and any(
            (
                self.reference_identifiers,
                self.independent_official_reference_count,
                self.graph_evidence_present,
                self.subsystem_evidence_present,
                self.manual_semantic_evidence_present,
            )
        ):
            raise MetadataCandidateDiscoveryError("unsupported record contains evidence")

    @property
    def identity(self) -> tuple[str, str]:
        return (self.source_identity, self.target_identity)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_summary": self.evidence_summary,
            "evidence_tier": self.evidence_tier,
            "graph_evidence_present": self.graph_evidence_present,
            "independent_official_reference_count": self.independent_official_reference_count,
            "manual_semantic_evidence_present": self.manual_semantic_evidence_present,
            "reference_identifiers": list(self.reference_identifiers),
            "source_identity": self.source_identity,
            "subsystem_evidence_present": self.subsystem_evidence_present,
            "supported_status": self.supported_status,
            "target_identity": self.target_identity,
        }


def _binding_map(bindings: Sequence[Any]) -> dict[str, Any]:
    return {item.variable: item for item in bindings}


def discover_metadata_pair_records_v1(
    *,
    universe: FrozenUniverseBindingV1,
    evidence: ReviewedMetadataEvidenceInputV1,
    graph: OfficialPhysicalGraphV1,
) -> tuple[MetadataPairEvidenceRecordV1, ...]:
    """Classify every frozen pair using the exact C0 tier precedence."""

    validate_evidence_against_universe_v1(universe, evidence)
    source_graph = _binding_map(evidence.source_graph_bindings)
    target_graph = _binding_map(evidence.target_graph_bindings)
    source_subsystems = _binding_map(evidence.source_subsystem_bindings)
    target_subsystems = _binding_map(evidence.target_subsystem_bindings)
    explicit = {item.identity: item for item in evidence.manual_explicit_pairs}
    catalog = evidence.reference_by_id

    for binding in (*evidence.source_graph_bindings, *evidence.target_graph_bindings):
        if binding.graph_node_id is not None and binding.graph_node_id not in graph.node_ids:
            raise MetadataCandidateDiscoveryError("reviewed graph binding uses unknown node")

    records: list[MetadataPairEvidenceRecordV1] = []
    for source, target in universe.pairs:
        source_node = source_graph[source].graph_node_id
        target_node = target_graph[target].graph_node_id
        graph_adjacent = (
            source_node is not None
            and target_node is not None
            and (source_node, target_node) in graph.directed_edges
        )
        shared_subsystems = set(source_subsystems[source].subsystem_ids) & set(
            target_subsystems[target].subsystem_ids
        )
        explicit_pair = explicit.get((source, target))
        reference_ids: set[str] = set()
        manual_semantic = False
        subsystem_evidence = False

        if explicit_pair is not None:
            tier = "M1_EXPLICIT"
            manual_semantic = True
            reference_ids.update(explicit_pair.reference_ids)
            if graph_adjacent:
                reference_ids.add(evidence.graph_reference_id)
                reference_ids.update(source_graph[source].reference_ids)
                reference_ids.update(target_graph[target].reference_ids)
                summary = "manual_explicit_control_chain_and_graph_adjacent"
            else:
                summary = "manual_explicit_control_chain"
        elif graph_adjacent:
            tier = "M2_GRAPH_ADJACENT"
            manual_semantic = True
            reference_ids.add(evidence.graph_reference_id)
            reference_ids.update(source_graph[source].reference_ids)
            reference_ids.update(target_graph[target].reference_ids)
            summary = "graph_adjacent_with_reviewed_semantic_mapping"
        elif shared_subsystems:
            tier = "M3_SUBSYSTEM_SUPPORTED"
            manual_semantic = True
            subsystem_evidence = True
            reference_ids.update(source_subsystems[source].reference_ids)
            reference_ids.update(target_subsystems[target].reference_ids)
            summary = "reviewed_same_control_subsystem_no_direct_graph_edge"
        else:
            tier = "UNSUPPORTED"
            summary = "no_approved_prioritization_evidence"

        independent_sources = {
            catalog[reference_id].independent_source_id
            for reference_id in reference_ids
        }
        records.append(
            MetadataPairEvidenceRecordV1(
                source_identity=source,
                target_identity=target,
                evidence_tier=tier,
                independent_official_reference_count=len(independent_sources),
                reference_identifiers=tuple(sorted(reference_ids)),
                graph_evidence_present=graph_adjacent,
                subsystem_evidence_present=subsystem_evidence,
                manual_semantic_evidence_present=manual_semantic,
                evidence_summary=summary,
                supported_status=tier != "UNSUPPORTED",
            )
        )
    if len(records) != 144 or tuple(item.identity for item in records) != universe.pairs:
        raise MetadataCandidateDiscoveryError("metadata ledger changed the frozen universe")
    return tuple(records)


def rank_supported_metadata_records_v1(
    records: Sequence[MetadataPairEvidenceRecordV1],
) -> tuple[MetadataPairEvidenceRecordV1, ...]:
    """Rank supported records only, with no score and no unsupported padding."""

    by_identity = {item.identity: item for item in records}
    if len(by_identity) != len(records):
        raise MetadataCandidateDiscoveryError("metadata ledger contains duplicates")
    rank_inputs = tuple(
        MetadataRankInputV1(
            item.source_identity,
            item.target_identity,
            item.evidence_tier,
            item.independent_official_reference_count,
        )
        for item in records
        if item.supported_status
    )
    ranked = rank_metadata_candidates_v1(rank_inputs)
    return tuple(by_identity[(item.source, item.target)] for item in ranked)


def evidence_ledger_payload_v1(
    *, records: Sequence[MetadataPairEvidenceRecordV1], evidence_input_hash: str
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "arm_id": ARM_ID,
        "artifact_type": "metadata_candidate_evidence_ledger_v1",
        "c0_protocol_bundle_hash": C0_PROTOCOL_BUNDLE_HASH,
        "evaluated_pair_count": len(records),
        "evidence_input_hash": evidence_input_hash,
        "metadata_policy_hash": METADATA_POLICY_HASH,
        "pair_universe_hash": PAIR_UNIVERSE_HASH,
        "records": [item.to_dict() for item in records],
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
    }
    payload["artifact_hash"] = stable_hash_v1(payload)
    return payload


def data_access_audit_payload_v1(
    *, code_commit: str, created_at: str, evidence_input_hash: str
) -> dict[str, Any]:
    parse_iso_datetime(created_at, "created_at")
    payload: dict[str, Any] = {
        "arm_id": ARM_ID,
        "artifact_type": "metadata_candidate_data_access_audit_v1",
        "br2_pair_supervision_used": False,
        "c0_protocol_bundle_hash": C0_PROTOCOL_BUNDLE_HASH,
        "creation_metadata": {
            "code_commit": code_commit,
            "created_at": created_at,
            "created_by": TASK_ID,
        },
        "cross_arm_score_used": False,
        "evidence_input_hash": evidence_input_hash,
        "feature_value_file_access_count": 0,
        "official_reference_files": [
            {
                "content_sha256": OFFICIAL_MANUAL_SHA256,
                "git_blob_sha": OFFICIAL_MANUAL_GIT_BLOB,
                "pinned_relative_path": "hai_dataset_technical_details.pdf",
                "reference_kind": "official_HAI_technical_manual",
            },
            {
                "content_sha256": OFFICIAL_GRAPH_SHA256,
                "git_blob_sha": OFFICIAL_GRAPH_GIT_BLOB,
                "pinned_relative_path": "graph/boiler/phy_boiler.json",
                "reference_kind": "official_P1_process_physical_graph",
            },
        ],
        "pair_universe_hash": PAIR_UNIVERSE_HASH,
        "prohibited_input_access_count": 0,
        "real_hai_feature_values_accessed": False,
        "schema_version": SCHEMA_VERSION,
        "snapshot_commit": OFFICIAL_SNAPSHOT_COMMIT,
        "status": "passed_metadata_data_boundary",
        "task_id": TASK_ID,
    }
    payload["artifact_hash"] = stable_hash_v1(payload)
    assert_public_metadata_payload_v1(payload)
    return payload


def _ranked_record_dict(
    record: MetadataPairEvidenceRecordV1, rank: int
) -> dict[str, Any]:
    payload = record.to_dict()
    payload["rank"] = rank
    return dict(sorted(payload.items()))


def _identity_dict(record: MetadataPairEvidenceRecordV1) -> dict[str, str]:
    return {
        "source_identity": record.source_identity,
        "target_identity": record.target_identity,
    }


def build_metadata_candidate_result_v1(
    *,
    records: Sequence[MetadataPairEvidenceRecordV1],
    code_commit: str,
    created_at: str,
    evidence_ledger_hash: str,
    data_access_audit_ref: str,
) -> dict[str, Any]:
    """Build and self-hash the immutable public META result payload."""

    parse_iso_datetime(created_at, "created_at")
    require_sha256(evidence_ledger_hash, "evidence_ledger_hash")
    require_sha256(data_access_audit_ref, "data_access_audit_ref")
    if len(records) != 144:
        raise MetadataCandidateDiscoveryError("result requires exactly 144 records")
    ranked = rank_supported_metadata_records_v1(records)
    identities = tuple(item.identity for item in ranked)
    views = derive_candidate_budget_views_v1(identities)
    by_identity = {item.identity: item for item in ranked}
    tier_counts = {tier: 0 for tier in EVIDENCE_TIERS}
    for record in records:
        tier_counts[record.evidence_tier] += 1
    supported_count = len(ranked)

    def view_payload(view: Sequence[tuple[str, str]]) -> list[dict[str, str]]:
        return [_identity_dict(by_identity[identity]) for identity in view]

    shortfall = {
        f"top{k}": {
            "candidate_shortfall": views.candidate_shortfall[k] > 0,
            "requested_count": k,
            "returned_count": k - views.candidate_shortfall[k],
            "shortfall_count": views.candidate_shortfall[k],
        }
        for k in (10, 20, 40)
    }
    payload: dict[str, Any] = {
        "BR2_pair_supervision_used": False,
        "arm_id": ARM_ID,
        "artifact_type": "metadata_candidate_result_v1",
        "c0_protocol_bundle_hash": C0_PROTOCOL_BUNDLE_HASH,
        "candidate_shortfall": shortfall,
        "creation_metadata": {
            "code_commit": code_commit,
            "created_at": created_at,
            "created_by": TASK_ID,
        },
        "cross_arm_score_used": False,
        "data_access_audit_ref": data_access_audit_ref,
        "evaluated_pair_count": len(records),
        "evidence_ledger_hash": evidence_ledger_hash,
        "metadata_policy_hash": METADATA_POLICY_HASH,
        "numerical_weighting_used": False,
        "official_graph_claim_boundary": OFFICIAL_GRAPH_CLAIM_BOUNDARY,
        "pair_universe_hash": PAIR_UNIVERSE_HASH,
        "real_hai_feature_values_accessed": False,
        "schema_version": SCHEMA_VERSION,
        "source_identity_list_hash": SOURCE_IDENTITY_LIST_HASH,
        "status": PASSING_STATUS,
        "supported_count": supported_count,
        "supported_ranking": [
            _ranked_record_dict(record, rank)
            for rank, record in enumerate(ranked, start=1)
        ],
        "target_identity_list_hash": TARGET_IDENTITY_LIST_HASH,
        "task_id": TASK_ID,
        "tier_counts": tier_counts,
        "top10_identities": view_payload(views.top10),
        "top20_identities": view_payload(views.top20),
        "top40_identities": view_payload(views.top40),
        "unsupported_count": tier_counts["UNSUPPORTED"],
    }
    payload["artifact_hash"] = stable_hash_v1(payload)
    validate_metadata_candidate_result_v1(payload)
    return payload


_RESULT_FIELDS = frozenset(
    {
        "BR2_pair_supervision_used",
        "arm_id",
        "artifact_hash",
        "artifact_type",
        "c0_protocol_bundle_hash",
        "candidate_shortfall",
        "creation_metadata",
        "cross_arm_score_used",
        "data_access_audit_ref",
        "evaluated_pair_count",
        "evidence_ledger_hash",
        "metadata_policy_hash",
        "numerical_weighting_used",
        "official_graph_claim_boundary",
        "pair_universe_hash",
        "real_hai_feature_values_accessed",
        "schema_version",
        "source_identity_list_hash",
        "status",
        "supported_count",
        "supported_ranking",
        "target_identity_list_hash",
        "task_id",
        "tier_counts",
        "top10_identities",
        "top20_identities",
        "top40_identities",
        "unsupported_count",
    }
)


def validate_metadata_candidate_result_v1(payload: Mapping[str, Any]) -> None:
    """Validate result identity, invariants, prefixes, boundary, and self-hash."""

    reject_unknown_fields(payload, _RESULT_FIELDS, "metadata_candidate_result_v1")
    if (
        payload["artifact_type"] != "metadata_candidate_result_v1"
        or payload["schema_version"] != SCHEMA_VERSION
        or payload["task_id"] != TASK_ID
        or payload["arm_id"] != ARM_ID
        or payload["status"] != PASSING_STATUS
    ):
        raise MetadataCandidateDiscoveryError("META result identity mismatch")
    expected_hashes = {
        "c0_protocol_bundle_hash": C0_PROTOCOL_BUNDLE_HASH,
        "metadata_policy_hash": METADATA_POLICY_HASH,
        "source_identity_list_hash": SOURCE_IDENTITY_LIST_HASH,
        "target_identity_list_hash": TARGET_IDENTITY_LIST_HASH,
        "pair_universe_hash": PAIR_UNIVERSE_HASH,
    }
    if any(payload[field] != expected for field, expected in expected_hashes.items()):
        raise MetadataCandidateDiscoveryError("META result frozen hash mismatch")
    for field in (
        "real_hai_feature_values_accessed",
        "BR2_pair_supervision_used",
        "cross_arm_score_used",
        "numerical_weighting_used",
    ):
        if _require_bool(payload[field], field):
            raise MetadataCandidateDiscoveryError(f"{field} must remain false")
    if payload["official_graph_claim_boundary"] != OFFICIAL_GRAPH_CLAIM_BOUNDARY:
        raise MetadataCandidateDiscoveryError("official graph claim boundary changed")
    if payload["evaluated_pair_count"] != 144:
        raise MetadataCandidateDiscoveryError("evaluated pair count changed")
    if not isinstance(payload["tier_counts"], Mapping) or set(payload["tier_counts"]) != set(EVIDENCE_TIERS):
        raise MetadataCandidateDiscoveryError("tier counts are incomplete")
    tier_counts = {tier: int(payload["tier_counts"][tier]) for tier in EVIDENCE_TIERS}
    if sum(tier_counts.values()) != 144:
        raise MetadataCandidateDiscoveryError("tier counts do not sum to 144")
    if payload["unsupported_count"] != tier_counts["UNSUPPORTED"]:
        raise MetadataCandidateDiscoveryError("unsupported count mismatch")
    if payload["supported_count"] != 144 - tier_counts["UNSUPPORTED"]:
        raise MetadataCandidateDiscoveryError("supported count mismatch")
    ranking = payload["supported_ranking"]
    if not isinstance(ranking, list) or len(ranking) != payload["supported_count"]:
        raise MetadataCandidateDiscoveryError("supported ranking length mismatch")
    identities: list[dict[str, str]] = []
    previous_key: tuple[int, int, str, str] | None = None
    for expected_rank, entry in enumerate(ranking, start=1):
        if not isinstance(entry, Mapping) or entry.get("rank") != expected_rank:
            raise MetadataCandidateDiscoveryError("supported ranking rank mismatch")
        tier = str(entry.get("evidence_tier"))
        if tier == "UNSUPPORTED" or entry.get("supported_status") is not True:
            raise MetadataCandidateDiscoveryError("unsupported pair entered ranking")
        identity = {
            "source_identity": str(entry.get("source_identity")),
            "target_identity": str(entry.get("target_identity")),
        }
        identities.append(identity)
        key = (
            EVIDENCE_TIERS.index(tier),
            -int(entry.get("independent_official_reference_count")),
            identity["source_identity"],
            identity["target_identity"],
        )
        if previous_key is not None and key < previous_key:
            raise MetadataCandidateDiscoveryError("supported ranking is not canonical")
        previous_key = key
    for k in (10, 20, 40):
        field = f"top{k}_identities"
        expected_view = identities[:k]
        if payload[field] != expected_view:
            raise MetadataCandidateDiscoveryError(f"{field} is not a ranking prefix")
        shortfall = payload["candidate_shortfall"].get(f"top{k}")
        expected_returned = min(k, len(identities))
        expected_shortfall = k - expected_returned
        if shortfall != {
            "candidate_shortfall": expected_shortfall > 0,
            "requested_count": k,
            "returned_count": expected_returned,
            "shortfall_count": expected_shortfall,
        }:
            raise MetadataCandidateDiscoveryError("candidate shortfall record mismatch")
    _verify_supplied_self_hash(payload, "artifact_hash", "metadata_candidate_result_v1")
    assert_public_metadata_payload_v1(payload)


def assert_public_metadata_payload_v1(payload: Mapping[str, Any]) -> None:
    """Reject private paths, prohibited inputs, or raw feature-value containers."""

    serialized = canonical_json_v1(payload)
    lowered = serialized.lower()
    if _LOCAL_PATH.search(serialized) is not None:
        raise MetadataCandidateDiscoveryError("public payload contains an absolute local path")
    if any(token in lowered for token in _PROHIBITED_PUBLIC_TOKENS):
        raise MetadataCandidateDiscoveryError("public payload contains prohibited input detail")
    prohibited_keys = {
        "raw_rows",
        "raw_values",
        "feature_values",
        "attack_summary",
        "br2_pair_results",
        "stat_results",
        "gdn_results",
    }

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            if prohibited_keys & set(value):
                raise MetadataCandidateDiscoveryError("public payload contains prohibited fields")
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)


def load_reviewed_metadata_evidence_v1(path: Path) -> ReviewedMetadataEvidenceInputV1:
    """Load one ignored JSON evidence declaration after path boundary checks."""

    lowered = str(path).replace("\\", "/").lower()
    if path.name != "TASK-039C_META_REVIEWED_EVIDENCE_INPUT.json":
        raise MetadataCandidateDiscoveryError("reviewed evidence input filename changed")
    if "/artifacts/task039c_meta/" not in f"/{lowered}":
        raise MetadataCandidateDiscoveryError("reviewed evidence input must remain under artifacts")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise MetadataCandidateDiscoveryError("reviewed evidence input is not an object")
    return ReviewedMetadataEvidenceInputV1.from_dict(payload)


__all__ = [
    "ARM_ID",
    "C0_PROTOCOL_BUNDLE_HASH",
    "EVIDENCE_TIERS",
    "FrozenUniverseBindingV1",
    "ManualExplicitPairV1",
    "MetadataCandidateDiscoveryError",
    "MetadataPairEvidenceRecordV1",
    "OFFICIAL_GRAPH_CLAIM_BOUNDARY",
    "PASSING_STATUS",
    "ReviewedMetadataEvidenceInputV1",
    "VariableGraphBindingV1",
    "VariableSubsystemBindingV1",
    "assert_public_metadata_payload_v1",
    "authorize_metadata_reference_path_v1",
    "build_metadata_candidate_result_v1",
    "data_access_audit_payload_v1",
    "discover_metadata_pair_records_v1",
    "evidence_ledger_payload_v1",
    "load_frozen_c0_universe_v1",
    "load_official_physical_graph_v1",
    "load_reviewed_metadata_evidence_v1",
    "rank_supported_metadata_records_v1",
    "validate_evidence_against_universe_v1",
    "validate_metadata_candidate_result_v1",
    "verify_official_reference_file_v1",
]
