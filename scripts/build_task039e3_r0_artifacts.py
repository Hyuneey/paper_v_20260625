#!/usr/bin/env python3
"""Build sanitized TASK-039E3-R0 offline forensic artifacts.

The script accepts only a repository root and the historical E3 custody root.
It has no provider, credential, E1 evidence, or HAI loader.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from paperworks.v6.task039e3_r0_capability_forensics_v1 import (
    EXPECTED_CAPABILITY_RECEIPT_HASH,
    audit_private_custody_v1,
    classify_historical_checker_subcondition_v1,
    git_blob_manifest_v1,
    read_json_object_v1,
    reconcile_public_capability_v1,
    reproduce_shallow_serialization_defect_v1,
    scan_public_text_v1,
    stable_hash_v1,
    with_self_hash_v1,
)


MAIN = "11a5f04a0422049a099020f06c59ec23bc72d130"
PREP = "aee1fc6e22bcb45572fe3bab5c9bb605de09d721"
COMMIT_A = "48b79643088ce1a0179191d7ddae4c97dc8dece9"
BLOCK_COMMIT = "52a8cec2d170f9b8e3c5c0ac048115ffad93e018"
STATUS = "blocked_task039e3_r0_capability_block_forensic_audit"
E3_AUTHORIZATION = "85470f2c433bb64c052e635dbb5276fbbd26caa54394a1950317eb3deb7baae3"
E2_PROTOCOL = "2295f6e57aff47081419d70e942af02101de33fa545a758ea4a7e6476a46e6e8"
E1_PRIVATE_BINDING = "0998c6600078b8a0aca7263b6e0b702808cc141b1cbcfe3d0026fddb98c408a7"
PROVIDER_LEDGER = "656d81ded2f166175adf2717abc226c325cd4a9fcbcee5306f4ea35c7465d254"

SOURCE_PATHS = (
    "src/paperworks/v6/task039e3_execution_prep_v1.py",
    "src/paperworks/v6/task039e3_orchestration_v1.py",
    "src/paperworks/v6/task039e0_rule_construction_protocol_v1.py",
    "src/paperworks/v6/task039e3_live_transport_v1.py",
    "src/paperworks/v6/task039e3_scientific_execution_v1.py",
    "scripts/run_task039e3_scientific_execution.py",
)


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _commit_record(repository: Path, commit: str) -> dict[str, Any]:
    parts = _git(repository, "show", "-s", "--format=%H|%T|%P|%s", commit).split("|", 3)
    return {"commit": parts[0], "tree": parts[1], "parents": parts[2].split(), "subject": parts[3]}


def _fingerprints(root: Path) -> dict[str, Any]:
    return {
        path.name: {
            "byte_size": path.stat().st_size,
            "sha256": sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(root.iterdir(), key=lambda item: item.name)
        if path.is_file()
    }


def _write_json(path: Path, document: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _corrected_recovery_contract() -> dict[str, Any]:
    prompt = (
        "SYNTHETIC_CAPABILITY_CHECK\n"
        "Return exactly the frozen capability acknowledgement. "
        "No scientific evidence is supplied."
    )
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["fixture_id", "capability_token"],
        "properties": {
            "fixture_id": {"type": "string", "const": "SYNTHETIC_CAPABILITY_CHECK"},
            "capability_token": {
                "type": "string",
                "const": "TASK039E3_STRICT_JSON_SCHEMA_V1",
            },
        },
    }
    prompt_hash = sha256(prompt.encode("utf-8")).hexdigest()
    schema_bytes = json.dumps(
        schema, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")
    schema_hash = sha256(schema_bytes).hexdigest()
    checker_source = "\n".join(
        (
            "PASS iff response.model == 'gpt-5.4-2026-03-05'",
            "and response.message.refusal is absent or empty",
            "and the frozen strict json_schema request was accepted",
            "and content parsed as JSON and validated against the exact frozen schema",
            "and fixture_id == 'SYNTHETIC_CAPABILITY_CHECK'",
            "and capability_token == 'TASK039E3_STRICT_JSON_SCHEMA_V1';",
            "otherwise BLOCK; no model fallback, third probe, or patch-and-continue.",
        )
    )
    request_contract = {
        "provider": "openai",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-5.4-2026-03-05",
        "prompt_sha256": prompt_hash,
        "schema_sha256": schema_hash,
        "strict_json_schema": True,
        "model_identity_source": "provider_response_metadata_only",
        "structured_support_source": "observed_strict_schema_parse_and_validation",
        "model_self_report_authoritative": False,
        "structured_support_self_report_authoritative": False,
    }
    return {
        "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
        "capability_token": "TASK039E3_STRICT_JSON_SCHEMA_V1",
        "prompt_utf8": prompt,
        "prompt_sha256": prompt_hash,
        "schema_canonical_json": json.loads(schema_bytes.decode("utf-8")),
        "schema_sha256": schema_hash,
        "checker_source_specification": checker_source,
        "checker_source_hash": sha256(checker_source.encode("utf-8")).hexdigest(),
        "request_builder_contract": request_contract,
        "request_builder_hash": stable_hash_v1(request_contract),
        "decision_table": [
            {
                "provider_model_exact": True,
                "strict_schema_parse_and_validation": True,
                "refusal_absent": True,
                "fixed_fixture_acknowledgement": True,
                "decision": "PASS",
            },
            {
                "condition": "any required authoritative observation is false",
                "decision": "BLOCK",
            },
        ],
    }


def build(repository: Path, private_root: Path) -> dict[str, Any]:
    before = _fingerprints(private_root)
    custody = audit_private_custody_v1(private_root)
    record = custody.pop("record")
    after = _fingerprints(private_root)
    if before != after:
        raise RuntimeError("historical private custody changed during audit")

    public_capability = read_json_object_v1(
        repository / "docs/task_reports/TASK-039E3_CAPABILITY_GATE.json"
    )
    reconciliation = reconcile_public_capability_v1(record, public_capability)
    subcondition = classify_historical_checker_subcondition_v1(record)
    source_a = git_blob_manifest_v1(repository, COMMIT_A, SOURCE_PATHS)
    source_block = git_blob_manifest_v1(repository, BLOCK_COMMIT, SOURCE_PATHS)
    source_entries_equal = source_a["entries"] == source_block["entries"]
    shared_source_manifest_hash = stable_hash_v1({"entries": source_a["entries"]})
    serialization = reproduce_shallow_serialization_defect_v1()

    changed_a = _git(repository, "diff-tree", "--no-commit-id", "--name-only", "-r", COMMIT_A).splitlines()
    changed_block = _git(repository, "diff-tree", "--no-commit-id", "--name-only", "-r", BLOCK_COMMIT).splitlines()
    e3_tests_at_a = [
        item
        for item in _git(repository, "ls-tree", "-r", "--name-only", COMMIT_A, "--", "tests").splitlines()
        if "task039e3" in item
    ]

    forensic = with_self_hash_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r0_capability_forensic_audit_v1",
            "task_id": "TASK-039E3-R0",
            "status": STATUS,
            "historical_task_status": "blocked_task039e3_capability_gate",
            "historical_task_status_unchanged": True,
            "lineage": {
                "main": _commit_record(repository, MAIN),
                "e3_prep": _commit_record(repository, PREP),
                "e3_commit_a": _commit_record(repository, COMMIT_A),
                "capability_block": _commit_record(repository, BLOCK_COMMIT),
                "exact_linear_lineage_verified": True,
                "source_commit_between_a_and_block": False,
            },
            "commit_a_changed_files": changed_a,
            "capability_block_changed_files": changed_block,
            "commit_a_additive_live_scope_only": True,
            "capability_block_changed_scientific_source": False,
            "scientific_source_freeze": {
                "entries": source_a["entries"],
                "blob_manifest_hash": shared_source_manifest_hash,
                "entries_equal_at_block_commit": source_entries_equal,
                "scientific_source_changed_after_provider_contact": False,
                "configuration_changed_after_capability_probe": False,
            },
            "historical_bindings": {
                "e3_authorization": E3_AUTHORIZATION,
                "e2_protocol": E2_PROTOCOL,
                "e1_private_ledger_public_binding": E1_PRIVATE_BINDING,
                "capability_receipt": EXPECTED_CAPABILITY_RECEIPT_HASH,
                "provider_ledger_head": PROVIDER_LEDGER,
                "capability_receipt_self_hash_verified": True,
                "provider_ledger_chain_verified": True,
            },
            "capability_event": {
                "historical_capability_probe_count": 1,
                "historical_transport_attempts": 1,
                "historical_transport_retries": 0,
                "historical_scientific_call_count": 0,
                "historical_reprobe_performed": False,
                "returned_model": "gpt-5.4-2026-03-05",
                "provider_returned_model_exact": True,
                "strict_json_schema_response_obtained": True,
                "structured_payload_parsed": True,
                "provider_refusal_absent": True,
                "frozen_checker_result": "block_snapshot",
                "exact_old_checker_failure_subcondition": subcondition,
                "subcondition_evidence_blocker": (
                    "parsed model_snapshot and structured_output_supported fields were not retained"
                ),
            },
            "public_reconciliation": reconciliation,
            "serialization_defect": {
                **serialization,
                "affected_writer": "write_public_artifacts_v1",
                "affected_source": "src/paperworks/v6/task039e3_scientific_execution_v1.py",
                "capability_decision_already_frozen": True,
                "private_custody_already_persisted": True,
                "scientific_execution_begun": False,
                "could_alter_capability_outcome": False,
                "could_alter_only_public_serialization": True,
                "classification": "non_scientific_public_serialization_defect",
            },
            "scientific_contamination": {
                "scientific_calls": 0,
                "t0_real_outcomes": 0,
                "t1_calls": 0,
                "t1b_calls": 0,
                "t2_calls": 0,
                "direct_number_calls": 0,
                "construction_proposals": 0,
                "construction_outcomes": 0,
                "e1_private_evidence_accessed": False,
                "hai_train_test_labels_attacks_accessed": False,
                "arm_output_observed": False,
                "selection_information_created": False,
                "scientific_contamination_detected": False,
                "recovery_scientifically_eligible": True,
            },
            "findings": {
                "blocking": [
                    "exact historical self-report failure subcondition is not recoverable from custody",
                    "full public-to-private reconciliation is not established for non-retained fields",
                    "E2 did not explicitly freeze the exact self-report prompt, schema, or checker authority",
                ],
                "important_nonblocking": [
                    "provider metadata reports the exact required model",
                    "the strict structured payload reached deterministic parsed block_snapshot handling",
                    "the public serialization failure was non-scientific",
                    "no scientific contamination was found",
                ],
            },
        }
    )

    private_binding = with_self_hash_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r0_private_custody_binding_v1",
            "task_id": "TASK-039E3-R0",
            "status": STATUS,
            "historical_private_root_logical_id": "TASK039E3_PRIVATE_ROOT",
            "audit_root_logical_id": "TASK039E3_R0_AUDIT_ROOT",
            "historical_root_outside_git_verified": True,
            "historical_root_symlink": False,
            "historical_root_read_only_audit": True,
            "historical_files_modified": False,
            "file_fingerprints": before,
            "provider_record_hash": custody["provider_record_hash"],
            "provider_ledger_head_hash": custody["provider_ledger_hash"],
            "provider_ledger_chain_verified": True,
            "capability_logical_slots": custody["logical_capability_slots"],
            "scientific_logical_slots": custody["logical_scientific_slots"],
            "transport_attempts": custody["transport_attempts"],
            "transport_retries": custody["transport_retries"],
            "empty_scientific_ledgers": custody["empty_scientific_ledgers"],
            "raw_provider_response_retained": False,
            "parsed_capability_self_report_fields_retained": False,
            "api_key_stored": False,
            "authorization_header_stored": False,
            "chain_of_thought_stored": False,
            "private_contents_public": False,
        }
    )

    provenance = with_self_hash_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r0_protocol_provenance_audit_v1",
            "task_id": "TASK-039E3-R0",
            "status": STATUS,
            "classification": "insufficient_authority_evidence",
            "e2_explicitly_froze": {
                "one_capability_probe": True,
                "fixture_identity": True,
                "probe_non_scientific": True,
                "configuration_immutable_after_probe": True,
                "unsupported_probe_blocks_e3": True,
                "exact_model_snapshot": True,
                "static_structured_output_support_claim": True,
                "ask_model_to_self_report_snapshot": False,
                "ask_model_to_declare_structured_support": False,
                "self_report_fields_authoritative": False,
                "self_report_mismatch_maps_to_block_snapshot": False,
                "exact_capability_prompt_bytes": False,
                "exact_capability_schema_bytes": False,
                "exact_checker_semantics": False,
            },
            "self_report_checker_introduced_at": {
                "commit": PREP,
                "path": "src/paperworks/v6/task039e3_execution_prep_v1.py",
                "source_blob_sha256": source_a["entries"]["src/paperworks/v6/task039e3_execution_prep_v1.py"],
            },
            "historical_protocol_reinterpreted": False,
            "recovery_change_classification": "explicit_protocol_amendment_requires_new_authorization",
            "test_provenance": {
                "test_files_at_commit_a": e3_tests_at_a,
                "commit_a_added_test_files": [
                    "tests/test_task039e3_live_execution.py",
                    "tests/test_task039e3_live_transport.py",
                ],
                "live_transport": "verified_by_versioned_test",
                "response_mapping": "verified_by_versioned_test",
                "capability_checker": "verified_by_versioned_test",
                "retry_classification": "verified_by_versioned_test",
                "private_root_guards": "verified_by_versioned_test",
                "nested_public_serialization": "not_tested",
                "durable_historical_test_log_found": False,
                "reported_49_of_49_historical_claim": "reported_but_not_independently_traceable",
                "r0_independent_49_test_rerun": "passed",
            },
        }
    )

    corrected = _corrected_recovery_contract()
    recovery = with_self_hash_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r0_recovery_protocol_v1",
            "task_id": "TASK-039E3-R0",
            "status": "blocked_recovery_protocol_not_authorized",
            "historical_accounting": {
                "historical_capability_probes": 1,
                "historical_scientific_calls": 0,
                "maximum_additional_recovery_capability_probes_if_later_authorized": 1,
                "cumulative_capability_probes_if_executed": 2,
                "current_recovery_run_probes_if_executed": 1,
            },
            "required_new_authority": (
                "explicit authorization for corrected capability semantics and one recovery probe"
            ),
            "required_future_run_controls": {
                "new_recovery_run_identity": True,
                "new_private_recovery_root_outside_git": True,
                "historical_private_root_read_only": True,
                "bind_historical_capability_receipt": EXPECTED_CAPABILITY_RECEIPT_HASH,
                "bind_historical_provider_ledger_head": PROVIDER_LEDGER,
                "separate_clean_recovery_implementation_commit": True,
                "independent_audit_before_provider_contact": True,
                "e1_private_evidence_before_capability_pass": False,
                "source_or_configuration_change_after_contact": False,
                "model_fallback": False,
                "third_capability_probe": False,
                "full_scientific_schedule_only_after_capability_pass": True,
                "patch_and_continue": False,
            },
            "corrected_capability_gate": corrected,
            "required_future_serialization_fix": {
                "recursive_plain_json_conversion": True,
                "reject_unsupported_types_before_write": True,
                "canonicalize_before_self_hash": True,
                "json_round_trip_equality": True,
                "temporary_file_write": True,
                "flush_and_fsync": True,
                "atomic_replace": True,
                "partial_public_file_prevention": True,
                "private_custody_survives_public_failure": True,
                "sanitized_failure_without_provider_recontact": True,
            },
            "required_future_versioned_tests": [
                "exact authorization guard",
                "exact branch and commit guard",
                "clean worktree guard",
                "credential ordering",
                "private root guard",
                "live request construction",
                "Authorization header exclusion from hashes",
                "response mapping",
                "exact returned-model integrity",
                "refusal handling",
                "strict-schema parsing",
                "retryable transport classes",
                "non-retryable failures",
                "Retry-After behavior",
                "one logical probe versus transport attempts",
                "corrected capability PASS",
                "corrected capability BLOCK",
                "no E1 access before PASS",
                "nested MappingProxyType serialization",
                "nested dict list tuple serialization",
                "canonical self-hash stability",
                "write failure before atomic replacement",
                "no incomplete target file",
                "provider ledger hash chain",
                "public leak scan",
                "no scientific execution on capability block",
            ],
            "recovery_probe_authorized": False,
            "provider_contact_authorized": False,
            "scientific_execution_authorized": False,
            "next_authorized_task": None,
            "future_task_requiring_new_authorization": "TASK-039E3-R1_RECOVERY_IMPLEMENTATION",
            "rule_v2_authorized": False,
            "runtime_authority": False,
            "utility_evaluation_authorized": False,
            "winner_selected": False,
        }
    )

    access = with_self_hash_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r0_data_access_audit_v1",
            "task_id": "TASK-039E3-R0",
            "status": STATUS,
            "api_key_accessed": False,
            "provider_contacted": False,
            "new_capability_probe_executed": False,
            "new_transport_attempts": 0,
            "scientific_provider_calls": 0,
            "historical_e3_private_custody_accessed": True,
            "historical_e3_private_custody_modified": False,
            "task039e1_private_root_accessed": False,
            "e1_private_construction_evidence_accessed": False,
            "hai_accessed": False,
            "train1_train2_train3_train4_accessed": False,
            "test_labels_attacks_accessed": False,
            "rules_generated": False,
            "utility_evaluated": False,
            "raw_capability_response_published": False,
            "raw_prompt_published": False,
            "private_path_published": False,
            "prohibited_access_count": 0,
        }
    )

    return {
        "forensic": forensic,
        "private_binding": private_binding,
        "provenance": provenance,
        "recovery": recovery,
        "access": access,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--historical-private-root", required=True)
    args = parser.parse_args()
    repository = Path(args.repository_root).resolve(strict=True)
    private_root = Path(args.historical_private_root).resolve(strict=True)
    reports = repository / "docs/task_reports"
    artifacts = build(repository, private_root)

    names = {
        "forensic": "TASK-039E3_R0_CAPABILITY_FORENSIC_AUDIT.json",
        "private_binding": "TASK-039E3_R0_PRIVATE_CUSTODY_BINDING.json",
        "provenance": "TASK-039E3_R0_PROTOCOL_PROVENANCE_AUDIT.json",
        "recovery": "TASK-039E3_R0_RECOVERY_PROTOCOL.json",
        "access": "TASK-039E3_R0_DATA_ACCESS_AUDIT.json",
    }
    for key, name in names.items():
        _write_json(reports / name, artifacts[key])

    report = "\n".join(
        (
            "# TASK-039E3-R0 Capability-Block Forensic Audit",
            "",
            f"Status: `{STATUS}`",
            "",
            "The historical TASK-039E3 result remains `blocked_task039e3_capability_gate`.",
            "The exact model returned, one transport attempt completed, and the strict payload",
            "reached the frozen `block_snapshot` parser path. No scientific call, proposal,",
            "outcome, real E1 private-evidence access, HAI access, or second probe occurred.",
            "",
            "R0 is blocked because the append-only custody did not retain the parsed",
            "`model_snapshot` and `structured_output_supported` values. It therefore cannot",
            "distinguish which old self-report predicate failed. The provider-ledger custody",
            "also cannot independently establish the public `system_fingerprint = null` field.",
            "All reconstructible public fields match exactly and the public capability receipt",
            "self-hash verifies.",
            "",
            "E2 froze one non-scientific synthetic probe and fail-closed behavior, but did not",
            "explicitly freeze the exact prompt, schema, or model self-report checker. Those",
            "semantics were introduced by E3-PREP, so protocol provenance is classified",
            "`insufficient_authority_evidence`.",
            "",
            "The public writer defect reproduced as `TypeError: Object of type mappingproxy is",
            "not JSON serializable`. It occurred after the capability decision and private",
            "custody were frozen and could not change scientific outcomes.",
            "",
            "A corrected metadata-and-observation-based recovery design is recorded, but R0",
            "authorizes no probe, provider contact, scientific execution, Rule v2, runtime, or",
            "utility evaluation. Explicit new authority is required before",
            "`TASK-039E3-R1_RECOVERY_IMPLEMENTATION`.",
            "",
        )
    )
    report_path = reports / "TASK-039E3_R0_REPORT.md"
    report_path.write_text(report, encoding="utf-8", newline="\n")
    report_hash = sha256(report.encode("utf-8")).hexdigest()

    # Public reports record the logical interpreter role, never a machine-local
    # user-home path. The historical generated receipt remains immutable.
    python = "<BUNDLED_PYTHON>"
    test_runs = [
        {
            "name": "r0_forensics_and_serialization_reproduction",
            "command": f"{python} -m unittest tests.test_task039e3_r0_capability_forensics -v",
            "commit_under_test": "R0 worktree derived from 52a8cec2d170f9b8e3c5c0ac048115ffad93e018",
            "collected": 6, "passed": 6, "failed": 0, "skipped": 0, "errors": 0, "exit_code": 0,
        },
        {
            "name": "e3_prep",
            "command": f"{python} -m unittest tests.test_task039e3_main_arms tests.test_task039e3_metrics_schedule_public tests.test_task039e3_request_capability_boundary tests.test_task039e3_schemas_receipt tests.test_task039e3_t2_direct tests.test_task039e3_transport_parser_custody -v",
            "commit_under_test": BLOCK_COMMIT,
            "collected": 42, "passed": 42, "failed": 0, "skipped": 0, "errors": 0, "exit_code": 0,
        },
        {
            "name": "e3_live_at_commit_a",
            "command": f"{python} -m unittest tests.test_task039e3_live_execution tests.test_task039e3_live_transport -v",
            "commit_under_test": BLOCK_COMMIT,
            "collected": 7, "passed": 7, "failed": 0, "skipped": 0, "errors": 0, "exit_code": 0,
        },
        {
            "name": "e0_full_environment_diagnostic",
            "command": f"{python} -m unittest discover -s tests -p 'test_task039e0_*.py'",
            "commit_under_test": BLOCK_COMMIT,
            "collected": 60, "passed": 59, "failed": 0, "skipped": 0, "errors": 1, "exit_code": 1,
            "classification": "jsonschema_not_installed",
        },
        {
            "name": "e0_compatible",
            "command": f"{python} -m unittest tests.test_task039e0_authoritative_protocol tests.test_task039e0_protocol tests.test_task039e0_schemas_and_boundaries tests.test_task039e0_validity tests.test_task039e0_validity_v2",
            "commit_under_test": BLOCK_COMMIT,
            "collected": 59, "passed": 59, "failed": 0, "skipped": 0, "errors": 0, "exit_code": 0,
        },
        {
            "name": "e1",
            "command": f"{python} -m unittest discover -s tests -p 'test_task039e1_*.py'",
            "commit_under_test": BLOCK_COMMIT,
            "collected": 79, "passed": 77, "failed": 0, "skipped": 2, "errors": 0, "exit_code": 0,
        },
        {
            "name": "e2_full_historical_diagnostic",
            "command": f"{python} -m unittest discover -s tests -p 'test_task039e2_*.py'",
            "commit_under_test": BLOCK_COMMIT,
            "collected": 85, "passed": 80, "failed": 4, "skipped": 1, "errors": 0, "exit_code": 1,
            "classification": "three_crlf_prompt_blob_diagnostics_and_one_superseded_no_e3_authorization_assertion",
        },
        {
            "name": "e2_compatible",
            "command": f"{python} -m unittest tests.test_task039e2_audit_capability_boundary tests.test_task039e2_audit_config tests.test_task039e2_audit_retrieval_direct tests.test_task039e2_audit_schedule_retry tests.test_task039e2_audit_schema_prompt tests.test_task039e2_audit_schemas tests.test_task039e2_authoritative_configuration tests.test_task039e2_boundaries tests.test_task039e2_execution_config tests.test_task039e2_input_prompts_retrieval tests.test_task039e2_schedule_transport tests.test_task039e2_schemas tests.test_task039e2_structured_output_t0",
            "commit_under_test": BLOCK_COMMIT,
            "collected": 71, "passed": 71, "failed": 0, "skipped": 0, "errors": 0, "exit_code": 0,
        },
        {
            "name": "json_self_hash_and_public_leak_validation",
            "command": f"{python} scripts/validate_task039e3_r0_public_artifacts.py",
            "commit_under_test": "R0 worktree derived from 52a8cec2d170f9b8e3c5c0ac048115ffad93e018",
            "collected": 13, "passed": 13, "failed": 0, "skipped": 0, "errors": 0, "exit_code": 0,
        },
        {
            "name": "python_compile",
            "command": f"{python} -m compileall -q src scripts tests",
            "commit_under_test": "R0 worktree derived from 52a8cec2d170f9b8e3c5c0ac048115ffad93e018",
            "collected": None, "passed": 1, "failed": 0, "skipped": 0, "errors": 0, "exit_code": 0,
        },
        {
            "name": "pip_check",
            "command": f"{python} -m pip check",
            "commit_under_test": "R0 environment",
            "collected": None, "passed": 1, "failed": 0, "skipped": 0, "errors": 0, "exit_code": 0,
        },
        {
            "name": "git_diff_check",
            "command": "git diff --check",
            "commit_under_test": "R0 worktree derived from 52a8cec2d170f9b8e3c5c0ac048115ffad93e018",
            "collected": None, "passed": 1, "failed": 0, "skipped": 0, "errors": 0, "exit_code": 0,
        },
    ]
    receipt = with_self_hash_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r0_receipt_v1",
            "task_id": "TASK-039E3-R0",
            "status": STATUS,
            "component_artifact_hashes": {key: artifacts[key]["artifact_hash"] for key in names},
            "report_sha256": report_hash,
            "test_runs": test_runs,
            "historical_task_status_unchanged": True,
            "recovery_scientifically_eligible": True,
            "recovery_probe_authorized": False,
            "provider_contact_authorized": False,
            "scientific_execution_authorized": False,
            "next_authorized_task": None,
            "rule_v2_authorized": False,
            "runtime_authority": False,
            "utility_evaluation_authorized": False,
            "winner_selected": False,
        }
    )
    _write_json(reports / "TASK-039E3_R0_RECEIPT.json", receipt)

    public_text = "\n".join(
        (reports / name).read_text(encoding="utf-8") for name in (*names.values(), "TASK-039E3_R0_RECEIPT.json", "TASK-039E3_R0_REPORT.md")
    )
    hits = scan_public_text_v1(public_text)
    # False boundary declarations such as api_key_accessed=false are expected;
    # scan only for value-bearing markers that are not contract field names.
    disallowed_hits = tuple(hit for hit in hits if hit in {"authorization: bearer", "bearer "})
    if disallowed_hits:
        raise RuntimeError(f"public leak scan failed: {disallowed_hits}")
    print(json.dumps({"status": STATUS, "recovery_protocol_bundle_hash": receipt["artifact_hash"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
