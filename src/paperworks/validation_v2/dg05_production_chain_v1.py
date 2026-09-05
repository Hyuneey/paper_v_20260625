"""Prospective DG-05 production-chain authority and guarded adapters.

The module is pre-access infrastructure.  It never opens attack containers or
label sources by itself.  A release manifest is the immutable root; the older
V2 prediction manifest may be listed as a nested dependency but can never
replace that root in receipts or state.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence


class DG05ProductionChainError(ValueError):
    """Fail-closed production-chain error."""


REQUIRED_IMPLEMENTATION_ROLES_V1 = frozenset(
    {
        "release_initializer", "production_orchestrator", "state_machine",
        "projection_adapter", "prediction_dispatch", "global_manifest_builder",
        "global_freeze_builder", "custodian_launcher", "custodian",
        "scenario_builder", "denominator_builder", "normal_burden_replay",
        "metric_primitive_builder", "result_builder", "upstream_verifier",
        "result_verifier",
    }
)
REQUIRED_NESTED_AUTHORITY_ROLES_V1 = frozenset(
    {
        "method_bundle", "metric_contract", "detector_registry",
        "rule_runtime_registry", "dispatch_registry", "full_process_scope",
        "p1_custodian", "attack_feature_allowlist", "attack_file_census",
        "fusion", "etapr", "statistical_contract",
    }
)


def canonical_bytes_v1(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def digest_v1(value: Any) -> str:
    return sha256(canonical_bytes_v1(value)).hexdigest()


def self_hashed_v1(body: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(body)
    return {**value, "self_hash": digest_v1(value)}


def file_sha256_v1(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_canonical_self_hashed_v1(path: Path, schema: str) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DG05ProductionChainError("CANONICAL_JSON_REQUIRED") from exc
    body = {key: item for key, item in value.items() if key != "self_hash"}
    if (
        type(value) is not dict
        or value.get("schema") != schema
        or value.get("self_hash") != digest_v1(body)
        or raw != canonical_bytes_v1(value) + b"\n"
    ):
        raise DG05ProductionChainError(f"CANONICAL_SELF_HASH_REPLAY_FAILED:{schema}")
    return value


@dataclass(frozen=True)
class ProductionReleaseImplementationV1:
    logical_name: str
    relative_path: str
    byte_hash: str

    def document(self) -> dict[str, str]:
        return {"logical_name": self.logical_name, "relative_path": self.relative_path, "byte_hash": self.byte_hash}


def build_production_release_manifest_v1(
    *,
    repository_root: Path,
    predecessor_v3_manifest_path: Path,
    predecessor_v3_closure_path: Path,
    implementation_paths: Mapping[str, Path],
    nested_authority_hashes: Mapping[str, str],
    semantic_binding_status: str,
    semantic_binding_hash: str,
    normal_burden_source_status: str,
    normal_burden_source_registry_hash: str | None,
    source_commit: str,
) -> dict[str, Any]:
    """Build a prospective release root without a self-referential code hash."""
    predecessor_manifest = load_canonical_self_hashed_v1(predecessor_v3_manifest_path, "dg05_executable_authority_manifest_v3")
    predecessor_closure = load_canonical_self_hashed_v1(predecessor_v3_closure_path, "dg05_executable_closure_authority_v3")
    if predecessor_closure.get("executable_manifest_hash") != predecessor_manifest["self_hash"]:
        raise DG05ProductionChainError("PREDECESSOR_V3_BINDING_MISMATCH")
    root = repository_root.resolve()
    implementations = []
    for logical_name, path in sorted(implementation_paths.items()):
        resolved = path.resolve()
        if root not in resolved.parents or not resolved.is_file() or resolved.is_symlink():
            raise DG05ProductionChainError("IMPLEMENTATION_PATH_OUTSIDE_REPOSITORY")
        implementations.append(
            ProductionReleaseImplementationV1(logical_name, resolved.relative_to(root).as_posix(), file_sha256_v1(resolved)).document()
        )
    if len(implementations) != len({row["logical_name"] for row in implementations}):
        raise DG05ProductionChainError("UNIQUE_IMPLEMENTATION_NAMES_REQUIRED")
    if {row["logical_name"] for row in implementations} != REQUIRED_IMPLEMENTATION_ROLES_V1:
        raise DG05ProductionChainError("COMPLETE_PRODUCTION_IMPLEMENTATION_CENSUS_REQUIRED")
    if set(nested_authority_hashes) != REQUIRED_NESTED_AUTHORITY_ROLES_V1:
        raise DG05ProductionChainError("COMPLETE_NESTED_AUTHORITY_CENSUS_REQUIRED")
    if semantic_binding_status not in ("APPROVED", "USER_DECISION_REQUIRED"):
        raise DG05ProductionChainError("SEMANTIC_BINDING_STATUS_REQUIRED")
    if normal_burden_source_status not in ("COMPLETE", "EVIDENCE_MISSING"):
        raise DG05ProductionChainError("NORMAL_BURDEN_SOURCE_STATUS_REQUIRED")
    for value in (semantic_binding_hash, *(nested_authority_hashes.values())):
        if type(value) is not str or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise DG05ProductionChainError("SHA256_AUTHORITY_REQUIRED")
    if normal_burden_source_status == "COMPLETE" and (
        type(normal_burden_source_registry_hash) is not str or len(normal_burden_source_registry_hash) != 64
    ):
        raise DG05ProductionChainError("NORMAL_BURDEN_SOURCE_REGISTRY_REQUIRED")
    if type(source_commit) is not str or len(source_commit) != 40 or any(character not in "0123456789abcdef" for character in source_commit):
        raise DG05ProductionChainError("SOURCE_COMMIT_REQUIRED")
    readiness = (
        "READY_FOR_USER_REAPPROVAL"
        if semantic_binding_status == "APPROVED" and normal_burden_source_status == "COMPLETE"
        else "DECISION_OR_EVIDENCE_REQUIRED"
    )
    return self_hashed_v1(
        {
            "schema": "dg05_production_release_manifest_v1",
            "approval_status": "DG05_PRODUCTION_RELEASE_USER_REAPPROVAL_REQUIRED",
            "readiness": readiness,
            "predecessor_v3_manifest_hash": predecessor_manifest["self_hash"],
            "predecessor_v3_closure_hash": predecessor_closure["self_hash"],
            "semantic_binding_status": semantic_binding_status,
            "semantic_binding_hash": semantic_binding_hash,
            "normal_burden_source_status": normal_burden_source_status,
            "normal_burden_source_registry_hash": normal_burden_source_registry_hash,
            "nested_authority_hashes": dict(sorted(nested_authority_hashes.items())),
            "implementation_authorities": implementations,
            "source_commit": source_commit,
            "attack_test_accesses": 0,
            "label_scenario_accesses": 0,
            "provider_calls": 0,
            "credential_reads": 0,
        }
    )


def initialize_production_release_v1(
    *,
    release_manifest_path: Path,
    repository_root: Path,
    predecessor_v3_manifest_path: Path,
    predecessor_v3_closure_path: Path,
    approved_release_hash: str | None,
    authority_mode: str,
) -> dict[str, Any]:
    """Replay the exact release root before any protected resource access."""
    release = load_canonical_self_hashed_v1(release_manifest_path, "dg05_production_release_manifest_v1")
    predecessor_manifest = load_canonical_self_hashed_v1(predecessor_v3_manifest_path, "dg05_executable_authority_manifest_v3")
    predecessor_closure = load_canonical_self_hashed_v1(predecessor_v3_closure_path, "dg05_executable_closure_authority_v3")
    if (
        release.get("predecessor_v3_manifest_hash") != predecessor_manifest["self_hash"]
        or release.get("predecessor_v3_closure_hash") != predecessor_closure["self_hash"]
    ):
        raise DG05ProductionChainError("PREDECESSOR_V3_REPLAY_MISMATCH")
    root = repository_root.resolve()
    for row in release.get("implementation_authorities", ()):
        path = (root / row["relative_path"]).resolve()
        if root not in path.parents or not path.is_file() or path.is_symlink() or file_sha256_v1(path) != row["byte_hash"]:
            raise DG05ProductionChainError(f"IMPLEMENTATION_BYTE_REPLAY_MISMATCH:{row.get('logical_name')}")
    derived_ready = (
        {row.get("logical_name") for row in release.get("implementation_authorities", ())} == REQUIRED_IMPLEMENTATION_ROLES_V1
        and set(release.get("nested_authority_hashes", {})) == REQUIRED_NESTED_AUTHORITY_ROLES_V1
        and release.get("semantic_binding_status") == "APPROVED"
        and release.get("normal_burden_source_status") == "COMPLETE"
        and type(release.get("normal_burden_source_registry_hash")) is str
    )
    expected_readiness = "READY_FOR_USER_REAPPROVAL" if derived_ready else "DECISION_OR_EVIDENCE_REQUIRED"
    if release.get("readiness") != expected_readiness:
        raise DG05ProductionChainError("RELEASE_READINESS_DERIVATION_MISMATCH")
    if authority_mode == "PRODUCTION":
        if release.get("readiness") != "READY_FOR_USER_REAPPROVAL":
            raise DG05ProductionChainError("PRODUCTION_RELEASE_NOT_READY")
        if approved_release_hash is None or approved_release_hash != release["self_hash"]:
            raise DG05ProductionChainError("EXACT_PRODUCTION_RELEASE_APPROVAL_REQUIRED")
        state = "APPROVED_PRODUCTION_RELEASE_INITIALIZED"
        protected_access_authorized = True
    elif authority_mode == "SYNTHETIC_REHEARSAL":
        if approved_release_hash != release["self_hash"]:
            raise DG05ProductionChainError("EXACT_SYNTHETIC_RELEASE_HASH_REQUIRED")
        state = "SYNTHETIC_RELEASE_INITIALIZED"
        protected_access_authorized = False
    else:
        raise DG05ProductionChainError("AUTHORITY_MODE_REQUIRED")
    return self_hashed_v1(
        {
            "schema": "dg05_production_chain_state_v1",
            "state": state,
            "release_manifest_hash": release["self_hash"],
            "predecessor_v3_manifest_hash": predecessor_manifest["self_hash"],
            "protected_access_authorized": protected_access_authorized,
            "authority_mode": authority_mode,
            "attack_test_accesses": 0,
            "label_scenario_accesses": 0,
        }
    )


def launch_custodian_fresh_process_v2(
    *,
    request_path: Path,
    resource_policy_path: Path,
    launcher_path: Path,
    repository_root: Path,
    expected_launcher_hash: str,
    expected_resource_policy_hash: str,
    expected_custodian_implementation_hash: str,
    predecessor_state: Mapping[str, Any],
    expected_global_freeze_hash: str,
    expected_release_manifest_hash: str,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Invoke the static custodian launcher in a distinct Python process."""
    body = {key: item for key, item in predecessor_state.items() if key != "self_hash"}
    if predecessor_state.get("self_hash") != digest_v1(body):
        raise DG05ProductionChainError("VALID_PREDECESSOR_STATE_REQUIRED")
    if predecessor_state.get("state") != "LABEL_SCENARIO_LEASE_ISSUED":
        raise DG05ProductionChainError("LABEL_LEASE_ISSUED_PREDECESSOR_REQUIRED")
    if (
        predecessor_state.get("release_manifest_hash") != expected_release_manifest_hash
        or predecessor_state.get("global_prediction_freeze_hash") != expected_global_freeze_hash
        or predecessor_state.get("authority_mode") not in ("PRODUCTION", "SYNTHETIC_REHEARSAL")
    ):
        raise DG05ProductionChainError("GLOBAL_FREEZE_RELEASE_BINDING_REQUIRED")
    if file_sha256_v1(launcher_path) != expected_launcher_hash:
        raise DG05ProductionChainError("CUSTODIAN_LAUNCHER_BYTE_MISMATCH")
    raw_request = request_path.read_bytes()
    request = json.loads(raw_request.decode("utf-8"))
    if raw_request != canonical_bytes_v1(request) + b"\n":
        raise DG05ProductionChainError("CANONICAL_CUSTODIAN_REQUEST_REQUIRED")
    lease = request.get("lease_receipt")
    policy = load_canonical_self_hashed_v1(resource_policy_path, "custodian_resource_policy_authority_v2")
    if (
        request.get("global_freeze_hash") != expected_global_freeze_hash
        or request.get("executable_manifest_hash") != expected_release_manifest_hash
        or request.get("predecessor_state_hash") != predecessor_state.get("self_hash")
        or request.get("authority_mode") != predecessor_state.get("authority_mode")
        or type(lease) is not dict
        or request.get("lease_issue_predecessor_hash") != predecessor_state.get("lease_issue_predecessor_hash")
        or lease.get("state_hash") != predecessor_state.get("lease_issue_predecessor_hash")
        or lease.get("self_hash") != predecessor_state.get("lease_receipt_hash")
        or lease.get("token_hash") != predecessor_state.get("lease_token_hash")
        or policy.get("self_hash") != expected_resource_policy_hash
        or policy.get("self_hash") != request.get("resource_policy_hash")
        or policy.get("scenario_adapter_implementation_hash") != expected_custodian_implementation_hash
    ):
        raise DG05ProductionChainError("CUSTODIAN_REQUEST_FREEZE_MISMATCH")
    # Do not copy arbitrary coordinator secrets into the label-capable child.
    environment = {
        key: os.environ[key]
        for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "PATH")
        if key in os.environ
    }
    environment["PYTHONPATH"] = str((repository_root / "src").resolve())
    completed = subprocess.run(
        [
            sys.executable,
            str(launcher_path.resolve()),
            "--request",
            str(request_path.resolve()),
            "--resource-policy-authority",
            str(resource_policy_path.resolve()),
        ],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        failure_text = completed.stdout.strip()
        try:
            failure_code = json.loads(failure_text).get("error", "CUSTODIAN_CHILD_FAILED")
        except json.JSONDecodeError:
            failure_code = "CUSTODIAN_CHILD_FAILED_WITHOUT_SAFE_RECEIPT"
        raise DG05ProductionChainError(f"FRESH_CUSTODIAN_PROCESS_FAILED:{failure_code}")
    try:
        receipt = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise DG05ProductionChainError("FRESH_CUSTODIAN_RECEIPT_REQUIRED") from exc
    if receipt.get("custodian_pid") in (None, os.getpid()) or receipt.get("custodian_parent_pid") != os.getpid():
        raise DG05ProductionChainError("FRESH_PROCESS_IDENTITY_REQUIRED")
    return self_hashed_v1(
        {
            "schema": "dg05_fresh_process_custodian_invocation_v1",
            "launcher_byte_hash": expected_launcher_hash,
            "request_byte_hash": file_sha256_v1(request_path),
            "resource_policy_byte_hash": file_sha256_v1(resource_policy_path),
            "resource_policy_hash": expected_resource_policy_hash,
            "custodian_implementation_hash": expected_custodian_implementation_hash,
            "predecessor_state_hash": predecessor_state["self_hash"],
            "global_freeze_hash": expected_global_freeze_hash,
            "release_manifest_hash": expected_release_manifest_hash,
            "release_manifest_hash": expected_release_manifest_hash,
            "custodian_pid": receipt["custodian_pid"],
            "custodian_parent_pid": receipt["custodian_parent_pid"],
            "consume_receipt_hash": receipt["consume_receipt_hash"],
            "output_self_hash": receipt["output_self_hash"],
            "output_byte_hash": receipt["output_byte_hash"],
            "isolation_mechanism": "FRESH_PROCESS_PLUS_APPLICATION_PATH_CAPABILITY_GUARDS",
            "os_sandbox_claimed": False,
            "coordinator_environment_forwarding": "MINIMAL_ALLOWLIST_NO_PROVIDER_OR_CREDENTIAL_VARIABLES",
            "coordinator_environment_forwarding": "MINIMAL_ALLOWLIST_NO_PROVIDER_OR_CREDENTIAL_VARIABLES",
        }
    )


def validate_strict_one_second_coordinates_v1(timestamps: Sequence[str]) -> tuple[datetime, ...]:
    """Fixture-safe preflight; production use requires the approved time binding."""
    parsed = tuple(datetime.fromisoformat(value) for value in timestamps)
    if not parsed:
        raise DG05ProductionChainError("EMPTY_TIMESTAMP_VECTOR")
    for previous, current in zip(parsed, parsed[1:]):
        delta = (current - previous).total_seconds()
        if delta == 0:
            raise DG05ProductionChainError("DUPLICATE_TIMESTAMP_BINDING_REQUIRED")
        if delta != 1:
            raise DG05ProductionChainError("NON_UNIT_TIMESTAMP_GAP_BINDING_REQUIRED")
    return parsed


def scenario_hit_any_interval_v1(
    *, alarm_timestamps: Sequence[str], closed_intervals: Sequence[Sequence[str]]
) -> bool:
    """Frozen primary rule: one scenario, one hit at most, any interval."""
    alarms = tuple(datetime.fromisoformat(value) for value in alarm_timestamps)
    intervals = tuple((datetime.fromisoformat(value[0]), datetime.fromisoformat(value[1])) for value in closed_intervals)
    if not intervals or any(start > end for start, end in intervals):
        raise DG05ProductionChainError("VALID_CLOSED_INTERVALS_REQUIRED")
    return any(start <= alarm <= end for alarm in alarms for start, end in intervals)


def derive_runtime_census_strict_v1(traces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Require measured per-Rule evidence; never convert absence to zero."""
    if not traces:
        raise DG05ProductionChainError("EVIDENCE_MISSING:RUNTIME_TRACES")
    totals = {field: 0 for field in ("opportunities", "pass", "fail", "abstain", "system_errors")}
    configured: set[str] = set()
    formed: set[str] = set()
    evaluated: set[str] = set()
    alarming: set[str] = set()
    sources = {"configured": set(), "formed": set(), "evaluated": set(), "alarming": set()}
    episodes = 0
    file_ids: set[str] = set()
    rule_sources: dict[str, str] = {}
    for trace in traces:
        per_rule = trace.get("per_rule_runtime")
        alarm_rows = trace.get("rule_alarm_rows")
        file_id = trace.get("file_id")
        if type(per_rule) is not list or not per_rule or type(alarm_rows) is not list or type(file_id) is not str or not file_id:
            raise DG05ProductionChainError("EVIDENCE_MISSING:RUNTIME_PER_RULE_OR_ALARM_ROWS")
        if file_id in file_ids:
            raise DG05ProductionChainError("DUPLICATE_RUNTIME_FILE_ID")
        file_ids.add(file_id)
        if any(type(row) is not int or row < 0 for row in alarm_rows) or alarm_rows != sorted(set(alarm_rows)):
            raise DG05ProductionChainError("INVALID_RULE_ALARM_ROWS")
        episodes += sum(index == 0 or alarm_rows[index - 1] + 1 != row for index, row in enumerate(alarm_rows))
        for field in totals:
            if type(trace.get(field)) is not int or isinstance(trace[field], bool) or trace[field] < 0:
                raise DG05ProductionChainError("INVALID_RUNTIME_COUNT")
            totals[field] += trace[field]
        if trace["opportunities"] != trace["pass"] + trace["fail"] + trace["abstain"] + trace["system_errors"]:
            raise DG05ProductionChainError("RUNTIME_OUTCOME_CENSUS_MISMATCH")
        if len(alarm_rows) != trace["fail"]:
            raise DG05ProductionChainError("RUNTIME_ALARM_FAIL_COUNT_MISMATCH")
        per_rule_sums = {field: 0 for field in totals}
        local_rule_ids: set[str] = set()
        for row in per_rule:
            required = {"rule_id", "source_id", "opportunities", "pass", "fail", "abstain", "system_errors"}
            if type(row) is not dict or set(row) != required:
                raise DG05ProductionChainError("PER_RULE_RUNTIME_SCHEMA_REQUIRED")
            rule_id, source_id = str(row["rule_id"]), str(row["source_id"])
            if not rule_id or not source_id or rule_id in local_rule_ids:
                raise DG05ProductionChainError("UNIQUE_PER_RULE_RUNTIME_IDENTITY_REQUIRED")
            local_rule_ids.add(rule_id)
            if any(type(row[field]) is not int or isinstance(row[field], bool) or row[field] < 0 for field in totals):
                raise DG05ProductionChainError("INVALID_PER_RULE_RUNTIME_COUNT")
            if row["opportunities"] != row["pass"] + row["fail"] + row["abstain"] + row["system_errors"]:
                raise DG05ProductionChainError("PER_RULE_OUTCOME_CENSUS_MISMATCH")
            for field in totals:
                per_rule_sums[field] += row[field]
            if rule_id in rule_sources and rule_sources[rule_id] != source_id:
                raise DG05ProductionChainError("RULE_SOURCE_IDENTITY_CONFLICT")
            rule_sources[rule_id] = source_id
            configured.add(rule_id)
            sources["configured"].add(source_id)
            if row["opportunities"] > 0:
                formed.add(rule_id)
                sources["formed"].add(source_id)
            if row["pass"] + row["fail"] > 0:
                evaluated.add(rule_id)
                sources["evaluated"].add(source_id)
            if row["fail"] > 0:
                alarming.add(rule_id)
                sources["alarming"].add(source_id)
        if any(per_rule_sums[field] != trace[field] for field in totals):
            raise DG05ProductionChainError("AGGREGATE_PER_RULE_RUNTIME_MISMATCH")
    return {
        **totals,
        "configured_rules": sorted(configured),
        "formed_rules": sorted(formed),
        "evaluated_rules": sorted(evaluated),
        "alarming_rules": sorted(alarming),
        "configured_source_identities": sorted(sources["configured"]),
        "formed_source_identities": sorted(sources["formed"]),
        "evaluated_source_identities": sorted(sources["evaluated"]),
        "alarming_source_identities": sorted(sources["alarming"]),
        "rule_alarm_episodes": episodes,
    }


__all__ = [
    "DG05ProductionChainError",
    "REQUIRED_IMPLEMENTATION_ROLES_V1",
    "REQUIRED_NESTED_AUTHORITY_ROLES_V1",
    "ProductionReleaseImplementationV1",
    "build_production_release_manifest_v1",
    "initialize_production_release_v1",
    "launch_custodian_fresh_process_v2",
    "validate_strict_one_second_coordinates_v1",
    "scenario_hit_any_interval_v1",
    "derive_runtime_census_strict_v1",
]
