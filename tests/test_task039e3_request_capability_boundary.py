import ast
from dataclasses import replace
import json
from pathlib import Path
import unittest

from paperworks.v6.task039e2_execution_configuration_v1 import (
    render_main_initial_model_content_v1,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    API_KEY_ACCESSED,
    BASE_COMMIT,
    CAPABILITY_PROBE_EXECUTED,
    CREDENTIAL_ACCESSED,
    E0_PROTOCOL_BUNDLE_HASH,
    E1_CONSTRUCTION_EVIDENCE_COHORT_HASH,
    E1_MATERIALIZATION_RESULT_HASH,
    E1_PRIVATE_LEDGER_HASH,
    E3_AUTHORIZATION_HASH,
    FROZEN_E2_BINDING,
    LIVE_PROVIDER_TRANSPORT_ENABLED,
    LLM_CALLED,
    PROVIDER_CONTACTED,
    REAL_E1_PRIVATE_EVIDENCE_ACCESSED,
    REAL_E1_RESULT_ACCESSED,
    REAL_PROPOSAL_GENERATED,
    REAL_T0_GENERATED,
    RULE_V2_AUTHORIZED,
    RUNTIME_AUTHORITY_GRANTED,
    CapabilityProbeRunnerV1,
    FutureLiveRunnerBoundaryV1,
    MockProviderEventV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    TASK039E3PreparationError,
    assert_preparation_boundary_v1,
    build_direct_number_request_v1,
    build_main_request_v1,
    instantiate_live_provider_request_v1,
    open_live_provider_transport_v1,
    read_openai_api_key_v1,
    render_main_construction_input_v1,
    validate_e3_authorization_v1,
)
from task039e3_support import capability_payload, make_evidence


