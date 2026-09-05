"""DG-05 executable-authority closure (prospective, synthetic-testable).

This module deliberately does not know where real attack, label, scenario,
model, or portfolio files live.  All execution is capability-bound to typed
authorities and canonical bytes.  Historical V2 custody contracts remain
unchanged; this is the V3 execution layer that closes B1--B8.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import secrets
from typing import Any, Callable, Mapping, Sequence

from paperworks.data.hai_normal_projection_v2 import schema as csv_schema, selected_rows
from paperworks.validation_v2.multipanel_custody_v1 import (
    FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
    FROZEN_FEATURE_IDS_V2,
    FROZEN_FUSION_POLICY_HASH_V2,
    FROZEN_METHOD_BUNDLE_HASH_V2,
    FROZEN_PANEL_ORDER_V2,
    FROZEN_PORTFOLIO_HASHES_V2,
    FrozenFeatureAllowlistAuthorityV2,
    FrozenPhysicalFileAuthorityV2,
    PhysicalFileIdentityV2,
)
from paperworks.validation_v2.multipanel_metrics_v1 import wilson95_v1


class DG05ClosureError(ValueError):
    """A fail-closed executable authority or custody violation."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def digest(value: Any) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def self_hashed(body: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(body)
    value["self_hash"] = digest(value)
    return value


def validate_self_hashed(value: Mapping[str, Any]) -> None:
    if set(value) == {"self_hash"} or value.get("self_hash") != digest({k: v for k, v in value.items() if k != "self_hash"}):
        raise DG05ClosureError("SELF_HASH_MISMATCH")


def _sha(value: str, field: str) -> None:
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise DG05ClosureError(f"{field}:SHA256_REQUIRED")


def _git(value: str, field: str) -> None:
    if type(value) is not str or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise DG05ClosureError(f"{field}:FULL_GIT_SHA_REQUIRED")


def _id(value: str, field: str) -> None:
    if type(value) is not str or not value or any(c in value for c in ("/", "\\", ":")):
        raise DG05ClosureError(f"{field}:SAFE_ID_REQUIRED")


