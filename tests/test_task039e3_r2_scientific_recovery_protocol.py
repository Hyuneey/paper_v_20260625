from __future__ import annotations

import copy
import hashlib
import io
import json
import unittest
from pathlib import Path
from typing import Any, Mapping

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    canonical_proposal_hash_v1,
)
from paperworks.v6.task039e0_validity_v2 import verify_prepared_rule_proposal_v2
from paperworks.v6.task039e2_execution_configuration_v1 import (
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1,
    MAIN_PROVIDER_SCHEMA_V1,
    ProviderProposalCoreV1,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    DIRECT_NUMBER_PROMPT_HASH,
    DIRECT_NUMBER_SCHEMA_HASH,
    MAIN_PROMPT_HASH,
    T2_FOLLOWUP_PROMPT_HASH,
)
from paperworks.v6 import task039e3_orchestration_v1 as orchestration
from tests.task039e3_support import make_evidence, synthetic_hash, valid_core_document


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
TASK_ID = "TASK-039E3-R2-SCIENTIFIC-RECOVERY-PROTOCOL"
FORENSIC_COMMIT_A = "ede40a2dc1cad07d2125a1b599f115538d1ccf1d"
FORENSIC_COMMIT_B = "12a974eb06999ec35266c73c8665852c072b1a41"
FORENSIC_RECEIPT = "caa4a5b7537aaa62dd83f32253fa00aa9474c6472bdd48b23f16d80c89a15b46"
FORENSIC_BUNDLE = "8c01943ec1ac99ee2021a7e085eeffa45403590ca8f0857d71131ce20369a514"
FAILED_TERMINAL = "871afdea4753ae04594037ebaf973f2bf2963accb258df8b890076aa64cb837c"
CAPABILITY_RECEIPT = "9ee4637da31b585a34eda4bad3b3be1dfa5597396ce1e78ef0564fa53da2b428"
CAPABILITY_HEAD = "e0b449ca96ffbf229954c059780baf8fb115aa79fc5d65802dd19e3a54120471"
MAIN_V1_HASH = "92c628faf78e5ebdcfc3ec2dbeb9daa42b6beff0875cbf226c87c2f2c43cc216"
MAIN_V2_HASH = "bcbc9debc32ec9e4b02d5781c7f8b512023752ccb90f60154648bb5d9de67aa1"
DIRECT_V1_HASH = "b1b91bf27fd191da57984be625a2547e4e5ee96a0aca52535df071af92bfd6ca"


def _load(name: str) -> dict[str, Any]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def _verify_self_hash(document: Mapping[str, Any]) -> None:
    content = {key: value for key, value in document.items() if key != "artifact_hash"}
    assert document["artifact_hash"] == stable_hash_v1(content)


def _validate_basic_schema(instance: Any, schema: Mapping[str, Any], path: str = "$") -> None:
    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(instance, Mapping):
            raise AssertionError(f"{path} is not an object")
        required = set(schema.get("required", ()))
        if not required.issubset(instance):
            raise AssertionError(f"{path} misses required fields")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and not set(instance).issubset(properties):
            raise AssertionError(f"{path} has extra fields")
        for key, value in instance.items():
            if key in properties:
                _validate_basic_schema(value, properties[key], f"{path}.{key}")
    elif expected_type == "array":
        if not isinstance(instance, list):
            raise AssertionError(f"{path} is not an array")
        for index, value in enumerate(instance):
            _validate_basic_schema(value, schema["items"], f"{path}[{index}]")
    elif expected_type == "string":
        if not isinstance(instance, str):
            raise AssertionError(f"{path} is not a string")
    elif expected_type == "integer":
        if isinstance(instance, bool) or not isinstance(instance, int):
            raise AssertionError(f"{path} is not an integer")
    elif expected_type == "number":
        if isinstance(instance, bool) or not isinstance(instance, (int, float)):
            raise AssertionError(f"{path} is not numeric")
    if "enum" in schema and instance not in schema["enum"]:
        raise AssertionError(f"{path} is outside enum")


