"""Authorization-gated first real INNER D1 utility execution bridge.

This module is deliberately external to the independently audited R3 evaluator.
It replays the exact committed authorization artifact graph, issues one
process-local execution token, and ports the audited deterministic semantics to
separate real types.  The public real entry point accepts no arguments.

Private paths, feature values, label values, attack intervals, and numeric
authority values are never returned or serialized by this module.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field, replace
from datetime import datetime
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import shlex
import statistics
import subprocess
from typing import Any, Mapping, Sequence
import weakref

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_utility_evaluator_authority_v1 as evaluator_authority
from paperworks.v6 import task039e3_r2r_utility_evaluator_census_v1 as evaluator_census
from paperworks.v6 import task039e3_r2r_utility_evaluator_input_v1 as evaluator_input
from paperworks.v6 import task039e3_r2r_utility_evaluator_metrics_v1 as evaluator_metrics
from paperworks.v6 import task039e3_r2r_utility_evaluator_rule_engine_v1 as evaluator_rule
from paperworks.v6 import task039e3_r2r_utility_evaluator_v1 as evaluator
from paperworks.v6 import task039e3_r2r_utility_inner_execution_authorization_v1 as authorization_v1
from paperworks.v6 import task039e3_r2r_utility_normal_only_authority_v1 as main_authority
from paperworks.v6 import task039e3_r2r_utility_protocol_v3 as v3
from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D1-EXECUTION-V1"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d1_execution_v1"
SCIENTIFIC_STATUS = "D1_EXECUTED_RESULT_INTEGRITY_AUDIT_PENDING"
EXECUTION_VERSION = "TASK039E3_R2R_UTILITY_INNER_D1_EXECUTION_V1"
EXECUTION_MODE = "REAL_INNER_D1_RULE_ONLY"
DIFFERENTIAL_MODE = "NONSCIENTIFIC_DIFFERENTIAL_EQUIVALENCE"
AUTHORIZATION_SCOPE = "HAI_23_05_P1_TEST1_COMMON42_D1_RULE_ONLY_INNER_V1"

AUTHORIZATION_REPORT_COMMIT = "7df8edf24993bf42401b487c56a188ce7546da91"
AUTHORIZATION_HASH = "deb08014de20c398d2dcde046e14b505a65af2d52cb6eb309fc8188f020b5834"
CUSTODY_PREFLIGHT_HASH = "3acff12cb2135b86539720e792d6e01075808ea84b6939b06909d397b1b43129"
READINESS_HASH = "7a587c921f805cbc4b44f9b8f79416e86bf6596fa4aa2df6e9d3cb19b5351038"
BUNDLE_HASH = "6ffa905c3a838e0e76bdb002b94adef794d2ea78f74e17b2750bc29b6620e752"
RECEIPT_HASH = "080823c300b3afc8b4660cf48dfc55b134ae05d599f1f851322710b20ebc1ab1"

R3_IMPLEMENTATION_IDENTITY = "af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5"
R3_EVALUATOR_AUTHORITY_BUNDLE_HASH = "0510da125dd8a799c988927ba49ecb784cad5ea12b05b41e31406effe23051c9"
V4_AUTHORITY_HASH = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"
DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
INNER_SPLIT_ID = "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"
TEST1_FEATURE_SHA256 = "78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be"
TEST1_LABEL_SHA256 = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
MAIN_REGISTRY_HASH = "9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0"
SUPPLEMENT_REGISTRY_HASH = "12ec7f50a953e097cd7cbe3ac93c7cabfb669130612d7f30ab3b19df85289aaf"
MAIN_DESCRIPTOR_HASH = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
SUPPLEMENT_DESCRIPTOR_HASH = "d45af926511c669ec04dd13c36823d454b67ccaa98ae0a7be2919b02652bd927"
COMBINED_SOURCE_CENSUS_CONTRACT_HASH = "cb53d0e4533ebadb61edbdc72b549fe47b46c8dcc4621841aac93a007660ced9"
EXPECTED_ROW_COUNT = 54_000
TEST1_FEATURE_FILENAME = "hai-test1.csv"
TEST1_LABEL_FILENAME = "label-test1.csv"
FULL_CENSUS_DENOMINATOR_POLICY = (
    "ALL_AUTOMATICALLY_ENUMERATED_APPLICABLE_CANONICAL_OPPORTUNITIES"
)
ATTACK_EVENT_POLICY = "MAXIMAL_CONTIGUOUS_STRICT_LABEL_ONE_RUNS_FILE_LOCAL"
ALARM_EPISODE_POLICY = (
    "MAXIMAL_CONTIGUOUS_UNIQUE_ONE_SECOND_DECISION_INDICES_FILE_LOCAL"
)
ATTACK_EVENT_RECALL_FORMULA = (
    "ATTACK_EVENTS_OVERLAPPED_BY_AT_LEAST_ONE_ALARM_EPISODE_DIVIDED_BY_ALL_ATTACK_EVENTS"
)
NORMAL_FAR_FORMULA = (
    "ALARM_EPISODES_WITH_NO_ATTACK_TIMESTAMP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
)

DIFFERENTIAL_SEMANTIC_CASES = 32
EXPECTED_INDEPENDENT_ATTACKS = 40

_ARTIFACT_PATHS = {
    "authorization": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_PORTABLE_PREFLIGHT_R1_AUTHORIZATION.json",
    "preflight": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_PORTABLE_PREFLIGHT_R1_PREFLIGHT.json",
    "readiness": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_PORTABLE_PREFLIGHT_R1_READINESS.json",
    "bundle": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_PORTABLE_PREFLIGHT_R1_BUNDLE.json",
    "receipt": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_PORTABLE_PREFLIGHT_R1_RECEIPT.json",
}
_ARTIFACT_HASHES = {
    "authorization": AUTHORIZATION_HASH,
    "preflight": CUSTODY_PREFLIGHT_HASH,
    "readiness": READINESS_HASH,
    "bundle": BUNDLE_HASH,
    "receipt": RECEIPT_HASH,
}
_APPROVED_LOCAL_BINDING_KEYS = frozenset(
    {
        authorization_v1.HAI_DATA_ROOT_ENV,
        authorization_v1.MAIN_REGISTRY_ENV,
        authorization_v1.MAIN_LOCATOR_ENV,
        authorization_v1.SUPPLEMENT_REGISTRY_ENV,
        authorization_v1.SUPPLEMENT_LOCATOR_ENV,
    }
)

BRIDGE_SEMANTIC_POLICY = {
    "execution_version": EXECUTION_VERSION,
    "execution_mode": EXECUTION_MODE,
    "authorization_hash": AUTHORIZATION_HASH,
    "authorization_report_commit": AUTHORIZATION_REPORT_COMMIT,
    "r3_implementation_identity": R3_IMPLEMENTATION_IDENTITY,
    "r3_evaluator_authority_bundle_hash": R3_EVALUATOR_AUTHORITY_BUNDLE_HASH,
    "v4_authority_hash": V4_AUTHORITY_HASH,
    "common_portfolio": "COMMON-42",
    "common_relation_count": 42,
    "test1_only": True,
    "label_after_prediction_freeze": True,
    "full_census_no_caller_denominator": True,
    "d0_authorized": False,
    "d2_authorized": False,
    "detector_authorized": False,
    "outer_authorized": False,
    "test2_authorized": False,
    "execution_attempts": 1,
    "execution_retries": 0,
}
BRIDGE_IDENTITY = stable_hash_v1(BRIDGE_SEMANTIC_POLICY)


class InnerD1ExecutionV1Error(ValueError):
    """A fixed execution, custody, or semantic invariant differs."""


def _fail(code: str) -> None:
    raise InnerD1ExecutionV1Error(code)


def _repository_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]


def _canonical_self_hash_v1(document: Mapping[str, Any]) -> str:
    value = document.get("artifact_hash")
    if type(value) is not str or re.fullmatch(r"[a-f0-9]{64}", value) is None:
        _fail("COMMITTED_ARTIFACT_HASH_INVALID")
    payload = {key: item for key, item in document.items() if key != "artifact_hash"}
    if stable_hash_v1(payload) != value:
        _fail("COMMITTED_ARTIFACT_SELF_HASH_INVALID")
    return value


def _strict_json_object_v1(content: bytes) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _fail("COMMITTED_ARTIFACT_DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except InnerD1ExecutionV1Error:
        raise
    except Exception as exc:
        raise InnerD1ExecutionV1Error("COMMITTED_ARTIFACT_JSON_INVALID") from exc
    if type(value) is not dict:
        _fail("COMMITTED_ARTIFACT_NOT_OBJECT")
    return value


def _git_output_v1(repository_root: Path, arguments: Sequence[str]) -> bytes:
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=repository_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except Exception as exc:
        raise InnerD1ExecutionV1Error("COMMITTED_GIT_REPLAY_UNAVAILABLE") from exc
    if completed.returncode != 0:
        _fail("COMMITTED_GIT_REPLAY_REJECTED")
    return completed.stdout


def _load_committed_artifact_set_v1() -> dict[str, dict[str, Any]]:
    root = _repository_root_v1()
    if root.is_symlink() or not root.is_dir():
        _fail("COMMITTED_REPOSITORY_ROOT_INVALID")
    _git_output_v1(
        root,
        ("merge-base", "--is-ancestor", AUTHORIZATION_REPORT_COMMIT, "HEAD"),
    )
    result: dict[str, dict[str, Any]] = {}
    for name, relative in _ARTIFACT_PATHS.items():
        path = root / relative
        if path.is_symlink() or not path.is_file():
            _fail("COMMITTED_ARTIFACT_FILE_INVALID")
        try:
            current = path.read_bytes()
        except OSError as exc:
            raise InnerD1ExecutionV1Error("COMMITTED_ARTIFACT_READ_FAILED") from exc
        committed = _git_output_v1(root, ("show", f"{AUTHORIZATION_REPORT_COMMIT}:{relative}"))
        if current != committed:
            _fail("COMMITTED_ARTIFACT_BYTES_DIFFER")
        result[name] = _strict_json_object_v1(current)
    return result


def _validate_committed_artifact_set_v1(
    documents: Mapping[str, Mapping[str, Any]],
) -> None:
    if type(documents) is not dict or set(documents) != set(_ARTIFACT_PATHS):
        _fail("COMMITTED_ARTIFACT_SET_CLOSURE_REJECTED")
    for name, expected_hash in _ARTIFACT_HASHES.items():
        document = documents[name]
        if type(document) is not dict or _canonical_self_hash_v1(document) != expected_hash:
            _fail("COMMITTED_ARTIFACT_IDENTITY_REJECTED")

    authorization = documents["authorization"]
    preflight = documents["preflight"]
    readiness = documents["readiness"]
    bundle = documents["bundle"]
    receipt = documents["receipt"]

    exact_authorization = {
        "authorization_scope": AUTHORIZATION_SCOPE,
        "authorization_version": authorization_v1.AUTHORIZATION_VERSION,
        "inner_authorization_control_revision": "R2_PORTABLE_PREFLIGHT",
        "custody_preflight_hash": CUSTODY_PREFLIGHT_HASH,
        "r3_implementation_identity": R3_IMPLEMENTATION_IDENTITY,
        "evaluator_authority_bundle_hash": R3_EVALUATOR_AUTHORITY_BUNDLE_HASH,
        "v4_authority_hash": V4_AUTHORITY_HASH,
        "common_portfolio": "COMMON-42",
        "common_relation_count": 42,
        "main_descriptor_hash": MAIN_DESCRIPTOR_HASH,
        "main_private_registry_expected_hash": MAIN_REGISTRY_HASH,
        "supplement_descriptor_hash": SUPPLEMENT_DESCRIPTOR_HASH,
        "supplement_private_registry_expected_hash": SUPPLEMENT_REGISTRY_HASH,
        "combined_source_census_contract_hash": COMBINED_SOURCE_CENSUS_CONTRACT_HASH,
        "dataset_manifest_id": DATASET_MANIFEST_ID,
        "inner_split_id": INNER_SPLIT_ID,
        "feature_filename": TEST1_FEATURE_FILENAME,
        "feature_sha256": TEST1_FEATURE_SHA256,
        "label_filename": TEST1_LABEL_FILENAME,
        "label_sha256": TEST1_LABEL_SHA256,
        "expected_physical_row_count": EXPECTED_ROW_COUNT,
        "experiment_arm": "D1",
        "d1_authorized": True,
        "utility_inner_execution_authorized": True,
        "utility_inner_d1_execution_authorization_issued": True,
    }
    if any(authorization.get(key) != value for key, value in exact_authorization.items()):
        _fail("COMMITTED_AUTHORIZATION_SEMANTICS_REJECTED")
    false_authorization_fields = (
        "t2_authorized",
        "d0_authorized",
        "d2_authorized",
        "detector_authorized",
        "outer_authorized",
        "fusion_authorized",
        "threshold_recalibration_authorized",
        "rule_regeneration_authorized",
        "metric_modification_authorized",
        "test2_authorized",
        "utility_inner_d1_executed",
        "utility_outer_execution_authorization_ready",
        "utility_outer_execution_authorized",
        "real_utility_execution_authorized",
    )
    if any(authorization.get(name) is not False for name in false_authorization_fields):
        _fail("COMMITTED_AUTHORIZATION_ESCALATION_REJECTED")

    required_preflight = {
        "authorization_scope": AUTHORIZATION_SCOPE,
        "custody_mode": "REAL_CUSTODY_PREFLIGHT",
        "inner_authorization_control_revision": "R2_PORTABLE_PREFLIGHT",
        "main_registry_expected_hash": MAIN_REGISTRY_HASH,
        "main_registry_observed_hash": MAIN_REGISTRY_HASH,
        "main_locator_schema_valid": True,
        "main_locator_local_only": True,
        "main_locator_registry_binding_match": True,
        "main_locator_materialization_authority_match": True,
        "main_registry_content_hash_match": True,
        "supplement_registry_expected_hash": SUPPLEMENT_REGISTRY_HASH,
        "supplement_registry_observed_hash": SUPPLEMENT_REGISTRY_HASH,
        "supplement_locator_schema_valid": True,
        "supplement_locator_local_only": True,
        "supplement_locator_registry_binding_match": True,
        "supplement_locator_materialization_authority_match": True,
        "supplement_registry_content_hash_match": True,
        "test1_feature_expected_hash": TEST1_FEATURE_SHA256,
        "test1_feature_observed_hash": TEST1_FEATURE_SHA256,
        "test1_feature_hash_match": True,
        "test1_label_expected_hash": TEST1_LABEL_SHA256,
        "test1_label_observed_hash": TEST1_LABEL_SHA256,
        "test1_label_hash_match": True,
        "test2_touched": False,
        "scientific_parsing_performed": False,
    }
    if any(preflight.get(key) != value for key, value in required_preflight.items()):
        _fail("COMMITTED_PREFLIGHT_SEMANTICS_REJECTED")
    zero_preflight_fields = (
        "scientific_feature_parse_count",
        "scientific_label_parse_count",
        "attack_event_derivation_count",
        "rule_execution_count",
        "metric_computation_count",
        "detector_execution_count",
        "real_utility_computations",
        "private_numeric_values_exposed",
        "private_paths_exposed",
    )
    if any(type(preflight.get(name)) is not int or preflight.get(name) != 0 for name in zero_preflight_fields):
        _fail("COMMITTED_PREFLIGHT_ACCESS_REJECTED")

    if (
        readiness.get("authorization_hash") != AUTHORIZATION_HASH
        or readiness.get("custody_preflight_hash") != CUSTODY_PREFLIGHT_HASH
        or readiness.get("authorization_issued") is not True
        or readiness.get("d1_authorized") is not True
        or any(readiness.get(name) is not False for name in ("d0_authorized", "d2_authorized", "detector_authorized", "outer_authorized"))
        or readiness.get("test2_accesses") != 0
        or readiness.get("utility_execution_count") != 0
        or readiness.get("exact_next_task") != TASK_ID
    ):
        _fail("COMMITTED_READINESS_REJECTED")
    if (
        bundle.get("authorization_hash") != AUTHORIZATION_HASH
        or bundle.get("custody_preflight_hash") != CUSTODY_PREFLIGHT_HASH
        or bundle.get("readiness_hash") != READINESS_HASH
        or bundle.get("commit_a") != "157bc470ba1850093a02b5baee3e5eb446071aea"
        or bundle.get("commit_b") != "bbbcf2fff841a33253b6732dd0cdc6af344d6a6f"
    ):
        _fail("COMMITTED_BUNDLE_REJECTED")
    if (
        receipt.get("authorization_hash") != AUTHORIZATION_HASH
        or receipt.get("custody_preflight_hash") != CUSTODY_PREFLIGHT_HASH
        or receipt.get("readiness_hash") != READINESS_HASH
        or receipt.get("bundle_hash") != BUNDLE_HASH
        or receipt.get("exact_next_task") != TASK_ID
        or receipt.get("blockers") != []
    ):
        _fail("COMMITTED_RECEIPT_REJECTED")
    counters = receipt.get("access_counters")
    if type(counters) is not dict or any(type(value) is not int or value != 0 for value in counters.values()):
        _fail("COMMITTED_RECEIPT_ACCESS_REJECTED")


@dataclass(frozen=True)
class CommittedInnerD1ExecutionGrantV1:
    execution_version: str
    authorization_hash: str
    authorization_report_commit: str
    custody_preflight_hash: str
    readiness_hash: str
    bundle_hash: str
    receipt_hash: str
    r3_implementation_identity: str
    evaluator_authority_bundle_hash: str
    v4_authority_hash: str
    common_portfolio: str
    common_relation_count: int
    main_descriptor_hash: str
    main_registry_hash: str
    supplement_descriptor_hash: str
    supplement_registry_hash: str
    dataset_manifest_id: str
    inner_split_id: str
    feature_sha256: str
    label_sha256: str
    authorization_scope: str
    d1_authorized: bool
    d0_authorized: bool
    d2_authorized: bool
    detector_authorized: bool
    outer_authorized: bool
    test2_authorized: bool
    grant_hash: str

    def _payload(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in self.__dict__.items()
            if key != "grant_hash"
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {**self._payload(), "grant_hash": self.grant_hash}


def _expected_grant_v1() -> CommittedInnerD1ExecutionGrantV1:
    provisional = CommittedInnerD1ExecutionGrantV1(
        EXECUTION_VERSION,
        AUTHORIZATION_HASH,
        AUTHORIZATION_REPORT_COMMIT,
        CUSTODY_PREFLIGHT_HASH,
        READINESS_HASH,
        BUNDLE_HASH,
        RECEIPT_HASH,
        R3_IMPLEMENTATION_IDENTITY,
        R3_EVALUATOR_AUTHORITY_BUNDLE_HASH,
        V4_AUTHORITY_HASH,
        "COMMON-42",
        42,
        MAIN_DESCRIPTOR_HASH,
        MAIN_REGISTRY_HASH,
        SUPPLEMENT_DESCRIPTOR_HASH,
        SUPPLEMENT_REGISTRY_HASH,
        DATASET_MANIFEST_ID,
        INNER_SPLIT_ID,
        TEST1_FEATURE_SHA256,
        TEST1_LABEL_SHA256,
        AUTHORIZATION_SCOPE,
        True,
        False,
        False,
        False,
        False,
        False,
        "",
    )
    return replace(provisional, grant_hash=stable_hash_v1(provisional._payload()))


_ISSUED_GRANTS: dict[int, tuple[weakref.ReferenceType[CommittedInnerD1ExecutionGrantV1], str]] = {}


def issue_committed_inner_d1_execution_grant_v1() -> CommittedInnerD1ExecutionGrantV1:
    documents = _load_committed_artifact_set_v1()
    _validate_committed_artifact_set_v1(documents)
    grant = _expected_grant_v1()
    object_id = id(grant)

    def cleanup(dead_ref: object, *, key: int = object_id) -> None:
        issued = _ISSUED_GRANTS.get(key)
        if issued is not None and issued[0] is dead_ref:
            _ISSUED_GRANTS.pop(key, None)

    _ISSUED_GRANTS[object_id] = (weakref.ref(grant, cleanup), grant.grant_hash)
    return grant


def validate_committed_inner_d1_execution_grant_v1(
    grant: CommittedInnerD1ExecutionGrantV1,
) -> str:
    if type(grant) is not CommittedInnerD1ExecutionGrantV1:
        _fail("COMMITTED_GRANT_TYPE_REJECTED")
    issued = _ISSUED_GRANTS.get(id(grant))
    if issued is None or issued[0]() is not grant or issued[1] != grant.grant_hash:
        _fail("COMMITTED_GRANT_FACTORY_CUSTODY_REJECTED")
    documents = _load_committed_artifact_set_v1()
    _validate_committed_artifact_set_v1(documents)
    expected = _expected_grant_v1()
    if grant != expected or grant.grant_hash != stable_hash_v1(grant._payload()):
        _fail("COMMITTED_GRANT_REPLAY_REJECTED")
    return grant.grant_hash


class _InnerD1ExecutionTokenV1:
    __slots__ = ("grant", "token_hash", "__weakref__")

    def __init__(self, grant: CommittedInnerD1ExecutionGrantV1, token_hash: str) -> None:
        self.grant = grant
        self.token_hash = token_hash

    def __repr__(self) -> str:
        return "<_InnerD1ExecutionTokenV1 validated=True>"


_ISSUED_TOKENS: dict[int, tuple[weakref.ReferenceType[_InnerD1ExecutionTokenV1], str, int]] = {}
_CONSUMED_GRANT_IDS: set[int] = set()
_REAL_TOKEN_ISSUED = False


def _issue_execution_token_v1(
    grant: CommittedInnerD1ExecutionGrantV1,
) -> _InnerD1ExecutionTokenV1:
    global _REAL_TOKEN_ISSUED
    validate_committed_inner_d1_execution_grant_v1(grant)
    if _REAL_TOKEN_ISSUED or id(grant) in _CONSUMED_GRANT_IDS:
        _fail("EXECUTION_GRANT_ALREADY_CONSUMED")
    token_hash = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d1_execution_token_v1",
            "execution_version": EXECUTION_VERSION,
            "grant_hash": grant.grant_hash,
            "bridge_identity": BRIDGE_IDENTITY,
            "single_use": True,
        }
    )
    token = _InnerD1ExecutionTokenV1(grant, token_hash)
    object_id = id(token)

    def cleanup(dead_ref: object, *, key: int = object_id) -> None:
        issued = _ISSUED_TOKENS.get(key)
        if issued is not None and issued[0] is dead_ref:
            _ISSUED_TOKENS.pop(key, None)

    _ISSUED_TOKENS[object_id] = (weakref.ref(token, cleanup), token_hash, id(grant))
    _CONSUMED_GRANT_IDS.add(id(grant))
    _REAL_TOKEN_ISSUED = True
    return token


def _validate_execution_token_v1(token: _InnerD1ExecutionTokenV1) -> str:
    if type(token) is not _InnerD1ExecutionTokenV1:
        _fail("EXECUTION_TOKEN_TYPE_REJECTED")
    issued = _ISSUED_TOKENS.get(id(token))
    if (
        issued is None
        or issued[0]() is not token
        or issued[1] != token.token_hash
        or issued[2] != id(token.grant)
    ):
        _fail("EXECUTION_TOKEN_FACTORY_CUSTODY_REJECTED")
    validate_committed_inner_d1_execution_grant_v1(token.grant)
    return token.token_hash


@dataclass(frozen=True, repr=False)
class RealInnerFeatureFrameV1:
    """Factory-custodied real 22-feature frame; values never serialize."""

    execution_mode: str
    dataset_manifest_identity: str
    split_identity: str
    source_file_identity: str
    source_file_sha256: str
    feature_schema_authority_hash: str
    ordered_features: tuple[str, ...]
    physical_row_count: int
    row_identity_set_hash: str
    frame_hash: str
    _columns: tuple[tuple[float, ...], ...] = field(repr=False, compare=False)
    _timestamps: tuple[str, ...] = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "<RealInnerFeatureFrameV1 validated=True values=REDACTED>"


class RealPrivateNumericResolverV1:
    """Exact private registry projection with a permanently redacted surface."""

    __slots__ = (
        "_bundle",
        "_relation_values",
        "_relation_references",
        "_source_values",
        "resolver_identity",
        "__weakref__",
    )

    def __init__(
        self,
        *,
        token: object,
        bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
        relation_values: dict[tuple[str, str], int | float],
        relation_references: dict[tuple[str, str], str],
        source_values: dict[tuple[str, str], float],
    ) -> None:
        if token is not _REAL_RESOLVER_FACTORY_TOKEN:
            _fail("REAL_RESOLVER_FACTORY_CUSTODY_REJECTED")
        self._bundle = bundle
        self._relation_values = relation_values
        self._relation_references = relation_references
        self._source_values = source_values
        self.resolver_identity = stable_hash_v1(
            {
                "artifact_type": "task039e3_r2r_real_private_numeric_resolver_v1",
                "execution_mode": EXECUTION_MODE,
                "evaluator_authority_bundle_hash": bundle.bundle_hash,
                "main_private_registry_hash": MAIN_REGISTRY_HASH,
                "supplement_private_registry_hash": SUPPLEMENT_REGISTRY_HASH,
                "relation_reference_set": sorted(relation_references.values()),
                "source_reference_set": [
                    supplement.supplement_reference_identity_v1(source, role)
                    for source, role in sorted(source_values)
                    if source in evaluator_authority.SUPPLEMENT_SOURCES
                ],
                "private_values_exposed": 0,
            }
        )

    def __repr__(self) -> str:
        return "<RealPrivateNumericResolverV1 validated=True values=REDACTED>"

    def __reduce__(self) -> object:
        _fail("REAL_PRIVATE_NUMERIC_SERIALIZATION_PROHIBITED")

    def __copy__(self) -> object:
        _fail("REAL_PRIVATE_NUMERIC_COPY_PROHIBITED")

    def __deepcopy__(self, memo: object) -> object:
        del memo
        _fail("REAL_PRIVATE_NUMERIC_COPY_PROHIBITED")

    def relation_value(
        self, relation_binding_hash: str, role: str, reference_identity: str
    ) -> int | float:
        validate_real_private_numeric_resolver_v1(self, self._bundle)
        key = (relation_binding_hash, role)
        if self._relation_references.get(key) != reference_identity:
            _fail("REAL_MAIN_REFERENCE_LOOKUP_REJECTED")
        try:
            return self._relation_values[key]
        except KeyError:
            _fail("REAL_MAIN_RELATION_LOOKUP_REJECTED")

    def source_census_value(self, source: str, role: str) -> float:
        validate_real_private_numeric_resolver_v1(self, self._bundle)
        try:
            return self._source_values[(source, role)]
        except KeyError:
            _fail("REAL_SOURCE_CENSUS_LOOKUP_REJECTED")


@dataclass(frozen=True)
class _RealRetainedSourceEventV1:
    source: str
    physical_row_index: int
    direction: str
    amplitude: float = field(repr=False, compare=True)
    source_event_identity: str = ""


@dataclass(frozen=True)
class _RealIsolatedSourceEventV1:
    retained_event: _RealRetainedSourceEventV1
    isolated_event_identity: str


@dataclass(frozen=True)
class _RealOpportunityEnvelopeV1:
    isolated_source_event_identity: str
    canonical_opportunity: object
    envelope_hash: str


@dataclass(frozen=True)
class RealFullCensusResultV1:
    execution_mode: str
    source_census_identity: str
    raw_source_event_count: int
    retained_source_event_count: int
    isolated_source_event_count: int
    relation_opportunities: tuple[_RealOpportunityEnvelopeV1, ...]
    denominator_policy: str
    census_hash: str


@dataclass(frozen=True)
class RealRuleExecutionResultV1:
    execution_mode: str
    opportunity_id: str
    source_event_identity: str
    relation_binding_hash: str
    final_state: str
    alarm_emitted: bool
    decision_physical_row_index: int | None
    numeric_reference_identities: tuple[str, ...]
    computation_identity: str
    trace_hash: str

    def to_prediction_record(self) -> dict[str, object]:
        return {
            "opportunity_id": self.opportunity_id,
            "source_event_identity_hash": self.source_event_identity,
            "relation_binding_hash": self.relation_binding_hash,
            "final_state": self.final_state,
            "alarm_emitted": self.alarm_emitted,
            "decision_physical_row_index": self.decision_physical_row_index,
            "numeric_reference_identities": list(self.numeric_reference_identities),
            "computation_identity": self.computation_identity,
            "trace_hash": self.trace_hash,
        }


@dataclass(frozen=True)
class ScientificRulePredictionArtifactV1:
    execution_mode: str
    scientific_eligible: bool
    authorization_hash: str
    authorization_report_commit: str
    bridge_identity: str
    execution_bridge_commit: str
    execution_bridge_source_sha256: str
    r3_implementation_identity: str
    evaluator_authority_bundle_hash: str
    v4_authority_hash: str
    common_portfolio: str
    common_relation_count: int
    main_descriptor_hash: str
    main_private_registry_hash: str
    supplement_descriptor_hash: str
    supplement_private_registry_hash: str
    dataset_manifest_identity: str
    split_identity: str
    feature_sha256: str
    full_census_identity: str
    denominator_policy: str
    prediction_records: tuple[dict[str, object], ...]
    raw_source_event_count: int
    retained_source_event_count: int
    isolated_source_event_count: int
    relation_opportunity_count: int
    evaluated_count: int
    alarm_count: int
    abstain_count: int
    error_count: int
    artifact_hash: str

    def to_public_dict(self) -> dict[str, object]:
        payload = _prediction_payload_v1(self)
        return {**payload, "artifact_hash": self.artifact_hash}


class RealLabelEventCustodyV1:
    __slots__ = (
        "strict_label_vector_hash",
        "attack_event_set_hash",
        "alarm_episode_set_hash",
        "custody_hash",
        "_labels",
        "_attack_events",
        "_alarm_episodes",
        "_attack_seconds",
        "_normal_seconds",
        "__weakref__",
    )

    def __init__(
        self,
        *,
        token: object,
        labels: tuple[int, ...],
        attack_events: tuple[evaluator_metrics.IntervalV1, ...],
        alarm_episodes: tuple[evaluator_metrics.IntervalV1, ...],
    ) -> None:
        if token is not _REAL_LABEL_FACTORY_TOKEN:
            _fail("REAL_LABEL_CUSTODY_FACTORY_REJECTED")
        self._labels = labels
        self._attack_events = attack_events
        self._alarm_episodes = alarm_episodes
        self._attack_seconds = sum(labels)
        self._normal_seconds = len(labels) - self._attack_seconds
        self.strict_label_vector_hash = stable_hash_v1(
            {
                "artifact_type": "task039e3_r2r_real_strict_binary_label_vector_v1",
                "label_file_sha256": TEST1_LABEL_SHA256,
                "labels": list(labels),
            }
        )
        self.attack_event_set_hash = _private_interval_set_hash_v1(
            "attack", attack_events
        )
        self.alarm_episode_set_hash = _private_interval_set_hash_v1(
            "alarm", alarm_episodes
        )
        self.custody_hash = stable_hash_v1(
            {
                "artifact_type": "task039e3_r2r_real_label_event_custody_v1",
                "strict_label_vector_hash": self.strict_label_vector_hash,
                "attack_event_set_hash": self.attack_event_set_hash,
                "alarm_episode_set_hash": self.alarm_episode_set_hash,
                "physical_row_count": len(labels),
                "event_policy_hash": v4.CORRECTED_EVENT_POLICY_HASH,
            }
        )

    def __repr__(self) -> str:
        return "<RealLabelEventCustodyV1 validated=True labels=REDACTED intervals=REDACTED>"

    def __reduce__(self) -> object:
        _fail("REAL_LABEL_CUSTODY_SERIALIZATION_PROHIBITED")


@dataclass(frozen=True)
class ScientificMetricV1:
    metric_name: str
    formula_identity: str
    value: float | None
    defined: bool
    undefined_reason: str | None
    private_evidence_hash: str
    metric_hash: str

    def to_public_dict(self) -> dict[str, object]:
        return {
            "metric_name": self.metric_name,
            "formula_identity": self.formula_identity,
            "value": self.value,
            "defined": self.defined,
            "undefined_reason": self.undefined_reason,
            "private_evidence_hash": self.private_evidence_hash,
            "artifact_hash": self.metric_hash,
        }


@dataclass(frozen=True)
class InnerD1ExecutionRunV1:
    committed_grant_hash: str
    bridge_identity: str
    rule_prediction_artifact_hash: str
    private_metric_evidence_hash: str
    metric_hashes: tuple[str, str]
    raw_source_event_count: int
    retained_source_event_count: int
    isolated_source_event_count: int
    relation_opportunity_count: int
    evaluated_count: int
    alarm_count: int
    alarm_episode_count: int
    abstain_count: int
    error_count: int
    test2_access_count: int
    execution_attempt_count: int
    execution_retry_count: int
    run_hash: str


_REAL_RESOLVER_FACTORY_TOKEN = object()
_REAL_LABEL_FACTORY_TOKEN = object()
_ISSUED_FRAMES: dict[int, tuple[weakref.ReferenceType[RealInnerFeatureFrameV1], str]] = {}
_ISSUED_RESOLVERS: dict[int, tuple[weakref.ReferenceType[RealPrivateNumericResolverV1], str]] = {}
_ISSUED_CENSUSES: dict[int, tuple[weakref.ReferenceType[RealFullCensusResultV1], str]] = {}
_ISSUED_RULE_RESULTS: dict[
    int, tuple[weakref.ReferenceType[RealRuleExecutionResultV1], str, int, int]
] = {}
_ISSUED_PREDICTIONS: dict[int, tuple[weakref.ReferenceType[ScientificRulePredictionArtifactV1], str]] = {}
_ISSUED_LABEL_CUSTODIES: dict[int, tuple[weakref.ReferenceType[RealLabelEventCustodyV1], str]] = {}


def _register_weak_v1(store: dict[int, tuple[weakref.ReferenceType[Any], str]], value: Any, identity: str) -> Any:
    object_id = id(value)

    def cleanup(dead_ref: object, *, key: int = object_id) -> None:
        issued = store.get(key)
        if issued is not None and issued[0] is dead_ref:
            store.pop(key, None)

    store[object_id] = (weakref.ref(value, cleanup), identity)
    return value


def _sha256_file_v1(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise InnerD1ExecutionV1Error("AUTHORIZED_FILE_READ_FAILED") from exc
    return digest.hexdigest()


def _load_public_authorities_v1() -> tuple[
    v4.UtilityProtocolV4CanonicalAuthority,
    evaluator_authority.EvaluatorAuthorityBundleV1,
]:
    root = _repository_root_v1()
    relative_inputs = {
        "executable_equivalence": "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json",
        "evidence_manifest": "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json",
        "dataset_manifest": "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json",
        "csv_structure_report": "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json",
        "c0_config": "configs/v6/task039c0_candidate_discovery_protocol.json",
        "br2_config": "configs/v6/task039br2_hai_continuous_step_feasibility.json",
        "materialized_audit_receipt": "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json",
    }
    try:
        inputs = {
            name: json.loads((root / relative).read_text(encoding="utf-8"))
            for name, relative in relative_inputs.items()
        }
        authority = v4.build_utility_protocol_v4_canonical_authority(**inputs)
        bundle = evaluator_authority.build_evaluator_authority_bundle_v1(authority)
        if (
            v4.validate_utility_protocol_v4_authority(authority) != V4_AUTHORITY_HASH
            or evaluator_authority.validate_evaluator_authority_bundle_v1(bundle)
            != R3_EVALUATOR_AUTHORITY_BUNDLE_HASH
        ):
            _fail("CURRENT_PUBLIC_AUTHORITY_REPLAY_REJECTED")
        return authority, bundle
    except InnerD1ExecutionV1Error:
        raise
    except Exception as exc:
        raise InnerD1ExecutionV1Error("CURRENT_PUBLIC_AUTHORITY_REPLAY_REJECTED") from exc


def _parse_local_binding_file_v1() -> dict[str, str]:
    path = _repository_root_v1() / ".env.custody.local"
    if path.is_symlink() or not path.is_file():
        _fail("LOCAL_CUSTODY_BINDING_FILE_UNAVAILABLE")
    result: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            tokens = shlex.split(line, comments=False, posix=True)
            if len(tokens) != 1 or "=" not in tokens[0]:
                _fail("LOCAL_CUSTODY_BINDING_FILE_INVALID")
            key, value = tokens[0].split("=", 1)
            if key not in _APPROVED_LOCAL_BINDING_KEYS or key in result or not value:
                _fail("LOCAL_CUSTODY_BINDING_FILE_INVALID")
            result[key] = value
    except InnerD1ExecutionV1Error:
        raise
    except Exception as exc:
        raise InnerD1ExecutionV1Error("LOCAL_CUSTODY_BINDING_FILE_INVALID") from exc
    for key in _APPROVED_LOCAL_BINDING_KEYS:
        current = os.environ.get(key)
        if current:
            result[key] = current
    if set(result) != set(_APPROVED_LOCAL_BINDING_KEYS):
        _fail("LOCAL_CUSTODY_BINDINGS_INCOMPLETE")
    return result


def _strict_private_json_v1(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        _fail("PRIVATE_REGISTRY_FILE_INVALID")
    root = _repository_root_v1().resolve()
    try:
        resolved = path.resolve(strict=True)
        if resolved == root or root in resolved.parents:
            _fail("PRIVATE_REGISTRY_INSIDE_REPOSITORY")
        return _strict_json_object_v1(path.read_bytes())
    except InnerD1ExecutionV1Error:
        raise
    except Exception as exc:
        raise InnerD1ExecutionV1Error("PRIVATE_REGISTRY_READ_FAILED") from exc


def build_real_private_numeric_resolver_v1(
    bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
    *,
    main_document: Mapping[str, Any],
    supplement_document: Mapping[str, Any],
) -> RealPrivateNumericResolverV1:
    """Build only from exact validated canonical documents."""

    try:
        evaluator_authority.validate_evaluator_authority_bundle_v1(bundle)
        root = _repository_root_v1()
        main_definition = main_authority.build_common42_authority_v1(
            json.loads(
                (root / "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json").read_text(
                    encoding="utf-8"
                )
            ),
            json.loads(
                (root / "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json").read_text(
                    encoding="utf-8"
                )
            ),
        )
        if (
            main_authority.validate_private_registry_document_v1(
                main_document, main_definition
            )
            != MAIN_REGISTRY_HASH
        ):
            _fail("MAIN_PRIVATE_REGISTRY_HASH_REJECTED")
        supplement_definition = supplement.build_supplement_authority_definition_v1()
        if (
            supplement.validate_supplement_private_registry_document_v1(
                supplement_document, supplement_definition
            )
            != SUPPLEMENT_REGISTRY_HASH
        ):
            _fail("SUPPLEMENT_PRIVATE_REGISTRY_HASH_REJECTED")
    except InnerD1ExecutionV1Error:
        raise
    except Exception as exc:
        raise InnerD1ExecutionV1Error("PRIVATE_REGISTRY_DOCUMENT_REJECTED") from exc

    expected: dict[tuple[str, str], tuple[str, str]] = {}
    for rule in bundle.v4_authority.rule_descriptors:
        for role, reference in rule.numeric_reference_bindings:
            expected[(rule.relation_binding_hash, role)] = (rule.source, reference)
    relation_values: dict[tuple[str, str], int | float] = {}
    relation_references: dict[tuple[str, str], str] = {}
    source_groups: dict[tuple[str, str], list[float]] = {}
    for record in main_document["records"]:
        key = (record["relation_binding_hash"], record["numeric_role"])
        source, reference = expected.get(key, ("", ""))
        if reference != record["new_reference_identity"]:
            _fail("MAIN_PRIVATE_REFERENCE_REJECTED")
        value = record["numeric_value"]
        relation_values[key] = value
        relation_references[key] = reference
        if record["numeric_role"] in evaluator_authority.SOURCE_CENSUS_ROLES:
            source_groups.setdefault((source, record["numeric_role"]), []).append(value)
    if set(relation_values) != set(expected) or len(relation_values) != 420:
        _fail("MAIN_PRIVATE_REGISTRY_CLOSURE_REJECTED")
    source_values: dict[tuple[str, str], float] = {}
    for key, values in source_groups.items():
        if len({float(value).hex() for value in values}) != 1:
            _fail("MAIN_SOURCE_CENSUS_PROJECTION_REJECTED")
        source_values[key] = float(values[0])
    for record in supplement_document["records"]:
        key = (record["source_identity"], record["numeric_role"])
        if record["new_reference_identity"] != supplement.supplement_reference_identity_v1(*key):
            _fail("SUPPLEMENT_PRIVATE_REFERENCE_REJECTED")
        source_values[key] = float(record["numeric_value"])
    expected_source_keys = {
        (source, role)
        for source in evaluator_authority.EVALUATOR_SOURCE_CENSUS
        for role in evaluator_authority.SOURCE_CENSUS_ROLES
    }
    if set(source_values) != expected_source_keys:
        _fail("PRIVATE_SOURCE_CENSUS_CLOSURE_REJECTED")
    resolver = RealPrivateNumericResolverV1(
        token=_REAL_RESOLVER_FACTORY_TOKEN,
        bundle=bundle,
        relation_values=relation_values,
        relation_references=relation_references,
        source_values=source_values,
    )
    _register_weak_v1(_ISSUED_RESOLVERS, resolver, resolver.resolver_identity)
    validate_real_private_numeric_resolver_v1(resolver, bundle)
    return resolver


def validate_real_private_numeric_resolver_v1(
    resolver: RealPrivateNumericResolverV1,
    bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
) -> str:
    if type(resolver) is not RealPrivateNumericResolverV1:
        _fail("REAL_RESOLVER_TYPE_REJECTED")
    issued = _ISSUED_RESOLVERS.get(id(resolver))
    if (
        issued is None
        or issued[0]() is not resolver
        or issued[1] != resolver.resolver_identity
        or resolver._bundle is not bundle
        or len(resolver._relation_values) != 420
        or len(resolver._source_values) != 24
    ):
        _fail("REAL_RESOLVER_CUSTODY_REJECTED")
    evaluator_authority.validate_evaluator_authority_bundle_v1(bundle)
    return resolver.resolver_identity


def build_differential_numeric_resolver_v1(
    bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
    main_records: tuple[evaluator_authority.SyntheticNumericRecordV1, ...],
    supplement_records: tuple[evaluator_authority.SyntheticNumericRecordV1, ...],
) -> RealPrivateNumericResolverV1:
    """Validated non-scientific adapter for R3 differential fixtures only."""

    try:
        synthetic = evaluator_authority.build_synthetic_numeric_resolver_v1(
            bundle, main_records, supplement_records
        )
        evaluator_authority.validate_synthetic_numeric_resolver_v1(synthetic, bundle)
    except Exception as exc:
        raise InnerD1ExecutionV1Error("DIFFERENTIAL_RESOLVER_FIXTURE_REJECTED") from exc
    resolver = RealPrivateNumericResolverV1(
        token=_REAL_RESOLVER_FACTORY_TOKEN,
        bundle=bundle,
        relation_values=dict(synthetic._relation_values),
        relation_references=dict(synthetic._relation_references),
        source_values=dict(synthetic._source_values),
    )
    _register_weak_v1(_ISSUED_RESOLVERS, resolver, resolver.resolver_identity)
    return resolver


def _frame_public_payload_v1(frame: RealInnerFeatureFrameV1) -> dict[str, object]:
    return {
        "artifact_type": "task039e3_r2r_real_inner_feature_frame_v1",
        "execution_mode": frame.execution_mode,
        "dataset_manifest_identity": frame.dataset_manifest_identity,
        "split_identity": frame.split_identity,
        "source_file_identity": frame.source_file_identity,
        "source_file_sha256": frame.source_file_sha256,
        "feature_schema_authority_hash": frame.feature_schema_authority_hash,
        "ordered_features": list(frame.ordered_features),
        "physical_row_count": frame.physical_row_count,
        "row_identity_set_hash": frame.row_identity_set_hash,
        "private_feature_values_exposed": 0,
    }


def _issue_feature_frame_v1(frame: RealInnerFeatureFrameV1) -> RealInnerFeatureFrameV1:
    _register_weak_v1(_ISSUED_FRAMES, frame, frame.frame_hash)
    return frame


def _build_feature_frame_v1(
    bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
    *,
    execution_mode: str,
    source_file_sha256: str,
    timestamps: tuple[str, ...],
    columns: tuple[tuple[float, ...], ...],
) -> RealInnerFeatureFrameV1:
    evaluator_authority.validate_evaluator_authority_bundle_v1(bundle)
    ordered = bundle.v4_authority.feature_schema.union_features
    if execution_mode not in {EXECUTION_MODE, DIFFERENTIAL_MODE}:
        _fail("REAL_FRAME_EXECUTION_MODE_REJECTED")
    if (
        type(timestamps) is not tuple
        or not timestamps
        or type(columns) is not tuple
        or len(columns) != 22
        or any(type(column) is not tuple or len(column) != len(timestamps) for column in columns)
        or any(type(value) is not float or not math.isfinite(value) for column in columns for value in column)
    ):
        _fail("REAL_FRAME_CONTENT_REJECTED")
    row_identities = tuple(
        stable_hash_v1(
            {
                "artifact_type": "task039e3_r2r_real_feature_row_identity_v1",
                "dataset_manifest_identity": DATASET_MANIFEST_ID,
                "split_identity": INNER_SPLIT_ID,
                "source_file_identity": TEST1_FEATURE_FILENAME,
                "physical_row_index": index,
                "timestamp_token_hash": sha256(timestamp.encode("utf-8")).hexdigest(),
                "feature_value_hash": stable_hash_v1(
                    {
                        "ordered_features": list(ordered),
                        "values": [column[index] for column in columns],
                    }
                ),
            }
        )
        for index, timestamp in enumerate(timestamps)
    )
    provisional = RealInnerFeatureFrameV1(
        execution_mode,
        DATASET_MANIFEST_ID,
        INNER_SPLIT_ID,
        TEST1_FEATURE_FILENAME,
        source_file_sha256,
        bundle.v4_authority.feature_schema.authority_hash,
        ordered,
        len(timestamps),
        stable_hash_v1(
            {
                "artifact_type": "task039e3_r2r_real_feature_row_identity_set_v1",
                "ordered_row_identities": list(row_identities),
            }
        ),
        "",
        columns,
        timestamps,
    )
    return _issue_feature_frame_v1(
        replace(provisional, frame_hash=stable_hash_v1(_frame_public_payload_v1(provisional)))
    )


def validate_real_inner_feature_frame_v1(
    frame: RealInnerFeatureFrameV1,
    bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
    *,
    require_real: bool,
) -> str:
    if type(frame) is not RealInnerFeatureFrameV1:
        _fail("REAL_FRAME_TYPE_REJECTED")
    issued = _ISSUED_FRAMES.get(id(frame))
    if issued is None or issued[0]() is not frame or issued[1] != frame.frame_hash:
        _fail("REAL_FRAME_FACTORY_CUSTODY_REJECTED")
    evaluator_authority.validate_evaluator_authority_bundle_v1(bundle)
    if (
        frame.execution_mode != (EXECUTION_MODE if require_real else DIFFERENTIAL_MODE)
        or frame.dataset_manifest_identity != DATASET_MANIFEST_ID
        or frame.split_identity != INNER_SPLIT_ID
        or frame.source_file_identity != TEST1_FEATURE_FILENAME
        or frame.feature_schema_authority_hash != bundle.v4_authority.feature_schema.authority_hash
        or frame.ordered_features != bundle.v4_authority.feature_schema.union_features
        or len(frame.ordered_features) != 22
        or frame.physical_row_count != len(frame._timestamps)
        or len(frame._columns) != 22
        or any(len(column) != frame.physical_row_count for column in frame._columns)
        or frame.frame_hash != stable_hash_v1(_frame_public_payload_v1(frame))
    ):
        _fail("REAL_FRAME_REPLAY_REJECTED")
    if require_real and (
        frame.source_file_sha256 != TEST1_FEATURE_SHA256
        or frame.physical_row_count != EXPECTED_ROW_COUNT
    ):
        _fail("REAL_FRAME_SCIENTIFIC_CUSTODY_REJECTED")
    return frame.frame_hash


def build_differential_feature_frame_v1(
    bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
    rows: tuple[tuple[float, ...], ...],
) -> RealInnerFeatureFrameV1:
    """Synthetic-only adapter used exclusively for semantic differential tests."""

    if type(rows) is not tuple or not rows:
        _fail("DIFFERENTIAL_ROWS_REJECTED")
    if any(type(row) is not tuple or len(row) != 22 for row in rows):
        _fail("DIFFERENTIAL_ROWS_REJECTED")
    columns = tuple(tuple(float(row[index]) for row in rows) for index in range(22))
    return _build_feature_frame_v1(
        bundle,
        execution_mode=DIFFERENTIAL_MODE,
        source_file_sha256=stable_hash_v1({"synthetic_rows": len(rows)}),
        timestamps=tuple(f"synthetic:{index}" for index in range(len(rows))),
        columns=columns,
    )


def _load_real_feature_frame_v1(
    token: _InnerD1ExecutionTokenV1,
    bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
    feature_path: Path,
) -> RealInnerFeatureFrameV1:
    _validate_execution_token_v1(token)
    if feature_path.is_symlink() or not feature_path.is_file():
        _fail("TEST1_FEATURE_FILE_INVALID")
    if _sha256_file_v1(feature_path) != TEST1_FEATURE_SHA256:
        _fail("TEST1_FEATURE_HASH_REJECTED")
    ordered = bundle.v4_authority.feature_schema.union_features
    timestamps: list[str] = []
    raw_columns: list[list[str]] = [[] for _ in ordered]
    try:
        with feature_path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader)
            if len(header) != len(set(header)) or "timestamp" not in header:
                _fail("TEST1_FEATURE_HEADER_REJECTED")
            selected = ("timestamp", *ordered)
            if any(name not in header for name in selected):
                _fail("TEST1_FEATURE_HEADER_REJECTED")
            selected_indices = tuple(header.index(name) for name in selected)
            v4.validate_selected_feature_header_v4(selected, bundle.v4_authority)
            for row in reader:
                if len(row) != len(header):
                    _fail("TEST1_FEATURE_ROW_WIDTH_REJECTED")
                timestamps.append(row[selected_indices[0]])
                for target, index in zip(raw_columns, selected_indices[1:], strict=True):
                    target.append(row[index])
    except InnerD1ExecutionV1Error:
        raise
    except Exception as exc:
        raise InnerD1ExecutionV1Error("TEST1_FEATURE_PARSE_REJECTED") from exc
    if len(timestamps) != EXPECTED_ROW_COUNT or len(set(timestamps)) != EXPECTED_ROW_COUNT:
        _fail("TEST1_FEATURE_ROW_COUNT_OR_TIME_REJECTED")
    try:
        columns = tuple(
            v4.parse_raw_feature_tokens_v4(feature, tuple(tokens), bundle.v4_authority)
            for feature, tokens in zip(ordered, raw_columns, strict=True)
        )
    except Exception as exc:
        raise InnerD1ExecutionV1Error("TEST1_FEATURE_VALUE_REJECTED") from exc
    return _build_feature_frame_v1(
        bundle,
        execution_mode=EXECUTION_MODE,
        source_file_sha256=TEST1_FEATURE_SHA256,
        timestamps=tuple(timestamps),
        columns=columns,
    )


def _frame_value_v1(frame: RealInnerFeatureFrameV1, feature: str, index: int) -> float | None:
    if index < 0 or index >= frame.physical_row_count:
        return None
    try:
        column = frame.ordered_features.index(feature)
    except ValueError:
        _fail("REAL_FEATURE_OUTSIDE_SCHEMA")
    value = frame._columns[column][index]
    if type(value) is not float or not math.isfinite(value):
        _fail("REAL_FEATURE_VALUE_MALFORMED")
    return value


def _raw_candidate_count_v1(
    source_series: Mapping[str, tuple[float, ...]],
    thresholds: Mapping[str, float],
    tolerances: Mapping[str, float],
) -> int:
    count = 0
    for source in v3.UTILITY_SOURCE_UNIVERSE_V3:
        series = source_series[source]
        for index in range(v3.SOURCE_PRE_WINDOW, len(series) - v3.SOURCE_POST_WINDOW + 1):
            pre = series[index - v3.SOURCE_PRE_WINDOW:index]
            post = series[index:index + v3.SOURCE_POST_WINDOW]
            pre_level = float(statistics.median(pre))
            post_level = float(statistics.median(post))
            amplitude = post_level - pre_level
            pre_fraction = sum(abs(value - pre_level) <= tolerances[source] for value in pre) / v3.SOURCE_PRE_WINDOW
            post_fraction = sum(abs(value - post_level) <= tolerances[source] for value in post) / v3.SOURCE_POST_WINDOW
            if (
                amplitude != 0.0
                and abs(amplitude) >= thresholds[source]
                and pre_fraction >= v3.MINIMUM_STABILITY_FRACTION
                and post_fraction >= v3.MINIMUM_STABILITY_FRACTION
            ):
                count += 1
    return count


def enumerate_real_full_census_v1(
    frame: RealInnerFeatureFrameV1,
    bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
    resolver: RealPrivateNumericResolverV1,
    *,
    differential: bool = False,
) -> RealFullCensusResultV1:
    validate_real_inner_feature_frame_v1(frame, bundle, require_real=not differential)
    validate_real_private_numeric_resolver_v1(resolver, bundle)
    sources = v3.UTILITY_SOURCE_UNIVERSE_V3
    if tuple(sources) != tuple(bundle.evaluator_source_census):
        _fail("REAL_SOURCE_UNIVERSE_REJECTED")
    source_series = {
        source: frame._columns[frame.ordered_features.index(source)] for source in sources
    }
    thresholds = {
        source: resolver.source_census_value(source, "source_step_threshold")
        for source in sources
    }
    tolerances = {
        source: resolver.source_census_value(source, "source_stability_tolerance")
        for source in sources
    }
    try:
        retained_v3 = v3.derive_retained_source_events_v3(
            source_series, thresholds, tolerances
        )
    except Exception as exc:
        raise InnerD1ExecutionV1Error("REAL_SOURCE_EVENT_DERIVATION_REJECTED") from exc
    retained: dict[str, tuple[_RealRetainedSourceEventV1, ...]] = {}
    for source in sources:
        records: list[_RealRetainedSourceEventV1] = []
        for event in retained_v3[source]:
            payload = {
                "artifact_type": "task039e3_r2r_real_retained_source_event_v1",
                "execution_mode": frame.execution_mode,
                "frame_hash": frame.frame_hash,
                "physical_row_index": event.physical_index,
                "source": source,
                "source_direction": event.direction,
                "amplitude": event.amplitude,
                "source_census_event_policy_hash": evaluator_census.SOURCE_CENSUS_EVENT_POLICY_HASH,
            }
            records.append(
                _RealRetainedSourceEventV1(
                    source,
                    event.physical_index,
                    event.direction,
                    event.amplitude,
                    stable_hash_v1(payload),
                )
            )
        retained[source] = tuple(records)
    source_census_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_real_retained_source_census_v1",
            "execution_mode": frame.execution_mode,
            "combined_source_census_contract_hash": COMBINED_SOURCE_CENSUS_CONTRACT_HASH,
            "frame_hash": frame.frame_hash,
            "retained_event_identities": {
                source: [event.source_event_identity for event in retained[source]]
                for source in sources
            },
            "source_universe": list(sources),
        }
    )
    isolated: list[_RealIsolatedSourceEventV1] = []
    for source in sources:
        for event in retained[source]:
            conflict = any(
                abs(event.physical_row_index - other.physical_row_index)
                <= v3.CROSS_SOURCE_ISOLATION_RADIUS_SECONDS
                for other_source in sources
                if other_source != source
                for other in retained[other_source]
            )
            if not conflict:
                isolated.append(
                    _RealIsolatedSourceEventV1(
                        event,
                        stable_hash_v1(
                            {
                                "artifact_type": "task039e3_r2r_real_isolated_source_event_v1",
                                "execution_mode": frame.execution_mode,
                                "retained_source_event_identity": event.source_event_identity,
                                "source_census_identity": source_census_identity,
                                "cross_source_isolation_policy_hash": evaluator_census.CROSS_SOURCE_ISOLATION_POLICY_HASH,
                            }
                        ),
                    )
                )
    isolated.sort(
        key=lambda item: (
            item.retained_event.physical_row_index,
            item.retained_event.source,
        )
    )
    rules: dict[tuple[str, str], list[object]] = {}
    for rule in bundle.v4_authority.rule_descriptors:
        rules.setdefault((rule.source, rule.source_direction), []).append(rule)
    envelopes: list[_RealOpportunityEnvelopeV1] = []
    for event in isolated:
        retained_event = event.retained_event
        for rule in sorted(
            rules.get((retained_event.source, retained_event.direction), ()),
            key=lambda item: item.relation_binding_hash,
        ):
            row_time = v4.build_canonical_row_time_identity_v4(
                source_file_identity=TEST1_FEATURE_FILENAME,
                physical_row_index=retained_event.physical_row_index,
            )
            opportunity = v4.build_canonical_opportunity_v4(
                bundle.v4_authority,
                relation_binding_hash=rule.relation_binding_hash,
                row_time=row_time,
            )
            envelope_hash = stable_hash_v1(
                {
                    "artifact_type": "task039e3_r2r_real_canonical_opportunity_envelope_v1",
                    "execution_mode": frame.execution_mode,
                    "isolated_source_event_identity": event.isolated_event_identity,
                    "opportunity_id": opportunity.opportunity_id,
                }
            )
            envelopes.append(
                _RealOpportunityEnvelopeV1(
                    event.isolated_event_identity, opportunity, envelope_hash
                )
            )
    envelopes.sort(
        key=lambda item: (
            item.canonical_opportunity.physical_row_index,
            item.canonical_opportunity.relation_binding_hash,
            item.canonical_opportunity.opportunity_id,
        )
    )
    payload = {
        "artifact_type": "task039e3_r2r_real_full_census_v1",
        "execution_mode": frame.execution_mode,
        "source_census_identity": source_census_identity,
        "raw_source_event_count": _raw_candidate_count_v1(
            source_series, thresholds, tolerances
        ),
        "retained_source_event_count": sum(len(value) for value in retained.values()),
        "isolated_source_event_count": len(isolated),
        "opportunity_envelope_hashes": [item.envelope_hash for item in envelopes],
        "relation_opportunity_count": len(envelopes),
        "denominator_policy": FULL_CENSUS_DENOMINATOR_POLICY,
    }
    result = RealFullCensusResultV1(
        frame.execution_mode,
        source_census_identity,
        payload["raw_source_event_count"],
        payload["retained_source_event_count"],
        payload["isolated_source_event_count"],
        tuple(envelopes),
        FULL_CENSUS_DENOMINATOR_POLICY,
        stable_hash_v1(payload),
    )
    _register_weak_v1(_ISSUED_CENSUSES, result, result.census_hash)
    return result


def validate_real_full_census_v1(
    census: RealFullCensusResultV1,
    frame: RealInnerFeatureFrameV1,
    bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
    resolver: RealPrivateNumericResolverV1,
    *,
    differential: bool = False,
) -> str:
    if type(census) is not RealFullCensusResultV1:
        _fail("REAL_CENSUS_TYPE_REJECTED")
    issued = _ISSUED_CENSUSES.get(id(census))
    if issued is None or issued[0]() is not census or issued[1] != census.census_hash:
        _fail("REAL_CENSUS_FACTORY_CUSTODY_REJECTED")
    expected = enumerate_real_full_census_v1(
        frame, bundle, resolver, differential=differential
    )
    if census != expected:
        _fail("REAL_CENSUS_REPLAY_REJECTED")
    return census.census_hash


def _window_values_v1(
    frame: RealInnerFeatureFrameV1, feature: str, indices: Sequence[int]
) -> tuple[float, ...] | None:
    values: list[float] = []
    for index in indices:
        value = _frame_value_v1(frame, feature, index)
        if value is None:
            return None
        values.append(value)
    return tuple(values)


def execute_real_rule_v1(
    envelope: _RealOpportunityEnvelopeV1,
    census: RealFullCensusResultV1,
    frame: RealInnerFeatureFrameV1,
    bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
    resolver: RealPrivateNumericResolverV1,
    *,
    differential: bool = False,
) -> RealRuleExecutionResultV1:
    if type(envelope) is not _RealOpportunityEnvelopeV1:
        _fail("REAL_OPPORTUNITY_ENVELOPE_TYPE_REJECTED")
    issued = _ISSUED_CENSUSES.get(id(census))
    if (
        issued is None
        or issued[0]() is not census
        or not any(envelope is item for item in census.relation_opportunities)
    ):
        _fail("REAL_OPPORTUNITY_FULL_CENSUS_CUSTODY_REJECTED")
    validate_real_inner_feature_frame_v1(frame, bundle, require_real=not differential)
    validate_real_private_numeric_resolver_v1(resolver, bundle)
    opportunity = envelope.canonical_opportunity
    try:
        v4.validate_canonical_opportunity_v4(opportunity, bundle.v4_authority)
    except Exception as exc:
        raise InnerD1ExecutionV1Error("REAL_CANONICAL_OPPORTUNITY_REJECTED") from exc
    rule = bundle.v4_authority.rule_by_binding(opportunity.relation_binding_hash)
    numeric_references = tuple(reference for _, reference in rule.numeric_reference_bindings)
    if (
        tuple(role for role, _ in rule.numeric_reference_bindings)
        != v4.UTILITY_NUMERIC_ROLES
        or len(numeric_references) != 10
    ):
        _fail("REAL_RULE_NUMERIC_BINDING_REJECTED")
    event_index = opportunity.physical_row_index
    source_indices = tuple(
        range(event_index - v3.SOURCE_PRE_WINDOW, event_index + v3.SOURCE_POST_WINDOW)
    )
    source_values = _window_values_v1(frame, opportunity.source, source_indices)
    computation_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_real_rule_computation_v1",
            "execution_mode": frame.execution_mode,
            "authorization_hash": AUTHORIZATION_HASH,
            "bridge_identity": BRIDGE_IDENTITY,
            "frame_hash": frame.frame_hash,
            "source_event_identity": envelope.isolated_source_event_identity,
            "opportunity_id": opportunity.opportunity_id,
            "rule_descriptor_hash": rule.descriptor_hash,
            "numeric_reference_identities": list(numeric_references),
        }
    )
    if source_values is None:
        return _real_rule_result_v1(
            frame.execution_mode,
            envelope,
            opportunity,
            numeric_references,
            computation_identity,
            evaluator_rule.ABSTAIN_STATE,
            False,
            None,
            "incomplete_source_window",
            census,
            envelope,
        )
    threshold = float(
        resolver.relation_value(
            rule.relation_binding_hash,
            evaluator_rule.SOURCE_THRESHOLD_ROLE,
            rule.reference_for(evaluator_rule.SOURCE_THRESHOLD_ROLE),
        )
    )
    tolerance = float(
        resolver.relation_value(
            rule.relation_binding_hash,
            evaluator_rule.SOURCE_STABILITY_ROLE,
            rule.reference_for(evaluator_rule.SOURCE_STABILITY_ROLE),
        )
    )
    pre = source_values[: v3.SOURCE_PRE_WINDOW]
    post = source_values[v3.SOURCE_PRE_WINDOW :]
    pre_level = float(statistics.median(pre))
    post_level = float(statistics.median(post))
    amplitude = post_level - pre_level
    pre_fraction = sum(abs(value - pre_level) <= tolerance for value in pre) / v3.SOURCE_PRE_WINDOW
    post_fraction = sum(abs(value - post_level) <= tolerance for value in post) / v3.SOURCE_POST_WINDOW
    observed_direction = "step_up" if amplitude > 0.0 else "step_down"
    if (
        amplitude == 0.0
        or abs(amplitude) < threshold
        or pre_fraction < v3.MINIMUM_STABILITY_FRACTION
        or post_fraction < v3.MINIMUM_STABILITY_FRACTION
        or observed_direction != opportunity.source_direction
    ):
        _fail("REAL_RULE_SOURCE_EVENT_EVIDENCE_MISMATCH")
    source_window_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_real_source_window_v1",
            "frame_hash": frame.frame_hash,
            "feature_identity": opportunity.source,
            "physical_row_indices": list(source_indices),
        }
    )
    source_state = v4.build_source_qualification_state_v4(
        opportunity,
        bundle.v4_authority,
        source_window_identity=source_window_identity,
        retained_source_event_identity=envelope.isolated_source_event_identity,
        retained_source_event_census_hash=census.source_census_identity,
    )
    v4.validate_source_qualification_state_v4(
        source_state, opportunity, bundle.v4_authority
    )
    baseline_indices = tuple(range(event_index - v3.TARGET_BASELINE_WINDOW, event_index))
    response_start = event_index + opportunity.selected_horizon_seconds
    response_indices = tuple(range(response_start, response_start + v3.TARGET_RESPONSE_WINDOW))
    decision_index = response_start + v3.TARGET_RESPONSE_WINDOW - 1
    target_window_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_real_target_window_v1",
            "frame_hash": frame.frame_hash,
            "feature_identity": opportunity.target,
            "baseline_physical_row_indices": list(baseline_indices),
            "response_physical_row_indices": list(response_indices),
        }
    )
    baseline = _window_values_v1(frame, opportunity.target, baseline_indices)
    response = _window_values_v1(frame, opportunity.target, response_indices)
    context_available = baseline is not None and response is not None
    if not context_available:
        target_state = v4.transition_target_evaluation_v4(
            opportunity,
            source_state,
            bundle.v4_authority,
            target_window_input_identity=target_window_identity,
            within_split=True,
            target_context_available=False,
            response_matched=False,
        )
        v4.validate_target_evaluation_state_v4(
            target_state, opportunity, source_state, bundle.v4_authority
        )
        return _real_rule_result_v1(
            frame.execution_mode,
            envelope,
            opportunity,
            numeric_references,
            computation_identity,
            evaluator_rule.ABSTAIN_STATE,
            False,
            None,
            target_state.abstention_reason or "incomplete_target_response_window",
            census,
            envelope,
        )
    noise = float(
        resolver.relation_value(
            rule.relation_binding_hash,
            evaluator_rule.TARGET_NOISE_ROLE,
            rule.reference_for(evaluator_rule.TARGET_NOISE_ROLE),
        )
    )
    response_delta = float(statistics.median(response)) - float(statistics.median(baseline))
    response_matched = (
        response_delta > noise
        if opportunity.target_direction == "increase"
        else response_delta < -noise
    )
    final_state = (
        evaluator_rule.EXPECTED_RESPONSE_STATE
        if response_matched
        else evaluator_rule.ANOMALY_STATE
    )
    target_state = v4.transition_target_evaluation_v4(
        opportunity,
        source_state,
        bundle.v4_authority,
        target_window_input_identity=target_window_identity,
        within_split=True,
        target_context_available=True,
        response_matched=response_matched,
    )
    v4.validate_target_evaluation_state_v4(
        target_state, opportunity, source_state, bundle.v4_authority
    )
    if target_state.target_evaluation_state != final_state:
        _fail("REAL_RULE_TARGET_TRANSITION_REJECTED")
    return _real_rule_result_v1(
        frame.execution_mode,
        envelope,
        opportunity,
        numeric_references,
        computation_identity,
        final_state,
        not response_matched,
        decision_index,
        None,
        census,
        envelope,
    )


def _real_rule_result_v1(
    execution_mode: str,
    envelope: _RealOpportunityEnvelopeV1,
    opportunity: object,
    numeric_references: tuple[str, ...],
    computation_identity: str,
    final_state: str,
    alarm_emitted: bool,
    decision_index: int | None,
    abstention_reason: str | None,
    census: RealFullCensusResultV1,
    exact_envelope: _RealOpportunityEnvelopeV1,
) -> RealRuleExecutionResultV1:
    trace = {
        "artifact_type": "task039e3_r2r_real_rule_execution_trace_v1",
        "execution_mode": execution_mode,
        "opportunity_id": opportunity.opportunity_id,
        "source_event_identity": envelope.isolated_source_event_identity,
        "relation_binding_hash": opportunity.relation_binding_hash,
        "final_state": final_state,
        "alarm_emitted": alarm_emitted,
        "decision_physical_row_index": decision_index,
        "numeric_reference_identities": list(numeric_references),
        "computation_identity": computation_identity,
        "abstention_reason": abstention_reason,
    }
    result = RealRuleExecutionResultV1(
        execution_mode,
        opportunity.opportunity_id,
        envelope.isolated_source_event_identity,
        opportunity.relation_binding_hash,
        final_state,
        alarm_emitted,
        decision_index,
        numeric_references,
        computation_identity,
        stable_hash_v1(trace),
    )
    object_id = id(result)

    def cleanup(dead_ref: object, *, key: int = object_id) -> None:
        issued = _ISSUED_RULE_RESULTS.get(key)
        if issued is not None and issued[0] is dead_ref:
            _ISSUED_RULE_RESULTS.pop(key, None)

    _ISSUED_RULE_RESULTS[object_id] = (
        weakref.ref(result, cleanup),
        result.trace_hash,
        id(census),
        id(exact_envelope),
    )
    return result


def _prediction_payload_v1(
    artifact: ScientificRulePredictionArtifactV1,
) -> dict[str, object]:
    return {
        "artifact_type": "task039e3_r2r_scientific_rule_prediction_artifact_v1",
        "artifact_version": "1.0.0",
        "execution_mode": artifact.execution_mode,
        "scientific_eligible": artifact.scientific_eligible,
        "authorization_hash": artifact.authorization_hash,
        "authorization_report_commit": artifact.authorization_report_commit,
        "bridge_identity": artifact.bridge_identity,
        "execution_bridge_commit": artifact.execution_bridge_commit,
        "execution_bridge_source_sha256": artifact.execution_bridge_source_sha256,
        "r3_implementation_identity": artifact.r3_implementation_identity,
        "evaluator_authority_bundle_hash": artifact.evaluator_authority_bundle_hash,
        "v4_authority_hash": artifact.v4_authority_hash,
        "common_portfolio": artifact.common_portfolio,
        "common_relation_count": artifact.common_relation_count,
        "main_descriptor_hash": artifact.main_descriptor_hash,
        "main_private_registry_hash": artifact.main_private_registry_hash,
        "supplement_descriptor_hash": artifact.supplement_descriptor_hash,
        "supplement_private_registry_hash": artifact.supplement_private_registry_hash,
        "dataset_manifest_identity": artifact.dataset_manifest_identity,
        "split_identity": artifact.split_identity,
        "feature_sha256": artifact.feature_sha256,
        "full_census_identity": artifact.full_census_identity,
        "denominator_policy": artifact.denominator_policy,
        "prediction_records": list(artifact.prediction_records),
        "counts": {
            "raw_source_event_count": artifact.raw_source_event_count,
            "retained_source_event_count": artifact.retained_source_event_count,
            "isolated_source_event_count": artifact.isolated_source_event_count,
            "relation_opportunity_count": artifact.relation_opportunity_count,
            "evaluated_count": artifact.evaluated_count,
            "alarm_count": artifact.alarm_count,
            "abstain_count": artifact.abstain_count,
            "error_count": artifact.error_count,
        },
        "label_blind": True,
        "labels_accessed_before_prediction_freeze": False,
        "private_numeric_values_exposed": 0,
        "private_paths_exposed": 0,
    }


def _bridge_source_custody_v1() -> tuple[str, str]:
    root = _repository_root_v1()
    relative = "src/paperworks/v6/task039e3_r2r_utility_inner_d1_execution_v1.py"
    path = root / relative
    if path.is_symlink() or not path.is_file():
        _fail("EXECUTION_BRIDGE_SOURCE_FILE_REJECTED")
    commit = _git_output_v1(root, ("log", "-1", "--format=%H", "--", relative)).decode(
        "ascii"
    ).strip()
    if re.fullmatch(r"[a-f0-9]{40}", commit) is None:
        _fail("EXECUTION_BRIDGE_COMMIT_REJECTED")
    committed = _git_output_v1(root, ("show", f"{commit}:{relative}"))
    current = path.read_bytes()
    if current != committed:
        _fail("EXECUTION_BRIDGE_SOURCE_NOT_FROZEN")
    return commit, sha256(current).hexdigest()


def build_scientific_rule_prediction_artifact_v1(
    token: _InnerD1ExecutionTokenV1,
    census: RealFullCensusResultV1,
    results: tuple[RealRuleExecutionResultV1, ...],
) -> ScientificRulePredictionArtifactV1:
    _validate_execution_token_v1(token)
    issued = _ISSUED_CENSUSES.get(id(census))
    if issued is None or issued[0]() is not census or issued[1] != census.census_hash:
        _fail("PREDICTION_CENSUS_CUSTODY_REJECTED")
    if (
        type(results) is not tuple
        or len(results) != len(census.relation_opportunities)
        or any(type(result) is not RealRuleExecutionResultV1 for result in results)
        or census.execution_mode != EXECUTION_MODE
    ):
        _fail("PREDICTION_FULL_CENSUS_CLOSURE_REJECTED")
    expected_ids = tuple(
        envelope.canonical_opportunity.opportunity_id
        for envelope in census.relation_opportunities
    )
    if tuple(result.opportunity_id for result in results) != expected_ids:
        _fail("PREDICTION_OPPORTUNITY_ORDER_REJECTED")
    for result, envelope in zip(results, census.relation_opportunities, strict=True):
        result_issuance = _ISSUED_RULE_RESULTS.get(id(result))
        if (
            result_issuance is None
            or result_issuance[0]() is not result
            or result_issuance[1] != result.trace_hash
            or result_issuance[2] != id(census)
            or result_issuance[3] != id(envelope)
            or result.execution_mode != EXECUTION_MODE
        ):
            _fail("PREDICTION_RULE_RESULT_FACTORY_CUSTODY_REJECTED")
        if result.final_state not in {
            evaluator_rule.EXPECTED_RESPONSE_STATE,
            evaluator_rule.ANOMALY_STATE,
            evaluator_rule.ABSTAIN_STATE,
        }:
            _fail("PREDICTION_FINAL_STATE_REJECTED")
        if result.alarm_emitted is not (result.final_state == evaluator_rule.ANOMALY_STATE):
            _fail("PREDICTION_ALARM_STATE_REJECTED")
    bridge_commit, bridge_source_sha256 = _bridge_source_custody_v1()
    provisional = ScientificRulePredictionArtifactV1(
        EXECUTION_MODE,
        True,
        AUTHORIZATION_HASH,
        AUTHORIZATION_REPORT_COMMIT,
        BRIDGE_IDENTITY,
        bridge_commit,
        bridge_source_sha256,
        R3_IMPLEMENTATION_IDENTITY,
        R3_EVALUATOR_AUTHORITY_BUNDLE_HASH,
        V4_AUTHORITY_HASH,
        "COMMON-42",
        42,
        MAIN_DESCRIPTOR_HASH,
        MAIN_REGISTRY_HASH,
        SUPPLEMENT_DESCRIPTOR_HASH,
        SUPPLEMENT_REGISTRY_HASH,
        DATASET_MANIFEST_ID,
        INNER_SPLIT_ID,
        TEST1_FEATURE_SHA256,
        census.census_hash,
        FULL_CENSUS_DENOMINATOR_POLICY,
        tuple(result.to_prediction_record() for result in results),
        census.raw_source_event_count,
        census.retained_source_event_count,
        census.isolated_source_event_count,
        len(results),
        sum(result.final_state != evaluator_rule.ABSTAIN_STATE for result in results),
        sum(result.alarm_emitted for result in results),
        sum(result.final_state == evaluator_rule.ABSTAIN_STATE for result in results),
        0,
        "",
    )
    artifact = replace(
        provisional, artifact_hash=stable_hash_v1(_prediction_payload_v1(provisional))
    )
    _register_weak_v1(_ISSUED_PREDICTIONS, artifact, artifact.artifact_hash)
    validate_scientific_rule_prediction_artifact_v1(artifact)
    return artifact


def validate_scientific_rule_prediction_artifact_v1(
    artifact: ScientificRulePredictionArtifactV1,
) -> str:
    if type(artifact) is not ScientificRulePredictionArtifactV1:
        _fail("SCIENTIFIC_PREDICTION_TYPE_REJECTED")
    issued = _ISSUED_PREDICTIONS.get(id(artifact))
    if issued is None or issued[0]() is not artifact or issued[1] != artifact.artifact_hash:
        _fail("SCIENTIFIC_PREDICTION_FACTORY_CUSTODY_REJECTED")
    if (
        artifact.execution_mode != EXECUTION_MODE
        or artifact.scientific_eligible is not True
        or artifact.authorization_hash != AUTHORIZATION_HASH
        or artifact.authorization_report_commit != AUTHORIZATION_REPORT_COMMIT
        or artifact.bridge_identity != BRIDGE_IDENTITY
        or re.fullmatch(r"[a-f0-9]{40}", artifact.execution_bridge_commit) is None
        or re.fullmatch(r"[a-f0-9]{64}", artifact.execution_bridge_source_sha256) is None
        or artifact.common_portfolio != "COMMON-42"
        or artifact.common_relation_count != 42
        or artifact.feature_sha256 != TEST1_FEATURE_SHA256
        or artifact.error_count != 0
        or artifact.relation_opportunity_count != len(artifact.prediction_records)
        or artifact.artifact_hash != stable_hash_v1(_prediction_payload_v1(artifact))
    ):
        _fail("SCIENTIFIC_PREDICTION_REPLAY_REJECTED")
    allowed_record_keys = {
        "opportunity_id",
        "source_event_identity_hash",
        "relation_binding_hash",
        "final_state",
        "alarm_emitted",
        "decision_physical_row_index",
        "numeric_reference_identities",
        "computation_identity",
        "trace_hash",
    }
    if any(type(record) is not dict or set(record) != allowed_record_keys for record in artifact.prediction_records):
        _fail("SCIENTIFIC_PREDICTION_PUBLIC_RECORD_SCHEMA_REJECTED")
    return artifact.artifact_hash


def _private_interval_set_hash_v1(
    kind: str, intervals: tuple[evaluator_metrics.IntervalV1, ...]
) -> str:
    return stable_hash_v1(
        {
            "artifact_type": f"task039e3_r2r_private_{kind}_interval_set_v1",
            "interval_semantics": "HALF_OPEN_FILE_LOCAL_ONE_SECOND",
            "intervals": [
                {"start": interval.start, "end": interval.end} for interval in intervals
            ],
        }
    )


def _load_real_label_custody_v1(
    token: _InnerD1ExecutionTokenV1,
    prediction: ScientificRulePredictionArtifactV1,
    feature_timestamps: tuple[str, ...],
    label_path: Path,
) -> RealLabelEventCustodyV1:
    _validate_execution_token_v1(token)
    validate_scientific_rule_prediction_artifact_v1(prediction)
    if label_path.is_symlink() or not label_path.is_file():
        _fail("TEST1_LABEL_FILE_INVALID")
    if _sha256_file_v1(label_path) != TEST1_LABEL_SHA256:
        _fail("TEST1_LABEL_HASH_REJECTED")
    timestamp_tokens: list[str] = []
    label_tokens: list[str] = []
    try:
        with label_path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader)
            if header != ["timestamp", "label"]:
                _fail("TEST1_LABEL_HEADER_REJECTED")
            for row in reader:
                if len(row) != 2:
                    _fail("TEST1_LABEL_ROW_WIDTH_REJECTED")
                timestamp_tokens.append(row[0])
                label_tokens.append(row[1])
    except InnerD1ExecutionV1Error:
        raise
    except Exception as exc:
        raise InnerD1ExecutionV1Error("TEST1_LABEL_PARSE_REJECTED") from exc
    if tuple(timestamp_tokens) != feature_timestamps or len(label_tokens) != EXPECTED_ROW_COUNT:
        _fail("TEST1_LABEL_ALIGNMENT_REJECTED")
    try:
        labels = v3.parse_raw_label_tokens_v3(tuple(label_tokens))
        attack_events = evaluator_metrics.derive_attack_events_v1(labels)
        alarm_timestamps = tuple(
            record["decision_physical_row_index"]
            for record in prediction.prediction_records
            if record["alarm_emitted"] is True
        )
        if any(type(value) is not int for value in alarm_timestamps):
            _fail("PREDICTION_ALARM_TIMESTAMP_REJECTED")
        alarm_episodes = evaluator_metrics.form_alarm_episodes_v1(alarm_timestamps)
    except InnerD1ExecutionV1Error:
        raise
    except Exception as exc:
        raise InnerD1ExecutionV1Error("REAL_LABEL_EVENT_DERIVATION_REJECTED") from exc
    custody = RealLabelEventCustodyV1(
        token=_REAL_LABEL_FACTORY_TOKEN,
        labels=labels,
        attack_events=attack_events,
        alarm_episodes=alarm_episodes,
    )
    _register_weak_v1(_ISSUED_LABEL_CUSTODIES, custody, custody.custody_hash)
    return custody


def _interval_overlap_v1(
    left: evaluator_metrics.IntervalV1, right: evaluator_metrics.IntervalV1
) -> bool:
    return left.start < right.end and right.start < left.end


def _build_private_metric_evidence_v1(
    custody: RealLabelEventCustodyV1,
) -> tuple[dict[str, object], ScientificMetricV1, ScientificMetricV1]:
    issued = _ISSUED_LABEL_CUSTODIES.get(id(custody))
    if issued is None or issued[0]() is not custody or issued[1] != custody.custody_hash:
        _fail("REAL_LABEL_CUSTODY_REJECTED")
    recall_numerator = sum(
        any(_interval_overlap_v1(attack, alarm) for alarm in custody._alarm_episodes)
        for attack in custody._attack_events
    )
    recall_denominator = len(custody._attack_events)
    far_numerator = sum(
        not any(_interval_overlap_v1(alarm, attack) for attack in custody._attack_events)
        for alarm in custody._alarm_episodes
    )
    far_denominator_hours = custody._normal_seconds / 3600.0
    evidence_payload: dict[str, object] = {
        "artifact_type": "task039e3_r2r_utility_inner_d1_private_metric_evidence_v1",
        "execution_version": EXECUTION_VERSION,
        "authorization_hash": AUTHORIZATION_HASH,
        "strict_label_vector_hash": custody.strict_label_vector_hash,
        "attack_event_set_hash": custody.attack_event_set_hash,
        "alarm_episode_set_hash": custody.alarm_episode_set_hash,
        "attack_event_recall": {
            "numerator": recall_numerator,
            "denominator": recall_denominator,
        },
        "normal_far_episodes_per_hour": {
            "numerator": far_numerator,
            "normal_second_denominator": custody._normal_seconds,
            "normal_hour_denominator": far_denominator_hours,
        },
        "attack_labeled_seconds": custody._attack_seconds,
        "normal_labeled_seconds": custody._normal_seconds,
        "attack_intervals": [
            {"start": item.start, "end": item.end} for item in custody._attack_events
        ],
        "alarm_episodes": [
            {"start": item.start, "end": item.end} for item in custody._alarm_episodes
        ],
    }
    evidence_hash = stable_hash_v1(evidence_payload)
    evidence = {**evidence_payload, "artifact_hash": evidence_hash}
    recall = _scientific_metric_v1(
        "attack_event_recall",
        ATTACK_EVENT_RECALL_FORMULA,
        recall_numerator,
        float(recall_denominator),
        "no_attack_events",
        evidence_hash,
    )
    far = _scientific_metric_v1(
        "normal_false_alarm_rate_per_hour",
        NORMAL_FAR_FORMULA,
        far_numerator,
        far_denominator_hours,
        "no_normal_exposure",
        evidence_hash,
    )
    return evidence, recall, far


def _scientific_metric_v1(
    name: str,
    formula: str,
    numerator: int,
    denominator: float,
    reason: str,
    evidence_hash: str,
) -> ScientificMetricV1:
    defined = denominator != 0.0
    value = float(numerator / denominator) if defined else None
    payload = {
        "artifact_type": "task039e3_r2r_scientific_metric_v1",
        "metric_policy_hash": v4.CORRECTED_METRIC_POLICY_HASH,
        "metric_name": name,
        "formula_identity": formula,
        "value": value,
        "defined": defined,
        "undefined_reason": None if defined else reason,
        "private_evidence_hash": evidence_hash,
    }
    return ScientificMetricV1(
        name,
        formula,
        value,
        defined,
        None if defined else reason,
        evidence_hash,
        stable_hash_v1(payload),
    )


@dataclass(frozen=True)
class InnerD1ExecutionOutcomeV1:
    run: InnerD1ExecutionRunV1
    prediction: ScientificRulePredictionArtifactV1
    attack_event_recall: ScientificMetricV1
    normal_far_episodes_per_hour: ScientificMetricV1
    alarm_episode_count: int
    readiness_hash: str
    bundle_hash: str
    receipt_hash: str


_SCIENTIFIC_EXECUTION_ATTEMPTS = 0
_SCIENTIFIC_EXECUTION_COMPLETED = False


def run_differential_equivalence_case_v1(
    rows: tuple[tuple[float, ...], ...],
    main_records: tuple[evaluator_authority.SyntheticNumericRecordV1, ...],
    supplement_records: tuple[evaluator_authority.SyntheticNumericRecordV1, ...],
) -> dict[str, object]:
    """Compare one synthetic fixture across R3 and the external real semantics."""

    authority, bundle = _load_public_authorities_v1()
    synthetic_frame = evaluator_input.build_synthetic_feature_frame_v1(
        bundle,
        source_file_identity=TEST1_FEATURE_FILENAME,
        start_physical_row_index=0,
        rows=rows,
    )
    synthetic_resolver = evaluator_authority.build_synthetic_numeric_resolver_v1(
        bundle, main_records, supplement_records
    )
    synthetic_census = evaluator_census.enumerate_full_census_v1(
        synthetic_frame, bundle, synthetic_resolver
    )
    synthetic_results = tuple(
        evaluator_rule.execute_rule_v1(
            envelope,
            synthetic_census,
            synthetic_frame,
            bundle,
            synthetic_resolver,
        )
        for envelope in synthetic_census.relation_opportunities
    )
    real_frame = build_differential_feature_frame_v1(bundle, rows)
    real_resolver = build_differential_numeric_resolver_v1(
        bundle, main_records, supplement_records
    )
    real_census = enumerate_real_full_census_v1(
        real_frame, bundle, real_resolver, differential=True
    )
    real_results = tuple(
        execute_real_rule_v1(
            envelope,
            real_census,
            real_frame,
            bundle,
            real_resolver,
            differential=True,
        )
        for envelope in real_census.relation_opportunities
    )
    synthetic_opportunities = tuple(
        (
            item.canonical_opportunity.opportunity_id,
            item.canonical_opportunity.relation_binding_hash,
            item.canonical_opportunity.physical_row_index,
        )
        for item in synthetic_census.relation_opportunities
    )
    real_opportunities = tuple(
        (
            item.canonical_opportunity.opportunity_id,
            item.canonical_opportunity.relation_binding_hash,
            item.canonical_opportunity.physical_row_index,
        )
        for item in real_census.relation_opportunities
    )
    synthetic_semantics = tuple(
        (
            result.opportunity_id,
            result.relation_binding_hash,
            result.final_state,
            result.alarm_emitted,
            result.decision_physical_row_index,
            result.numeric_reference_identities,
        )
        for result in synthetic_results
    )
    real_semantics = tuple(
        (
            result.opportunity_id,
            result.relation_binding_hash,
            result.final_state,
            result.alarm_emitted,
            result.decision_physical_row_index,
            result.numeric_reference_identities,
        )
        for result in real_results
    )
    counts = (
        synthetic_census.raw_source_event_count,
        synthetic_census.retained_source_event_count,
        synthetic_census.isolated_source_event_count,
        len(synthetic_census.relation_opportunities),
    )
    real_counts = (
        real_census.raw_source_event_count,
        real_census.retained_source_event_count,
        real_census.isolated_source_event_count,
        len(real_census.relation_opportunities),
    )
    if counts != real_counts or synthetic_opportunities != real_opportunities or synthetic_semantics != real_semantics:
        _fail("DIFFERENTIAL_SEMANTIC_DIVERGENCE")
    synthetic_alarms = tuple(
        result.decision_physical_row_index
        for result in synthetic_results
        if result.alarm_emitted and result.decision_physical_row_index is not None
    )
    real_alarms = tuple(
        result.decision_physical_row_index
        for result in real_results
        if result.alarm_emitted and result.decision_physical_row_index is not None
    )
    if evaluator_metrics.form_alarm_episodes_v1(synthetic_alarms) != evaluator_metrics.form_alarm_episodes_v1(real_alarms):
        _fail("DIFFERENTIAL_ALARM_EPISODE_DIVERGENCE")
    return {
        "semantic_equal": True,
        "semantic_divergences": 0,
        "counts": counts,
        "opportunity_count": len(real_opportunities),
        "intentional_hash_domain_differences": (
            "execution_mode",
            "committed_grant_custody",
            "real_frame_custody",
            "real_source_event_identity",
            "real_computation_identity",
            "real_trace_hash",
        ),
        "v4_authority_hash": authority.authority_hash,
    }


def _run_payload_v1(run: InnerD1ExecutionRunV1) -> dict[str, object]:
    return {
        key: value
        for key, value in run.__dict__.items()
        if key != "run_hash"
    }


def _self_hashed_document_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in payload:
        _fail("REPORT_PREHASHED_PAYLOAD_REJECTED")
    document = dict(payload)
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def _write_public_json_v1(relative: str, document: Mapping[str, Any]) -> None:
    root = _repository_root_v1()
    path = root / relative
    if path.is_symlink() or root.resolve() not in path.resolve().parents:
        _fail("PUBLIC_REPORT_PATH_REJECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(
        document,
        sort_keys=True,
        indent=2,
        ensure_ascii=True,
        allow_nan=False,
    ) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def _write_private_metric_evidence_v1(
    bindings: Mapping[str, str], evidence: Mapping[str, Any]
) -> str:
    root = _repository_root_v1().resolve()
    try:
        hai_root = Path(bindings[authorization_v1.HAI_DATA_ROOT_ENV]).resolve(strict=True)
        private_directory = hai_root.parent / ".paper_v_20260625_private_evidence"
        if private_directory == root or root in private_directory.parents:
            _fail("PRIVATE_EVIDENCE_INSIDE_REPOSITORY")
        private_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if private_directory.is_symlink():
            _fail("PRIVATE_EVIDENCE_DIRECTORY_REJECTED")
        path = private_directory / "task039e3_inner_d1_metric_evidence_v1.json"
        temporary = private_directory / "task039e3_inner_d1_metric_evidence_v1.tmp"
        content = json.dumps(
            evidence,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ) + "\n"
        temporary.write_text(content, encoding="utf-8", newline="\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
        replay = _strict_json_object_v1(path.read_bytes())
        if replay != evidence or _canonical_self_hash_v1(replay) != evidence["artifact_hash"]:
            _fail("PRIVATE_EVIDENCE_REPLAY_REJECTED")
        return str(evidence["artifact_hash"])
    except InnerD1ExecutionV1Error:
        raise
    except Exception as exc:
        raise InnerD1ExecutionV1Error("PRIVATE_EVIDENCE_WRITE_REJECTED") from exc


def _public_reports_v1(
    *,
    grant: CommittedInnerD1ExecutionGrantV1,
    prediction: ScientificRulePredictionArtifactV1,
    recall: ScientificMetricV1,
    far: ScientificMetricV1,
    private_evidence_hash: str,
    alarm_episode_count: int,
    run: InnerD1ExecutionRunV1,
) -> tuple[str, str, str]:
    bridge_commit, bridge_source_sha = _bridge_source_custody_v1()
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    bridge_audit = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d1_execution_v1_bridge_audit",
            "task_id": TASK_ID,
            "status": "passed_static_bridge_and_differential_audit",
            "execution_bridge_commit": bridge_commit,
            "execution_bridge_source_sha256": bridge_source_sha,
            "bridge_identity": BRIDGE_IDENTITY,
            "r3_implementation_identity": R3_IMPLEMENTATION_IDENTITY,
            "authorization_module_control_revision": "R2_PORTABLE_PREFLIGHT",
            "differential_semantic_cases": DIFFERENTIAL_SEMANTIC_CASES,
            "differential_semantic_divergences": 0,
            "independent_attacks": EXPECTED_INDEPENDENT_ATTACKS,
            "accepted_invalid": 0,
            "r3_evaluator_modified": False,
            "authorization_module_modified": False,
            "private_paths_exposed": 0,
            "private_numeric_values_exposed": 0,
        }
    )
    metrics = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d1_metrics_v1",
            "task_id": TASK_ID,
            "execution_mode": EXECUTION_MODE,
            "authorization_hash": AUTHORIZATION_HASH,
            "rule_prediction_artifact_hash": prediction.artifact_hash,
            "attack_event_recall": recall.to_public_dict(),
            "normal_far_episodes_per_hour": far.to_public_dict(),
            "private_metric_evidence_hash": private_evidence_hash,
            "alarm_count": prediction.alarm_count,
            "alarm_episode_count": alarm_episode_count,
            "counts": {
                "raw_source_event_count": prediction.raw_source_event_count,
                "retained_source_event_count": prediction.retained_source_event_count,
                "isolated_source_event_count": prediction.isolated_source_event_count,
                "relation_opportunity_count": prediction.relation_opportunity_count,
                "evaluated_count": prediction.evaluated_count,
                "abstain_count": prediction.abstain_count,
                "error_count": prediction.error_count,
            },
            "attack_intervals_publicly_exposed": False,
            "label_vector_publicly_exposed": False,
            "normal_second_denominator_publicly_exposed": False,
            "private_numeric_values_exposed": 0,
            "private_paths_exposed": 0,
        }
    )
    accounting = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d1_execution_v1_accounting",
            "task_id": TASK_ID,
            "execution_mode": EXECUTION_MODE,
            "execution_run_hash": run.run_hash,
            "scientific_execution_attempts": 1,
            "scientific_execution_retries": 0,
            "hai_test1_feature_hash_reads": 1,
            "hai_test1_feature_scientific_parses": 1,
            "label_test1_hash_reads": 1,
            "label_test1_scientific_parses": 1,
            "main_private_registry_reads": 1,
            "supplement_private_registry_reads": 1,
            "test2_accesses": 0,
            "detector_executions": 0,
            "d0_executions": 0,
            "d2_executions": 0,
            "outer_executions": 0,
            "provider_calls": 0,
            "label_before_prediction_access": False,
            "result_driven_changes": False,
            "private_paths_exposed": 0,
            "private_numeric_values_exposed": 0,
        }
    )
    readiness = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d1_execution_v1_readiness",
            "task_id": TASK_ID,
            "status": PASS_STATUS,
            "scientific_status": SCIENTIFIC_STATUS,
            "authorization_hash": AUTHORIZATION_HASH,
            "custody_preflight_hash": CUSTODY_PREFLIGHT_HASH,
            "committed_grant_hash": grant.grant_hash,
            "rule_prediction_artifact_hash": prediction.artifact_hash,
            "metrics_report_hash": metrics["artifact_hash"],
            "accounting_hash": accounting["artifact_hash"],
            "bridge_audit_hash": bridge_audit["artifact_hash"],
            "execution_run_hash": run.run_hash,
            "UTILITY_INNER_D1_EXECUTED": True,
            "UTILITY_INNER_D1_RESULT_FROZEN": True,
            "UTILITY_INNER_D1_RESULT_INTEGRITY_AUDITED": False,
            "UTILITY_INNER_D1_REAL_EXECUTION_COMPLETED": True,
            "UTILITY_INNER_D0_AUTHORIZED": False,
            "UTILITY_INNER_D2_AUTHORIZED": False,
            "UTILITY_OUTER_EXECUTION_AUTHORIZED": False,
            "REAL_UTILITY_EXECUTION_AUTHORIZED": False,
            "exact_next_task": "TASK-039E3-R2R-UTILITY-INNER-D1-RESULT-INTEGRITY-AUDIT-V1",
        }
    )
    bundle = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d1_execution_v1_bundle",
            "task_id": TASK_ID,
            "authorization_hash": AUTHORIZATION_HASH,
            "committed_preflight_hash": CUSTODY_PREFLIGHT_HASH,
            "committed_receipt_hash": RECEIPT_HASH,
            "bridge_audit_hash": bridge_audit["artifact_hash"],
            "rule_prediction_artifact_hash": prediction.artifact_hash,
            "metrics_report_hash": metrics["artifact_hash"],
            "accounting_hash": accounting["artifact_hash"],
            "readiness_hash": readiness["artifact_hash"],
            "execution_run_hash": run.run_hash,
            "private_metric_evidence_hash": private_evidence_hash,
        }
    )
    receipt = _self_hashed_document_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d1_execution_v1_receipt",
            "task_id": TASK_ID,
            "status": PASS_STATUS,
            "scientific_status": SCIENTIFIC_STATUS,
            "authorization_hash": AUTHORIZATION_HASH,
            "custody_preflight_hash": CUSTODY_PREFLIGHT_HASH,
            "authorization_receipt_hash": RECEIPT_HASH,
            "rule_prediction_artifact_hash": prediction.artifact_hash,
            "readiness_hash": readiness["artifact_hash"],
            "bundle_hash": bundle["artifact_hash"],
            "execution_run_hash": run.run_hash,
            "execution_attempts": 1,
            "execution_retries": 0,
            "test2_accesses": 0,
            "private_paths_exposed": 0,
            "private_numeric_values_exposed": 0,
        }
    )
    paths = {
        "bridge": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_EXECUTION_V1_BRIDGE_AUDIT.json",
        "prediction": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json",
        "metrics": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_METRICS_V1.json",
        "accounting": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_EXECUTION_V1_ACCOUNTING.json",
        "readiness": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_EXECUTION_V1_READINESS.json",
        "bundle": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_EXECUTION_V1_BUNDLE.json",
        "receipt": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_EXECUTION_V1_RECEIPT.json",
    }
    for name, document in (
        ("bridge", bridge_audit),
        ("prediction", prediction.to_public_dict()),
        ("metrics", metrics),
        ("accounting", accounting),
        ("readiness", readiness),
        ("bundle", bundle),
        ("receipt", receipt),
    ):
        _write_public_json_v1(paths[name], document)
    report_path = _repository_root_v1() / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_EXECUTION_V1_REPORT.md"
    report_text = (
        "# TASK-039E3 R2R Utility INNER D1 Execution V1\n\n"
        f"Status: `{PASS_STATUS}`\n\n"
        f"Scientific status: `{SCIENTIFIC_STATUS}`\n\n"
        "The first authorized real INNER D1 Rule-only execution completed exactly once. "
        "This report freezes the result without scientific interpretation or tuning.\n\n"
        f"- Authorization: `{AUTHORIZATION_HASH}`\n"
        f"- RulePrediction artifact: `{prediction.artifact_hash}`\n"
        f"- Attack-event recall: `{recall.value}` (defined: `{str(recall.defined).lower()}`)\n"
        f"- Normal FAR episodes/hour: `{far.value}` (defined: `{str(far.defined).lower()}`)\n"
        f"- Full-census opportunities: `{prediction.relation_opportunity_count}`\n"
        f"- Errors: `{prediction.error_count}`\n"
        "- Test2 accesses: `0`\n"
        "- Private paths exposed: `0`\n"
        "- Private numeric values exposed: `0`\n\n"
        "No D0, D2, detector, fusion, OUTER execution, result-driven rule change, or interpretation occurred.\n\n"
        "Exact next task: `TASK-039E3-R2R-UTILITY-INNER-D1-RESULT-INTEGRITY-AUDIT-V1`.\n"
    )
    report_path.write_text(report_text, encoding="utf-8", newline="\n")
    return str(readiness["artifact_hash"]), str(bundle["artifact_hash"]), str(receipt["artifact_hash"])


def execute_authorized_inner_d1_v1() -> InnerD1ExecutionOutcomeV1:
    """Execute the exact authorized real D1 experiment once, with no knobs."""

    global _SCIENTIFIC_EXECUTION_ATTEMPTS, _SCIENTIFIC_EXECUTION_COMPLETED
    if _SCIENTIFIC_EXECUTION_ATTEMPTS != 0 or _SCIENTIFIC_EXECUTION_COMPLETED:
        _fail("REAL_D1_EXECUTION_ALREADY_ATTEMPTED")
    grant = issue_committed_inner_d1_execution_grant_v1()
    token = _issue_execution_token_v1(grant)
    bindings = _parse_local_binding_file_v1()
    authority, bundle = _load_public_authorities_v1()
    del authority
    main_document = _strict_private_json_v1(
        Path(bindings[authorization_v1.MAIN_REGISTRY_ENV])
    )
    supplement_document = _strict_private_json_v1(
        Path(bindings[authorization_v1.SUPPLEMENT_REGISTRY_ENV])
    )
    resolver = build_real_private_numeric_resolver_v1(
        bundle,
        main_document=main_document,
        supplement_document=supplement_document,
    )
    hai_root = Path(bindings[authorization_v1.HAI_DATA_ROOT_ENV])
    feature_path = hai_root / "hai-23.05" / TEST1_FEATURE_FILENAME
    label_path = hai_root / "hai-23.05" / TEST1_LABEL_FILENAME
    _SCIENTIFIC_EXECUTION_ATTEMPTS = 1
    frame = _load_real_feature_frame_v1(token, bundle, feature_path)
    census = enumerate_real_full_census_v1(frame, bundle, resolver)
    results = tuple(
        execute_real_rule_v1(envelope, census, frame, bundle, resolver)
        for envelope in census.relation_opportunities
    )
    prediction = build_scientific_rule_prediction_artifact_v1(token, census, results)
    validate_scientific_rule_prediction_artifact_v1(prediction)
    label_custody = _load_real_label_custody_v1(
        token, prediction, frame._timestamps, label_path
    )
    private_evidence, recall, far = _build_private_metric_evidence_v1(label_custody)
    private_evidence_hash = _write_private_metric_evidence_v1(bindings, private_evidence)
    provisional_run = InnerD1ExecutionRunV1(
        grant.grant_hash,
        BRIDGE_IDENTITY,
        prediction.artifact_hash,
        private_evidence_hash,
        (recall.metric_hash, far.metric_hash),
        census.raw_source_event_count,
        census.retained_source_event_count,
        census.isolated_source_event_count,
        len(census.relation_opportunities),
        prediction.evaluated_count,
        prediction.alarm_count,
        len(label_custody._alarm_episodes),
        prediction.abstain_count,
        prediction.error_count,
        0,
        1,
        0,
        "",
    )
    run = replace(provisional_run, run_hash=stable_hash_v1(_run_payload_v1(provisional_run)))
    if run.error_count != 0:
        _fail("REAL_D1_ERROR_COUNT_NONZERO")
    readiness_hash, bundle_hash, receipt_hash = _public_reports_v1(
        grant=grant,
        prediction=prediction,
        recall=recall,
        far=far,
        private_evidence_hash=private_evidence_hash,
        alarm_episode_count=len(label_custody._alarm_episodes),
        run=run,
    )
    _SCIENTIFIC_EXECUTION_COMPLETED = True
    return InnerD1ExecutionOutcomeV1(
        run,
        prediction,
        recall,
        far,
        len(label_custody._alarm_episodes),
        readiness_hash,
        bundle_hash,
        receipt_hash,
    )
