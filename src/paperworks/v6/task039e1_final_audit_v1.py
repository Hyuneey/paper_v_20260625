"""Independent real-ledger audit for TASK-039E1.

This module intentionally does not import the E1 production materializer, its
numeric-reference helper, or its runner.  Canonical JSON, record construction,
reference resolution, and public reconstruction are independently implemented
with the Python standard library.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "1.0.0"
TASK_ID = "TASK-039E1-AUDIT"
STATUS = "passed_task039e1_final_audit"
READINESS = "READY_FOR_TASK039E2"
RELATION_FAMILY = "continuous_step_delayed_response_v1"
PROCESS = "P1"

E1_PREP_MERGE = "f32e02136e2471c6bfc3fed584d4a58b16c7aad1"
E1_COMMIT_A = "e8fd2ed47bb0214a0e364bf978eebe75ae4a79a3"
E1_COMMIT_B = "89788b78a98eee3565bd3cbb774541b4c96825bd"
AUDIT_PREP_COMMIT = "5ed61b03ce6138ed9b2e763e568cbb01fb91ee23"

E0_PROTOCOL_BUNDLE_HASH = "a95aecffeaff82d0c67f966f19293ef947827cb0e1e7621a38ecd7c1fd96e17b"
E0_COHORT_HASH = "e71fa69999dbc18310ebb1730fd1d0ea36403763e891b99841ab8cef7ec18732"
E0_IDENTITY_LIST_HASH = "c7f198388bbe53f44bebe5378116a35cc9ed342de7c4df29e255cb5d39cf0479"
E1_AUTHORIZATION_HASH = "03ad2a9e534d553cad75aa811090c1255988156bf1d2a217fb6b883620e05580"

D0_PROTOCOL_BUNDLE_HASH = "888e3d642eba6f8ad8784d428bc4b27d7db7592d34779ba9a1f817860d76e1eb"
SOURCE_EVENT_POLICY_HASH = "1f07a72b380b9ffb2ceb42e029517ef42716145062a57b1770d118b9db252342"
TARGET_RESPONSE_POLICY_HASH = "4b007b9511152396e03722ad8ce0e9cf659ebef2760cef5110414e4ce4bcbeaf"
CONFIRMATION_POLICY_HASH = "83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27"

D1_SOURCE_LEDGER_HASH = "3eb6ff199dbc67b183d35a804754e557bdfa869a899c754e551cd77e8dcfb304"
D1_TARGET_LEDGER_HASH = "f36f4b424c85b228043f9685a22a25c73d6b165e28714b627cf51e8bbb77f96e"
D1_DIRECTIONAL_LEDGER_HASH = "e372d7ccf4a7dde5f7ccd91049cc73b443b3b19a3a0c563f451aea50e8faddc7"
D2_CONFIRMATION_LEDGER_HASH = "d349421ae9a866b924c329dcb2546088466866e09f45851ec5d18090509dc062"
E1_PRIVATE_LEDGER_HASH = "0998c6600078b8a0aca7263b6e0b702808cc141b1cbcfe3d0026fddb98c408a7"

WINDOW_BUNDLE_HASH = "53c3d6ff60987621b38b002f088a5b5f4b686e59c0040e5de7226b6dace6d863"
PUBLIC_MANIFEST_HASH = "ee8c5b7e9895f5f6afdd1be2563244e3b82dca9c3eadca502dd522940931e3ae"
PUBLIC_COHORT_HASH = "4eb4da843a61a9c72aba59edcdf90e49766fc571af7eade14d500b3d04d363d4"
MATERIALIZATION_RESULT_HASH = "2831f175f777bc0544513c35926269e05b6360c17e13f70b89d1768f1c7aa164"
DATA_ACCESS_AUDIT_HASH = "7a52f89262070cf51a3ecb1784c159ee31894d445d4fe54ae06c654d1551c88b"
EXECUTION_RECEIPT_HASH = "5d09cc438344222bdb2a70644ccb3a5a5b7d7b8342ba9a906ba9c8097343f9c7"

EXPECTED_RELATIONS = 42
EXPECTED_PAIRS = 23
EXPECTED_BINDINGS = 462
APPROVED_EVIDENCE_AUTHORITY = "approved_construction_evidence"

NUMERIC_ROLE_ORDER = (
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
    "selected_delay_horizon_seconds",
    "source_pre_window_seconds",
    "source_post_window_seconds",
    "minimum_source_stability_fraction",
    "source_refractory_seconds",
    "cross_source_isolation_radius_seconds",
    "target_baseline_window_seconds",
    "target_response_window_seconds",
)
ROLE_ORIGINS = {
    "source_step_threshold": "d1_fit_derived_source_parameter",
    "source_stability_tolerance": "d1_fit_derived_source_parameter",
    "target_noise_scale": "d1_fit_derived_target_parameter",
    "selected_delay_horizon_seconds": "d1_fit_selected_horizon",
    **{
        role: "d0_preregistered_window_constant"
        for role in NUMERIC_ROLE_ORDER[4:]
    },
}
WINDOW_VALUES: Mapping[str, int | float] = {
    "source_pre_window_seconds": 5,
    "source_post_window_seconds": 5,
    "minimum_source_stability_fraction": 0.8,
    "source_refractory_seconds": 10,
    "cross_source_isolation_radius_seconds": 2,
    "target_baseline_window_seconds": 5,
    "target_response_window_seconds": 3,
}

PRIVATE_SOURCE_LEDGER_NAME = "TASK-039D1_SOURCE_PARAMETER_LEDGER.json"
PRIVATE_TARGET_LEDGER_NAME = "TASK-039D1_TARGET_PARAMETER_LEDGER.json"
PRIVATE_DIRECTIONAL_LEDGER_NAME = "TASK-039D1_DIRECTIONAL_FIT_LEDGER.json"
PRIVATE_D2_LEDGER_NAME = "TASK039D2_DIRECTIONAL_CONFIRMATION_LEDGER.json"
PRIVATE_E1_LEDGER_NAME = "TASK039E1_PRIVATE_CONSTRUCTION_EVIDENCE_LEDGER.json"
PRIVATE_AUDIT_LEDGER_NAME = "TASK039E1_INDEPENDENT_AUDIT_REPLAY_LEDGER.json"

_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_GIT_SHA = re.compile(r"^[a-f0-9]{40}$")


class TASK039E1FinalAuditError(ValueError):
    """Raised when the independent E1 audit fails closed."""


def canonical_json_bytes_v1(document: Any) -> bytes:
    try:
        return json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TASK039E1FinalAuditError("document is not canonical JSON") from exc


def independent_hash_v1(document: Any) -> str:
    return sha256(canonical_json_bytes_v1(document)).hexdigest()


def with_hash_v1(content: Mapping[str, Any]) -> dict[str, Any]:
    copy = json.loads(json.dumps(content, allow_nan=False, sort_keys=True))
    return {**copy, "artifact_hash": independent_hash_v1(copy)}


def verify_self_hash_v1(
    document: Mapping[str, Any], *, expected_hash: str | None = None
) -> str:
    supplied = document.get("artifact_hash")
    if not isinstance(supplied, str) or _SHA256.fullmatch(supplied) is None:
        raise TASK039E1FinalAuditError("artifact hash is malformed")
    observed = independent_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )
    if observed != supplied or (expected_hash is not None and supplied != expected_hash):
        raise TASK039E1FinalAuditError("artifact self-hash mismatch")
    return supplied


def read_json_v1(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TASK039E1FinalAuditError(
            f"required JSON artifact unavailable: {path.name}"
        ) from exc
    if not isinstance(document, dict):
        raise TASK039E1FinalAuditError("artifact must be a JSON object")
    return document


def write_json_v1(path: Path, document: Mapping[str, Any], *, public: bool) -> None:
    if public:
        assert_public_safe_v1(document)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def assert_public_safe_v1(document: Mapping[str, Any]) -> None:
    calibrated_value_keys = {
        "source_step_threshold",
        "source_stability_tolerance",
        "target_noise_scale",
    }

    def walk(value: Any, path: tuple[str, ...] = ()) -> None:
        if isinstance(value, Mapping):
            if "numeric_value" in value:
                raise TASK039E1FinalAuditError(
                    "failed_task039e1_public_private_audit"
                )
            if path[-1:] != ("role_frequencies",) and calibrated_value_keys.intersection(value):
                raise TASK039E1FinalAuditError(
                    "failed_task039e1_public_private_audit"
                )
            for key, item in value.items():
                walk(item, (*path, str(key)))
        elif isinstance(value, list):
            for item in value:
                walk(item, path)
        elif isinstance(value, str) and len(value) >= 3 and value[1:3] in {
            ":\\",
            ":/",
        }:
            raise TASK039E1FinalAuditError("absolute path in public artifact")

    walk(document)


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_external_roots_v1(
    *,
    repository_root: Path,
    d1_private_value: str,
    d2_private_value: str,
    e1_private_value: str,
    audit_private_value: str,
) -> tuple[Path, Path, Path, Path]:
    """Validate four distinct outside-Git roots before any private read."""

    values = (
        d1_private_value,
        d2_private_value,
        e1_private_value,
        audit_private_value,
    )
    paths = tuple(Path(value) for value in values)
    if any(not value or not path.is_absolute() or ".." in path.parts for value, path in zip(values, paths, strict=True)):
        raise TASK039E1FinalAuditError(
            "private roots must be explicit absolute traversal-free paths"
        )
    repository = repository_root.resolve(strict=True)
    d1_root = paths[0].resolve(strict=True)
    d2_root = paths[1].resolve(strict=True)
    e1_root = paths[2].resolve(strict=True)
    if paths[3].exists():
        raise TASK039E1FinalAuditError("audit private root must be fresh")
    paths[3].mkdir(parents=True, exist_ok=False)
    audit_root = paths[3].resolve(strict=True)
    roots = (d1_root, d2_root, e1_root, audit_root)
    if len({str(root).casefold() for root in roots}) != 4:
        raise TASK039E1FinalAuditError("all private roots must be distinct")
    if any(_inside(root, repository) for root in roots):
        raise TASK039E1FinalAuditError("private roots must remain outside Git")
    return roots


def _private_file(root: Path, name: str) -> Path:
    path = (root / name).resolve(strict=True)
    if not _inside(path, root):
        raise TASK039E1FinalAuditError("private artifact escaped its custody root")
    return path


def validate_ledger_v1(
    document: Mapping[str, Any],
    *,
    expected_hash: str,
    expected_type: str,
    expected_count: int,
) -> list[dict[str, Any]]:
    verify_self_hash_v1(document, expected_hash=expected_hash)
    if document.get("artifact_type") != expected_type:
        raise TASK039E1FinalAuditError("private ledger artifact type mismatch")
    if document.get("record_count") != expected_count:
        raise TASK039E1FinalAuditError("private ledger record count mismatch")
    records = document.get("records")
    if not isinstance(records, list) or len(records) != expected_count:
        raise TASK039E1FinalAuditError("private ledger records mismatch")
    hashes: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            raise TASK039E1FinalAuditError("private record must be an object")
        hashes.append(verify_self_hash_v1(record))
    if len(set(hashes)) != expected_count:
        raise TASK039E1FinalAuditError("private record hashes are not unique")
    return records


def window_bundle_v1() -> dict[str, Any]:
    return with_hash_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "task039e1_real_window_constant_bundle_v1",
            "bundle_identity": "task039e1_preregistered_window_constants_v1",
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "source_event_policy_hash": SOURCE_EVENT_POLICY_HASH,
            "target_response_policy_hash": TARGET_RESPONSE_POLICY_HASH,
            "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
            **WINDOW_VALUES,
            "value_origin": "d0_preregistered_window_constant",
            "llm_generated": False,
            "runtime_authority": False,
        }
    )


def independent_numeric_binding_v1(
    *,
    relation_identity: str,
    numeric_role: str,
    numeric_value: int | float,
    source_parameter_record_hash: str,
    target_parameter_record_hash: str,
    d1_fit_evidence_hash: str,
    d2_confirmation_evidence_hash: str,
    window_constant_bundle_hash: str,
) -> dict[str, Any]:
    if numeric_role not in ROLE_ORIGINS:
        raise TASK039E1FinalAuditError("numeric role is outside the freeze")
    if isinstance(numeric_value, bool) or not isinstance(numeric_value, (int, float)) or not math.isfinite(float(numeric_value)):
        raise TASK039E1FinalAuditError("numeric value must be finite")
    content = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "task039e1_real_private_numeric_binding_v1",
        "relation_identity": relation_identity,
        "numeric_role": numeric_role,
        "numeric_value": numeric_value,
        "value_origin": ROLE_ORIGINS[numeric_role],
        "source_parameter_record_hash": source_parameter_record_hash,
        "target_parameter_record_hash": target_parameter_record_hash,
        "d1_fit_evidence_hash": d1_fit_evidence_hash,
        "d2_confirmation_evidence_hash": d2_confirmation_evidence_hash,
        "window_constant_bundle_hash": window_constant_bundle_hash,
        "evidence_authority": APPROVED_EVIDENCE_AUTHORITY,
        "llm_generated": False,
        "runtime_authority": False,
    }
    return {**content, "numeric_reference": independent_hash_v1(content)}


def independent_primitive_v1(
    relation: Mapping[str, Any], bindings: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    by_role = {item["numeric_role"]: item["numeric_reference"] for item in bindings}
    content = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "confirmed_relation_primitive_v1",
        "relation_identity": relation["relation_identity"],
        "relation_family": RELATION_FAMILY,
        "source": relation["source"],
        "source_step_direction": relation["source_step_direction"],
        "target": relation["target"],
        "target_response_direction": relation["target_response_direction"],
        "selected_delay_horizon_seconds": relation["selected_delay_horizon_seconds"],
        "approved_source_threshold_reference": by_role["source_step_threshold"],
        "approved_source_stability_reference": by_role["source_stability_tolerance"],
        "approved_target_scale_reference": by_role["target_noise_scale"],
        "fit_evidence_reference": relation["d1_directional_record_hash"],
        "confirmation_evidence_reference": relation["d2_confirmation_record_hash"],
        "confirmed": True,
        "rule_authority_granted": False,
        "runtime_authority_granted": False,
    }
    return {**content, "binding_hash": independent_hash_v1(content)}


def independent_bundle_v1(
    primitive: Mapping[str, Any], bindings: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    by_role = {item["numeric_role"]: item["numeric_reference"] for item in bindings}
    content = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "approved_numeric_evidence_bundle_v1",
        "relation_binding_hash": primitive["binding_hash"],
        "source_threshold_reference": by_role["source_step_threshold"],
        "source_stability_reference": by_role["source_stability_tolerance"],
        "target_scale_reference": by_role["target_noise_scale"],
        "fit_evidence_reference": primitive["fit_evidence_reference"],
        "confirmation_evidence_reference": primitive["confirmation_evidence_reference"],
        "preregistered_window_constant_references": [
            by_role[role] for role in NUMERIC_ROLE_ORDER[4:]
        ],
        "numeric_origin": "deterministic_calibrated_evidence",
        "approved": True,
        "raw_numeric_values_included": False,
        "arbitrary_numeric_literals_allowed": False,
    }
    return with_hash_v1(content)


def independent_resolve_reference_v1(
    *,
    proposal_numeric_reference: str,
    relation_binding_hash: str,
    numeric_role: str,
    private_evidence_record_hash: str,
    private_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    if private_evidence.get("construction_evidence_status") != "approved":
        raise TASK039E1FinalAuditError("private evidence is not approved")
    if private_evidence.get("relation_binding_hash") != relation_binding_hash:
        raise TASK039E1FinalAuditError("relation binding mismatch")
    if private_evidence.get("artifact_hash") != private_evidence_record_hash:
        raise TASK039E1FinalAuditError("private evidence hash mismatch")
    matches = [
        item
        for item in private_evidence.get("numeric_bindings", [])
        if item.get("numeric_reference") == proposal_numeric_reference
    ]
    if len(matches) != 1 or matches[0].get("numeric_role") != numeric_role:
        raise TASK039E1FinalAuditError("numeric reference or role mismatch")
    return with_hash_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "task039e1_resolved_private_numeric_value_v1",
            "relation_binding_hash": relation_binding_hash,
            "numeric_role": numeric_role,
            "numeric_reference": proposal_numeric_reference,
            "private_evidence_record_hash": private_evidence_record_hash,
            "numeric_value": matches[0]["numeric_value"],
            "construction_only": True,
            "runtime_authority": False,
        }
    )


def _index(records: Sequence[Mapping[str, Any]], key: str) -> dict[str, Mapping[str, Any]]:
    result = {str(record[key]): record for record in records}
    if len(result) != len(records):
        raise TASK039E1FinalAuditError(f"duplicate private record index: {key}")
    return result


def _assert_relation_bindings(
    relation: Mapping[str, Any],
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    d1: Mapping[str, Any],
    d2: Mapping[str, Any],
) -> None:
    expected = (
        relation["source"],
        relation["target"],
        relation["source_step_direction"],
        relation["target_response_direction"],
        relation["selected_delay_horizon_seconds"],
    )
    if expected != (
        d1.get("source"), d1.get("target"), d1.get("source_step_direction"),
        d1.get("selected_target_direction"), d1.get("selected_horizon_seconds"),
    ):
        raise TASK039E1FinalAuditError("D1 relation binding mismatch")
    if expected != (
        d2.get("source"), d2.get("target"), d2.get("source_step_direction"),
        d2.get("target_response_direction"), d2.get("selected_horizon_seconds"),
    ):
        raise TASK039E1FinalAuditError("D2 relation binding mismatch")
    if d1.get("fit_result") != "fit_supported" or d1.get("lower_ranked_fallback_used") is not False:
        raise TASK039E1FinalAuditError("D1 relation is not fit-supported")
    if d2.get("confirmation_status") != "calibration_confirmed":
        raise TASK039E1FinalAuditError("D2 relation is not confirmed")
    if d2.get("d1_directional_record_hash") != d1.get("artifact_hash"):
        raise TASK039E1FinalAuditError("D2-to-D1 binding mismatch")
    if source.get("source") != relation["source"] or source.get("parameter_status") != "supported":
        raise TASK039E1FinalAuditError("source parameter binding mismatch")
    if target.get("target") != relation["target"]:
        raise TASK039E1FinalAuditError("target parameter binding mismatch")
    if d1.get("source_parameter_ref") != source.get("artifact_hash") or d2.get("source_parameter_record_hash") != source.get("artifact_hash"):
        raise TASK039E1FinalAuditError("source parameter reference mismatch")
    if d1.get("target_parameter_ref") != target.get("artifact_hash") or d2.get("target_parameter_record_hash") != target.get("artifact_hash"):
        raise TASK039E1FinalAuditError("target parameter reference mismatch")


def independently_replay_materialization_v1(
    *,
    cohort_document: Mapping[str, Any],
    source_records: Sequence[Mapping[str, Any]],
    target_records: Sequence[Mapping[str, Any]],
    d1_records: Sequence[Mapping[str, Any]],
    d2_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    verify_self_hash_v1(cohort_document, expected_hash=E0_COHORT_HASH)
    relations = cohort_document.get("relations")
    if not isinstance(relations, list) or len(relations) != EXPECTED_RELATIONS:
        raise TASK039E1FinalAuditError("confirmed cohort relation count mismatch")
    if len({item.get("identity_hash") for item in relations}) != EXPECTED_RELATIONS:
        raise TASK039E1FinalAuditError("confirmed relation identities are not unique")
    if len({(item.get("source"), item.get("target")) for item in relations}) != EXPECTED_PAIRS:
        raise TASK039E1FinalAuditError("confirmed pair context count mismatch")

    source_by_name = _index(source_records, "source")
    target_by_name = _index(target_records, "target")
    d1_by_hash = _index(d1_records, "artifact_hash")
    d2_by_hash = _index(d2_records, "artifact_hash")
    window = window_bundle_v1()
    if window["artifact_hash"] != WINDOW_BUNDLE_HASH:
        raise TASK039E1FinalAuditError("window constant bundle mismatch")

    private_records: list[dict[str, Any]] = []
    primitives: list[dict[str, Any]] = []
    bundles: list[dict[str, Any]] = []
    manifest_entries: list[dict[str, Any]] = []
    role_counts: Counter[str] = Counter()

    for relation in relations:
        if not isinstance(relation, dict):
            raise TASK039E1FinalAuditError("confirmed relation must be an object")
        try:
            source = source_by_name[relation["source"]]
            target = target_by_name[relation["target"]]
            d1 = d1_by_hash[relation["d1_directional_record_hash"]]
            d2 = d2_by_hash[relation["d2_confirmation_record_hash"]]
        except KeyError as exc:
            raise TASK039E1FinalAuditError("confirmed relation binding unavailable") from exc
        _assert_relation_bindings(relation, source, target, d1, d2)
        values: Mapping[str, int | float] = {
            "source_step_threshold": source["source_step_threshold"],
            "source_stability_tolerance": source["source_stability_tolerance"],
            "target_noise_scale": target["target_noise_scale"],
            "selected_delay_horizon_seconds": d1["selected_horizon_seconds"],
            **WINDOW_VALUES,
        }
        bindings = [
            independent_numeric_binding_v1(
                relation_identity=relation["relation_identity"],
                numeric_role=role,
                numeric_value=values[role],
                source_parameter_record_hash=source["artifact_hash"],
                target_parameter_record_hash=target["artifact_hash"],
                d1_fit_evidence_hash=d1["artifact_hash"],
                d2_confirmation_evidence_hash=d2["artifact_hash"],
                window_constant_bundle_hash=window["artifact_hash"],
            )
            for role in NUMERIC_ROLE_ORDER
        ]
        role_counts.update(item["numeric_role"] for item in bindings)
        primitive = independent_primitive_v1(relation, bindings)
        private = with_hash_v1(
            {
                "schema_version": SCHEMA_VERSION,
                "artifact_type": "task039e1_real_private_construction_evidence_v1",
                "relation_binding_hash": primitive["binding_hash"],
                "relation_identity": relation["relation_identity"],
                "source": relation["source"],
                "source_step_direction": relation["source_step_direction"],
                "target": relation["target"],
                "target_response_direction": relation["target_response_direction"],
                "selected_horizon_seconds": relation["selected_delay_horizon_seconds"],
                "source_parameter_record_hash": source["artifact_hash"],
                "target_parameter_record_hash": target["artifact_hash"],
                "d1_fit_evidence_hash": d1["artifact_hash"],
                "d2_confirmation_evidence_hash": d2["artifact_hash"],
                "window_constant_bundle_hash": window["artifact_hash"],
                "numeric_bindings": bindings,
                "evidence_authority": APPROVED_EVIDENCE_AUTHORITY,
                "construction_evidence_status": "approved",
                "private_record": True,
                "rule_generated": False,
                "runtime_authority": False,
            }
        )
        bundle = independent_bundle_v1(primitive, bindings)
        manifest_entry = with_hash_v1(
            {
                "schema_version": SCHEMA_VERSION,
                "artifact_type": "task039e1_public_manifest_entry_v1",
                "relation_identity": relation["relation_identity"],
                "source": relation["source"],
                "source_step_direction": relation["source_step_direction"],
                "target": relation["target"],
                "target_response_direction": relation["target_response_direction"],
                "selected_horizon_seconds": relation["selected_delay_horizon_seconds"],
                "relation_binding_hash": primitive["binding_hash"],
                "private_evidence_record_hash": private["artifact_hash"],
                "approved_numeric_roles": list(NUMERIC_ROLE_ORDER),
                "numeric_references": [
                    {
                        "numeric_role": item["numeric_role"],
                        "numeric_reference": item["numeric_reference"],
                    }
                    for item in bindings
                ],
                "source_parameter_record_hash": source["artifact_hash"],
                "target_parameter_record_hash": target["artifact_hash"],
                "d1_fit_evidence_hash": d1["artifact_hash"],
                "d2_confirmation_evidence_hash": d2["artifact_hash"],
                "window_constant_bundle_hash": window["artifact_hash"],
                "evidence_status": "approved",
                "private_numeric_values_included": False,
                "raw_hai_included": False,
                "rule_generated": False,
                "runtime_authority": False,
            }
        )
        for binding in bindings:
            resolved = independent_resolve_reference_v1(
                proposal_numeric_reference=binding["numeric_reference"],
                relation_binding_hash=private["relation_binding_hash"],
                numeric_role=binding["numeric_role"],
                private_evidence_record_hash=private["artifact_hash"],
                private_evidence=private,
            )
            if resolved["numeric_value"] != binding["numeric_value"] or resolved["runtime_authority"] is not False:
                raise TASK039E1FinalAuditError("independent resolver replay failed")
        private_records.append(private)
        primitives.append(primitive)
        bundles.append(bundle)
        manifest_entries.append(manifest_entry)

    if role_counts != Counter({role: EXPECTED_RELATIONS for role in NUMERIC_ROLE_ORDER}):
        raise TASK039E1FinalAuditError("failed_task039e1_role_accounting")

    private_ledger = with_hash_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "task039e1_private_construction_evidence_ledger_v1",
            "task_id": "TASK-039E1",
            "status": "frozen_task039e1_private_construction_evidence",
            "execution_code_commit": E1_COMMIT_A,
            "e0_cohort_hash": E0_COHORT_HASH,
            "e0_identity_list_hash": E0_IDENTITY_LIST_HASH,
            "record_count": EXPECTED_RELATIONS,
            "numeric_binding_count": EXPECTED_BINDINGS,
            "records": private_records,
            "raw_hai_included": False,
            "event_timestamps_included": False,
            "attack_test_label_information_included": False,
            "absolute_paths_included": False,
            "rule_generated": False,
            "runtime_authority": False,
        }
    )
    private_binding = with_hash_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "task039e1_private_ledger_binding_v1",
            "private_ledger_hash": private_ledger["artifact_hash"],
            "record_count": EXPECTED_RELATIONS,
            "numeric_binding_count": EXPECTED_BINDINGS,
            "storage_boundary": "outside_git",
            "private_contents_public": False,
            "private_numeric_values_public": False,
        }
    )
    manifest = with_hash_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "task039e1_construction_evidence_manifest_v1",
            "task_id": "TASK-039E1",
            "status": "frozen_task039e1_public_construction_evidence_manifest",
            "e0_cohort_hash": E0_COHORT_HASH,
            "relation_count": EXPECTED_RELATIONS,
            "numeric_binding_count": EXPECTED_BINDINGS,
            "entries": manifest_entries,
            "private_numeric_values_included": False,
            "raw_hai_included": False,
            "rule_generated": False,
            "runtime_authority": False,
        }
    )
    cohort = with_hash_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "task039e1_construction_evidence_cohort_v1",
            "task_id": "TASK-039E1",
            "status": "frozen_task039e1_construction_evidence_cohort",
            "process": PROCESS,
            "relation_family": RELATION_FAMILY,
            "e0_cohort_hash": E0_COHORT_HASH,
            "e0_identity_list_hash": E0_IDENTITY_LIST_HASH,
            "e0_protocol_bundle_hash": E0_PROTOCOL_BUNDLE_HASH,
            "e1_authorization_hash": E1_AUTHORIZATION_HASH,
            "window_constant_bundle_hash": window["artifact_hash"],
            "relation_count": EXPECTED_RELATIONS,
            "pair_context_count": EXPECTED_PAIRS,
            "numeric_binding_count": EXPECTED_BINDINGS,
            "confirmed_relation_primitives": primitives,
            "approved_numeric_evidence_bundles": bundles,
            "public_manifest_entries": manifest_entries,
            "private_ledger_hash": private_ledger["artifact_hash"],
            "scientific_ranking_created": False,
            "candidate_origin_filtering_used": False,
            "rule_generation_executed": False,
            "runtime_authority": False,
        }
    )
    return {
        "window": window,
        "private_ledger": private_ledger,
        "private_binding": private_binding,
        "manifest": manifest,
        "cohort": cohort,
        "primitives": primitives,
        "bundles": bundles,
        "manifest_entries": manifest_entries,
        "role_counts": dict(role_counts),
    }


def reconstruct_public_result_artifacts_v1(
    replay: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    access = with_hash_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "task039e1_data_access_audit_v1",
            "task_id": "TASK-039E1",
            "d1_source_ledger_accessed": True,
            "d1_target_ledger_accessed": True,
            "d1_directional_ledger_accessed": True,
            "d2_confirmation_ledger_accessed": True,
            "private_input_ledgers_modified": False,
            "hai_accessed": False,
            "train1_train2_train3_reread": False,
            "train4_accessed": False,
            "test_labels_attacks_accessed": False,
            "llm_called": False,
            "t0_generated": False,
            "t1_t1b_t2_generated": False,
            "rule_v2_authorized": False,
            "runtime_authority": False,
            "absolute_local_paths_public": False,
            "private_calibrated_values_public": False,
            "prohibited_access_count": 0,
        }
    )
    result = with_hash_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "task039e1_materialization_result_v1",
            "task_id": "TASK-039E1",
            "status": "passed_task039e1_evidence_materialization",
            "e0_cohort_hash": E0_COHORT_HASH,
            "e0_protocol_bundle_hash": E0_PROTOCOL_BUNDLE_HASH,
            "e1_authorization_hash": E1_AUTHORIZATION_HASH,
            "confirmed_input_relations": 42,
            "confirmed_pair_contexts": 23,
            "materialized_private_records": 42,
            "public_manifest_entries": 42,
            "relation_primitives": 42,
            "approved_numeric_bundles": 42,
            "numeric_bindings": 462,
            "failed_relations": 0,
            "skipped_relations": 0,
            "private_ledger_hash": replay["private_ledger"]["artifact_hash"],
            "public_manifest_hash": replay["manifest"]["artifact_hash"],
            "construction_evidence_cohort_hash": replay["cohort"]["artifact_hash"],
            "data_access_audit_hash": access["artifact_hash"],
            "rule_generated": False,
            "runtime_authority": False,
        }
    )
    receipt = with_hash_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "task039e1_execution_receipt_v1",
            "task_id": "TASK-039E1",
            "status": "passed_task039e1_evidence_materialization",
            "execution_code_commit": E1_COMMIT_A,
            "e0_protocol_bundle_hash": E0_PROTOCOL_BUNDLE_HASH,
            "e0_cohort_hash": E0_COHORT_HASH,
            "e1_authorization_hash": E1_AUTHORIZATION_HASH,
            "d1_source_ledger_hash": D1_SOURCE_LEDGER_HASH,
            "d1_target_ledger_hash": D1_TARGET_LEDGER_HASH,
            "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
            "d2_confirmation_ledger_hash": D2_CONFIRMATION_LEDGER_HASH,
            "window_constant_bundle_hash": replay["window"]["artifact_hash"],
            "private_e1_ledger_hash": replay["private_ledger"]["artifact_hash"],
            "public_manifest_hash": replay["manifest"]["artifact_hash"],
            "construction_evidence_cohort_hash": replay["cohort"]["artifact_hash"],
            "materialization_result_hash": result["artifact_hash"],
            "data_access_audit_hash": access["artifact_hash"],
            "hai_accessed": False,
            "llm_called": False,
            "rule_generated": False,
            "runtime_authority": False,
        }
    )
    return {"access": access, "result": result, "receipt": receipt}


def build_e2_authorization_v1() -> dict[str, Any]:
    return with_hash_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "task039e2_authorization_v1",
            "task_id": "TASK-039E2",
            "task_name": "Rule Construction Execution Configuration Freeze",
            "status": "authorized_task039e2_configuration_freeze_only",
            "readiness": READINESS,
            "e0_protocol_bundle_hash": E0_PROTOCOL_BUNDLE_HASH,
            "e1_materialization_result_hash": MATERIALIZATION_RESULT_HASH,
            "e1_construction_evidence_cohort_hash": PUBLIC_COHORT_HASH,
            "e1_private_ledger_hash": E1_PRIVATE_LEDGER_HASH,
            "relation_count": EXPECTED_RELATIONS,
            "numeric_binding_count": EXPECTED_BINDINGS,
            "provider_model_identity_freeze_authorized": True,
            "prompt_template_freeze_authorized": True,
            "structured_output_schema_freeze_authorized": True,
            "decoding_parameter_freeze_authorized": True,
            "seed_policy_freeze_authorized": True,
            "deterministic_execution_schedule_freeze_authorized": True,
            "transport_retry_policy_freeze_authorized": True,
            "private_evidence_rendering_policy_freeze_authorized": True,
            "t0_template_finalization_authorized": True,
            "t1_t1b_t2_harness_protocol_freeze_authorized": True,
            "provider_model_call_authorized": False,
            "real_t0_generation_authorized": False,
            "real_t1_t1b_t2_generation_authorized": False,
            "direct_number_execution_authorized": False,
            "rule_v2_authorized": False,
            "detector_runtime_authorized": False,
            "hai_test_labels_attacks_authorized": False,
        }
    )


def build_audit_artifact_v1(
    *, audit_execution_code_commit: str, audit_replay_ledger_hash: str,
    e2_authorization_hash: str,
) -> dict[str, Any]:
    if _GIT_SHA.fullmatch(audit_execution_code_commit) is None:
        raise TASK039E1FinalAuditError("audit execution code commit is malformed")
    content = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "task039e1_final_audit_v1",
        "task_id": TASK_ID,
        "status": STATUS,
        "readiness": READINESS,
        "lineage": {
            "e1_prep_merge_commit": E1_PREP_MERGE,
            "e1_execution_commit_a": E1_COMMIT_A,
            "e1_result_commit_b": E1_COMMIT_B,
            "audit_prep_commit": AUDIT_PREP_COMMIT,
            "audit_execution_code_commit": audit_execution_code_commit,
            "commit_separation_verified": True,
        },
        "private_input_hashes": {
            "d1_source_ledger_hash": D1_SOURCE_LEDGER_HASH,
            "d1_target_ledger_hash": D1_TARGET_LEDGER_HASH,
            "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
            "d2_confirmation_ledger_hash": D2_CONFIRMATION_LEDGER_HASH,
            "e1_private_ledger_hash": E1_PRIVATE_LEDGER_HASH,
            "all_self_hashes_verified": True,
            "all_record_hashes_verified": True,
            "original_ledgers_modified": False,
        },
        "independent_replay": {
            "audit_replay_ledger_hash": audit_replay_ledger_hash,
            "private_records_reproduced": 42,
            "numeric_bindings_reproduced": 462,
            "numeric_references_reproduced": 462,
            "role_frequencies": {role: 42 for role in NUMERIC_ROLE_ORDER},
            "window_bundle_hash": WINDOW_BUNDLE_HASH,
            "window_bundle_reproduced": True,
            "resolver_positive_replays": 462,
            "resolver_negative_guards_passed": True,
            "relation_binding_reproduced": True,
            "parameter_binding_reproduced": True,
            "origin_mapping_reproduced": True,
        },
        "public_reconstruction": {
            "relation_primitives_reproduced": 42,
            "approved_numeric_bundles_reproduced": 42,
            "public_manifest_entries_reproduced": 42,
            "public_manifest_hash": PUBLIC_MANIFEST_HASH,
            "construction_evidence_cohort_hash": PUBLIC_COHORT_HASH,
            "materialization_result_hash": MATERIALIZATION_RESULT_HASH,
            "data_access_audit_hash": DATA_ACCESS_AUDIT_HASH,
            "execution_receipt_hash": EXECUTION_RECEIPT_HASH,
            "byte_semantic_equality_verified": True,
        },
        "public_private_boundary": {
            "private_numeric_values_public": False,
            "absolute_local_paths_public": False,
            "raw_hai_public": False,
            "private_ledgers_committed": False,
            "hai_accessed_by_audit": False,
            "llm_called_by_audit": False,
            "rule_generated_by_audit": False,
            "runtime_authority_granted": False,
            "passed": True,
        },
        "findings": {"blocking": [], "important_nonblocking": []},
        "e2_authorization_created": True,
        "e2_authorization_hash": e2_authorization_hash,
    }
    return with_hash_v1(content)


def audit_replay_ledger_v1(
    private_records: Sequence[Mapping[str, Any]], *, audit_execution_code_commit: str
) -> dict[str, Any]:
    return with_hash_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "task039e1_independent_audit_replay_ledger_v1",
            "task_id": TASK_ID,
            "status": "frozen_task039e1_independent_audit_replay",
            "audit_execution_code_commit": audit_execution_code_commit,
            "e1_private_ledger_hash": E1_PRIVATE_LEDGER_HASH,
            "record_count": EXPECTED_RELATIONS,
            "numeric_binding_count": EXPECTED_BINDINGS,
            "records": list(private_records),
            "raw_hai_included": False,
            "absolute_paths_included": False,
            "rule_generated": False,
            "runtime_authority": False,
        }
    )


def schema_documents_v1() -> dict[str, dict[str, Any]]:
    meta = "https://json-schema.org/draft/2020-12/schema"
    sha = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    git = {"type": "string", "pattern": "^[a-f0-9]{40}$"}
    false = {"const": False}
    true = {"const": True}

    def obj(properties: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": dict(properties),
            "required": list(properties),
        }

    lineage = obj({
        "e1_prep_merge_commit": git, "e1_execution_commit_a": git,
        "e1_result_commit_b": git, "audit_prep_commit": git,
        "audit_execution_code_commit": git, "commit_separation_verified": true,
    })
    private = obj({
        "d1_source_ledger_hash": sha, "d1_target_ledger_hash": sha,
        "d1_directional_ledger_hash": sha, "d2_confirmation_ledger_hash": sha,
        "e1_private_ledger_hash": sha, "all_self_hashes_verified": true,
        "all_record_hashes_verified": true, "original_ledgers_modified": false,
    })
    replay = obj({
        "audit_replay_ledger_hash": sha, "private_records_reproduced": {"const": 42},
        "numeric_bindings_reproduced": {"const": 462},
        "numeric_references_reproduced": {"const": 462},
        "role_frequencies": obj({role: {"const": 42} for role in NUMERIC_ROLE_ORDER}),
        "window_bundle_hash": {"const": WINDOW_BUNDLE_HASH},
        "window_bundle_reproduced": true, "resolver_positive_replays": {"const": 462},
        "resolver_negative_guards_passed": true, "relation_binding_reproduced": true,
        "parameter_binding_reproduced": true, "origin_mapping_reproduced": true,
    })
    public = obj({
        "relation_primitives_reproduced": {"const": 42},
        "approved_numeric_bundles_reproduced": {"const": 42},
        "public_manifest_entries_reproduced": {"const": 42},
        "public_manifest_hash": {"const": PUBLIC_MANIFEST_HASH},
        "construction_evidence_cohort_hash": {"const": PUBLIC_COHORT_HASH},
        "materialization_result_hash": {"const": MATERIALIZATION_RESULT_HASH},
        "data_access_audit_hash": {"const": DATA_ACCESS_AUDIT_HASH},
        "execution_receipt_hash": {"const": EXECUTION_RECEIPT_HASH},
        "byte_semantic_equality_verified": true,
    })
    boundary = obj({
        "private_numeric_values_public": false, "absolute_local_paths_public": false,
        "raw_hai_public": false, "private_ledgers_committed": false,
        "hai_accessed_by_audit": false, "llm_called_by_audit": false,
        "rule_generated_by_audit": false, "runtime_authority_granted": false,
        "passed": true,
    })
    findings = obj({
        "blocking": {"type": "array", "maxItems": 0},
        "important_nonblocking": {"type": "array", "maxItems": 0},
    })
    audit = obj({
        "schema_version": {"const": SCHEMA_VERSION},
        "artifact_type": {"const": "task039e1_final_audit_v1"},
        "task_id": {"const": TASK_ID}, "status": {"const": STATUS},
        "readiness": {"const": READINESS}, "lineage": lineage,
        "private_input_hashes": private, "independent_replay": replay,
        "public_reconstruction": public, "public_private_boundary": boundary,
        "findings": findings, "e2_authorization_created": true,
        "e2_authorization_hash": sha, "artifact_hash": sha,
    })
    e2 = obj({
        "schema_version": {"const": SCHEMA_VERSION},
        "artifact_type": {"const": "task039e2_authorization_v1"},
        "task_id": {"const": "TASK-039E2"},
        "task_name": {"const": "Rule Construction Execution Configuration Freeze"},
        "status": {"const": "authorized_task039e2_configuration_freeze_only"},
        "readiness": {"const": READINESS},
        "e0_protocol_bundle_hash": {"const": E0_PROTOCOL_BUNDLE_HASH},
        "e1_materialization_result_hash": {"const": MATERIALIZATION_RESULT_HASH},
        "e1_construction_evidence_cohort_hash": {"const": PUBLIC_COHORT_HASH},
        "e1_private_ledger_hash": {"const": E1_PRIVATE_LEDGER_HASH},
        "relation_count": {"const": 42}, "numeric_binding_count": {"const": 462},
        "provider_model_identity_freeze_authorized": true,
        "prompt_template_freeze_authorized": true,
        "structured_output_schema_freeze_authorized": true,
        "decoding_parameter_freeze_authorized": true,
        "seed_policy_freeze_authorized": true,
        "deterministic_execution_schedule_freeze_authorized": true,
        "transport_retry_policy_freeze_authorized": true,
        "private_evidence_rendering_policy_freeze_authorized": true,
        "t0_template_finalization_authorized": true,
        "t1_t1b_t2_harness_protocol_freeze_authorized": true,
        "provider_model_call_authorized": false,
        "real_t0_generation_authorized": false,
        "real_t1_t1b_t2_generation_authorized": false,
        "direct_number_execution_authorized": false,
        "rule_v2_authorized": false, "detector_runtime_authorized": false,
        "hai_test_labels_attacks_authorized": false, "artifact_hash": sha,
    })
    return {
        "task039e1_final_audit_v1": {
            "$schema": meta,
            "$id": "https://paperworks.local/schemas/v6/task039e1_final_audit_v1.json",
            **audit,
        },
        "task039e2_authorization_v1": {
            "$schema": meta,
            "$id": "https://paperworks.local/schemas/v6/task039e2_authorization_v1.json",
            **e2,
        },
    }


__all__ = [
    "AUDIT_PREP_COMMIT", "DATA_ACCESS_AUDIT_HASH", "D1_DIRECTIONAL_LEDGER_HASH",
    "D1_SOURCE_LEDGER_HASH", "D1_TARGET_LEDGER_HASH", "D2_CONFIRMATION_LEDGER_HASH",
    "E1_COMMIT_A", "E1_COMMIT_B", "E1_PRIVATE_LEDGER_HASH", "EXECUTION_RECEIPT_HASH",
    "MATERIALIZATION_RESULT_HASH", "NUMERIC_ROLE_ORDER", "PRIVATE_AUDIT_LEDGER_NAME",
    "PRIVATE_D2_LEDGER_NAME", "PRIVATE_DIRECTIONAL_LEDGER_NAME", "PRIVATE_E1_LEDGER_NAME",
    "PRIVATE_SOURCE_LEDGER_NAME", "PRIVATE_TARGET_LEDGER_NAME", "PUBLIC_COHORT_HASH",
    "PUBLIC_MANIFEST_HASH", "READINESS", "STATUS", "TASK039E1FinalAuditError",
    "WINDOW_BUNDLE_HASH", "assert_public_safe_v1", "audit_replay_ledger_v1",
    "build_audit_artifact_v1", "build_e2_authorization_v1", "independent_hash_v1",
    "independent_numeric_binding_v1", "independent_resolve_reference_v1",
    "independently_replay_materialization_v1", "read_json_v1",
    "reconstruct_public_result_artifacts_v1", "schema_documents_v1",
    "validate_external_roots_v1", "validate_ledger_v1", "verify_self_hash_v1",
    "window_bundle_v1", "with_hash_v1", "write_json_v1",
]
