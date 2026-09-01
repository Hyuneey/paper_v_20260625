"""Formal V4 scientific authority for prospective VALIDATION V2 execution.

The frozen PILOT V1 ``CanonicalRuleDescriptorV4`` implementation is bound to
COMMON-42 and cannot be parameterized for a new portfolio.  This module
formalizes the same continuous-step execution family for new V2 identities.
It intentionally does not claim canonical RuleV1 or VerifierV1 authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping, Sequence

from .io_hash_v1 import sha256_file_v1
from .runtime_policy_v1 import (
    FORMAL_V4_RESPONSE_POLICY_HASH,
    FORMAL_V4_TRACE_CONTRACT_HASH,
    FORMAL_V4_TRIGGER_POLICY_HASH,
)


FORMAL_V4_AUTHORITY_VERSION = "VALIDATION_V2_FORMAL_V4_AUTHORITY_V1"
FORMAL_V4_SCHEMA_VERSION = "1.0.0"
FORMAL_V4_AUTHORITY_FAMILY = "FORMAL_V4"
V4_NUMERIC_ROLES = (
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
    "source_pre_window_seconds",
    "source_post_window_seconds",
    "minimum_source_stability_fraction",
    "source_refractory_seconds",
    "cross_source_isolation_radius_seconds",
    "target_baseline_window_seconds",
    "target_response_window_seconds",
)
V4_HORIZONS_SECONDS = (1, 5, 10, 30, 60)
V4_SOURCE_DIRECTIONS = ("step_up", "step_down")
V4_TARGET_DIRECTIONS = ("increase", "decrease")
V4_RUNTIME_OUTCOMES = ("PASS", "FAIL", "ABSTAIN")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_AUTHORIZATION_CAPABILITY = object()


class FormalV4AuthorityError(ValueError):
    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code
        self.message = message


def _fail(code: str, message: str) -> None:
    raise FormalV4AuthorityError(code, message)


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value:
        _fail("V4_TEXT_INVALID", f"{name} must be a non-empty exact string")
    return value


def _hash(value: object, name: str) -> str:
    result = _text(value, name)
    if _SHA256.fullmatch(result) is None:
        _fail("V4_HASH_INVALID", f"{name} must be a lowercase SHA-256")
    return result


def _git_commit(value: object, name: str) -> str:
    result = _text(value, name)
    if _GIT_COMMIT.fullmatch(result) is None:
        _fail("V4_GIT_COMMIT_INVALID", f"{name} must be a 40-character Git commit")
    return result


def _exact_tuple(value: object, name: str) -> tuple[Any, ...]:
    if type(value) is not tuple:
        _fail("V4_TUPLE_INVALID", f"{name} must be an exact tuple")
    return value


def _safe_relative_path(value: object, name: str) -> str:
    path = _text(value, name).replace("\\", "/")
    pure = PurePosixPath(path)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        _fail("V4_PATH_INVALID", f"{name} must be a safe repository-relative path")
    if ":" in path:
        _fail("V4_PATH_INVALID", f"{name} must not contain a drive or URI prefix")
    return path


def _resolve_bound_file(repository_root: Path, relative_path: str) -> Path:
    root = repository_root.resolve(strict=True)
    candidate = (root / _safe_relative_path(relative_path, "relative_path")).resolve(strict=True)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        _fail("V4_PATH_ESCAPE", "bound artifact escapes the repository root")
        raise AssertionError from exc
    if not candidate.is_file():
        _fail("V4_BOUND_ARTIFACT_NOT_FILE", "bound artifact is not a regular file")
    return candidate


def _file_sha256(repository_root: Path, relative_path: str) -> str:
    return sha256_file_v1(_resolve_bound_file(repository_root, relative_path))


def _jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if type(value) is tuple:
        return [_jsonable(item) for item in value]
    if type(value) is dict:
        return {key: _jsonable(value[key]) for key in sorted(value)}
    return value


def canonical_json_bytes_v1(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        _jsonable(dict(document)),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def canonical_document_hash_v1(document: Mapping[str, Any]) -> str:
    return sha256(canonical_json_bytes_v1(document)).hexdigest()


@dataclass(frozen=True)
class NumericReferenceBindingV1:
    numeric_role: str
    reference_id: str
    reference_hash: str

    def __post_init__(self) -> None:
        if self.numeric_role not in V4_NUMERIC_ROLES:
            _fail("V4_NUMERIC_ROLE_INVALID", "numeric role is outside Formal V4")
        _text(self.reference_id, "reference_id")
        _hash(self.reference_hash, "reference_hash")

    def to_dict(self) -> dict[str, Any]:
        return {
            "numeric_role": self.numeric_role,
            "reference_hash": self.reference_hash,
            "reference_id": self.reference_id,
        }


@dataclass(frozen=True)
class FormalV4ArtifactBindingV1:
    artifact_id: str
    relative_path: str
    content_sha256: str

    def __post_init__(self) -> None:
        _text(self.artifact_id, "artifact_id")
        normalized = _safe_relative_path(self.relative_path, "relative_path")
        if normalized != self.relative_path:
            _fail("V4_PATH_NOT_NORMALIZED", "relative_path must use normalized forward slashes")
        _hash(self.content_sha256, "content_sha256")

    def verify(self, repository_root: Path) -> str:
        observed = _file_sha256(repository_root, self.relative_path)
        if observed != self.content_sha256:
            _fail("V4_BOUND_ARTIFACT_HASH_MISMATCH", f"artifact bytes differ: {self.artifact_id}")
        return observed

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact_id": self.artifact_id,
            "content_sha256": self.content_sha256,
            "relative_path": self.relative_path,
        }


@dataclass(frozen=True)
class FormalV4ExecutionContextV1:
    source_commit: str
    runtime_config_binding: FormalV4ArtifactBindingV1
    relation_authority_binding: FormalV4ArtifactBindingV1
    numeric_authority_binding: FormalV4ArtifactBindingV1
    feature_contract_binding: FormalV4ArtifactBindingV1
    file_contract_binding: FormalV4ArtifactBindingV1
    sampling_contract_binding: FormalV4ArtifactBindingV1
    evaluator_implementation_binding: FormalV4ArtifactBindingV1

    def __post_init__(self) -> None:
        _git_commit(self.source_commit, "source_commit")
        for name in (
            "runtime_config_binding",
            "relation_authority_binding",
            "numeric_authority_binding",
            "feature_contract_binding",
            "file_contract_binding",
            "sampling_contract_binding",
            "evaluator_implementation_binding",
        ):
            if type(getattr(self, name)) is not FormalV4ArtifactBindingV1:
                _fail("V4_EXECUTION_BINDING_TYPE_INVALID", f"{name} type differs")

    def verify(self, repository_root: Path) -> str:
        for binding in (
            self.runtime_config_binding,
            self.relation_authority_binding,
            self.numeric_authority_binding,
            self.feature_contract_binding,
            self.file_contract_binding,
            self.sampling_contract_binding,
            self.evaluator_implementation_binding,
        ):
            binding.verify(repository_root)
        return self.context_hash

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_formal_v4_execution_context_v1",
            "evaluator_implementation_binding": self.evaluator_implementation_binding.to_dict(),
            "feature_contract_binding": self.feature_contract_binding.to_dict(),
            "file_contract_binding": self.file_contract_binding.to_dict(),
            "numeric_authority_binding": self.numeric_authority_binding.to_dict(),
            "relation_authority_binding": self.relation_authority_binding.to_dict(),
            "runtime_config_binding": self.runtime_config_binding.to_dict(),
            "sampling_contract_binding": self.sampling_contract_binding.to_dict(),
            "schema_version": FORMAL_V4_SCHEMA_VERSION,
            "source_commit": self.source_commit,
        }

    @property
    def context_hash(self) -> str:
        return canonical_document_hash_v1(self._payload())

    @property
    def runtime_config_hash(self) -> str:
        return self.runtime_config_binding.content_sha256

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "context_hash": self.context_hash}


@dataclass(frozen=True)
class FormalV4RuleDescriptorV1:
    relation_id: str
    relation_binding_hash: str
    semantic_execution_hash: str
    source: str
    target: str
    source_direction: str
    target_direction: str
    selected_horizon_seconds: int
    numeric_reference_bindings: tuple[NumericReferenceBindingV1, ...]
    numeric_authority_hash: str

    def __post_init__(self) -> None:
        _text(self.relation_id, "relation_id")
        _hash(self.relation_binding_hash, "relation_binding_hash")
        _hash(self.semantic_execution_hash, "semantic_execution_hash")
        _text(self.source, "source")
        _text(self.target, "target")
        if self.source == self.target:
            _fail("V4_SELF_RELATION_PROHIBITED", "source and target must differ")
        if self.source_direction not in V4_SOURCE_DIRECTIONS:
            _fail("V4_SOURCE_DIRECTION_INVALID", "unsupported source direction")
        if self.target_direction not in V4_TARGET_DIRECTIONS:
            _fail("V4_TARGET_DIRECTION_INVALID", "unsupported target direction")
        if type(self.selected_horizon_seconds) is not int:
            _fail("V4_HORIZON_TYPE_INVALID", "horizon must be an exact integer")
        if self.selected_horizon_seconds not in V4_HORIZONS_SECONDS:
            _fail("V4_HORIZON_INVALID", "horizon is outside the Formal V4 set")
        bindings = _exact_tuple(
            self.numeric_reference_bindings, "numeric_reference_bindings"
        )
        if any(type(item) is not NumericReferenceBindingV1 for item in bindings):
            _fail("V4_NUMERIC_BINDING_TYPE_INVALID", "numeric binding type differs")
        if tuple(item.numeric_role for item in bindings) != V4_NUMERIC_ROLES:
            _fail("V4_NUMERIC_BINDING_ORDER_INVALID", "all ten roles are required in order")
        if len({item.reference_id for item in bindings}) != len(V4_NUMERIC_ROLES):
            _fail("V4_NUMERIC_REFERENCE_DUPLICATE", "numeric reference IDs duplicate")
        _hash(self.numeric_authority_hash, "numeric_authority_hash")

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_formal_v4_rule_descriptor_v1",
            "numeric_authority_hash": self.numeric_authority_hash,
            "numeric_reference_bindings": [
                item.to_dict() for item in self.numeric_reference_bindings
            ],
            "relation_binding_hash": self.relation_binding_hash,
            "relation_id": self.relation_id,
            "schema_version": FORMAL_V4_SCHEMA_VERSION,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "semantic_execution_hash": self.semantic_execution_hash,
            "source": self.source,
            "source_direction": self.source_direction,
            "target": self.target,
            "target_direction": self.target_direction,
        }

    @property
    def descriptor_hash(self) -> str:
        return canonical_document_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "descriptor_hash": self.descriptor_hash}


@dataclass(frozen=True)
class FormalV4EvaluatorContractV1:
    evaluator_id: str
    implementation_path: str
    implementation_hash: str
    trigger_policy_hash: str
    response_policy_hash: str
    trace_contract_hash: str
    deterministic: bool = True
    llm_free: bool = True

    def __post_init__(self) -> None:
        _text(self.evaluator_id, "evaluator_id")
        path = _safe_relative_path(self.implementation_path, "implementation_path")
        if path != self.implementation_path:
            _fail("V4_IMPLEMENTATION_PATH_INVALID", "implementation path must be normalized")
        for name in (
            "implementation_hash",
            "trigger_policy_hash",
            "response_policy_hash",
            "trace_contract_hash",
        ):
            _hash(getattr(self, name), name)
        if (
            self.trigger_policy_hash != FORMAL_V4_TRIGGER_POLICY_HASH
            or self.response_policy_hash != FORMAL_V4_RESPONSE_POLICY_HASH
            or self.trace_contract_hash != FORMAL_V4_TRACE_CONTRACT_HASH
        ):
            _fail("V4_EVALUATOR_POLICY_HASH_MISMATCH", "evaluator policy identities differ")
        if type(self.deterministic) is not bool or self.deterministic is not True:
            _fail("V4_EVALUATOR_NONDETERMINISTIC", "evaluator must be deterministic")
        if type(self.llm_free) is not bool or self.llm_free is not True:
            _fail("V4_EVALUATOR_LLM_PROHIBITED", "runtime evaluator must be LLM-free")

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_formal_v4_evaluator_contract_v1",
            "deterministic": self.deterministic,
            "evaluator_id": self.evaluator_id,
            "implementation_hash": self.implementation_hash,
            "implementation_path": self.implementation_path,
            "llm_free": self.llm_free,
            "response_policy_hash": self.response_policy_hash,
            "runtime_outcomes": list(V4_RUNTIME_OUTCOMES),
            "schema_version": FORMAL_V4_SCHEMA_VERSION,
            "trace_contract_hash": self.trace_contract_hash,
            "trigger_policy_hash": self.trigger_policy_hash,
        }

    @property
    def contract_hash(self) -> str:
        return canonical_document_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "contract_hash": self.contract_hash}


@dataclass(frozen=True)
class FormalV4PortfolioAuthorityV1:
    method_id: str
    config_id: str
    experiment_id: str
    portfolio_id: str
    source_commit: str
    descriptors: tuple[FormalV4RuleDescriptorV1, ...]
    relation_authority_binding: FormalV4ArtifactBindingV1
    numeric_authority_binding: FormalV4ArtifactBindingV1
    feature_contract_binding: FormalV4ArtifactBindingV1
    file_contract_binding: FormalV4ArtifactBindingV1
    sampling_contract_binding: FormalV4ArtifactBindingV1
    evaluator_contract_hash: str
    allowed_split_roles: tuple[str, ...]
    authority_family: str = FORMAL_V4_AUTHORITY_FAMILY
    canonical_rule_v1_authoritative: bool = False
    verifier_v1_authoritative: bool = False
    canonical_to_v4_bridge_used: bool = False
    heldout_authorized: bool = False

    def __post_init__(self) -> None:
        for name in (
            "method_id",
            "config_id",
            "experiment_id",
            "portfolio_id",
        ):
            _text(getattr(self, name), name)
        _git_commit(self.source_commit, "source_commit")
        _hash(self.evaluator_contract_hash, "evaluator_contract_hash")
        for name in (
            "relation_authority_binding",
            "numeric_authority_binding",
            "feature_contract_binding",
            "file_contract_binding",
            "sampling_contract_binding",
        ):
            if type(getattr(self, name)) is not FormalV4ArtifactBindingV1:
                _fail("V4_PORTFOLIO_BINDING_TYPE_INVALID", f"{name} type differs")
        descriptors = _exact_tuple(self.descriptors, "descriptors")
        if not descriptors or any(type(item) is not FormalV4RuleDescriptorV1 for item in descriptors):
            _fail("V4_PORTFOLIO_EMPTY_OR_INVALID", "portfolio requires typed descriptors")
        if len({item.descriptor_hash for item in descriptors}) != len(descriptors):
            _fail("V4_PORTFOLIO_DESCRIPTOR_DUPLICATE", "descriptor hashes duplicate")
        if len({item.relation_id for item in descriptors}) != len(descriptors):
            _fail("V4_PORTFOLIO_RELATION_DUPLICATE", "relation IDs duplicate")
        if any(item.numeric_authority_hash != self.numeric_authority_binding.content_sha256 for item in descriptors):
            _fail("V4_NUMERIC_AUTHORITY_MISMATCH", "descriptor numeric authority differs")
        roles = _exact_tuple(self.allowed_split_roles, "allowed_split_roles")
        if roles != ("DEVELOPMENT_TEST1",):
            _fail("V4_SPLIT_ROLE_INVALID", "V2 runtime is development-test1 only")
        if self.authority_family != FORMAL_V4_AUTHORITY_FAMILY:
            _fail("V4_AUTHORITY_FAMILY_INVALID", "authority family must be FORMAL_V4")
        for name in (
            "canonical_rule_v1_authoritative",
            "verifier_v1_authoritative",
            "canonical_to_v4_bridge_used",
            "heldout_authorized",
        ):
            if type(getattr(self, name)) is not bool or getattr(self, name):
                _fail("V4_CLAIM_BOUNDARY_VIOLATION", f"{name} must be false")

    @property
    def descriptor_set_hash(self) -> str:
        return canonical_document_hash_v1(
            {
                "ordered_descriptor_hashes": [
                    item.descriptor_hash for item in self.descriptors
                ],
                "portfolio_id": self.portfolio_id,
            }
        )

    def _payload(self) -> dict[str, Any]:
        return {
            "allowed_split_roles": list(self.allowed_split_roles),
            "artifact_type": "validation_v2_formal_v4_portfolio_authority_v1",
            "authority_family": self.authority_family,
            "canonical_rule_v1_authoritative": self.canonical_rule_v1_authoritative,
            "canonical_to_v4_bridge_used": self.canonical_to_v4_bridge_used,
            "config_id": self.config_id,
            "descriptor_set_hash": self.descriptor_set_hash,
            "descriptors": [item.to_dict() for item in self.descriptors],
            "evaluator_contract_hash": self.evaluator_contract_hash,
            "experiment_id": self.experiment_id,
            "feature_contract_binding": self.feature_contract_binding.to_dict(),
            "file_contract_binding": self.file_contract_binding.to_dict(),
            "heldout_authorized": self.heldout_authorized,
            "method_id": self.method_id,
            "numeric_authority_binding": self.numeric_authority_binding.to_dict(),
            "portfolio_id": self.portfolio_id,
            "relation_authority_binding": self.relation_authority_binding.to_dict(),
            "sampling_contract_binding": self.sampling_contract_binding.to_dict(),
            "schema_version": FORMAL_V4_SCHEMA_VERSION,
            "source_commit": self.source_commit,
            "verifier_v1_authoritative": self.verifier_v1_authoritative,
        }

    @property
    def authority_hash(self) -> str:
        return canonical_document_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "authority_hash": self.authority_hash}


@dataclass(frozen=True)
class FormalV4RuntimeAuthorizationReceiptV1:
    authorization_id: str
    authority_hash: str
    portfolio_id: str
    descriptor_set_hash: str
    numeric_authority_hash: str
    evaluator_contract_hash: str
    runtime_config_hash: str
    feature_contract_hash: str
    file_contract_hash: str
    sampling_contract_hash: str
    execution_context_hash: str
    split_role: str
    authorization_hash: str
    authority_family: str = FORMAL_V4_AUTHORITY_FAMILY
    label_access_before_prediction_freeze: bool = False
    heldout_authorized: bool = False

    def __post_init__(self) -> None:
        _text(self.authorization_id, "authorization_id")
        _text(self.portfolio_id, "portfolio_id")
        for name in (
            "authority_hash",
            "descriptor_set_hash",
            "numeric_authority_hash",
            "evaluator_contract_hash",
            "runtime_config_hash",
            "feature_contract_hash",
            "file_contract_hash",
            "sampling_contract_hash",
            "execution_context_hash",
            "authorization_hash",
        ):
            _hash(getattr(self, name), name)
        if self.split_role != "DEVELOPMENT_TEST1":
            _fail("V4_RUNTIME_SPLIT_PROHIBITED", "only development test1 is authorized")
        if self.authority_family != FORMAL_V4_AUTHORITY_FAMILY:
            _fail("V4_AUTHORITY_FAMILY_INVALID", "receipt authority family differs")
        if self.label_access_before_prediction_freeze or self.heldout_authorized:
            _fail("V4_RUNTIME_BOUNDARY_VIOLATION", "label/held-out boundary differs")

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_formal_v4_runtime_authorization_v1",
            "authority_family": self.authority_family,
            "authority_hash": self.authority_hash,
            "authorization_id": self.authorization_id,
            "descriptor_set_hash": self.descriptor_set_hash,
            "evaluator_contract_hash": self.evaluator_contract_hash,
            "execution_context_hash": self.execution_context_hash,
            "feature_contract_hash": self.feature_contract_hash,
            "file_contract_hash": self.file_contract_hash,
            "heldout_authorized": self.heldout_authorized,
            "label_access_before_prediction_freeze": self.label_access_before_prediction_freeze,
            "numeric_authority_hash": self.numeric_authority_hash,
            "portfolio_id": self.portfolio_id,
            "runtime_config_hash": self.runtime_config_hash,
            "sampling_contract_hash": self.sampling_contract_hash,
            "schema_version": FORMAL_V4_SCHEMA_VERSION,
            "split_role": self.split_role,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "authorization_hash": self.authorization_hash}


@dataclass(frozen=True)
class FormalV4AuthorizedRuntimeV1:
    authority: FormalV4PortfolioAuthorityV1
    evaluator: FormalV4EvaluatorContractV1
    receipt: FormalV4RuntimeAuthorizationReceiptV1
    execution_context: FormalV4ExecutionContextV1
    _capability: object | None = field(default=None, repr=False, compare=False)

    @property
    def runtime_authorized(self) -> bool:
        return self._capability is _AUTHORIZATION_CAPABILITY


def _read_exact_json_object_v1(repository_root: Path, binding: FormalV4ArtifactBindingV1) -> dict[str, Any]:
    binding.verify(repository_root)
    raw = _resolve_bound_file(repository_root, binding.relative_path).read_bytes()
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("V4_BOUND_ARTIFACT_JSON_INVALID", f"artifact is not UTF-8 JSON: {binding.artifact_id}")
        raise AssertionError from exc
    if type(document) is not dict:
        _fail("V4_BOUND_ARTIFACT_JSON_TYPE_INVALID", f"artifact is not an exact object: {binding.artifact_id}")
    return document


def _validate_descriptor_materialization_v1(
    descriptors: tuple[FormalV4RuleDescriptorV1, ...],
    *,
    relation_authority_binding: FormalV4ArtifactBindingV1,
    numeric_authority_binding: FormalV4ArtifactBindingV1,
    repository_root: Path,
) -> None:
    relation_document = _read_exact_json_object_v1(repository_root, relation_authority_binding)
    numeric_document = _read_exact_json_object_v1(repository_root, numeric_authority_binding)
    if set(relation_document) != {"artifact_type", "relations", "schema_version"}:
        _fail("V4_RELATION_AUTHORITY_SCHEMA_INVALID", "relation authority keys differ")
    if (
        relation_document["artifact_type"] != "validation_v2_formal_v4_relation_authority_v1"
        or relation_document["schema_version"] != FORMAL_V4_SCHEMA_VERSION
        or type(relation_document["relations"]) is not list
    ):
        _fail("V4_RELATION_AUTHORITY_SCHEMA_INVALID", "relation authority contract differs")
    if set(numeric_document) != {"artifact_type", "bindings", "schema_version"}:
        _fail("V4_NUMERIC_AUTHORITY_SCHEMA_INVALID", "numeric authority keys differ")
    if (
        numeric_document["artifact_type"] != "validation_v2_formal_v4_numeric_authority_v1"
        or numeric_document["schema_version"] != FORMAL_V4_SCHEMA_VERSION
        or type(numeric_document["bindings"]) is not list
    ):
        _fail("V4_NUMERIC_AUTHORITY_SCHEMA_INVALID", "numeric authority contract differs")

    relation_records: dict[str, dict[str, Any]] = {}
    expected_relation_keys = {
        "relation_id",
        "relation_binding_hash",
        "semantic_execution_hash",
        "source",
        "target",
        "source_direction",
        "target_direction",
        "selected_horizon_seconds",
    }
    for record in relation_document["relations"]:
        if type(record) is not dict or set(record) != expected_relation_keys:
            _fail("V4_RELATION_RECORD_SCHEMA_INVALID", "relation record keys differ")
        relation_id = _text(record["relation_id"], "relation_id")
        if relation_id in relation_records:
            _fail("V4_RELATION_RECORD_DUPLICATE", "relation record duplicates")
        relation_records[relation_id] = record

    numeric_records: dict[tuple[str, str], dict[str, Any]] = {}
    expected_numeric_keys = {"numeric_role", "reference_hash", "reference_id", "relation_id", "value"}
    for record in numeric_document["bindings"]:
        if type(record) is not dict or set(record) != expected_numeric_keys:
            _fail("V4_NUMERIC_RECORD_SCHEMA_INVALID", "numeric record keys differ")
        key = (_text(record["relation_id"], "relation_id"), _text(record["numeric_role"], "numeric_role"))
        if type(record["value"]) is not float or not math.isfinite(record["value"]):
            _fail("V4_NUMERIC_RECORD_VALUE_INVALID", "numeric authority value must be finite float")
        reference_payload = {
            "numeric_role": record["numeric_role"],
            "reference_id": record["reference_id"],
            "relation_id": record["relation_id"],
            "value": record["value"],
        }
        if record["reference_hash"] != canonical_document_hash_v1(reference_payload):
            _fail("V4_NUMERIC_REFERENCE_HASH_MISMATCH", "numeric value/reference hash differs")
        if key in numeric_records:
            _fail("V4_NUMERIC_RECORD_DUPLICATE", "numeric binding record duplicates")
        numeric_records[key] = record

    if set(relation_records) != {item.relation_id for item in descriptors}:
        _fail("V4_RELATION_AUTHORITY_COVERAGE_MISMATCH", "descriptor and relation authority sets differ")
    expected_numeric_keys_set = {
        (item.relation_id, role) for item in descriptors for role in V4_NUMERIC_ROLES
    }
    if set(numeric_records) != expected_numeric_keys_set:
        _fail("V4_NUMERIC_AUTHORITY_COVERAGE_MISMATCH", "descriptor and numeric authority sets differ")

    for descriptor in descriptors:
        record = relation_records[descriptor.relation_id]
        expected_relation_values = {
            "relation_id": descriptor.relation_id,
            "relation_binding_hash": descriptor.relation_binding_hash,
            "semantic_execution_hash": descriptor.semantic_execution_hash,
            "source": descriptor.source,
            "target": descriptor.target,
            "source_direction": descriptor.source_direction,
            "target_direction": descriptor.target_direction,
            "selected_horizon_seconds": descriptor.selected_horizon_seconds,
        }
        if record != expected_relation_values:
            _fail("V4_RELATION_RECORD_MISMATCH", f"relation authority differs: {descriptor.relation_id}")
        for binding in descriptor.numeric_reference_bindings:
            numeric_record = numeric_records[(descriptor.relation_id, binding.numeric_role)]
            expected_numeric_values = {
                "numeric_role": binding.numeric_role,
                "reference_hash": binding.reference_hash,
                "reference_id": binding.reference_id,
                "relation_id": descriptor.relation_id,
                "value": numeric_record["value"],
            }
            if numeric_record != expected_numeric_values:
                _fail("V4_NUMERIC_RECORD_MISMATCH", f"numeric authority differs: {descriptor.relation_id}")
        if descriptor.numeric_authority_hash != numeric_authority_binding.content_sha256:
            _fail("V4_NUMERIC_AUTHORITY_HASH_MISMATCH", "descriptor numeric authority bytes differ")


def _validate_execution_context_bindings_v1(
    authority: FormalV4PortfolioAuthorityV1,
    evaluator: FormalV4EvaluatorContractV1,
    context: FormalV4ExecutionContextV1,
) -> None:
    if context.source_commit != authority.source_commit:
        _fail("V4_EXECUTION_SOURCE_COMMIT_MISMATCH", "execution source commit differs")
    expected_pairs = (
        (context.relation_authority_binding, authority.relation_authority_binding),
        (context.numeric_authority_binding, authority.numeric_authority_binding),
        (context.feature_contract_binding, authority.feature_contract_binding),
        (context.file_contract_binding, authority.file_contract_binding),
        (context.sampling_contract_binding, authority.sampling_contract_binding),
    )
    if any(observed != expected for observed, expected in expected_pairs):
        _fail("V4_EXECUTION_ARTIFACT_BINDING_MISMATCH", "execution artifact bindings differ")
    if (
        context.evaluator_implementation_binding.relative_path != evaluator.implementation_path
        or context.evaluator_implementation_binding.content_sha256 != evaluator.implementation_hash
    ):
        _fail("V4_EXECUTION_EVALUATOR_BINDING_MISMATCH", "evaluator implementation bytes differ")


def load_formal_v4_numeric_values_v1(
    *,
    descriptor: FormalV4RuleDescriptorV1,
    numeric_authority_binding: FormalV4ArtifactBindingV1,
    repository_root: Path,
) -> tuple[tuple[str, str, float], ...]:
    """Load exact value-bearing numeric records from the bound private artifact."""

    return load_formal_v4_numeric_value_map_v1(
        descriptors=(descriptor,),
        numeric_authority_binding=numeric_authority_binding,
        repository_root=repository_root,
    )[0][1]


def load_formal_v4_numeric_value_map_v1(
    *,
    descriptors: Sequence[FormalV4RuleDescriptorV1],
    numeric_authority_binding: FormalV4ArtifactBindingV1,
    repository_root: Path,
) -> tuple[tuple[str, tuple[tuple[str, str, float], ...]], ...]:
    """Load one bound numeric document and project all requested descriptors.

    The returned order exactly follows ``descriptors``.  This is a batch I/O
    adapter only: every descriptor/reference check is identical to the single
    descriptor loader and no numeric selection or transformation occurs.
    """

    if type(descriptors) not in {tuple, list} or not descriptors:
        _fail("V4_DESCRIPTOR_SEQUENCE_INVALID", "descriptors must be a non-empty sequence")
    descriptor_rows = tuple(descriptors)
    if any(type(item) is not FormalV4RuleDescriptorV1 for item in descriptor_rows):
        _fail("V4_DESCRIPTOR_TYPE_INVALID", "descriptor type differs")
    if len({item.relation_id for item in descriptor_rows}) != len(descriptor_rows):
        _fail("V4_DESCRIPTOR_RELATION_DUPLICATE", "descriptor relation IDs duplicate")
    document = _read_exact_json_object_v1(repository_root, numeric_authority_binding)
    if (
        set(document) != {"artifact_type", "bindings", "schema_version"}
        or document.get("artifact_type") != "validation_v2_formal_v4_numeric_authority_v1"
        or document.get("schema_version") != FORMAL_V4_SCHEMA_VERSION
        or type(document.get("bindings")) is not list
    ):
        _fail("V4_NUMERIC_AUTHORITY_SCHEMA_INVALID", "numeric authority contract differs")
    by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for record in document["bindings"]:
        if type(record) is not dict or set(record) != {"numeric_role", "reference_hash", "reference_id", "relation_id", "value"}:
            _fail("V4_NUMERIC_RECORD_SCHEMA_INVALID", "numeric record keys differ")
        key = (record.get("relation_id"), record.get("numeric_role"))
        if key in by_key:
            _fail("V4_NUMERIC_RECORD_DUPLICATE", "numeric binding record duplicates")
        by_key[key] = record
    result: list[tuple[str, tuple[tuple[str, str, float], ...]]] = []
    for descriptor in descriptor_rows:
        values: list[tuple[str, str, float]] = []
        for binding in descriptor.numeric_reference_bindings:
            record = by_key.get((descriptor.relation_id, binding.numeric_role))
            if record is None:
                _fail("V4_NUMERIC_RECORD_MISSING", "numeric binding record missing")
            value = record["value"]
            payload = {
                "numeric_role": binding.numeric_role,
                "reference_id": binding.reference_id,
                "relation_id": descriptor.relation_id,
                "value": value,
            }
            if (
                record["reference_id"] != binding.reference_id
                or record["reference_hash"] != binding.reference_hash
                or binding.reference_hash != canonical_document_hash_v1(payload)
                or type(value) is not float
                or not math.isfinite(value)
            ):
                _fail(
                    "V4_NUMERIC_VALUE_BINDING_MISMATCH",
                    "numeric value/reference binding differs",
                )
            values.append((binding.numeric_role, binding.reference_id, value))
        result.append((descriptor.relation_id, tuple(values)))
    return tuple(result)


def build_formal_v4_portfolio_authority_v1(
    *,
    method_id: str,
    config_id: str,
    experiment_id: str,
    portfolio_id: str,
    source_commit: str,
    descriptors: Sequence[FormalV4RuleDescriptorV1],
    relation_authority_binding: FormalV4ArtifactBindingV1,
    numeric_authority_binding: FormalV4ArtifactBindingV1,
    feature_contract_binding: FormalV4ArtifactBindingV1,
    file_contract_binding: FormalV4ArtifactBindingV1,
    sampling_contract_binding: FormalV4ArtifactBindingV1,
    evaluator: FormalV4EvaluatorContractV1,
    repository_root: Path,
) -> FormalV4PortfolioAuthorityV1:
    if type(evaluator) is not FormalV4EvaluatorContractV1:
        _fail("V4_EVALUATOR_TYPE_INVALID", "evaluator contract type differs")
    if type(descriptors) not in {list, tuple}:
        _fail("V4_DESCRIPTOR_SEQUENCE_INVALID", "descriptors must be a list or tuple")
    for binding in (
        relation_authority_binding,
        numeric_authority_binding,
        feature_contract_binding,
        file_contract_binding,
        sampling_contract_binding,
    ):
        if type(binding) is not FormalV4ArtifactBindingV1:
            _fail("V4_PORTFOLIO_BINDING_TYPE_INVALID", "portfolio binding type differs")
        binding.verify(repository_root)
    _validate_descriptor_materialization_v1(
        tuple(descriptors),
        relation_authority_binding=relation_authority_binding,
        numeric_authority_binding=numeric_authority_binding,
        repository_root=repository_root,
    )
    return FormalV4PortfolioAuthorityV1(
        method_id=method_id,
        config_id=config_id,
        experiment_id=experiment_id,
        portfolio_id=portfolio_id,
        source_commit=source_commit,
        descriptors=tuple(descriptors),
        relation_authority_binding=relation_authority_binding,
        numeric_authority_binding=numeric_authority_binding,
        feature_contract_binding=feature_contract_binding,
        file_contract_binding=file_contract_binding,
        sampling_contract_binding=sampling_contract_binding,
        evaluator_contract_hash=evaluator.contract_hash,
        allowed_split_roles=("DEVELOPMENT_TEST1",),
    )


def validate_formal_v4_portfolio_authority_v1(
    authority: FormalV4PortfolioAuthorityV1,
    *,
    evaluator: FormalV4EvaluatorContractV1,
    expected_source_commit: str,
    repository_root: Path,
) -> str:
    if type(authority) is not FormalV4PortfolioAuthorityV1:
        _fail("V4_AUTHORITY_TYPE_INVALID", "authority type differs")
    if type(evaluator) is not FormalV4EvaluatorContractV1:
        _fail("V4_EVALUATOR_TYPE_INVALID", "evaluator type differs")
    if authority.source_commit != _git_commit(expected_source_commit, "expected_source_commit"):
        _fail("V4_SOURCE_COMMIT_STALE", "source commit differs")
    if authority.evaluator_contract_hash != evaluator.contract_hash:
        _fail("V4_EVALUATOR_BINDING_MISMATCH", "evaluator contract differs")
    for binding in (
        authority.relation_authority_binding,
        authority.numeric_authority_binding,
        authority.feature_contract_binding,
        authority.file_contract_binding,
        authority.sampling_contract_binding,
    ):
        binding.verify(repository_root)
    _validate_descriptor_materialization_v1(
        authority.descriptors,
        relation_authority_binding=authority.relation_authority_binding,
        numeric_authority_binding=authority.numeric_authority_binding,
        repository_root=repository_root,
    )
    replay = FormalV4PortfolioAuthorityV1(
        method_id=authority.method_id,
        config_id=authority.config_id,
        experiment_id=authority.experiment_id,
        portfolio_id=authority.portfolio_id,
        source_commit=authority.source_commit,
        descriptors=tuple(authority.descriptors),
        relation_authority_binding=authority.relation_authority_binding,
        numeric_authority_binding=authority.numeric_authority_binding,
        feature_contract_binding=authority.feature_contract_binding,
        file_contract_binding=authority.file_contract_binding,
        sampling_contract_binding=authority.sampling_contract_binding,
        evaluator_contract_hash=authority.evaluator_contract_hash,
        allowed_split_roles=tuple(authority.allowed_split_roles),
        authority_family=authority.authority_family,
        canonical_rule_v1_authoritative=authority.canonical_rule_v1_authoritative,
        verifier_v1_authoritative=authority.verifier_v1_authoritative,
        canonical_to_v4_bridge_used=authority.canonical_to_v4_bridge_used,
        heldout_authorized=authority.heldout_authorized,
    )
    if replay.to_dict() != authority.to_dict():
        _fail("V4_AUTHORITY_REPLAY_MISMATCH", "authority replay differs")
    return authority.authority_hash


def authorize_formal_v4_runtime_v1(
    authority: FormalV4PortfolioAuthorityV1,
    evaluator: FormalV4EvaluatorContractV1,
    *,
    expected_source_commit: str,
    execution_context: FormalV4ExecutionContextV1,
    repository_root: Path,
    split_role: str,
) -> FormalV4AuthorizedRuntimeV1:
    if type(execution_context) is not FormalV4ExecutionContextV1:
        _fail("V4_EXECUTION_CONTEXT_TYPE_INVALID", "execution context type differs")
    execution_context.verify(repository_root)
    _validate_execution_context_bindings_v1(authority, evaluator, execution_context)
    authority_hash = validate_formal_v4_portfolio_authority_v1(
        authority,
        evaluator=evaluator,
        expected_source_commit=expected_source_commit,
        repository_root=repository_root,
    )
    if split_role not in authority.allowed_split_roles:
        _fail("V4_RUNTIME_SPLIT_PROHIBITED", "split role is not authorized")
    base = {
        "artifact_type": "validation_v2_formal_v4_runtime_authorization_v1",
        "authority_family": FORMAL_V4_AUTHORITY_FAMILY,
        "authority_hash": authority_hash,
        "authorization_id": f"V2-AUTH-{authority_hash[:16]}",
        "descriptor_set_hash": authority.descriptor_set_hash,
        "evaluator_contract_hash": evaluator.contract_hash,
        "execution_context_hash": execution_context.context_hash,
        "feature_contract_hash": authority.feature_contract_binding.content_sha256,
        "file_contract_hash": authority.file_contract_binding.content_sha256,
        "heldout_authorized": False,
        "label_access_before_prediction_freeze": False,
        "numeric_authority_hash": authority.numeric_authority_binding.content_sha256,
        "portfolio_id": authority.portfolio_id,
        "runtime_config_hash": execution_context.runtime_config_hash,
        "sampling_contract_hash": authority.sampling_contract_binding.content_sha256,
        "schema_version": FORMAL_V4_SCHEMA_VERSION,
        "split_role": split_role,
    }
    receipt = FormalV4RuntimeAuthorizationReceiptV1(
        authorization_id=base["authorization_id"],
        authority_hash=authority_hash,
        portfolio_id=authority.portfolio_id,
        descriptor_set_hash=authority.descriptor_set_hash,
        numeric_authority_hash=authority.numeric_authority_binding.content_sha256,
        evaluator_contract_hash=evaluator.contract_hash,
        runtime_config_hash=execution_context.runtime_config_hash,
        feature_contract_hash=authority.feature_contract_binding.content_sha256,
        file_contract_hash=authority.file_contract_binding.content_sha256,
        sampling_contract_hash=authority.sampling_contract_binding.content_sha256,
        execution_context_hash=execution_context.context_hash,
        split_role=split_role,
        authorization_hash=canonical_document_hash_v1(base),
    )
    bundle = FormalV4AuthorizedRuntimeV1(
        authority=authority,
        evaluator=evaluator,
        receipt=receipt,
        execution_context=execution_context,
        _capability=_AUTHORIZATION_CAPABILITY,
    )
    validate_formal_v4_runtime_authorization_v1(
        bundle,
        execution_context=execution_context,
        repository_root=repository_root,
    )
    return bundle


def validate_formal_v4_runtime_authorization_v1(
    bundle: FormalV4AuthorizedRuntimeV1,
    *,
    execution_context: FormalV4ExecutionContextV1,
    repository_root: Path,
) -> str:
    if type(bundle) is not FormalV4AuthorizedRuntimeV1 or not bundle.runtime_authorized:
        _fail("V4_RUNTIME_CAPABILITY_MISSING", "runtime bundle is not authorized")
    authority = bundle.authority
    evaluator = bundle.evaluator
    receipt = bundle.receipt
    if type(execution_context) is not FormalV4ExecutionContextV1 or execution_context != bundle.execution_context:
        _fail("V4_EXECUTION_CONTEXT_MISMATCH", "execution context differs from authorization")
    execution_context.verify(repository_root)
    _validate_execution_context_bindings_v1(authority, evaluator, execution_context)
    validate_formal_v4_portfolio_authority_v1(
        authority,
        evaluator=evaluator,
        expected_source_commit=execution_context.source_commit,
        repository_root=repository_root,
    )
    payload = receipt._payload()
    observed = canonical_document_hash_v1(payload)
    if receipt.authorization_hash != observed:
        _fail("V4_RUNTIME_AUTHORIZATION_HASH_MISMATCH", "receipt hash differs")
    if (
        receipt.authority_hash != authority.authority_hash
        or receipt.portfolio_id != authority.portfolio_id
        or receipt.descriptor_set_hash != authority.descriptor_set_hash
        or receipt.numeric_authority_hash != authority.numeric_authority_binding.content_sha256
        or receipt.evaluator_contract_hash != evaluator.contract_hash
        or receipt.feature_contract_hash != authority.feature_contract_binding.content_sha256
        or receipt.file_contract_hash != authority.file_contract_binding.content_sha256
        or receipt.sampling_contract_hash != authority.sampling_contract_binding.content_sha256
        or receipt.runtime_config_hash != execution_context.runtime_config_hash
        or receipt.execution_context_hash != execution_context.context_hash
    ):
        _fail("V4_RUNTIME_AUTHORIZATION_BINDING_MISMATCH", "receipt binding differs")
    if receipt.authorization_id != f"V2-AUTH-{authority.authority_hash[:16]}":
        _fail("V4_RUNTIME_AUTHORIZATION_ID_MISMATCH", "authorization ID differs")
    return receipt.authorization_hash