def _core(document: Mapping[str, Any]) -> ProviderProposalCoreV1:
    return ProviderProposalCoreV1(
        dsl_family=document["dsl_family"],
        relation_identity=document["relation_identity"],
        source=document["source"],
        source_step_direction=document["source_step_direction"],
        target=document["target"],
        target_response_direction=document["target_response_direction"],
        selected_delay_horizon_seconds=document["selected_delay_horizon_seconds"],
        source_threshold_reference=document["source_threshold_reference"],
        source_stability_reference=document["source_stability_reference"],
        target_scale_reference=document["target_scale_reference"],
        window_constant_references=document["window_constant_references"],
        variables=tuple(document["variables"]),
        runtime_logic_family=document["runtime_logic_family"],
    )


def _capture_bounded_error_body(stream: io.BytesIO) -> dict[str, Any]:
    observed = bytearray()
    eof = False
    while len(observed) < 65_537:
        chunk = stream.read(min(8192, 65_537 - len(observed)))
        if not chunk:
            eof = True
            break
        observed.extend(chunk)
    retained = bytes(observed[:65_536])
    truncated = len(observed) > 65_536
    return {
        "retained_length": len(retained),
        "retained_sha256": hashlib.sha256(retained).hexdigest(),
        "full_body_sha256": hashlib.sha256(retained).hexdigest() if eof and not truncated else None,
        "full_body_length_known": eof,
        "truncated": truncated,
    }


class ScientificRecoveryProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema_policy = _load("TASK-039E3_R2_RECOVERY_PROVIDER_SCHEMA_POLICY.json")
        self.schema_v2 = self.schema_policy["recovery_main_provider_schema"]
        self.evidence = make_evidence(1)
        self.valid_document = valid_core_document(self.evidence)

    def test_forensic_authority_and_private_capability_reuse_binding(self) -> None:
        receipt = _load("TASK-039E3_R2_FAILURE_FORENSIC_RECEIPT.json")
        self.assertEqual(receipt["artifact_hash"], FORENSIC_RECEIPT)
        self.assertEqual(receipt["forensic_bundle_hash"], FORENSIC_BUNDLE)
        self.assertEqual(receipt["forensic_audit_commit_a"], FORENSIC_COMMIT_A)
        self.assertEqual(receipt["r2_terminal_failure_artifact_hash"], FAILED_TERMINAL)
        binding = _load("TASK-039E3_R2_RECOVERY_CAPABILITY_REUSE_BINDING.json")
        _verify_self_hash(binding)
        self.assertEqual(binding["capability_receipt_hash"], CAPABILITY_RECEIPT)
        self.assertEqual(binding["capability_provider_ledger_head_hash"], CAPABILITY_HEAD)
        self.assertEqual(binding["gate_status"], "PASS")
        self.assertEqual(binding["returned_model"], "gpt-5.4-2026-03-05")
        self.assertTrue(binding["response_present"])
        self.assertTrue(binding["provider_authored_response"])
        self.assertEqual((binding["transport_attempts"], binding["transport_retries"]), (1, 0))

    def test_schema_v2_is_exact_closed_projection_and_direct_schema_unchanged(self) -> None:
        self.assertEqual(stable_hash_v1(MAIN_PROVIDER_SCHEMA_V1), MAIN_V1_HASH)
        self.assertEqual(stable_hash_v1(self.schema_v2), MAIN_V2_HASH)
        self.assertEqual(stable_hash_v1(DIRECT_NUMBER_PROVIDER_SCHEMA_V1), DIRECT_V1_HASH)
        self.assertEqual(DIRECT_NUMBER_SCHEMA_HASH, DIRECT_V1_HASH)
        self.assertNotIn("$schema", self.schema_v2)
        self.assertFalse(self.schema_v2["additionalProperties"])
        self.assertEqual(set(self.schema_v2["required"]), set(MAIN_PROVIDER_SCHEMA_V1["required"]))
        self.assertFalse(self.schema_v2["properties"]["window_constant_references"]["additionalProperties"])
        serialized = json.dumps(self.schema_v2, sort_keys=True)
        for keyword in ("minLength", "pattern", "minItems", "maxItems", "uniqueItems"):
            self.assertNotIn(keyword, serialized)
        self.assertEqual(self.schema_policy["direct_number_provider_schema_policy"], "UNCHANGED")

    def test_provider_schema_closed_required_and_basic_types(self) -> None:
        _validate_basic_schema(self.valid_document, self.schema_v2)
        for field in self.schema_v2["required"]:
            with self.subTest(missing=field):
                bad = dict(self.valid_document)
                bad.pop(field)
                with self.assertRaises(AssertionError):
                    _validate_basic_schema(bad, self.schema_v2)
        extra = dict(self.valid_document, unsupported=True)
        with self.assertRaises(AssertionError):
            _validate_basic_schema(extra, self.schema_v2)
        bad_window = copy.deepcopy(self.valid_document)
        bad_window["window_constant_references"]["extra"] = synthetic_hash("extra-window")
        with self.assertRaises(AssertionError):
            _validate_basic_schema(bad_window, self.schema_v2)

    def test_relaxed_provider_core_risks_are_rejected_by_project_validity(self) -> None:
        valid = orchestration.wrap_and_verify_core_v1(
            core=_core(self.valid_document), evidence=self.evidence, arm="T1",
            call_number=1, prompt_hash=MAIN_PROMPT_HASH,
        )
        self.assertEqual(valid.validity_result.status, "admissible")
        mutations = {
            "empty_relation": ("relation_identity", ""),
            "empty_source": ("source", ""),
            "wrong_source": ("source", "SYNTHETIC_UNSUPPORTED_SOURCE"),
            "empty_target": ("target", ""),
            "wrong_target": ("target", "SYNTHETIC_UNSUPPORTED_TARGET"),
            "wrong_source_direction": ("source_step_direction", "step_down"),
            "wrong_target_direction": ("target_response_direction", "decrease"),
            "wrong_horizon": ("selected_delay_horizon_seconds", 5),
            "wrong_numeric_reference": ("source_threshold_reference", synthetic_hash("wrong-ref")),
            "duplicate_variables": ("variables", [self.evidence.relation.source, self.evidence.relation.source]),
            "one_variable": ("variables", [self.evidence.relation.source]),
            "three_variables": ("variables", [self.evidence.relation.source, self.evidence.relation.target, "EXTRA"]),
            "unsupported_variable": ("variables", [self.evidence.relation.source, "SYNTHETIC_UNSUPPORTED"]),
        }
        for name, (field, value) in mutations.items():
            with self.subTest(case=name):
                bad = copy.deepcopy(self.valid_document)
                bad[field] = value
                _validate_basic_schema(bad, self.schema_v2)
                result = orchestration.wrap_and_verify_core_v1(
                    core=_core(bad), evidence=self.evidence, arm="T1",
                    call_number=1, prompt_hash=MAIN_PROMPT_HASH,
                )
                self.assertEqual(result.validity_result.status, "rejected")

    def test_local_prevalidation_rejects_relaxed_malformed_references_and_maps(self) -> None:
        malformed_hash = copy.deepcopy(self.valid_document)
        malformed_hash["source_threshold_reference"] = "not-a-hash"
        _validate_basic_schema(malformed_hash, self.schema_v2)
        with self.assertRaises(Exception):
            _core(malformed_hash)
        malformed_window = copy.deepcopy(self.valid_document)
        malformed_window["window_constant_references"].pop(next(iter(malformed_window["window_constant_references"])))
        with self.assertRaises(AssertionError):
            _validate_basic_schema(malformed_window, self.schema_v2)
        wrong_runtime = copy.deepcopy(self.valid_document)
        wrong_runtime["runtime_logic_family"] = "unsupported_runtime"
        with self.assertRaises(AssertionError):
            _validate_basic_schema(wrong_runtime, self.schema_v2)

    def test_project_adversarial_parity_and_authority_preclaims(self) -> None:
        core = _core(self.valid_document)
        provenance = orchestration._provenance(
            evidence=self.evidence, arm="T1", prompt_version="MAIN_INITIAL_PROMPT_V1"
        )
        valid = orchestration._project_proposal_document(
            core=core, evidence=self.evidence, provenance=provenance
        )
        cases = {
            "numeric_literal": ("numeric_literals", [999.0], True),
            "provenance_mismatch": ("construction_provenance_hash", synthetic_hash("wrong-provenance"), True),
            "authority_preclaim": ("runtime_authority_granted", True, True),
            "serialization_hash": ("proposal_hash", "0" * 64, False),
            "prohibited_data": ("prohibited_data_references", ["SEALED_TEST"], True),
            "numeric_origin": ("numeric_origin", "unapproved_origin", True),
            "free_text_runtime": ("free_text_runtime_logic", "execute arbitrary code", True),
        }
        for name, (field, value, rehash) in cases.items():
            with self.subTest(case=name):
                bad = copy.deepcopy(valid)
                bad[field] = value
                if rehash:
                    bad["proposal_hash"] = canonical_proposal_hash_v1(bad)
                result = verify_prepared_rule_proposal_v2(
                    bad,
                    relation=self.evidence.relation,
                    numeric_evidence=self.evidence.numeric_evidence,
                    provenance=provenance,
                    budget=orchestration._BUDGET,
                    allowed_variables=frozenset({self.evidence.relation.source, self.evidence.relation.target}),
                )
                self.assertEqual(result.status, "rejected")

    def test_fresh_cohort_accounting_and_shared_arm_fairness(self) -> None:
        accounting = _load("TASK-039E3_R2_RECOVERY_COHORT_ACCOUNTING_POLICY.json")
        fairness = _load("TASK-039E3_R2_RECOVERY_FAIRNESS_POLICY.json")
        self.assertEqual(accounting["recovery_execution_mode"], "FRESH_FULL_COHORT_RESTART")
        self.assertEqual(accounting["historical_aborted_r2_accounting"]["scientific_logical_calls"], 1)
        self.assertEqual(accounting["recovery_cohort_scientific_logical_calls"], {"minimum": 252, "maximum": 336})
        self.assertEqual(accounting["lifetime_scientific_logical_call_attempts_range"], {"minimum": 253, "maximum": 337})
        self.assertFalse(accounting["prior_t0_reused"])
        self.assertFalse(accounting["prior_failed_t1_reused"])
        self.assertEqual(len(accounting["fresh_cohort_ledgers_required_empty"]), 4)
        self.assertEqual(set(fairness["recovery_main_schema_hash_shared_by"].values()), {MAIN_V2_HASH})
        self.assertEqual(fairness["t1_b_policy"]["calls_per_relation"], 3)
        self.assertEqual(fairness["t2_policy"]["maximum_calls_per_relation"], 3)
        self.assertEqual((fairness["scientific_concurrency"], fairness["scientific_generation_retries"]), (1, 0))

    def test_capability_probe_ceiling_and_authority_graph_are_closed(self) -> None:
        capability = _load("TASK-039E3_R2_RECOVERY_CAPABILITY_REUSE_POLICY.json")
        authority = _load("TASK-039E3_R2_RECOVERY_AUTHORITY_BOUNDARY.json")
        self.assertEqual(capability["recovery_capability_policy"], "REUSE_DURABLE_CORRECTED_CAPABILITY_PASS")
        self.assertEqual(capability["additional_capability_probes"], 0)
        self.assertEqual(capability["cumulative_capability_probes_after_r2r"], 2)
        self.assertFalse(capability["third_capability_probe_authorized"])
        self.assertFalse(capability["diagnostic_provider_call_authorized"])
        self.assertEqual(authority["future_task_graph"], [
            TASK_ID,
            "TASK-039E3-R2R-REQUEST-CONTRACT-REMEDIATION",
            "TASK-039E3-R2R-INDEPENDENT-AUDIT",
            "TASK-039E3-R2R-AUTHORIZATION-FREEZE",
            "TASK-039E3-R2R-SCIENTIFIC-EXECUTION",
        ])
        for field in (
            "provider_contact_authorized", "capability_probe_authorized",
            "scientific_reexecution_authorized", "resume_authorized",
            "rule_v2_authorized", "runtime_authority",
            "utility_evaluation_authorized", "winner_selected",
        ):
            self.assertFalse(authority[field], field)

    def test_http_error_custody_is_bounded_private_and_does_not_change_retry(self) -> None:
        policy = _load("TASK-039E3_R2_RECOVERY_HTTP_ERROR_CUSTODY_POLICY.json")
        bound = policy["bounded_read_algorithm"]
        self.assertEqual((bound["maximum_retained_error_body_bytes"], bound["maximum_error_body_read_bytes"]), (65536, 65537))
        self.assertTrue(bound["never_unbounded_read"])
        self.assertFalse(policy["http400_retry_eligible"])
        self.assertFalse(policy["http_error_custody_changes_retry_semantics"])
        self.assertFalse(policy["http_error_payload_is_scientific_response"])
        separation = policy["response_semantic_separation"]
        self.assertTrue(separation["http_transport_response_received"])
        for field in ("model_completion_response_present", "response_present", "provider_payload_received", "provider_authored_response", "structured_payload_valid"):
            self.assertFalse(separation[field])
        self.assertIn("raw_error_body", policy["public_fields_prohibited"])
        self.assertNotIn("raw_error_body", policy["public_fields_allowed"])

    def test_bounded_http_error_body_oracle_covers_empty_exact_and_truncated(self) -> None:
        cases = (
            (b"", 0, False, True),
            (b'{"error":"synthetic"}', 21, False, True),
            (b"\xff\xfe" * 17, 34, False, True),
            (b"a" * 65_536, 65_536, False, True),
            (b"b" * 65_537, 65_536, True, False),
            (b"c" * 80_000, 65_536, True, False),
        )
        for body, retained, truncated, full_known in cases:
            with self.subTest(length=len(body)):
                result = _capture_bounded_error_body(io.BytesIO(body))
                self.assertEqual(result["retained_length"], retained)
                self.assertEqual(result["truncated"], truncated)
                self.assertEqual(result["full_body_length_known"], full_known)
                self.assertEqual(result["full_body_sha256"] is not None, full_known)

    def test_protocol_artifacts_are_self_hashed_and_prompt_model_policy_unchanged(self) -> None:
        names = (
            "TASK-039E3_R2_SCIENTIFIC_RECOVERY_PROTOCOL.json",
            "TASK-039E3_R2_RECOVERY_CAPABILITY_REUSE_BINDING.json",
            "TASK-039E3_R2_RECOVERY_CAPABILITY_REUSE_POLICY.json",
            "TASK-039E3_R2_RECOVERY_COHORT_ACCOUNTING_POLICY.json",
            "TASK-039E3_R2_RECOVERY_PROVIDER_SCHEMA_POLICY.json",
            "TASK-039E3_R2_RECOVERY_VALIDITY_PARITY_POLICY.json",
            "TASK-039E3_R2_RECOVERY_HTTP_ERROR_CUSTODY_POLICY.json",
            "TASK-039E3_R2_RECOVERY_FAIRNESS_POLICY.json",
            "TASK-039E3_R2_RECOVERY_AUTHORITY_BOUNDARY.json",
        )
        for name in names:
            with self.subTest(name=name):
                document = _load(name)
                _verify_self_hash(document)
                self.assertEqual(document["task_id"], TASK_ID)
        protocol = _load(names[0])
        unchanged = protocol["unchanged_provider_configuration"]
        self.assertEqual(unchanged["main_prompt_hash"], MAIN_PROMPT_HASH)
        self.assertEqual(unchanged["t2_followup_prompt_hash"], T2_FOLLOWUP_PROMPT_HASH)
        self.assertEqual(unchanged["direct_number_prompt_hash"], DIRECT_NUMBER_PROMPT_HASH)
        self.assertEqual(unchanged["model"], "gpt-5.4-2026-03-05")
        self.assertEqual(unchanged["endpoint"], "https://api.openai.com/v1/chat/completions")
        self.assertFalse(protocol["scientific_gate_lowered"])


if __name__ == "__main__":
    unittest.main()