def file_sha256(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def publish_new(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    except FileExistsError as exc:
        raise DG05ClosureError("APPEND_ONLY_CONFLICT") from exc
    finally:
        if temporary.exists():
            temporary.unlink()
    if path.read_bytes() != payload:
        raise DG05ClosureError("DURABLE_REPLAY_MISMATCH")
    return sha256(payload).hexdigest()


# Unchanged scientific authorities.  A manifest is valid only if every value
# equals this closed set; no "latest/current/default" lookup exists.
FROZEN_SCIENTIFIC_AUTHORITIES_V1: dict[str, str] = {
    "scientific_preregistration": "cffa6f00dadee1bdd400cdbee545eb9cccd93dcf5da8c6bab3f67809644e8c61",
    "method_bundle": FROZEN_METHOD_BUNDLE_HASH_V2,
    "metric": "1222d0c7431376dbfa77451875f811123f41af881ae1472b30cd4a2e0f1f0776",
    "statistical": "cf90fee47e9294873e09aa516df8163328ee924d756c66b18a811c4ea2f9b463",
    "etapr": "5381ceb1f19f25354a8feb36488dfaa85d3f2945770dc352f2bf8c18fd86cae4",
    "fusion": FROZEN_FUSION_POLICY_HASH_V2,
    "attack_file_census": FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
    "feature_allowlist_bundle": "e49ba9ee3f6a2f1273666c41ac1584636a53d5b4334d6cb95e3eed0b17a2764b",
    "p1_mapping_bundle_v2": "93b94ab988096020907bc2de738618ce7a9121230f9d4a19111dd3b0f034689d",
    "global_custody_v2": "df0fe200b0a2278eeb7209411c952be58f63119f77f521763419020e3c1e8e60",
}

FROZEN_METHOD_IDS_BY_PANEL_V1: dict[str, tuple[str, ...]] = {
    "HAI23_TEST2_PRIMARY_HELDOUT_V1": (
        "M0_PCA_SPE", "M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0",
        "M4_PCA_PLUS_T2", "ISOLATION_FOREST", "ISOLATION_FOREST_PLUS_T2",
        "V2A_RULE_ONLY_REFERENCE", "HISTORICAL_PCA_PLUS_V2A_CONTINUITY",
    ),
    "HAI22_EXTERNAL_REPLICATION_V1": (
        "M0_PCA_SPE", "M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0",
        "M4_PCA_PLUS_T2", "ISOLATION_FOREST", "ISOLATION_FOREST_PLUS_T2",
    ),
    "HAI21_EXTERNAL_REPLICATION_V1": (
        "M0_PCA_SPE", "M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0",
        "M4_PCA_PLUS_T2", "ISOLATION_FOREST", "ISOLATION_FOREST_PLUS_T2",
    ),
}

_P1_23 = "P1_FCV01D P1_FCV01Z P1_FCV02D P1_FCV02Z P1_FCV03D P1_FCV03Z P1_FT01 P1_FT01Z P1_FT02 P1_FT02Z P1_FT03 P1_FT03Z P1_LCV01D P1_LCV01Z P1_LIT01 P1_PCV01D P1_PCV01Z P1_PCV02D P1_PCV02Z P1_PIT01 P1_PIT01_HH P1_PIT02 P1_PP01AD P1_PP01AR P1_PP01BD P1_PP01BR P1_PP02D P1_PP02R P1_PP04 P1_PP04D P1_PP04SP P1_SOL01D P1_SOL03D P1_STSP P1_TIT01 P1_TIT02 P1_TIT03 x1001_05_SETPOINT_OUT x1001_15_ASSIGN_OUT x1002_07_SETPOINT_OUT x1002_08_SETPOINT_OUT x1003_10_SETPOINT_OUT x1003_18_SETPOINT_OUT x1003_24_SUM_OUT".split()
_P1_22 = "P1_B2004 P1_B2016 P1_B3004 P1_B3005 P1_B4002 P1_B4005 P1_B400B P1_B4022 P1_FCV01D P1_FCV01Z P1_FCV02D P1_FCV02Z P1_FCV03D P1_FCV03Z P1_FT01 P1_FT01Z P1_FT02 P1_FT02Z P1_FT03 P1_FT03Z P1_LCV01D P1_LCV01Z P1_LIT01 P1_PCV01D P1_PCV01Z P1_PCV02D P1_PCV02Z P1_PIT01 P1_PIT01_HH P1_PIT02 P1_PP01AD P1_PP01AR P1_PP01BD P1_PP01BR P1_PP02D P1_PP02R P1_PP04 P1_PP04SP P1_SOL01D P1_SOL03D P1_STSP P1_TIT01 P1_TIT02 P1_TIT03".split()
_P1_21 = "P1_B2004 P1_B2016 P1_B3004 P1_B3005 P1_B4002 P1_B4005 P1_B400B P1_B4022 P1_FCV01D P1_FCV01Z P1_FCV02D P1_FCV02Z P1_FCV03D P1_FCV03Z P1_FT01 P1_FT01Z P1_FT02 P1_FT02Z P1_FT03 P1_FT03Z P1_LCV01D P1_LCV01Z P1_LIT01 P1_PCV01D P1_PCV01Z P1_PCV02D P1_PCV02Z P1_PIT01 P1_PIT02 P1_PP01AD P1_PP01AR P1_PP01BD P1_PP01BR P1_PP02D P1_PP02R P1_STSP P1_TIT01 P1_TIT02".split()
_P2_23_22 = "P2_24Vdc P2_ATSW_Lamp P2_AutoGO P2_AutoSD P2_Emerg P2_MASW P2_MASW_Lamp P2_ManualGO P2_ManualSD P2_OnOff P2_RTR P2_SCO P2_SCST P2_SIT01 P2_TripEx P2_VIBTR01 P2_VIBTR02 P2_VIBTR03 P2_VIBTR04 P2_VT01 P2_VTR01 P2_VTR02 P2_VTR03 P2_VTR04".split()
_P2_21 = "P2_24Vdc P2_ASD P2_AutoGO P2_CO_rpm P2_Emerg P2_HILout P2_MSD P2_ManualGO P2_OnOff P2_RTR P2_SIT01 P2_SIT02 P2_TripEx P2_VT01 P2_VTR01 P2_VTR02 P2_VTR03 P2_VTR04 P2_VXT02 P2_VXT03 P2_VYT02 P2_VYT03".split()
_P3_23_22 = "P3_FIT01 P3_LCP01D P3_LCV01D P3_LH01 P3_LIT01 P3_LL01 P3_PIT01".split()
_P3_21 = "P3_FIT01 P3_LCP01D P3_LCV01D P3_LH P3_LIT01 P3_LL P3_PIT01".split()
_P4_23_22 = "P4_HT_FD P4_HT_PO P4_HT_PS P4_LD P4_ST_FD P4_ST_GOV P4_ST_LD P4_ST_PO P4_ST_PS P4_ST_PT01 P4_ST_TT01".split()
_P4_21 = "P4_HT_FD P4_HT_LD P4_HT_PO P4_HT_PS P4_LD P4_ST_FD P4_ST_GOV P4_ST_LD P4_ST_PO P4_ST_PS P4_ST_PT01 P4_ST_TT01".split()
FROZEN_FULL_SCOPE_PROCESS_MAP_V1: dict[str, dict[str, tuple[str, ...]]] = {
    "23.05": {"P1": tuple(_P1_23), "P2": tuple(_P2_23_22), "P3": tuple(_P3_23_22), "P4": tuple(_P4_23_22)},
    "22.04": {"P1": tuple(_P1_22), "P2": tuple(_P2_23_22), "P3": tuple(_P3_23_22), "P4": tuple(_P4_23_22)},
    "21.03": {"P1": tuple(_P1_21), "P2": tuple(_P2_21), "P3": tuple(_P3_21), "P4": tuple(_P4_21)},
}


@dataclass(frozen=True, order=True)
class FullProcessPointV1:
    dataset_version: str
    canonical_identity: str
    official_process: str
    p1_membership: str
    evidence_hash: str
    authority_status: str = "OFFICIAL_EXACT_IDENTITY"

    def validate(self) -> None:
        _id(self.dataset_version, "dataset_version")
        _id(self.canonical_identity, "canonical_identity")
        if self.official_process not in ("P1", "P2", "P3", "P4"):
            raise DG05ClosureError("OFFICIAL_PROCESS_REQUIRED")
        if self.p1_membership not in ("YES", "NO", "UNRESOLVED"):
            raise DG05ClosureError("P1_MEMBERSHIP_REQUIRED")
        if self.p1_membership == "YES" and self.official_process != "P1":
            raise DG05ClosureError("P1_PROCESS_CONTRADICTION")
        if self.p1_membership == "NO" and self.official_process == "P1":
            raise DG05ClosureError("NON_P1_PROCESS_CONTRADICTION")
        _sha(self.evidence_hash, "evidence_hash")

    def document(self) -> dict[str, str]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class FullProcessScopeAuthorityV1:
    points: tuple[FullProcessPointV1, ...]
    official_manual_hash: str
    official_schema_hashes: tuple[tuple[str, str], ...]
    source_commit: str
    version_counts: tuple[tuple[str, int], ...] = ()
    declared_count_discrepancies: tuple[str, ...] = ()
    official_identity_set_hashes: tuple[tuple[str, str], ...] = ()
    supplemental_authority_hashes: tuple[tuple[str, str], ...] = ()
    authority_mode: str = "PRODUCTION"

    def document(self) -> dict[str, Any]:
        body = {
            "schema": "full_process_scope_authority_v1",
            "points": [p.document() for p in self.points],
            "official_manual_hash": self.official_manual_hash,
            "official_schema_hashes": [list(v) for v in self.official_schema_hashes],
            "source_commit": self.source_commit,
            "version_counts": {k: v for k, v in self.version_counts},
            "declared_count_discrepancies": list(self.declared_count_discrepancies),
            "official_identity_set_hashes": {k: v for k, v in self.official_identity_set_hashes},
            "supplemental_authority_hashes": {k: v for k, v in self.supplemental_authority_hashes},
            "authority_mode": self.authority_mode,
        }
        return self_hashed(body)

    def validate(self) -> None:
        _sha(self.official_manual_hash, "official_manual_hash")
        _git(self.source_commit, "source_commit")
        if not self.points or tuple(sorted(self.points)) != self.points:
            raise DG05ClosureError("CANONICAL_FULL_SCOPE_REQUIRED")
        keys = [(p.dataset_version, p.canonical_identity) for p in self.points]
        if len(keys) != len(set(keys)):
            raise DG05ClosureError("DUPLICATE_OFFICIAL_IDENTITY")
        for p in self.points:
            p.validate()
        for version, value in self.official_schema_hashes:
            _id(version, "schema_version")
            _sha(value, "official_schema_hash")
        actual = {version: sum(p.dataset_version == version for p in self.points) for version, _ in self.official_schema_hashes}
        if actual != dict(self.version_counts):
            raise DG05ClosureError("FULL_SCOPE_VERSION_COUNT_MISMATCH")
        if self.authority_mode == "PRODUCTION":
            if actual != {"21.03": 79, "22.04": 86, "23.05": 86}:
                raise DG05ClosureError("FULL_OFFICIAL_SCHEMA_UNIVERSE_REQUIRED")
            if "HAI21_MANUAL_DECLARED_78_BUT_OFFICIAL_NORMAL_SCHEMA_CONTAINS_79" not in self.declared_count_discrepancies:
                raise DG05ClosureError("HAI21_DECLARED_SCHEMA_COUNT_DISCREPANCY_REQUIRED")
            observed_hashes = {version: digest(sorted(p.canonical_identity for p in self.points if p.dataset_version == version)) for version in actual}
            if observed_hashes != dict(self.official_identity_set_hashes):
                raise DG05ClosureError("EXACT_OFFICIAL_IDENTITY_SET_REQUIRED")
            for version, process_map in FROZEN_FULL_SCOPE_PROCESS_MAP_V1.items():
                expected = {(identity, process) for process, identities in process_map.items() for identity in identities}
                observed = {(p.canonical_identity, p.official_process) for p in self.points if p.dataset_version == version}
                if observed != expected:
                    raise DG05ClosureError("FROZEN_OFFICIAL_PROCESS_MAP_REQUIRED")
            supplemental = dict(self.supplemental_authority_hashes)
            required_supplemental = {"HAI23_BOILER_GRAPH", "HAI23_DCS_1001H", "HAI23_DCS_1002H", "HAI23_DCS_1003H"}
            if set(supplemental) != required_supplemental:
                raise DG05ClosureError("COMPLETE_HAI23_DCS_GRAPH_AUTHORITY_REQUIRED")
            for value in supplemental.values():
                _sha(value, "supplemental_authority_hash")
            schema_hashes = dict(self.official_schema_hashes)
            for point in self.points:
                if point.authority_status not in ("MANUAL_EXACT", "OFFICIAL_HEADER_EXACT", "VERIFIED_PUBLIC_GRAPH_ALIAS", "HEADER_ONLY_MANUAL_UNDOCUMENTED"):
                    raise DG05ClosureError("OFFICIAL_POINT_AUTHORITY_STATUS_REQUIRED")
                extra = None
                if point.dataset_version == "23.05" and point.canonical_identity.startswith("x100"):
                    group = point.canonical_identity.split("_", 1)[0].upper().replace("X", "HAI23_DCS_") + "H"
                    extra = supplemental.get(group)
                    if point.authority_status != "VERIFIED_PUBLIC_GRAPH_ALIAS" or extra is None:
                        raise DG05ClosureError("HAI23_XTAG_DCS_GRAPH_BINDING_REQUIRED")
                if point.dataset_version == "21.03" and point.canonical_identity == "P2_SIT02":
                    if point.authority_status != "HEADER_ONLY_MANUAL_UNDOCUMENTED" or point.p1_membership != "UNRESOLVED":
                        raise DG05ClosureError("HAI21_P2_SIT02_DISCREPANCY_REQUIRED")
                expected = digest({"manual_hash": self.official_manual_hash, "schema_hash": schema_hashes[point.dataset_version],
                                   "identity": point.canonical_identity, "process": point.official_process,
                                   "p1_membership": point.p1_membership, "authority_status": point.authority_status,
                                   "supplemental_hash": extra})
                if point.evidence_hash != expected:
                    raise DG05ClosureError("POINT_OFFICIAL_EVIDENCE_BINDING_MISMATCH")
        elif self.authority_mode != "SYNTHETIC_REHEARSAL":
            raise DG05ClosureError("FULL_SCOPE_AUTHORITY_MODE_REQUIRED")

    def classify(self, dataset_version: str, identity: str) -> str:
        self.validate()
        point = next((p for p in self.points if (p.dataset_version, p.canonical_identity) == (dataset_version, identity)), None)
        if point is None or point.p1_membership == "UNRESOLVED":
            return "UNRESOLVED"
        return "P1" if point.p1_membership == "YES" else "KNOWN_NON_P1"


@dataclass(frozen=True, order=True)
class DetectorSubauthorityV1:
    panel_id: str
    detector_id: str
    umbrella_authority_hash: str
    implementation_hash: str
    feature_order_hash: str
    fitted_model_hash: str
    fit_authority_hash: str
    threshold_authority_hash: str
    prediction_schema_hash: str
    environment_hash: str

    def validate(self) -> None:
        if self.panel_id not in FROZEN_PANEL_ORDER_V2 or self.detector_id not in ("PCA_SPE", "ISOLATION_FOREST"):
            raise DG05ClosureError("EXACT_DETECTOR_IDENTITY_REQUIRED")
        for name in self.__dataclass_fields__:
            if name not in ("panel_id", "detector_id"):
                _sha(getattr(self, name), name)

    def document(self) -> dict[str, str]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class DetectorSubauthorityRegistryV1:
    entries: tuple[DetectorSubauthorityV1, ...]
    source_commit: str

    def document(self) -> dict[str, Any]:
        return self_hashed({"schema": "detector_subauthority_registry_v1", "entries": [e.document() for e in self.entries], "source_commit": self.source_commit})

    def validate(self) -> None:
        _git(self.source_commit, "source_commit")
        if tuple(sorted(self.entries)) != self.entries:
            raise DG05ClosureError("CANONICAL_DETECTOR_REGISTRY_REQUIRED")
        keys = {(e.panel_id, e.detector_id) for e in self.entries}
        if keys != {(p, d) for p in FROZEN_PANEL_ORDER_V2 for d in ("PCA_SPE", "ISOLATION_FOREST")}:
            raise DG05ClosureError("SIX_DETECTOR_SUBAUTHORITIES_REQUIRED")
        for e in self.entries:
            e.validate()

    def lookup(self, panel_id: str, detector_id: str) -> DetectorSubauthorityV1:
        self.validate()
        for entry in self.entries:
            if (entry.panel_id, entry.detector_id) == (panel_id, detector_id):
                return entry
        raise DG05ClosureError("DETECTOR_SUBAUTHORITY_NOT_FOUND")


@dataclass(frozen=True, order=True)
class MethodDispatchEntryV1:
    panel_id: str
    method_id: str
    executor_class: str
    component_hashes: tuple[str, ...]
    detector_id: str | None = None

    def validate(self) -> None:
        if self.panel_id not in FROZEN_PANEL_ORDER_V2:
            raise DG05ClosureError("UNKNOWN_PANEL")
        _id(self.method_id, "method_id")
        if self.executor_class not in ("PCA", "IF", "RULE", "FUSION"):
            raise DG05ClosureError("EXACT_EXECUTOR_CLASS_REQUIRED")
        if not self.component_hashes:
            raise DG05ClosureError("METHOD_COMPONENTS_REQUIRED")
        for value in self.component_hashes:
            _sha(value, "component_hash")
        expected_detector = "PCA_SPE" if self.executor_class == "PCA" or self.method_id.startswith("M3_") or self.method_id.startswith("M4_") or self.method_id.startswith("HISTORICAL_PCA") else None
        if self.executor_class == "IF" or self.method_id == "ISOLATION_FOREST_PLUS_T2":
            expected_detector = "ISOLATION_FOREST"
        if self.detector_id != expected_detector:
            raise DG05ClosureError("METHOD_SPECIFIC_DETECTOR_BINDING_REQUIRED")

    def document(self) -> dict[str, Any]:
        return {**self.__dict__, "component_hashes": list(self.component_hashes)}


@dataclass(frozen=True)
class MethodDispatchRegistryV1:
    entries: tuple[MethodDispatchEntryV1, ...]
    detector_registry_hash: str
    method_bundle_hash: str
    source_commit: str

    def document(self) -> dict[str, Any]:
        return self_hashed({"schema": "method_dispatch_registry_v1", "entries": [e.document() for e in self.entries], "detector_registry_hash": self.detector_registry_hash, "method_bundle_hash": self.method_bundle_hash, "source_commit": self.source_commit})

    def validate(self) -> None:
        _git(self.source_commit, "source_commit")
        _sha(self.detector_registry_hash, "detector_registry_hash")
        if self.method_bundle_hash != FROZEN_METHOD_BUNDLE_HASH_V2:
            raise DG05ClosureError("METHOD_BUNDLE_MISMATCH")
        if tuple(sorted(self.entries)) != self.entries or len({(e.panel_id, e.method_id) for e in self.entries}) != len(self.entries):
            raise DG05ClosureError("CANONICAL_UNIQUE_DISPATCH_REQUIRED")
        expected = {(panel, method) for panel, methods in FROZEN_METHOD_IDS_BY_PANEL_V1.items() for method in methods}
        if {(e.panel_id, e.method_id) for e in self.entries} != expected:
            raise DG05ClosureError("EXACT_23_METHOD_DISPATCH_MATRIX_REQUIRED")
        for e in self.entries:
            e.validate()

    def lookup(self, panel_id: str, method_id: str) -> MethodDispatchEntryV1:
        self.validate()
        matches = [e for e in self.entries if (e.panel_id, e.method_id) == (panel_id, method_id)]
        if len(matches) != 1:
            raise DG05ClosureError("EXACT_METHOD_DISPATCH_REQUIRED")
        return matches[0]


@dataclass(frozen=True)
class DG05ExecutableAuthorityManifestV1:
    scientific_authorities: tuple[tuple[str, str], ...]
    detector_registry_hash: str
    dispatch_registry_hash: str
    rule_portfolio_authority_hashes: tuple[str, ...]
    full_process_scope_hash: str
    p1_custodian_v3_hash: str
    implementation_hashes: tuple[tuple[str, str], ...]
    source_commit: str

    def document(self) -> dict[str, Any]:
        return self_hashed({
            "schema": "dg05_executable_authority_manifest_v1",
            "scientific_authorities": {k: v for k, v in self.scientific_authorities},
            "detector_registry_hash": self.detector_registry_hash,
            "dispatch_registry_hash": self.dispatch_registry_hash,
            "rule_portfolio_authority_hashes": list(self.rule_portfolio_authority_hashes),
            "full_process_scope_hash": self.full_process_scope_hash,
            "p1_custodian_v3_hash": self.p1_custodian_v3_hash,
            "implementation_hashes": {k: v for k, v in self.implementation_hashes},
            "source_commit": self.source_commit,
        })

    def validate(self) -> None:
        if dict(self.scientific_authorities) != FROZEN_SCIENTIFIC_AUTHORITIES_V1:
            raise DG05ClosureError("FROZEN_SCIENTIFIC_AUTHORITY_MISMATCH")
        required_impl = {
            "state_machine", "projection_adapter", "prediction_adapter", "timestamp_builder",
            "scenario_builder", "denominator_builder", "global_manifest_builder", "global_freeze_builder",
            "label_custodian", "result_builder", "result_verifier",
        }
        if {k for k, _ in self.implementation_hashes} != required_impl:
            raise DG05ClosureError("COMPLETE_EXECUTABLE_IMPLEMENTATION_BINDING_REQUIRED")
        for value in (self.detector_registry_hash, self.dispatch_registry_hash, self.full_process_scope_hash, self.p1_custodian_v3_hash, *self.rule_portfolio_authority_hashes, *(v for _, v in self.implementation_hashes)):
            _sha(value, "manifest_authority_hash")
        _git(self.source_commit, "source_commit")


STATE_ORDER_V3 = (
    "APPROVED_EXECUTION_INITIALIZED",
    "ATTACK_CONTAINER_CUSTODIED_LABEL_LOCKED",
    "ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED",
    "PREDICTIONS_IN_PROGRESS_LABEL_LOCKED",
    "GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED",
    "LABEL_SCENARIO_LEASE_OPEN",
    "SCENARIO_AUTHORITY_FROZEN",
    "DENOMINATOR_AUTHORITY_FROZEN",
    "RESULTS_COMPUTED",
    "RESULT_INTEGRITY_AUDITED",
)

STATE_EVIDENCE_POLICY_V1 = {
    "ATTACK_CONTAINER_CUSTODIED_LABEL_LOCKED": ("PHYSICAL_FILE_AUTHORITY", 10),
    "ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED": ("PROJECTION_CENSUS", 10),
    "PREDICTIONS_IN_PROGRESS_LABEL_LOCKED": ("EXECUTION_START", 1),
    "GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED": ("GLOBAL_FREEZE", 72),
    "LABEL_SCENARIO_LEASE_OPEN": ("LEASE_ISSUE", 1),
    "SCENARIO_AUTHORITY_FROZEN": ("SCENARIO_AUTHORITY", 146),
    "DENOMINATOR_AUTHORITY_FROZEN": ("DENOMINATOR_AUTHORITY", 146),
    "RESULTS_COMPUTED": ("RESULT_AUTHORITY_BUNDLE", 23),
    "RESULT_INTEGRITY_AUDITED": ("RESULT_INTEGRITY_QA", 23),
}


@dataclass(frozen=True)
class StateTransitionEvidenceV1:
    kind: str
    authority_hash: str
    item_count: int
    authority_document: Mapping[str, Any]

    def validate_for(self, state: str) -> None:
        _sha(self.authority_hash, "transition_authority_hash")
        if STATE_EVIDENCE_POLICY_V1.get(state) != (self.kind, self.item_count):
            raise DG05ClosureError("STATE_SPECIFIC_TYPED_EVIDENCE_REQUIRED")
        validate_self_hashed(self.authority_document)
        if self.authority_document["self_hash"] != self.authority_hash:
            raise DG05ClosureError("TRANSITION_ARTIFACT_REPLAY_REQUIRED")


def initialize_dg05_execution_v1(manifest: DG05ExecutableAuthorityManifestV1, *, approved_manifest_hash: str, execution_id: str) -> dict[str, Any]:
    if type(manifest) is not DG05ExecutableAuthorityManifestV1:
        raise DG05ClosureError("TYPED_EXECUTABLE_MANIFEST_REQUIRED")
    manifest.validate()
    actual = manifest.document()["self_hash"]
    if approved_manifest_hash != actual:
        raise DG05ClosureError("EXACT_APPROVED_MANIFEST_HASH_REQUIRED")
    _id(execution_id, "execution_id")
    return self_hashed({"schema": "dg05_execution_state_v3", "state": STATE_ORDER_V3[0], "previous_state_hash": None, "executable_approval_manifest_hash": actual, "execution_id": execution_id, "source_commit": manifest.source_commit, "evidence_hashes": []})


def advance_dg05_state_v1(current: Mapping[str, Any], manifest: DG05ExecutableAuthorityManifestV1, *, next_state: str, evidence: StateTransitionEvidenceV1) -> dict[str, Any]:
    validate_self_hashed(current)
    manifest.validate()
    manifest_hash = manifest.document()["self_hash"]
    if current.get("executable_approval_manifest_hash") != manifest_hash:
        raise DG05ClosureError("MANIFEST_REPLACEMENT_PROHIBITED")
    try:
        index = STATE_ORDER_V3.index(str(current["state"]))
    except (ValueError, KeyError) as exc:
        raise DG05ClosureError("INVALID_STATE") from exc
    if index + 1 >= len(STATE_ORDER_V3) or STATE_ORDER_V3[index + 1] != next_state:
        raise DG05ClosureError("NON_ADJACENT_STATE_TRANSITION")
    if type(evidence) is not StateTransitionEvidenceV1:
        raise DG05ClosureError("TYPED_TRANSITION_EVIDENCE_REQUIRED")
    evidence.validate_for(next_state)
    return self_hashed({"schema": "dg05_execution_state_v3", "state": next_state, "previous_state_hash": current["self_hash"], "executable_approval_manifest_hash": manifest_hash, "execution_id": current["execution_id"], "source_commit": manifest.source_commit, "evidence": {"kind": evidence.kind, "authority_hash": evidence.authority_hash, "item_count": evidence.item_count, "authority_schema": evidence.authority_document.get("schema")}})


def persist_state_receipt_v1(directory: Path, state: Mapping[str, Any]) -> str:
    validate_self_hashed(state)
    _id(str(state["execution_id"]), "execution_id")
    sequence = STATE_ORDER_V3.index(str(state["state"]))
    return publish_new(directory / f"{sequence:02d}-{state['state']}.json", canonical_bytes(dict(state)) + b"\n")


@dataclass(frozen=True)
class TimestampCoordinateAuthorityV1:
    panel_id: str
    dataset_version: str
    file_id: str
    physical_file_authority_hash: str
    projection_hash: str
    timestamp_id: str
    row_count: int
    timestamp_vector_hash: str
    canonical_representation: str
    timezone_contract: str
    monotonicity_contract: str
    duplicate_policy: str
    parser_implementation_hash: str
    source_commit: str

    def document(self) -> dict[str, Any]:
        return self_hashed({"schema": "timestamp_coordinate_authority_v1", **self.__dict__})

    def validate(self) -> None:
        if self.panel_id not in FROZEN_PANEL_ORDER_V2 or self.row_count <= 0:
            raise DG05ClosureError("INVALID_TIMESTAMP_AUTHORITY")
        for name in ("physical_file_authority_hash", "projection_hash", "timestamp_vector_hash", "parser_implementation_hash"):
            _sha(getattr(self, name), name)
        _git(self.source_commit, "source_commit")
        if self.canonical_representation != "UTF8_ISO8601_BYTES" or self.monotonicity_contract != "STRICT_FILE_ORDER":
            raise DG05ClosureError("FROZEN_TIMESTAMP_CONTRACT_REQUIRED")


@dataclass(frozen=True)
class FeatureProjectionAuthorityV1:
    panel_id: str
    dataset_version: str
    file_id: str
    raw_physical_file_hash: str
    header_hash: str
    allowlist_authority_hash: str
    timestamp_authority_hash: str
    feature_order_hash: str
    row_count: int
    projection_hash: str
    adapter_implementation_hash: str
    source_commit: str

    def document(self) -> dict[str, Any]:
        return self_hashed({"schema": "feature_only_projection_authority_v1", **self.__dict__, "label_values_parsed": False, "scenario_values_parsed": False})

    def validate(self) -> None:
        if self.panel_id not in FROZEN_PANEL_ORDER_V2 or self.row_count <= 0:
            raise DG05ClosureError("INVALID_FEATURE_PROJECTION_AUTHORITY")
        for name in ("raw_physical_file_hash", "header_hash", "allowlist_authority_hash", "timestamp_authority_hash",
                     "feature_order_hash", "projection_hash", "adapter_implementation_hash"):
            _sha(getattr(self, name), name)
        _git(self.source_commit, "source_commit")


def project_attack_feature_file_v1(*, source: Path, destination: Path, physical_file: PhysicalFileIdentityV2,
                                   panel_authority: FrozenFeatureAllowlistAuthorityV2, file_id: str,
                                   adapter_implementation_hash: str, source_commit: str) -> tuple[FeatureProjectionAuthorityV1, TimestampCoordinateAuthorityV1]:
    """Production positive-allowlist adapter; excluded values stay opaque bytes."""
    panel_authority.validate()
    if type(physical_file) is not PhysicalFileIdentityV2:
        raise DG05ClosureError("TYPED_PHYSICAL_FILE_IDENTITY_REQUIRED")
    physical_file.validate()
    _sha(adapter_implementation_hash, "adapter_implementation_hash")
    _git(source_commit, "source_commit")
    if (physical_file.panel_id, physical_file.file_id) != (panel_authority.panel_id, file_id):
        raise DG05ClosureError("PHYSICAL_FILE_PANEL_IDENTITY_MISMATCH")
    if file_sha256(source) != physical_file.raw_container_hash:
        raise DG05ClosureError("RAW_CONTAINER_HASH_REPLAY_MISMATCH")
    if source.is_symlink() or destination.exists():
        raise DG05ClosureError("SAFE_NEW_PROJECTION_PATH_REQUIRED")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(f".{destination.name}.{secrets.token_hex(8)}.partial")
    try:
        with source.open("rb") as incoming:
            header, delimiter = csv_schema(incoming)
            selected = (panel_authority.timestamp_id, *panel_authority.feature_ids)
            if any(name not in header for name in selected):
                raise DG05ClosureError("ALLOWLISTED_FIELD_ABSENT")
            indices = tuple(header.index(name) for name in selected)
            if len(set(indices)) != len(indices):
                raise DG05ClosureError("ALLOWLIST_INDEX_COLLISION")
            header_hash = digest(header)
            projection_hasher = sha256()
            timestamp_hasher = sha256()
            count = 0
            previous: datetime | None = None
            with partial.open("xb") as outgoing:
                first = canonical_bytes(list(selected)) + b"\n"
                outgoing.write(first)
                projection_hasher.update(first)
                for fields in selected_rows(incoming, delimiter, len(header), indices):
                    timestamp = fields[0].decode("utf-8")
                    current = datetime.fromisoformat(timestamp)
                    if previous is not None and current < previous:
                        raise DG05ClosureError("TIMESTAMP_ORDER_VIOLATION")
                    previous = current
                    numbers = [float(item.decode("ascii")) for item in fields[1:]]
                    if not all(math.isfinite(v) for v in numbers):
                        raise DG05ClosureError("NONFINITE_APPROVED_FEATURE")
                    record = canonical_bytes([timestamp, *numbers]) + b"\n"
                    outgoing.write(record)
                    projection_hasher.update(record)
                    timestamp_hasher.update(timestamp.encode("utf-8") + b"\n")
                    count += 1
                if count <= 0:
                    raise DG05ClosureError("EMPTY_FEATURE_PROJECTION")
                outgoing.flush()
                os.fsync(outgoing.fileno())
        os.link(partial, destination)
    finally:
        if partial.exists():
            partial.unlink()
    projection_hash = file_sha256(destination)
    if projection_hash != projection_hasher.hexdigest():
        raise DG05ClosureError("PROJECTION_REPLAY_MISMATCH")
    feature_order_hash = digest(list(panel_authority.feature_ids))
    timestamp = TimestampCoordinateAuthorityV1(panel_authority.panel_id, panel_authority.dataset_version, file_id,
        digest(physical_file.document()), projection_hash, panel_authority.timestamp_id, count, timestamp_hasher.hexdigest(),
        "UTF8_ISO8601_BYTES", "NAIVE_AS_RECORDED_NO_CONVERSION", "STRICT_FILE_ORDER", "PRESERVE_DUPLICATES_IN_ROW_ORDER",
        adapter_implementation_hash, source_commit)
    timestamp.validate()
    projection = FeatureProjectionAuthorityV1(panel_authority.panel_id, panel_authority.dataset_version, file_id,
        digest(physical_file.document()), header_hash, panel_authority.document()["self_hash"], timestamp.document()["self_hash"],
        feature_order_hash, count, projection_hash, adapter_implementation_hash, source_commit)
    projection.validate()
    return projection, timestamp


@dataclass(frozen=True, order=True)
class ExpectedPredictionCellV1:
    panel_id: str
    file_id: str
    method_id: str
    dispatch_authority_hash: str

    @property
    def cell_id(self) -> str:
        return digest(self.document())

    def document(self) -> dict[str, str]:
        return dict(self.__dict__)


def build_expected_prediction_cell_census_v1(*, physical: FrozenPhysicalFileAuthorityV2,
                                             dispatch: MethodDispatchRegistryV1) -> dict[str, Any]:
    physical.validate()
    dispatch.validate()
    registry_hash = dispatch.document()["self_hash"]
    entries = []
    order = {p: i for i, p in enumerate(FROZEN_PANEL_ORDER_V2)}
    method_order = {(e.panel_id, e.method_id): i for i, e in enumerate(dispatch.entries)}
    for item in physical.files:
        for entry in dispatch.entries:
            if entry.panel_id == item.panel_id:
                entries.append(ExpectedPredictionCellV1(item.panel_id, item.file_id, entry.method_id, registry_hash))
    entries.sort(key=lambda c: (order[c.panel_id], tuple(f.file_id for f in physical.files if f.panel_id == c.panel_id).index(c.file_id), method_order[(c.panel_id, c.method_id)]))
    if len({c.cell_id for c in entries}) != len(entries):
        raise DG05ClosureError("DUPLICATE_EXPECTED_CELL")
    return self_hashed({"schema": "expected_prediction_cell_census_builder_v1", "physical_file_authority_hash": physical.document()["self_hash"], "dispatch_registry_hash": registry_hash, "cells": [{**c.document(), "cell_id": c.cell_id} for c in entries], "count": len(entries)})


@dataclass(frozen=True)
class PredictionTerminalReceiptV1:
    cell_id: str
    panel_id: str
    file_id: str
    method_id: str
    method_authority_hash: str
    physical_file_authority_hash: str
    projection_hash: str
    timestamp_authority_hash: str
    row_count: int
    prediction_artifact_hash: str | None
    trace_artifact_hash: str | None
    trace_status: str
    status: str
    failure_code: str | None
    prediction_schema_hash: str
    executable_manifest_hash: str
    source_commit: str

    def document(self) -> dict[str, Any]:
        return self_hashed({"schema": "prediction_terminal_receipt_v1", **self.__dict__})

    def validate(self) -> None:
        if self.status not in ("SUCCESS", "METHOD_FAILURE"):
            raise DG05ClosureError("TERMINAL_STATUS_REQUIRED")
        if self.status == "SUCCESS" and (self.prediction_artifact_hash is None or self.row_count <= 0 or self.failure_code is not None):
            raise DG05ClosureError("INVALID_SUCCESS_RECEIPT")
        if self.status == "METHOD_FAILURE" and (self.prediction_artifact_hash is not None or self.failure_code is None):
            raise DG05ClosureError("FAILURE_MUST_NOT_INVENT_PREDICTION")
        if self.trace_status not in ("BOUND", "NOT_APPLICABLE"):
            raise DG05ClosureError("TRACE_STATUS_REQUIRED")
        if self.trace_status == "BOUND" and self.trace_artifact_hash is None:
            raise DG05ClosureError("RULE_TRACE_REQUIRED")
        for name in ("cell_id", "method_authority_hash", "physical_file_authority_hash", "projection_hash", "timestamp_authority_hash", "prediction_schema_hash", "executable_manifest_hash"):
            _sha(getattr(self, name), name)
        for name in ("prediction_artifact_hash", "trace_artifact_hash"):
            if getattr(self, name) is not None:
                _sha(getattr(self, name), name)
        _git(self.source_commit, "source_commit")


def execute_prediction_cell_v1(*, cell: Mapping[str, Any], dispatch: MethodDispatchRegistryV1,
                               projection: FeatureProjectionAuthorityV1, timestamp: TimestampCoordinateAuthorityV1,
                               executable_manifest_hash: str, executors: Mapping[str, Callable[[Path, MethodDispatchEntryV1], tuple[Sequence[bool], Mapping[str, Any] | None]]],
                               projection_path: Path, output_directory: Path, source_commit: str) -> PredictionTerminalReceiptV1:
    """Exact dispatch adapter.  There is no fallback or method autodetection."""
    _sha(executable_manifest_hash, "executable_manifest_hash")
    entry = dispatch.lookup(str(cell["panel_id"]), str(cell["method_id"]))
    projection.validate()
    expected_cell_id = digest({k: cell[k] for k in ("panel_id", "file_id", "method_id", "dispatch_authority_hash")})
    if cell.get("cell_id") != expected_cell_id or projection.panel_id != cell["panel_id"] or projection.file_id != cell["file_id"]:
        raise DG05ClosureError("CELL_PROJECTION_BINDING_MISMATCH")
    if timestamp.document()["self_hash"] != projection.timestamp_authority_hash or timestamp.projection_hash != projection.projection_hash:
        raise DG05ClosureError("TIMESTAMP_PROJECTION_BINDING_MISMATCH")
    if file_sha256(projection_path) != projection.projection_hash:
        raise DG05ClosureError("PROJECTION_ARTIFACT_BYTE_REPLAY_MISMATCH")
    method_authority_hash = digest(entry.document())
    if method_authority_hash not in executors:
        failure = PredictionTerminalReceiptV1(expected_cell_id, entry.panel_id, projection.file_id, entry.method_id,
            method_authority_hash, projection.raw_physical_file_hash, projection.projection_hash, timestamp.document()["self_hash"],
            projection.row_count, None, None, "NOT_APPLICABLE", "METHOD_FAILURE", "EXECUTOR_NOT_REGISTERED",
            digest({"schema": "dense_boolean_prediction_v1"}), executable_manifest_hash, source_commit)
        failure.validate()
        return failure
    alarms, trace = executors[method_authority_hash](projection_path, entry)
    if len(alarms) != projection.row_count or any(type(v) is not bool for v in alarms):
        raise DG05ClosureError("EXECUTOR_OUTPUT_SCHEMA_MISMATCH")
    prediction_body = {"schema": "dense_boolean_prediction_v1", "cell_id": expected_cell_id, "row_count": len(alarms), "alarms": list(alarms)}
    prediction_bytes = canonical_bytes(prediction_body) + b"\n"
    prediction_path = output_directory / f"{expected_cell_id}.prediction.json"
    prediction_hash = publish_new(prediction_path, prediction_bytes)
    rule_capable = entry.executor_class in ("RULE", "FUSION")
    trace_hash = None
    trace_status = "NOT_APPLICABLE"
    if rule_capable:
        if trace is None:
            raise DG05ClosureError("RULE_CAPABLE_EXECUTOR_TRACE_REQUIRED")
        trace_body = {"schema": "rule_trace_artifact_v1", "cell_id": expected_cell_id, "prediction_hash": prediction_hash,
                      "projection_hash": projection.projection_hash, "timestamp_authority_hash": timestamp.document()["self_hash"], **dict(trace)}
        trace_hash = publish_new(output_directory / f"{expected_cell_id}.trace.json", canonical_bytes(self_hashed(trace_body)) + b"\n")
        trace_status = "BOUND"
    receipt = PredictionTerminalReceiptV1(expected_cell_id, entry.panel_id, projection.file_id, entry.method_id,
        method_authority_hash, projection.raw_physical_file_hash, projection.projection_hash, timestamp.document()["self_hash"],
        projection.row_count, prediction_hash, trace_hash, trace_status, "SUCCESS", None,
        digest({"schema": "dense_boolean_prediction_v1"}), executable_manifest_hash, source_commit)
    receipt.validate()
    return receipt


def persist_prediction_receipt_v1(path: Path, receipt: PredictionTerminalReceiptV1) -> str:
    receipt.validate()
    return publish_new(path, canonical_bytes(receipt.document()) + b"\n")


def build_global_prediction_manifest_v1(*, census: Mapping[str, Any], receipts: Sequence[PredictionTerminalReceiptV1],
                                        executable_manifest_hash: str,
                                        dispatch: MethodDispatchRegistryV1 | None = None) -> dict[str, Any]:
    validate_self_hashed(census)
    expected = tuple(cell["cell_id"] for cell in census["cells"])
    actual = tuple(r.cell_id for r in receipts)
    if actual != expected or len(actual) != len(set(actual)):
        raise DG05ClosureError("GLOBAL_PREDICTION_CELL_CENSUS_INCOMPLETE")
    cell_by_id = {cell["cell_id"]: cell for cell in census["cells"]}
    for r in receipts:
        r.validate()
        if r.executable_manifest_hash != executable_manifest_hash:
            raise DG05ClosureError("RECEIPT_MANIFEST_MISMATCH")
        cell = cell_by_id[r.cell_id]
        if (r.panel_id, r.file_id, r.method_id) != (cell["panel_id"], cell["file_id"], cell["method_id"]):
            raise DG05ClosureError("RECEIPT_CELL_IDENTITY_MISMATCH")
        if dispatch is not None:
            entry = dispatch.lookup(r.panel_id, r.method_id)
            if r.method_authority_hash != digest(entry.document()):
                raise DG05ClosureError("RECEIPT_METHOD_AUTHORITY_MISMATCH")
    return self_hashed({"schema": "global_prediction_manifest_v3", "expected_cell_census_hash": census["self_hash"], "executable_approval_manifest_hash": executable_manifest_hash, "receipts": [r.document() for r in receipts], "success_count": sum(r.status == "SUCCESS" for r in receipts), "failure_count": sum(r.status == "METHOD_FAILURE" for r in receipts)})


def freeze_global_predictions_v1(*, manifest: Mapping[str, Any], census: Mapping[str, Any],
                                 receipt_artifacts: Mapping[str, tuple[Path | None, Path | None] | tuple[Path | None, Path | None, Path]],
                                 predecessor_state: Mapping[str, Any]) -> dict[str, Any]:
    validate_self_hashed(manifest)
    validate_self_hashed(census)
    validate_self_hashed(predecessor_state)
    if manifest["expected_cell_census_hash"] != census["self_hash"]:
        raise DG05ClosureError("FREEZE_CENSUS_MISMATCH")
    for receipt in manifest["receipts"]:
        validate_self_hashed(receipt)
        paths = receipt_artifacts[receipt["cell_id"]]
        prediction_path, trace_path = paths[0], paths[1]
        if len(paths) == 3:
            receipt_path = paths[2]
            if file_sha256(receipt_path) != sha256(canonical_bytes(receipt) + b"\n").hexdigest():
                raise DG05ClosureError("TERMINAL_RECEIPT_BYTE_REPLAY_MISMATCH")
        if receipt["status"] == "SUCCESS":
            if prediction_path is None or file_sha256(prediction_path) != receipt["prediction_artifact_hash"]:
                raise DG05ClosureError("PREDICTION_BYTE_REPLAY_MISMATCH")
            if receipt["trace_status"] == "BOUND" and (trace_path is None or file_sha256(trace_path) != receipt["trace_artifact_hash"]):
                raise DG05ClosureError("TRACE_BYTE_REPLAY_MISMATCH")
        elif len(paths) != 3:
            raise DG05ClosureError("FAILURE_RECEIPT_ARTIFACT_REQUIRED")
    return self_hashed({"schema": "global_prediction_freeze_v3", "manifest_hash": manifest["self_hash"], "census_hash": census["self_hash"], "predecessor_state_hash": predecessor_state["self_hash"], "executable_approval_manifest_hash": manifest["executable_approval_manifest_hash"], "status": "GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED"})


@dataclass(frozen=True, order=True)
class ScenarioRecordV1:
    panel_id: str
    dataset_version: str
    file_id: str
    scenario_id: str
    closed_intervals: tuple[tuple[str, str], ...]
    attacked_identities: tuple[str, ...]
    explicit_affected_processes: tuple[str, ...]
    physical_file_authority_hash: str
    timestamp_authority_hash: str
    official_source_hash: str

    def document(self) -> dict[str, Any]:
        return self_hashed({"schema": "official_scenario_record_v1", **self.__dict__, "closed_intervals": [list(v) for v in self.closed_intervals], "attacked_identities": list(self.attacked_identities), "explicit_affected_processes": list(self.explicit_affected_processes)})

    def validate(self) -> None:
        if self.panel_id not in FROZEN_PANEL_ORDER_V2 or not self.closed_intervals or not self.attacked_identities:
            raise DG05ClosureError("OFFICIAL_SCENARIO_FIELDS_REQUIRED")
        for start, end in self.closed_intervals:
            if datetime.fromisoformat(start) > datetime.fromisoformat(end):
                raise DG05ClosureError("INVALID_CLOSED_INTERVAL")
        for name in ("physical_file_authority_hash", "timestamp_authority_hash", "official_source_hash"):
            _sha(getattr(self, name), name)


def build_scenario_authority_v1(*, records: Sequence[ScenarioRecordV1], lease_completion_hash: str,
                                global_freeze_hash: str, source_commit: str, nominal_counts: Mapping[str, int],
                                authority_mode: str = "PRODUCTION",
                                timestamp_authorities: Mapping[tuple[str, str], TimestampCoordinateAuthorityV1] | None = None) -> dict[str, Any]:
    for value in (lease_completion_hash, global_freeze_hash):
        _sha(value, "scenario_parent_hash")
    _git(source_commit, "source_commit")
    ordered = tuple(sorted(records))
    if tuple(records) != ordered or len({(r.panel_id, r.scenario_id) for r in records}) != len(records):
        raise DG05ClosureError("CANONICAL_UNIQUE_SCENARIOS_REQUIRED")
    for r in records:
        r.validate()
        if timestamp_authorities is not None:
            timestamp = timestamp_authorities.get((r.panel_id, r.file_id))
            if timestamp is None:
                raise DG05ClosureError("SCENARIO_TIMESTAMP_AUTHORITY_ABSENT")
            timestamp.validate()
            if timestamp.document()["self_hash"] != r.timestamp_authority_hash or timestamp.physical_file_authority_hash != r.physical_file_authority_hash:
                raise DG05ClosureError("SCENARIO_PHYSICAL_TIMESTAMP_BINDING_MISMATCH")
    actual = {p: sum(r.panel_id == p for r in records) for p in FROZEN_PANEL_ORDER_V2}
    if actual != dict(nominal_counts):
        raise DG05ClosureError("OFFICIAL_SCENARIO_CENSUS_MISMATCH")
    official = dict(zip(FROZEN_PANEL_ORDER_V2, (38, 58, 50)))
    if authority_mode == "PRODUCTION" and actual != official:
        raise DG05ClosureError("FROZEN_NOMINAL_SCENARIO_COUNTS_REQUIRED")
    if authority_mode not in ("PRODUCTION", "SYNTHETIC_REHEARSAL"):
        raise DG05ClosureError("SCENARIO_AUTHORITY_MODE_REQUIRED")
    return self_hashed({"schema": "frozen_scenario_authority_v1", "records": [r.document() for r in records], "nominal_counts": dict(nominal_counts), "lease_completion_hash": lease_completion_hash, "global_freeze_hash": global_freeze_hash, "source_commit": source_commit, "method_inputs": False, "authority_mode": authority_mode})


def build_denominator_authority_v1(*, scenario_authority: Mapping[str, Any], full_scope: FullProcessScopeAuthorityV1,
                                   p1_custodian_v3_hash: str) -> dict[str, Any]:
    validate_self_hashed(scenario_authority)
    full_scope.validate()
    _sha(p1_custodian_v3_hash, "p1_custodian_v3_hash")
    output = []
    for record in scenario_authority["records"]:
        validate_self_hashed(record)
        observed = [full_scope.classify(record["dataset_version"], identity) for identity in record["attacked_identities"]]
        if "P1" in observed:
            primary, reason = "P1_ELIGIBLE", "DIRECT_VERIFIED_P1_IDENTITY"
        elif "UNRESOLVED" in observed:
            primary, reason = "UNRESOLVED", "AT_LEAST_ONE_IDENTITY_UNRESOLVED"
        else:
            primary, reason = "OUT_OF_SCOPE", "ALL_IDENTITIES_VERIFIED_NON_P1"
        cross = "P1" in record["explicit_affected_processes"] and primary != "P1_ELIGIBLE"
        output.append(self_hashed({"schema": "p1_eligibility_record_v3", "scenario_record_hash": record["self_hash"], "panel_id": record["panel_id"], "scenario_id": record["scenario_id"], "primary_status": primary, "secondary_cross_process_p1_relevant": cross, "reason": reason, "unresolved_identity_count": observed.count("UNRESOLVED"), "full_scope_hash": full_scope.document()["self_hash"], "p1_custodian_v3_hash": p1_custodian_v3_hash}))
    by_panel = []
    for panel in FROZEN_PANEL_ORDER_V2:
        rows = [r for r in output if r["panel_id"] == panel]
        by_panel.append({"panel_id": panel, "nominal_count": len(rows), "p1_eligible_ids": [r["scenario_id"] for r in rows if r["primary_status"] == "P1_ELIGIBLE"], "out_of_scope_ids": [r["scenario_id"] for r in rows if r["primary_status"] == "OUT_OF_SCOPE"], "unresolved_ids": [r["scenario_id"] for r in rows if r["primary_status"] == "UNRESOLVED"], "cross_process_secondary_ids": [r["scenario_id"] for r in rows if r["secondary_cross_process_p1_relevant"]]})
    return self_hashed({"schema": "denominator_authority_v1", "scenario_authority_hash": scenario_authority["self_hash"], "full_process_scope_hash": full_scope.document()["self_hash"], "p1_custodian_v3_hash": p1_custodian_v3_hash, "records": output, "panels": by_panel, "prediction_inputs": False})


@dataclass(frozen=True)
class CustodianRequestV1:
    opaque_lease: str
    lease_receipt: Mapping[str, Any]
    global_freeze_hash: str
    executable_manifest_hash: str
    approved_input: str
    approved_output: str
    public_authority_hashes: tuple[str, ...]

    def document(self) -> dict[str, Any]:
        return {"schema": "isolated_label_scenario_custodian_request_v1", **self.__dict__, "lease_receipt": dict(self.lease_receipt), "public_authority_hashes": list(self.public_authority_hashes)}

    def validate(self, *, input_root: Path, output_root: Path, forbidden_roots: Sequence[Path]) -> None:
        value = self.document()
        forbidden_tokens = ("prediction", "alarm", "method", "result", "score", "portfolio", "model")
        if any(any(token in str(key).lower() for token in forbidden_tokens) for key in value):
            raise DG05ClosureError("CUSTODIAN_SERIALIZED_PREDICTION_CAPABILITY")
        validate_self_hashed(self.lease_receipt)
        if sha256(self.opaque_lease.encode("utf-8")).hexdigest() != self.lease_receipt.get("token_hash"):
            raise DG05ClosureError("LEASE_TOKEN_BINDING_MISMATCH")
        for value in (self.global_freeze_hash, self.executable_manifest_hash, *self.public_authority_hashes):
            _sha(value, "custodian_hash")
        incoming = Path(self.approved_input).resolve()
        outgoing = Path(self.approved_output).resolve()
        if input_root.resolve() not in incoming.parents or output_root.resolve() not in outgoing.parents:
            raise DG05ClosureError("CUSTODIAN_RESOURCE_ALLOWLIST_VIOLATION")
        if any(root.resolve() == incoming or root.resolve() in incoming.parents or root.resolve() == outgoing or root.resolve() in outgoing.parents for root in forbidden_roots):
            raise DG05ClosureError("CUSTODIAN_PREDICTION_NAMESPACE_DENIED")


def issue_label_lease_v3(*, freeze: Mapping[str, Any], state: Mapping[str, Any], executable_manifest_hash: str) -> dict[str, Any]:
    validate_self_hashed(freeze)
    validate_self_hashed(state)
    if state["state"] != "GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED" or state["executable_approval_manifest_hash"] != executable_manifest_hash or freeze["executable_approval_manifest_hash"] != executable_manifest_hash:
        raise DG05ClosureError("GLOBAL_FREEZE_REPLAY_REQUIRED_FOR_LEASE")
    opaque_token = secrets.token_hex(32)
    receipt = self_hashed({"schema": "single_use_label_scenario_lease_v3", "token_hash": sha256(opaque_token.encode("utf-8")).hexdigest(), "global_freeze_hash": freeze["self_hash"], "state_hash": state["self_hash"], "executable_manifest_hash": executable_manifest_hash, "issue_count": 1, "consume_limit": 1})
    return {"opaque_token": opaque_token, "receipt": receipt}


def compute_bound_panel_method_result_v1(*, panel_id: str, method_id: str, method_authority_hash: str,
                                         prediction_manifest_hash: str, predictions: Mapping[str, tuple[TimestampCoordinateAuthorityV1, Sequence[str], Sequence[bool], str, str]],
                                         scenario_authority: Mapping[str, Any], denominator_authority: Mapping[str, Any],
                                         metric_authority_hash: str, p1_custodian_hash: str, etapr_authority_hash: str,
                                         normal_burden_hash: str, source_commit: str,
                                         executable_manifest_hash: str | None = None,
                                         statistical_authority_hash: str | None = None,
                                         failed_file_receipt_hashes: Mapping[str, str] | None = None,
                                         etapr_coordinate_binding_hash: str | None = None) -> dict[str, Any]:
    """Compute coordinate-bound scenario recall; no anonymous cross-file rows."""
    validate_self_hashed(scenario_authority)
    validate_self_hashed(denominator_authority)
    for value in (method_authority_hash, prediction_manifest_hash, metric_authority_hash, p1_custodian_hash, etapr_authority_hash, normal_burden_hash,
                  *(v for v in (executable_manifest_hash, statistical_authority_hash, etapr_coordinate_binding_hash) if v is not None)):
        _sha(value, "result_authority_hash")
    failed = dict(failed_file_receipt_hashes or {})
    for value in failed.values():
        _sha(value, "failure_receipt_hash")
    eligible = {r["scenario_id"] for r in denominator_authority["records"] if r["panel_id"] == panel_id and r["primary_status"] == "P1_ELIGIBLE"}
    hits = []
    for scenario in scenario_authority["records"]:
        if scenario["panel_id"] != panel_id or scenario["scenario_id"] not in eligible:
            continue
        file_id = scenario["file_id"]
        if file_id not in predictions:
            raise DG05ClosureError("PRIMARY_PREDICTION_COVERAGE_INCOMPLETE")
        timestamp, timestamp_values, alarms, prediction_hash, projection_hash = predictions[file_id]
        timestamp.validate()
        replayed_timestamp_hash = sha256(b"".join(str(v).encode("utf-8") + b"\n" for v in timestamp_values)).hexdigest()
        if timestamp.panel_id != panel_id or timestamp.file_id != file_id or timestamp.projection_hash != projection_hash or len(alarms) != timestamp.row_count or len(timestamp_values) != timestamp.row_count or replayed_timestamp_hash != timestamp.timestamp_vector_hash or timestamp.document()["self_hash"] != scenario["timestamp_authority_hash"]:
            raise DG05ClosureError("SCENARIO_PREDICTION_COORDINATE_MISMATCH")
        _sha(prediction_hash, "prediction_hash")
        # Synthetic/production adapters preserve row order and use ISO timestamps.
        # The evaluator consumes an authority-bound timestamp vector sidecar via
        # the tuple's TimestampCoordinateAuthority; intervals are canonical.
        alarm_times = {datetime.fromisoformat(timestamp_values[i]) for i, value in enumerate(alarms) if value}
        interval_hits = []
        for start, end in scenario["closed_intervals"]:
            start_dt, end_dt = datetime.fromisoformat(start), datetime.fromisoformat(end)
            interval_hits.append(any(start_dt <= value <= end_dt for value in alarm_times))
        hit = any(interval_hits)
        hits.append({"scenario_id": scenario["scenario_id"], "scenario_record_hash": scenario["self_hash"], "hit": hit, "physical_file_id": file_id, "prediction_hash": prediction_hash, "projection_hash": projection_hash, "timestamp_authority_hash": timestamp.document()["self_hash"]})
    n, k = len(hits), sum(item["hit"] for item in hits)
    interval = wilson95_v1(k, n) if n else None
    completeness = "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE" if failed else ("NOT_EVALUABLE_ZERO_ELIGIBLE_DENOMINATOR" if n == 0 else "COMPLETE")
    if failed:
        k_value = recall = interval_value = None
    else:
        k_value, recall, interval_value = k, (None if n == 0 else k / n), (None if interval is None else list(interval))
    body = {"schema": "panel_method_result_authority_v1", "panel_id": panel_id, "method_id": method_id,
            "executable_approval_manifest_hash": executable_manifest_hash,
            "method_authority_hash": method_authority_hash, "prediction_manifest_hash": prediction_manifest_hash,
            "scenario_authority_hash": scenario_authority["self_hash"], "denominator_authority_hash": denominator_authority["self_hash"],
            "metric_authority_hash": metric_authority_hash, "p1_custodian_hash": p1_custodian_hash,
            "etapr_authority_hash": etapr_authority_hash, "normal_burden_hash": normal_burden_hash,
            "statistical_authority_hash": statistical_authority_hash,
            "etapr_coordinate_binding_hash": etapr_coordinate_binding_hash,
            "completeness_status": completeness, "failure_receipt_hashes": failed,
            "eligible_count": n, "hit_count": k_value, "scenario_recall": recall,
            "wilson95": interval_value, "scenario_hits": [] if failed else hits,
            "physical_file_authority_hashes": sorted({v[0].physical_file_authority_hash for v in predictions.values()}),
            "feature_projection_hashes": sorted({v[4] for v in predictions.values()}),
            "timestamp_authority_hashes": sorted({v[0].document()["self_hash"] for v in predictions.values()}),
            "prediction_artifact_hashes": sorted({v[3] for v in predictions.values()}),
            "no_pooling": True, "source_commit": source_commit}
    _git(source_commit, "source_commit")
    return self_hashed(body)


def persist_result_authority_v1(path: Path, result: Mapping[str, Any]) -> dict[str, Any]:
    validate_self_hashed(result)
    payload = canonical_bytes(dict(result)) + b"\n"
    byte_hash = publish_new(path, payload)
    replay = json.loads(path.read_text(encoding="ascii"))
    validate_self_hashed(replay)
    if replay != dict(result):
        raise DG05ClosureError("RESULT_CANONICAL_BYTE_REPLAY_MISMATCH")
    return self_hashed({"schema": "result_authority_artifact_receipt_v1", "result_self_hash": result["self_hash"], "artifact_byte_hash": byte_hash, "byte_count": len(payload)})


def verify_result_authority_v1(*, path: Path, receipt: Mapping[str, Any], expected_bindings: Mapping[str, str]) -> dict[str, Any]:
    """Read-only result verifier; it never regenerates predictions."""
    validate_self_hashed(receipt)
    if file_sha256(path) != receipt["artifact_byte_hash"]:
        raise DG05ClosureError("RESULT_ARTIFACT_BYTES_CHANGED")
    result = json.loads(path.read_text(encoding="ascii"))
    validate_self_hashed(result)
    if result["self_hash"] != receipt["result_self_hash"]:
        raise DG05ClosureError("RESULT_SELF_HASH_RECEIPT_MISMATCH")
    for field, value in expected_bindings.items():
        if result.get(field) != value:
            raise DG05ClosureError(f"RESULT_NESTED_AUTHORITY_MISMATCH:{field}")
    if result["completeness_status"] == "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE":
        if any(result[name] is not None for name in ("hit_count", "scenario_recall", "wilson95")) or result["scenario_hits"]:
            raise DG05ClosureError("INCOMPLETE_PRIMARY_RESULT_MUST_NOT_REPORT_PARTIAL_RECALL")
        return self_hashed({"schema": "independent_result_integrity_verifier_v1", "result_artifact_byte_hash": receipt["artifact_byte_hash"], "result_self_hash": result["self_hash"], "nested_authorities_replayed": True, "metric_arithmetic_replayed": True, "predictions_regenerated": False, "status": "PASS"})
    n, k = result["eligible_count"], result["hit_count"]
    if k != sum(item["hit"] for item in result["scenario_hits"]) or n != len(result["scenario_hits"]):
        raise DG05ClosureError("RESULT_ARITHMETIC_MISMATCH")
    expected_recall = None if n == 0 else k / n
    if result["scenario_recall"] != expected_recall:
        raise DG05ClosureError("RESULT_RECALL_MISMATCH")
    expected_ci = None if n == 0 else list(wilson95_v1(k, n))
    if result["wilson95"] != expected_ci:
        raise DG05ClosureError("RESULT_WILSON_MISMATCH")
    return self_hashed({"schema": "independent_result_integrity_verifier_v1", "result_artifact_byte_hash": receipt["artifact_byte_hash"], "result_self_hash": result["self_hash"], "nested_authorities_replayed": True, "metric_arithmetic_replayed": True, "predictions_regenerated": False, "status": "PASS"})


def load_frozen_prediction_inputs_v1(*, panel_id: str, method_id: str, global_manifest: Mapping[str, Any],
                                     receipt_paths: Mapping[str, Path], prediction_paths: Mapping[str, Path],
                                     timestamp_authorities: Mapping[str, TimestampCoordinateAuthorityV1],
                                     projection_authorities: Mapping[str, FeatureProjectionAuthorityV1],
                                     projection_paths: Mapping[str, Path]) -> tuple[dict[str, tuple[TimestampCoordinateAuthorityV1, Sequence[str], Sequence[bool], str, str]], dict[str, str], str]:
    """Reopen frozen receipts and predictions; never accept caller-made alarm arrays."""
    validate_self_hashed(global_manifest)
    selected = [r for r in global_manifest["receipts"] if r["panel_id"] == panel_id and r["method_id"] == method_id]
    if not selected:
        raise DG05ClosureError("PANEL_METHOD_TERMINAL_RECEIPTS_REQUIRED")
    loaded: dict[str, tuple[TimestampCoordinateAuthorityV1, Sequence[str], Sequence[bool], str, str]] = {}
    failures: dict[str, str] = {}
    authority_hashes = set()
    for embedded in selected:
        validate_self_hashed(embedded)
        path = receipt_paths[embedded["cell_id"]]
        persisted = json.loads(path.read_text(encoding="ascii"))
        validate_self_hashed(persisted)
        if persisted != embedded or file_sha256(path) != sha256(canonical_bytes(embedded) + b"\n").hexdigest():
            raise DG05ClosureError("TERMINAL_RECEIPT_REPLAY_MISMATCH")
        authority_hashes.add(embedded["method_authority_hash"])
        if embedded["status"] == "METHOD_FAILURE":
            failures[embedded["file_id"]] = embedded["self_hash"]
            continue
        prediction_path = prediction_paths[embedded["cell_id"]]
        if file_sha256(prediction_path) != embedded["prediction_artifact_hash"]:
            raise DG05ClosureError("FROZEN_PREDICTION_BYTE_REPLAY_MISMATCH")
        prediction = json.loads(prediction_path.read_text(encoding="ascii"))
        timestamp = timestamp_authorities[embedded["file_id"]]
        projection = projection_authorities[embedded["file_id"]]
        timestamp.validate(); projection.validate()
        projection_path = projection_paths[embedded["file_id"]]
        if file_sha256(projection_path) != projection.projection_hash:
            raise DG05ClosureError("RESULT_PROJECTION_BYTE_REPLAY_MISMATCH")
        if (prediction.get("cell_id"), prediction.get("row_count")) != (embedded["cell_id"], embedded["row_count"]):
            raise DG05ClosureError("PREDICTION_RECEIPT_SCHEMA_MISMATCH")
        lines = projection_path.read_bytes().splitlines()
        if not lines:
            raise DG05ClosureError("EMPTY_REPLAYED_PROJECTION")
        timestamps = tuple(str(json.loads(line.decode("ascii"))[0]) for line in lines[1:])
        replayed = sha256(b"".join(v.encode("utf-8") + b"\n" for v in timestamps)).hexdigest()
        if len(timestamps) != timestamp.row_count or replayed != timestamp.timestamp_vector_hash:
            raise DG05ClosureError("RESULT_TIMESTAMP_VECTOR_REPLAY_MISMATCH")
        loaded[embedded["file_id"]] = (timestamp, timestamps, tuple(prediction["alarms"]), embedded["prediction_artifact_hash"], projection.projection_hash)
    if len(authority_hashes) != 1:
        raise DG05ClosureError("ONE_METHOD_AUTHORITY_PER_PANEL_RESULT_REQUIRED")
    return loaded, failures, next(iter(authority_hashes))
def build_etapr_coordinate_binding_v1(*, panel_id: str, file_bindings: Sequence[Mapping[str, Any]],
                                      etapr_authority_hash: str) -> dict[str, Any]:
    _sha(etapr_authority_hash, "etapr_authority_hash")
    ordered = sorted((dict(v) for v in file_bindings), key=lambda v: v["file_id"])
    required = {"file_id", "physical_file_authority_hash", "timestamp_authority_hash", "prediction_artifact_hash", "scenario_authority_hash"}
    if not ordered or any(set(v) != required for v in ordered) or len({v["file_id"] for v in ordered}) != len(ordered):
        raise DG05ClosureError("ETAPR_FILE_COORDINATE_BINDINGS_REQUIRED")
    for row in ordered:
        for field in required - {"file_id"}:
            _sha(row[field], field)
    return self_hashed({"schema": "etapr_coordinate_binding_v1", "panel_id": panel_id, "file_bindings": ordered,
                        "physical_file_set_hash": digest(sorted(v["physical_file_authority_hash"] for v in ordered)),
                        "etapr_authority_hash": etapr_authority_hash, "cross_file_anonymous_ranges": False})


def build_result_authority_bundle_v1(*, results: Sequence[Mapping[str, Any]], receipts: Sequence[Mapping[str, Any]],
                                     artifact_paths: Sequence[Path], executable_manifest_hash: str,
                                     global_prediction_manifest_hash: str, scenario_authority_hash: str,
                                     denominator_authority_hash: str, independent_qa_hash: str) -> dict[str, Any]:
    for value in (executable_manifest_hash, global_prediction_manifest_hash, scenario_authority_hash, denominator_authority_hash, independent_qa_hash):
        _sha(value, "result_bundle_authority_hash")
    if not (len(results) == len(receipts) == len(artifact_paths) == 23):
        raise DG05ClosureError("EXACT_23_RESULT_AUTHORITIES_REQUIRED")
    identities = []
    artifacts = []
    for result, receipt, path in zip(results, receipts, artifact_paths):
        validate_self_hashed(result); validate_self_hashed(receipt)
        if file_sha256(path) != receipt["artifact_byte_hash"] or result["self_hash"] != receipt["result_self_hash"]:
            raise DG05ClosureError("RESULT_BUNDLE_BYTE_REPLAY_MISMATCH")
        identities.append((result["panel_id"], result["method_id"]))
        artifacts.append({"panel_id": result["panel_id"], "method_id": result["method_id"], "result_self_hash": result["self_hash"], "artifact_byte_hash": receipt["artifact_byte_hash"]})
    expected = {(panel, method) for panel, methods in FROZEN_METHOD_IDS_BY_PANEL_V1.items() for method in methods}
    if set(identities) != expected or len(identities) != len(set(identities)):
        raise DG05ClosureError("EXACT_RESULT_METHOD_CENSUS_REQUIRED")
    return self_hashed({"schema": "result_authority_bundle_v1", "artifacts": sorted(artifacts, key=lambda v: (FROZEN_PANEL_ORDER_V2.index(v["panel_id"]), FROZEN_METHOD_IDS_BY_PANEL_V1[v["panel_id"]].index(v["method_id"]))),
                        "executable_approval_manifest_hash": executable_manifest_hash, "global_prediction_manifest_hash": global_prediction_manifest_hash,
                        "scenario_authority_hash": scenario_authority_hash, "denominator_authority_hash": denominator_authority_hash,
                        "independent_qa_hash": independent_qa_hash, "cross_version_pooled_result": False})


def build_paired_contrast_v1(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    for item in (a, b):
        validate_self_hashed(item)
    required = ("panel_id", "prediction_manifest_hash", "scenario_authority_hash", "denominator_authority_hash", "metric_authority_hash")
    if any(a[field] != b[field] for field in required):
        raise DG05ClosureError("PAIRED_CONTRAST_AUTHORITY_MISMATCH")
    ah = {v["scenario_id"]: v["hit"] for v in a["scenario_hits"]}
    bh = {v["scenario_id"]: v["hit"] for v in b["scenario_hits"]}
    if set(ah) != set(bh):
        raise DG05ClosureError("PAIRED_SCENARIO_SET_MISMATCH")
    return self_hashed({"schema": "bound_paired_contrast_v1", "panel_id": a["panel_id"], "method_a_result_hash": a["self_hash"], "method_b_result_hash": b["self_hash"], "a_only": sum(ah[k] and not bh[k] for k in ah), "b_only": sum(bh[k] and not ah[k] for k in ah), **{f"bound_{field}": a[field] for field in required[1:]}})


__all__ = [name for name in globals() if name.endswith("V1") or name in {
    "DG05ClosureError", "canonical_bytes", "digest", "self_hashed", "validate_self_hashed",
    "file_sha256", "publish_new", "initialize_dg05_execution_v1", "advance_dg05_state_v1",
    "project_attack_feature_file_v1", "build_expected_prediction_cell_census_v1",
    "execute_prediction_cell_v1", "build_global_prediction_manifest_v1", "freeze_global_predictions_v1",
    "persist_prediction_receipt_v1", "load_frozen_prediction_inputs_v1", "build_etapr_coordinate_binding_v1",
    "build_result_authority_bundle_v1",
    "build_scenario_authority_v1", "build_denominator_authority_v1", "issue_label_lease_v3",
    "compute_bound_panel_method_result_v1", "persist_result_authority_v1", "verify_result_authority_v1",
    "build_paired_contrast_v1",
}]