class Task039E3RequestCapabilityBoundaryTests(unittest.TestCase):
    def test_exact_public_e3_authorization_and_lineage_bindings(self) -> None:
        root = Path(__file__).parents[1]
        authorization = json.loads(
            (root / "docs" / "task_reports" / "TASK-039E3_AUTHORIZATION.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(validate_e3_authorization_v1(authorization), E3_AUTHORIZATION_HASH)
        self.assertEqual(BASE_COMMIT, "11a5f04a0422049a099020f06c59ec23bc72d130")
        self.assertEqual(
            authorization["e0_protocol_bundle_hash"], E0_PROTOCOL_BUNDLE_HASH
        )
        self.assertEqual(
            authorization["e1_materialization_result_hash"],
            E1_MATERIALIZATION_RESULT_HASH,
        )
        self.assertEqual(
            authorization["e1_construction_evidence_cohort_hash"],
            E1_CONSTRUCTION_EVIDENCE_COHORT_HASH,
        )
        self.assertEqual(
            authorization["e1_private_ledger_hash"], E1_PRIVATE_LEDGER_HASH
        )
        tampered = dict(authorization)
        tampered["relation_count"] = 41
        with self.assertRaises(TASK039E3PreparationError):
            validate_e3_authorization_v1(tampered)

    def test_exact_frozen_e2_binding(self) -> None:
        binding = FROZEN_E2_BINDING
        self.assertEqual(
            binding.protocol_bundle_hash,
            "2295f6e57aff47081419d70e942af02101de33fa545a758ea4a7e6476a46e6e8",
        )
        self.assertEqual(binding.endpoint, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(binding.exact_model, "gpt-5.4-2026-03-05")
        self.assertEqual(binding.temperature, 0.7)
        self.assertEqual(binding.top_p, 1.0)
        self.assertIsNone(binding.seed)
        self.assertFalse(binding.fallback_allowed)

    def test_request_hash_is_deterministic_and_contains_no_credentials(self) -> None:
        view = make_evidence().render_view()
        first = build_main_request_v1(view)
        second = build_main_request_v1(view)
        self.assertEqual(first.request_hash, second.request_hash)
        serialized = json.dumps(first.to_dict(), sort_keys=True).lower()
        self.assertNotIn("openai_api_key", serialized)
        self.assertNotIn("authorization_header", serialized)
        self.assertNotIn("bearer ", serialized)
        self.assertFalse(first.authorization_header_included)
        self.assertFalse(first.api_key_included)

    def test_renderer_matches_frozen_e2_and_initial_payloads_are_byte_identical(self) -> None:
        view = make_evidence().render_view()
        rendered = render_main_construction_input_v1(view)
        self.assertEqual(
            rendered, render_main_initial_model_content_v1(view.to_dict())
        )
        requests = tuple(build_main_request_v1(view) for _ in range(5))
        self.assertEqual(len({request.model_visible_content_hash for request in requests}), 1)
        self.assertEqual(len({request.request_hash for request in requests}), 1)

    def test_direct_number_request_hides_exact_three_values_and_references(self) -> None:
        evidence = make_evidence()
        request = build_direct_number_request_v1(evidence.render_view())
        content = request.request_body["messages"][0]["content"]
        for binding in evidence.numeric_bindings[:3]:
            self.assertNotIn(str(binding.value), content)
            self.assertNotIn(binding.reference, content)
        self.assertIn("selected_delay_horizon_seconds", content)
        for binding in evidence.numeric_bindings[3:]:
            self.assertIn(binding.numeric_role, content)

    def test_construction_view_rejects_prohibited_scientific_inputs(self) -> None:
        evidence = make_evidence()
        for prohibited in (
            "raw_hai",
            "labels",
            "attacks",
            "utility",
            "candidate_method_performance",
        ):
            with self.subTest(prohibited=prohibited):
                contaminated = replace(
                    evidence,
                    semantic_process_metadata={prohibited: "SYNTHETIC_FORBIDDEN"},
                )
                with self.assertRaises(TASK039E3PreparationError):
                    contaminated.render_view()

    def test_capability_probe_pass_block_snapshot_and_block_malformed(self) -> None:
        cases = (
            (
                MockProviderEventV1("capability_supported", capability_payload()),
                "PASS",
            ),
            (
                MockProviderEventV1(
                    "snapshot_unavailable", capability_payload(model="SYNTHETIC_MISSING")
                ),
                "BLOCK",
            ),
            (MockProviderEventV1("malformed_capability_response"), "BLOCK"),
        )
        for event, expected in cases:
            with self.subTest(expected=expected, scenario=event.scenario):
                ledger = ProviderCallLedgerV1()
                result = CapabilityProbeRunnerV1().run(
                    transport=MockProviderTransportV1((event,)), ledger=ledger
                )
                self.assertEqual(result.state, expected)
                self.assertFalse(result.live_probe_executed)
                self.assertFalse(result.frozen_configuration_modified)
                self.assertEqual(len(ledger.records), 1)
                self.assertFalse(ledger.records[0].slot.scientific)

    def test_live_transport_credential_and_request_paths_are_impossible(self) -> None:
        for function in (
            open_live_provider_transport_v1,
            read_openai_api_key_v1,
            instantiate_live_provider_request_v1,
        ):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TASK039E3PreparationError):
                    function(object())
        boundary = FutureLiveRunnerBoundaryV1()
        self.assertEqual(boundary.exact_authorization_hash, E3_AUTHORIZATION_HASH)
        self.assertFalse(boundary.live_runner_present)
        self.assertFalse(boundary.execution_authorized)

        class UnapprovedTransport:
            def send(self, request):
                raise AssertionError("must fail before transport use")

        from paperworks.v6.task039e3_execution_prep_v1 import (
            ProviderCallSlotV1,
            execute_mock_provider_slot_v1,
        )

        evidence = make_evidence()
        with self.assertRaises(TASK039E3PreparationError):
            execute_mock_provider_slot_v1(
                slot=ProviderCallSlotV1(
                    0, evidence.relation.binding_hash, "T1", 1, True
                ),
                request=build_main_request_v1(evidence.render_view()),
                transport=UnapprovedTransport(),
                ledger=ProviderCallLedgerV1(),
                parse_kind="proposal",
            )

    def test_all_prep_boundaries_remain_false(self) -> None:
        self.assertFalse(LIVE_PROVIDER_TRANSPORT_ENABLED)
        self.assertFalse(REAL_E1_RESULT_ACCESSED)
        self.assertFalse(REAL_E1_PRIVATE_EVIDENCE_ACCESSED)
        self.assertFalse(PROVIDER_CONTACTED)
        self.assertFalse(CREDENTIAL_ACCESSED)
        self.assertFalse(API_KEY_ACCESSED)
        self.assertFalse(CAPABILITY_PROBE_EXECUTED)
        self.assertFalse(LLM_CALLED)
        self.assertFalse(REAL_T0_GENERATED)
        self.assertFalse(REAL_PROPOSAL_GENERATED)
        self.assertFalse(RULE_V2_AUTHORIZED)
        self.assertFalse(RUNTIME_AUTHORITY_GRANTED)
        self.assertEqual(
            assert_preparation_boundary_v1(),
            "passed_task039e3_scientific_execution_preparation",
        )

    def test_execution_module_has_no_network_or_credential_library(self) -> None:
        module_path = (
            Path(__file__).parents[1]
            / "src"
            / "paperworks"
            / "v6"
            / "task039e3_execution_prep_v1.py"
        )
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertTrue({"urllib", "socket", "requests", "httpx", "os"}.isdisjoint(roots))
        self.assertNotIn("--live", source)


if __name__ == "__main__":
    unittest.main()
