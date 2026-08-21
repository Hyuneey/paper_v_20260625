"""Fail-closed D2 INNER execution authorization boundary.

This module validates public custody and one raw label hash.  It never computes
fusion, predictions, alarm episodes, or metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping
import weakref

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_d2_design_v1 import (
    D2_DESIGN_HASH,
    FROZEN_D0_DETECTOR_PREDICTION_HASH,
    FROZEN_D1_RULE_PREDICTION_HASH,
    REQUIRED_DISTINCT_SOURCE_COUNT,
    SAME_SECOND_POLICY,
    SOURCE_RESOLUTION_POLICY,
    build_d2_design_authority_v1,
    validate_d2_design_authority_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 import (
    ALARM_EPISODE_POLICY,
    ATTACK_EVENT_RECALL_FORMULA,
    NORMAL_FAR_FORMULA,
)
from paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 import (
    build_common42_authority_v1,
    validate_canonical_common42_authority_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import CANONICAL_V4_AUTHORITY_HASH


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-AUTHORIZATION-V1"
D2_EXECUTION_AUTHORIZATION_VERSION = "TASK039E3_R2R_D2_INNER_EXECUTION_AUTHORIZATION_V1"
D2_EXECUTION_AUTHORIZATION_SCOPE = "HAI_23_05_P1_TEST1_D2_D0_PLUS_VERIFIED_RULE_CORROBORATION_INNER_V1"
D2_ID = "D2_D0_PLUS_VERIFIED_RULE_CORROBORATION_V1"
D0_PRESERVATION_POLICY = "EVERY_FROZEN_D0_ALARM_IS_A_D2_ALARM"
LABEL_SHA256 = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
LABEL_BYTE_SIZE = 1242017
LABEL_ROWS = 54000
DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
INNER_SPLIT_ID = "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"
PROVENANCE_CLARIFICATION_HASH = "f0fbea249e11b6a3ae27a43b4b705d8537983511e2659d88f49b9c64dcf59e10"
D0_INTEGRITY_READINESS_HASH = "869fa95d7dd6282e45e73dfd6f5ad6b977747d7b63de1d65bdd0e933c10005e6"
D0_INTEGRITY_BUNDLE_HASH = "ec25c4da9d162e1ca493332e5b8b51f40de6de2839afeb809a53781421ad6d66"
D0_INTEGRITY_RECEIPT_HASH = "8f11f019f04e812f3a06f048b466256dfed0ad9b4b219ea033911a155b5d5835"
D1_INTEGRITY_READINESS_HASH = "8c6eb7f7b099bc48537c78cf7cb5510dbf599dfd58c37efc44705a6a9fd0f5be"
D1_INTEGRITY_BUNDLE_HASH = "e38b56e877842c1678fccaea0e23e5e1c761265534ff9fe8ccc0f5c24552c4db"
D1_INTEGRITY_RECEIPT_HASH = "1f42fecce799f09e2dfd73b2bc041f7f7bafd60522d95c004f27aa35b7846a4f"
REAL_CUSTODY_PREFLIGHT = "REAL_LABEL_AND_PREDICTION_CUSTODY_PREFLIGHT"
SYNTHETIC_CONTRACT_ONLY = "SYNTHETIC_CONTRACT_ONLY"
SOURCE_MAP_ARTIFACT_TYPE = "D2SourceResolutionMapV1"
FUTURE_ARTIFACT_FAMILY = "ScientificCombinedPredictionArtifactV1"

INCREMENTAL_METRIC_FORMULAS = (
    "D0_MISSED_ATTACK_EVENTS_RECOVERED_BY_RULE_RECOVERY_DIVIDED_BY_ALL_D0_MISSED_ATTACK_EVENTS",
    "D2_ATTACK_EVENT_RECALL_MINUS_D0_ATTACK_EVENT_RECALL",
    "RULE_RECOVERY_ALARM_EPISODES_WITH_ZERO_ATTACK_EVENT_OVERLAP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600",
    "D2_NORMAL_FAR_EPISODES_PER_HOUR_MINUS_D0_NORMAL_FAR_EPISODES_PER_HOUR",
)
FUTURE_EXECUTION_ORDER = (
    "REPLAY_COMMITTED_D2_AUTHORIZATION", "VALIDATE_D2_DESIGN", "VALIDATE_D0_PREDICTION",
    "VALIDATE_D1_PREDICTION", "VALIDATE_SOURCE_MAP", "PARSE_D0_PREDICTION",
    "PARSE_D1_PREDICTION", "COMPUTE_EXACT_SAME_SECOND_DISTINCT_SOURCE_CORROBORATION",
    "BUILD_COMBINED_PREDICTION", "FREEZE_COMBINED_PREDICTION", "VALIDATE_LABEL_RAW_HASH",
    "PARSE_LABELS", "DERIVE_ATTACK_EVENTS", "DERIVE_D2_ALARM_EPISODES",
    "COMPUTE_PRIMARY_METRICS", "COMPUTE_INCREMENTAL_METRICS", "FREEZE_RESULT", "STOP",
)

_REPORT_HASHES = {
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_DESIGN.json": "74e6d66fc506cf9be0d40848d4f3d5b51b51f398ee0c8448c1453d5344bc0b94",
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_INPUT_AUTHORITY.json": "6b483f8007db86f910524fea6204a6119f82c23ff6fa24d1302fc93e98c58fb9",
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_CORROBORATION_POLICY.json": "73069cade706c08065e4669dbe6b5c812f1e2d00d91d5e6ecc57e41d696a6751",
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_METRIC_POLICY.json": "a684368a13efe7699862cc626c4c6a28cb5eca342efe3cc3f4bb77adbfbaa012",
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_INDEPENDENCE.json": "4d684c5b2ea55ea6cd7280f5d64241b4f8483e4988319497388f193fd7db312e",
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_INDEPENDENT_AUDIT.json": "55599576c754c31f00519823d73ded39c924a114ac5eb94d006bba77ddc37932",
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_READINESS.json": "50a9547cadf0b6dca779dea5f107c6368fdde7d4e1251253c9394e328c1d5aea",
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_BUNDLE.json": "2b75563a57d89816b2936d4172762b9d3bca0cf1c8752c780d9c5ecc89cec675",
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_RECEIPT.json": "d14feaa9a1fe402159806f29ef7499d9ca1e119902fbf1d12faad7b010b0e245",
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_PROVENANCE_CLARIFICATION_R1.json": PROVENANCE_CLARIFICATION_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_PROVENANCE_R1_READINESS.json": "41a6dcf3428de7fa02284041a958be5926829db3f7527ccc1cd1a5f850a94211",
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_PROVENANCE_R1_BUNDLE.json": "b6e02a5319f78f15922a0d2f3239122ee11bcd33f6151ecfa80cc87741f63b83",
    "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_PROVENANCE_R1_RECEIPT.json": "bf049094ce211e86db22bdbdcfe78adddff76e1935cab792e594b09cf554355d",
    "TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_REPORT_HASH_R1_READINESS.json": D0_INTEGRITY_READINESS_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_REPORT_HASH_R1_BUNDLE.json": D0_INTEGRITY_BUNDLE_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_REPORT_HASH_R1_RECEIPT.json": D0_INTEGRITY_RECEIPT_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D1_RESULT_INTEGRITY_V1_READINESS.json": D1_INTEGRITY_READINESS_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D1_RESULT_INTEGRITY_V1_BUNDLE.json": D1_INTEGRITY_BUNDLE_HASH,
    "TASK-039E3_R2R_UTILITY_INNER_D1_RESULT_INTEGRITY_V1_RECEIPT.json": D1_INTEGRITY_RECEIPT_HASH,
}


class D2ExecutionAuthorizationError(ValueError):
    pass


def _fail(code: str) -> None:
    raise D2ExecutionAuthorizationError(code)


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except BaseException:
        _fail("D2_PUBLIC_ARTIFACT_INVALID")


def _validate_self_hash(document: Mapping[str, Any], expected: str) -> None:
    payload = dict(document)
    observed = payload.pop("artifact_hash", None)
    if observed != expected or stable_hash_v1(payload) != expected:
        _fail("D2_PUBLIC_ARTIFACT_HASH_REJECTED")


@dataclass(frozen=True)
class D2SourceResolutionEntryV1:
    relation_binding_hash: str
    source_variable_identity: str


@dataclass(frozen=True)
class D2SourceResolutionMapV1:
    artifact_type: str
    schema_version: str
    d2_design_hash: str
    v4_authority_hash: str
    portfolio: str
    source_resolution_policy: str
    entry_count: int
    unique_relation_count: int
    distinct_source_count: int
    entries: tuple[D2SourceResolutionEntryV1, ...]
    source_map_hash: str

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type, "schema_version": self.schema_version,
            "d2_design_hash": self.d2_design_hash, "v4_authority_hash": self.v4_authority_hash,
            "portfolio": self.portfolio, "source_resolution_policy": self.source_resolution_policy,
            "entry_count": self.entry_count, "unique_relation_count": self.unique_relation_count,
            "distinct_source_count": self.distinct_source_count,
            "entries": [entry.__dict__ for entry in self.entries],
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.source_map_hash}


_ISSUED_MAPS: dict[int, tuple[weakref.ReferenceType[D2SourceResolutionMapV1], str]] = {}


def _expected_source_map() -> D2SourceResolutionMapV1:
    reports = _root() / "docs" / "task_reports"
    authority = build_common42_authority_v1(
        _load_json(reports / "TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"),
        _load_json(reports / "TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"),
    )
    validate_canonical_common42_authority_v1(authority)
    entries = tuple(D2SourceResolutionEntryV1(item.relation_binding_hash, item.source) for item in authority.relations)
    provisional = D2SourceResolutionMapV1(SOURCE_MAP_ARTIFACT_TYPE, "1.0.0", D2_DESIGN_HASH,
        CANONICAL_V4_AUTHORITY_HASH, "COMMON-42", SOURCE_RESOLUTION_POLICY, len(entries),
        len({item.relation_binding_hash for item in entries}), len({item.source_variable_identity for item in entries}), entries, "")
    if provisional.entry_count != 42 or provisional.unique_relation_count != 42 or provisional.distinct_source_count != 9:
        _fail("D2_AUTHORIZATION_BLOCKED_SOURCE_MAPPING_NOT_CLOSED")
    return replace(provisional, source_map_hash=stable_hash_v1(provisional._payload()))


def build_d2_source_resolution_map_v1() -> D2SourceResolutionMapV1:
    value = _expected_source_map()
    oid = id(value)
    _ISSUED_MAPS[oid] = (weakref.ref(value, lambda _: _ISSUED_MAPS.pop(oid, None)), value.source_map_hash)
    return value


def validate_d2_source_resolution_map_v1(value: D2SourceResolutionMapV1) -> str:
    issued = _ISSUED_MAPS.get(id(value))
    if type(value) is not D2SourceResolutionMapV1 or issued is None or issued[0]() is not value or issued[1] != value.source_map_hash:
        _fail("D2_SOURCE_MAP_FACTORY_CUSTODY_REJECTED")
    expected = _expected_source_map()
    if value != expected or value.to_public_dict() != expected.to_public_dict():
        _fail("D2_SOURCE_MAP_REPLAY_REJECTED")
    return value.source_map_hash


@dataclass(frozen=True)
class D2PublicAuthorityReplayV1:
    authority_set_hash: str
    artifact_hashes: tuple[tuple[str, str], ...]


def replay_required_d2_public_authorities_v1() -> D2PublicAuthorityReplayV1:
    design = build_d2_design_authority_v1()
    validate_d2_design_authority_v1(design)
    reports = _root() / "docs" / "task_reports"
    for name, expected in _REPORT_HASHES.items():
        document = _load_json(reports / name)
        _validate_self_hash(document, expected)
    clarification = _load_json(reports / "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_PROVENANCE_CLARIFICATION_R1.json")
    if clarification.get("project_level_d0_inner_baseline_results_known_before_d2_policy_selection") is not True or clarification.get("project_level_d1_inner_baseline_results_known_before_d2_policy_selection") is not True or clarification.get("d2_result_observed_before_freeze") is not False:
        _fail("D2_PROVENANCE_CLARIFICATION_REJECTED")
    hashes = tuple(sorted(_REPORT_HASHES.items()))
    return D2PublicAuthorityReplayV1(stable_hash_v1({"artifact_hashes": hashes}), hashes)


def _validate_prediction_artifact(name: str, expected_hash: str, expected_type: str, expected_count: int) -> None:
    document = _load_json(_root() / "docs" / "task_reports" / name)
    _validate_self_hash(document, expected_hash)
    if document.get("artifact_type") != expected_type or document.get("label_blind") is not True or document.get("labels_accessed_before_prediction_freeze") is not False or len(document.get("prediction_records", ())) != expected_count:
        _fail("D2_PREDICTION_CUSTODY_REJECTED")


@dataclass(frozen=True)
class D2ExecutionCustodyPreflightReceiptV1:
    authorization_version: str
    authorization_scope: str
    custody_mode: str
    public_authority_set_hash: str
    d2_id: str
    d2_design_hash: str
    provenance_clarification_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    d0_integrity_receipt_hash: str
    d1_integrity_receipt_hash: str
    v4_authority_hash: str
    source_map_hash: str
    source_map_entry_count: int
    source_map_unique_relation_count: int
    source_map_distinct_source_count: int
    required_distinct_source_count: int
    same_second_policy: str
    d0_preservation_policy: str
    label_expected_hash: str
    label_hash_match: bool
    test1_feature_accesses: int
    label_scientific_parses: int
    fusion_computations: int
    d2_executions: int
    test2_accesses: int
    private_paths_exposed: int
    private_numeric_values_exposed: int
    real_preflight_attempts: int
    real_preflight_retries: int
    custody_preflight_hash: str
    _replay: D2PublicAuthorityReplayV1 = field(repr=False, compare=False)
    _source_map: D2SourceResolutionMapV1 = field(repr=False, compare=False)

    def _payload(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_") and k != "custody_preflight_hash"}
    def to_public_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.custody_preflight_hash}


_ISSUED_PREFLIGHTS: dict[int, tuple[weakref.ReferenceType[D2ExecutionCustodyPreflightReceiptV1], str]] = {}
_REAL_PREFLIGHT_ATTEMPTED = False


def _build_preflight(replay: D2PublicAuthorityReplayV1, source_map: D2SourceResolutionMapV1, real: bool) -> D2ExecutionCustodyPreflightReceiptV1:
    provisional = D2ExecutionCustodyPreflightReceiptV1(D2_EXECUTION_AUTHORIZATION_VERSION, D2_EXECUTION_AUTHORIZATION_SCOPE,
        REAL_CUSTODY_PREFLIGHT if real else SYNTHETIC_CONTRACT_ONLY, replay.authority_set_hash, D2_ID, D2_DESIGN_HASH,
        PROVENANCE_CLARIFICATION_HASH, FROZEN_D0_DETECTOR_PREDICTION_HASH, FROZEN_D1_RULE_PREDICTION_HASH,
        D0_INTEGRITY_RECEIPT_HASH, D1_INTEGRITY_RECEIPT_HASH, CANONICAL_V4_AUTHORITY_HASH, source_map.source_map_hash,
        42, 42, 9, 2, SAME_SECOND_POLICY, D0_PRESERVATION_POLICY, LABEL_SHA256, True, 0, 0, 0, 0, 0, 0, 0,
        1 if real else 0, 0, "", replay, source_map)
    return replace(provisional, custody_preflight_hash=stable_hash_v1(provisional._payload()))


def _issue_preflight(value: D2ExecutionCustodyPreflightReceiptV1) -> D2ExecutionCustodyPreflightReceiptV1:
    oid=id(value); _ISSUED_PREFLIGHTS[oid]=(weakref.ref(value,lambda _: _ISSUED_PREFLIGHTS.pop(oid,None)),value.custody_preflight_hash); return value


def build_synthetic_d2_execution_custody_preflight_receipt_v1() -> D2ExecutionCustodyPreflightReceiptV1:
    source_map=build_d2_source_resolution_map_v1(); return _issue_preflight(_build_preflight(replay_required_d2_public_authorities_v1(),source_map,False))


def validate_d2_execution_custody_preflight_receipt_v1(value: D2ExecutionCustodyPreflightReceiptV1, *, require_real: bool=False) -> str:
    issued=_ISSUED_PREFLIGHTS.get(id(value))
    if type(value) is not D2ExecutionCustodyPreflightReceiptV1 or issued is None or issued[0]() is not value or issued[1] != value.custody_preflight_hash:
        _fail("D2_PREFLIGHT_FACTORY_CUSTODY_REJECTED")
    validate_d2_source_resolution_map_v1(value._source_map)
    expected=_build_preflight(value._replay,value._source_map,value.custody_mode==REAL_CUSTODY_PREFLIGHT)
    if value != expected or value.to_public_dict() != expected.to_public_dict() or (require_real and value.custody_mode != REAL_CUSTODY_PREFLIGHT):
        _fail("D2_PREFLIGHT_REPLAY_REJECTED")
    return value.custody_preflight_hash


def _label_hash_from_binding() -> str:
    binding=_root()/".env.custody.local"
    try:
        if binding.is_symlink() or not binding.is_file(): _fail("D2_LABEL_CUSTODY_UNAVAILABLE")
        values={}
        for line in binding.read_text(encoding="utf-8").splitlines():
            m=re.fullmatch(r"([A-Z0-9_]+)='(.*)'",line)
            if m: values[m.group(1)]=m.group(2).replace("'\"'\"'", "'")
        root=Path(values["HAI_DATA_ROOT"]); path=root/"hai-23.05"/"label-test1.csv"
        if root.is_symlink() or not root.is_dir() or path.is_symlink() or not path.is_file() or path.stat().st_size != LABEL_BYTE_SIZE: _fail("D2_LABEL_CUSTODY_INVALID")
        digest=sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024*1024),b""): digest.update(chunk)
        return digest.hexdigest()
    except D2ExecutionAuthorizationError: raise
    except BaseException: _fail("D2_LABEL_CUSTODY_INVALID")


def perform_d2_inner_execution_custody_preflight_v1() -> D2ExecutionCustodyPreflightReceiptV1:
    global _REAL_PREFLIGHT_ATTEMPTED
    if _REAL_PREFLIGHT_ATTEMPTED: _fail("D2_REAL_PREFLIGHT_ALREADY_ATTEMPTED")
    _REAL_PREFLIGHT_ATTEMPTED=True
    replay=replay_required_d2_public_authorities_v1()
    _validate_prediction_artifact("TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json",FROZEN_D0_DETECTOR_PREDICTION_HASH,"ScientificDetectorPredictionArtifactV1",54000)
    _validate_prediction_artifact("TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json",FROZEN_D1_RULE_PREDICTION_HASH,"task039e3_r2r_scientific_rule_prediction_artifact_v1",6031)
    source_map=build_d2_source_resolution_map_v1()
    if _label_hash_from_binding()!=LABEL_SHA256: _fail("D2_LABEL_HASH_REJECTED")
    return _issue_preflight(_build_preflight(replay,source_map,True))


@dataclass(frozen=True)
class D2InnerExecutionAuthorizationV1:
    authorization_version: str
    authorization_scope: str
    authorization_status: str
    custody_preflight_hash: str
    d2_id: str
    d2_design_hash: str
    provenance_clarification_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    source_map_hash: str
    required_distinct_source_count: int
    same_second_policy: str
    d0_preservation_policy: str
    future_artifact_family: str
    future_record_count: int
    allowed_trigger_classes: tuple[str,...]
    future_execution_order: tuple[str,...]
    primary_metric_formulas: tuple[str,...]
    incremental_metric_formulas: tuple[str,...]
    d2_inner_execution_authorized: bool
    d2_combined_prediction_authorized: bool
    d0_prediction_consumption_authorized: bool
    d1_prediction_consumption_authorized: bool
    common42_source_map_consumption_authorized: bool
    label_metric_evaluation_authorized: bool
    label_access_before_combined_prediction_freeze_authorized: bool
    test1_feature_access_authorized: bool
    d0_rerun_authorized: bool
    d1_rerun_authorized: bool
    d0_score_access_authorized: bool
    rule_reevaluation_authorized: bool
    fusion_change_authorized: bool
    fusion_candidate_search_authorized: bool
    test2_authorized: bool
    outer_authorized: bool
    authorization_hash: str
    _receipt: D2ExecutionCustodyPreflightReceiptV1=field(repr=False,compare=False)
    def _payload(self)->dict[str,Any]: return {k:v for k,v in self.__dict__.items() if not k.startswith('_') and k!='authorization_hash'}
    def to_public_dict(self)->dict[str,Any]: return {**self._payload(),"artifact_hash":self.authorization_hash}


_ISSUED_AUTHS: dict[int,tuple[weakref.ReferenceType[D2InnerExecutionAuthorizationV1],str]]={}
_REAL_AUTH_ISSUED=False


def _build_auth(receipt:D2ExecutionCustodyPreflightReceiptV1)->D2InnerExecutionAuthorizationV1:
    real=receipt.custody_mode==REAL_CUSTODY_PREFLIGHT
    provisional=D2InnerExecutionAuthorizationV1(D2_EXECUTION_AUTHORIZATION_VERSION,D2_EXECUTION_AUTHORIZATION_SCOPE,
        "AUTHORIZED_FOR_FUTURE_D2_INNER_EXECUTION" if real else SYNTHETIC_CONTRACT_ONLY,receipt.custody_preflight_hash,D2_ID,D2_DESIGN_HASH,
        PROVENANCE_CLARIFICATION_HASH,FROZEN_D0_DETECTOR_PREDICTION_HASH,FROZEN_D1_RULE_PREDICTION_HASH,receipt.source_map_hash,2,SAME_SECOND_POLICY,
        D0_PRESERVATION_POLICY,FUTURE_ARTIFACT_FAMILY,54000,("NONE","D0_ONLY","RULE_RECOVERY","D0_AND_RULE_CORROBORATION"),FUTURE_EXECUTION_ORDER,
        (ATTACK_EVENT_RECALL_FORMULA,NORMAL_FAR_FORMULA),INCREMENTAL_METRIC_FORMULAS,real,real,real,real,real,real,False,False,False,False,False,False,False,False,False,False,"",receipt)
    return replace(provisional,authorization_hash=stable_hash_v1(provisional._payload()))


def issue_d2_inner_execution_authorization_v1(receipt:D2ExecutionCustodyPreflightReceiptV1)->D2InnerExecutionAuthorizationV1:
    global _REAL_AUTH_ISSUED
    validate_d2_execution_custody_preflight_receipt_v1(receipt)
    if receipt.custody_mode==REAL_CUSTODY_PREFLIGHT:
        if _REAL_AUTH_ISSUED: _fail("D2_REAL_AUTH_ALREADY_ISSUED")
        _REAL_AUTH_ISSUED=True
    value=_build_auth(receipt); oid=id(value); _ISSUED_AUTHS[oid]=(weakref.ref(value,lambda _: _ISSUED_AUTHS.pop(oid,None)),value.authorization_hash); return value


def validate_d2_inner_execution_authorization_v1(value:D2InnerExecutionAuthorizationV1,receipt:D2ExecutionCustodyPreflightReceiptV1,*,require_real:bool=False)->str:
    issued=_ISSUED_AUTHS.get(id(value))
    if type(value) is not D2InnerExecutionAuthorizationV1 or issued is None or issued[0]() is not value or issued[1]!=value.authorization_hash or value._receipt is not receipt:
        _fail("D2_AUTH_FACTORY_CUSTODY_REJECTED")
    validate_d2_execution_custody_preflight_receipt_v1(receipt,require_real=require_real)
    expected=_build_auth(receipt)
    if value!=expected or value.to_public_dict()!=expected.to_public_dict(): _fail("D2_AUTH_REPLAY_REJECTED")
    if require_real and not value.d2_inner_execution_authorized: _fail("D2_REAL_AUTH_REQUIRED")
    return value.authorization_hash


__all__=[name for name in globals() if name.startswith("D2") or name.startswith("build_") or name.startswith("validate_") or name.startswith("perform_") or name.startswith("issue_") or name.startswith("replay_")]
