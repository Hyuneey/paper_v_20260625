from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import paperworks.validation_v2.dg05_execution_closure_v1 as execution_module
import paperworks.validation_v2.dg05_label_custodian_v2 as custodian_module
import paperworks.data.hai_normal_projection_v2 as projection_parser_module
from paperworks.validation_v2.dg05_execution_closure_v1 import (
    PhysicalFileIdentityV2,
    canonical_bytes,
    digest,
    project_attack_feature_file_v1,
    self_hashed,
)
from paperworks.validation_v2.dg05_upstream_lineage_verifier_v2 import UpstreamPanelReplayPathsV2
from paperworks.validation_v2.dg05_upstream_lineage_verifier_v3 import (
    DG05UpstreamVerifierV3Error,
    RootToResultReplayPathsV3,
    _denominator_document,
    _scenario_document,
    reconstruct_metric_primitive_from_roots_v3,
)
from paperworks.validation_v2.multipanel_custody_v1 import (
    FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
    FROZEN_AUTHORITY_SOURCE_COMMIT_V2,
    FROZEN_PANEL_ORDER_V2,
    FrozenPhysicalFileAuthorityV2,
    frozen_feature_allowlist_authorities_v2,
)


H = "a" * 64
G = "b" * 40


def persist(path: Path, value: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value) + b"\n")
    return path


class RootReplayV3Tests(unittest.TestCase):
    def _fixture(self, root: Path, timestamps=None):
        panel = FROZEN_PANEL_ORDER_V2[0]
        allowlist = frozen_feature_allowlist_authorities_v2()[panel]
        projection_impl_hash = sha256(Path(execution_module.__file__).read_bytes()).hexdigest()
        projection_parser_hash = sha256(Path(projection_parser_module.__file__).read_bytes()).hexdigest()
        custodian_impl_hash = sha256(Path(custodian_module.__file__).read_bytes()).hexdigest()
        launcher_path = Path(execution_module.__file__).parents[3] / "scripts" / "run_dg05_label_custodian_v2.py"
        launcher_hash = sha256(launcher_path.read_bytes()).hexdigest()
        scope = self_hashed({
            "schema": "full_process_scope_authority_v1",
            "points": [{"dataset_version": "23.05", "canonical_identity": "P1_FCV01D",
                        "official_process": "P1", "p1_membership": "YES", "evidence_hash": H,
                        "authority_status": "OFFICIAL_EXACT_IDENTITY"}],
            "official_manual_hash": H, "official_schema_hashes": {"23.05": H},
            "source_commit": G, "version_counts": {"23.05": 1},
            "declared_count_discrepancies": [], "official_identity_set_hashes": {},
            "supplemental_authority_hashes": {}, "authority_mode": "SYNTHETIC_REHEARSAL",
        })
        scope_path = persist(root / "scope.json", scope)
        registry = self_hashed({"schema": "normal_burden_source_registry_v2", "components": []})
        registry_path = persist(root / "normal-registry.json", registry)
        release = self_hashed({
            "schema": "dg05_production_release_manifest_v2",
            "executable_version": "DG05_EXECUTABLE_V6",
            "implementation_authorities": [
                {"logical_name": "custodian", "relative_path": "fixture", "byte_hash": custodian_impl_hash},
                {"logical_name": "custodian_process_entrypoint", "relative_path": "fixture", "byte_hash": launcher_hash},
                {"logical_name": "projection_adapter", "relative_path": "fixture", "byte_hash": projection_impl_hash},
                {"logical_name": "projection_parser", "relative_path": "fixture", "byte_hash": projection_parser_hash},
            ],
            "semantic_binding_hash": H,
            "normal_burden_source_registry_hash": registry["self_hash"],
            "nested_authority_hashes": {
                "full_process_scope": scope["self_hash"],
                "p1_custodian": H,
                "attack_file_census": FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
            },
            "source_commit": G,
        })
        release_hash = release["self_hash"]
        release_path = persist(root / "release.json", release)
        timestamps = timestamps or ["2026-01-01T00:00:00", "2026-01-01T00:00:01", "2026-01-01T00:00:02"]
        raw_path = root / "raw.csv"
        header = [allowlist.timestamp_id, *allowlist.feature_ids, "Attack"]
        lines = [",".join(header)]
        lines.extend(",".join([stamp, *(["1.0"] * len(allowlist.feature_ids)), "opaque"]) for stamp in timestamps)
        raw_path.write_text("\n".join(lines) + "\n", encoding="ascii")
        physical_item = PhysicalFileIdentityV2(panel, "F1", sha256(raw_path.read_bytes()).hexdigest(), digest(header), H)
        physical = FrozenPhysicalFileAuthorityV2(
            (physical_item,), FROZEN_ATTACK_FILE_CENSUS_HASH_V2, H, FROZEN_AUTHORITY_SOURCE_COMMIT_V2)
        projection_path = root / "projection.jsonl"
        projection, timestamp = project_attack_feature_file_v1(
            source=raw_path, destination=projection_path, physical_file=physical_item,
            panel_authority=allowlist, file_id="F1", adapter_implementation_hash=projection_impl_hash, source_commit=G)
        physical_path = persist(root / "physical.json", physical.document())
        projection_doc_path = persist(root / "projection-authority.json", projection.document())
        timestamp_doc_path = persist(root / "timestamp-authority.json", timestamp.document())

        manifest = self_hashed({"schema": "global_prediction_manifest_v3",
                                "executable_approval_manifest_hash": release_hash, "receipts": []})
        freeze = self_hashed({"schema": "global_prediction_freeze_v3",
                              "manifest_hash": manifest["self_hash"],
                              "executable_approval_manifest_hash": release_hash})
        manifest_path = persist(root / "manifest.json", manifest)
        freeze_path = persist(root / "freeze.json", freeze)
        source_id = "SYNTHETIC-23.05"
        raw_scenario = {
            "schema": "synthetic_raw_official_scenario_fixture_v2",
            "records": [{
                "panel_id": panel, "dataset_version": "23.05", "file_id": "F1",
                "scenario_id": "S1", "closed_intervals": [[timestamps[0], timestamps[-1]]],
                "attacked_identities": ["P1_FCV01D"], "explicit_affected_processes": [],
            }],
        }
        scenario_source_path = persist(root / "incoming" / "scenario.json", raw_scenario)
        policy = self_hashed({
            "schema": "custodian_resource_policy_authority_v2",
            "input_root": str((root / "incoming").resolve()),
            "output_root": str((root / "outgoing").resolve()),
            "forbidden_roots": [str((root / "predictions").resolve())],
            "approved_sources": [{
                "source_id": source_id, "path": str(scenario_source_path.resolve()),
                "byte_hash": sha256(scenario_source_path.read_bytes()).hexdigest(),
                "official_source_hash": H, "dataset_version": "23.05",
                "source_format": "SYNTHETIC_JSON_V2",
                "adapter_id": "SYNTHETIC_OFFICIAL_SCENARIO_FIXTURE_V2",
            }],
            "executable_manifest_hash": release_hash, "scenario_adapter_implementation_hash": custodian_impl_hash,
            "resource_policy_contract_hash": H, "source_commit": G,
        })
        policy_path = persist(root / "policy.json", policy)
        state_before = self_hashed({"schema": "dg05_production_chain_state_v4", "state": "GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED",
                                    "release_manifest_hash": release_hash, "global_prediction_freeze_hash": freeze["self_hash"],
                                    "authority_mode": "SYNTHETIC_REHEARSAL"})
        token = "opaque-token"
        token_hash = sha256(token.encode()).hexdigest()
        lease = self_hashed({
            "schema": "single_use_label_scenario_lease_v3", "token_hash": token_hash,
            "global_freeze_hash": freeze["self_hash"], "state_hash": state_before["self_hash"],
            "executable_manifest_hash": release_hash, "resource_policy_hash": policy["self_hash"],
            "issue_count": 1, "consume_limit": 1,
        })
        issued = self_hashed({
            "schema": "dg05_production_chain_state_v4", "state": "LABEL_SCENARIO_LEASE_ISSUED",
            "release_manifest_hash": release_hash, "global_prediction_freeze_hash": freeze["self_hash"],
            "authority_mode": "SYNTHETIC_REHEARSAL", "lease_issue_predecessor_hash": state_before["self_hash"],
            "lease_receipt_hash": lease["self_hash"], "lease_token_hash": token_hash,
        })
        issued_path = persist(root / "issued.json", issued)
        binding = {
            "source_id": source_id, "panel_id": panel, "dataset_version": "23.05", "file_id": "F1",
            "physical_file_authority_hash": projection.raw_physical_file_hash,
            "timestamp_authority_hash": timestamp.document()["self_hash"], "official_source_hash": H,
        }
        request = {
            "schema": "isolated_label_scenario_custodian_request_v2", "opaque_lease": token,
            "lease_receipt": lease, "global_freeze_hash": freeze["self_hash"],
            "predecessor_state_hash": issued["self_hash"], "lease_issue_predecessor_hash": state_before["self_hash"],
            "executable_manifest_hash": release_hash, "approved_source_ids": [source_id],
            "approved_output_name": "scenario-output.json", "public_authority_hashes": [H],
            "resource_policy_hash": policy["self_hash"], "allowed_scenario_bindings": [binding],
            "authority_mode": "SYNTHETIC_REHEARSAL", "nominal_counts": {panel: 1},
        }
        request_path = root / "request.json"
        request_path.write_bytes(canonical_bytes(request) + b"\n")
        consumed = self_hashed({
            "schema": "label_scenario_lease_consumed_v2", "issue_receipt_hash": lease["self_hash"],
            "global_freeze_hash": freeze["self_hash"], "predecessor_state_hash": issued["self_hash"],
            "executable_manifest_hash": release_hash, "resource_policy_hash": policy["self_hash"],
            "token_hash": token_hash, "consume_count": 1,
        })
        consumed_path = persist(root / "consumed.json", consumed)
        bound_record = {**raw_scenario["records"][0],
                        "physical_file_authority_hash": projection.raw_physical_file_hash,
                        "timestamp_authority_hash": timestamp.document()["self_hash"],
                        "official_source_hash": H}
        output = self_hashed({
            "schema": "isolated_label_scenario_custodian_output_v2",
            "lease_consumed_hash": consumed["self_hash"], "global_freeze_hash": freeze["self_hash"],
            "predecessor_state_hash": issued["self_hash"], "executable_manifest_hash": release_hash,
            "authority_mode": "SYNTHETIC_REHEARSAL", "resource_policy_hash": policy["self_hash"],
            "scenario_adapter_implementation_hash": custodian_impl_hash,
            "source_receipts": [{"source_id": source_id,
                                 "byte_hash": sha256(scenario_source_path.read_bytes()).hexdigest(),
                                 "official_source_hash": H}],
            "records": [bound_record], "nominal_counts": {panel: 1},
            "allowed_scenario_binding_hash": sha256(canonical_bytes([binding])).hexdigest(),
            "prediction_capability": False,
        })
        output_path = persist(root / "output.json", output)
        invocation = self_hashed({
            "schema": "dg05_fresh_process_custodian_invocation_v1", "launcher_byte_hash": launcher_hash,
            "request_byte_hash": sha256(request_path.read_bytes()).hexdigest(),
            "resource_policy_byte_hash": sha256(policy_path.read_bytes()).hexdigest(),
            "resource_policy_hash": policy["self_hash"], "custodian_implementation_hash": custodian_impl_hash,
            "predecessor_state_hash": issued["self_hash"], "global_freeze_hash": freeze["self_hash"],
            "release_manifest_hash": release_hash, "custodian_pid": 2, "custodian_parent_pid": 1,
            "consume_receipt_hash": consumed["self_hash"], "output_self_hash": output["self_hash"],
            "output_byte_hash": sha256(output_path.read_bytes()).hexdigest(),
            "isolation_mechanism": "FRESH_PROCESS_PLUS_APPLICATION_PATH_CAPABILITY_GUARDS",
            "os_sandbox_claimed": False,
            "coordinator_environment_forwarding": "MINIMAL_ALLOWLIST_NO_PROVIDER_OR_CREDENTIAL_VARIABLES",
        })
        invocation_path = persist(root / "invocation.json", invocation)
        scenario = _scenario_document(output=output, global_freeze_hash=freeze["self_hash"], source_commit=G)
        denominator = _denominator_document(scenario=scenario, scope=scope, p1_custodian_hash=H)
        scenario_path = persist(root / "scenario-authority.json", scenario)
        denominator_path = persist(root / "denominator-authority.json", denominator)
        asserted = self_hashed({"schema": "metric_surface_primitives_v2", "fixture": True})
        asserted_path = persist(root / "asserted.json", asserted)
        intermediate = UpstreamPanelReplayPathsV2(
            manifest_path, freeze_path, scenario_path, denominator_path, {"F1": projection_path},
            {"CELL": persist(root / "predictions" / "cell.json", {"schema": "fixture_prediction"})},
            {}, registry_path, {}, asserted_path)
        paths = RootToResultReplayPathsV3(
            intermediate, release_path, physical_path, {"F1": raw_path}, {"F1": projection_doc_path},
            {"F1": timestamp_doc_path}, {source_id: scenario_source_path}, policy_path,
            request_path, issued_path, consumed_path, invocation_path, output_path, scope_path)
        roots = {
            "release": release_hash,
            "physical": physical.document()["self_hash"], "invocation": invocation["self_hash"],
            "scope": scope["self_hash"], "freeze": freeze["self_hash"], "registry": registry["self_hash"],
        }
        return panel, paths, roots, asserted

    def _run(self, panel, paths, roots, asserted):
        with patch(
            "paperworks.validation_v2.dg05_upstream_lineage_verifier_v3.reconstruct_metric_primitive_from_upstream_v2",
            return_value=asserted,
        ):
            return reconstruct_metric_primitive_from_roots_v3(
                panel_id=panel, paths=paths, expected_release_manifest_hash=roots["release"],
                expected_dec031_binding_hash=H,
                expected_normal_source_registry_hash=roots["registry"],
                expected_global_freeze_hash=roots["freeze"],
                expected_physical_authority_hash=roots["physical"],
                expected_custodian_invocation_hash=roots["invocation"],
                expected_full_process_scope_hash=roots["scope"],
                expected_p1_custodian_hash=H, source_commit=G)

    def _rehash_custodian_chain(
        self, paths, roots, *, mutate_policy=None, mutate_request=None,
        mutate_output=None, mutate_invocation=None,
    ):
        policy = _load_json(paths.custodian_policy_path)
        policy_body = {k: v for k, v in policy.items() if k != "self_hash"}
        if mutate_policy is not None:
            mutate_policy(policy_body)
        policy = self_hashed(policy_body)
        persist(paths.custodian_policy_path, policy)

        request = _load_json(paths.custodian_request_path)
        lease_body = {k: v for k, v in request["lease_receipt"].items() if k != "self_hash"}
        lease_body["resource_policy_hash"] = policy["self_hash"]
        lease = self_hashed(lease_body)
        issued = _load_json(paths.lease_issued_state_path)
        issued = self_hashed({
            **{k: v for k, v in issued.items() if k != "self_hash"},
            "lease_receipt_hash": lease["self_hash"],
        })
        persist(paths.lease_issued_state_path, issued)
        request.update({
            "lease_receipt": lease,
            "resource_policy_hash": policy["self_hash"],
            "predecessor_state_hash": issued["self_hash"],
        })
        if mutate_request is not None:
            mutate_request(request)
        paths.custodian_request_path.write_bytes(canonical_bytes(request) + b"\n")
        consumed = _load_json(paths.lease_consumed_path)
        consumed = self_hashed({
            **{k: v for k, v in consumed.items() if k != "self_hash"},
            "issue_receipt_hash": lease["self_hash"],
            "predecessor_state_hash": issued["self_hash"],
            "resource_policy_hash": policy["self_hash"],
        })
        persist(paths.lease_consumed_path, consumed)
        output = _load_json(paths.custodian_output_path)
        output_body = {
            **{k: v for k, v in output.items() if k != "self_hash"},
            "lease_consumed_hash": consumed["self_hash"],
            "predecessor_state_hash": issued["self_hash"],
            "resource_policy_hash": policy["self_hash"],
            "scenario_adapter_implementation_hash": policy["scenario_adapter_implementation_hash"],
        }
        if mutate_output is not None:
            mutate_output(output_body)
        output = self_hashed(output_body)
        persist(paths.custodian_output_path, output)
        invocation = _load_json(paths.custodian_invocation_path)
        invocation_body = {
            **{k: v for k, v in invocation.items() if k != "self_hash"},
            "request_byte_hash": sha256(paths.custodian_request_path.read_bytes()).hexdigest(),
            "resource_policy_byte_hash": sha256(paths.custodian_policy_path.read_bytes()).hexdigest(),
            "resource_policy_hash": policy["self_hash"],
            "predecessor_state_hash": issued["self_hash"],
            "consume_receipt_hash": consumed["self_hash"],
            "output_self_hash": output["self_hash"],
            "output_byte_hash": sha256(paths.custodian_output_path.read_bytes()).hexdigest(),
        }
        if mutate_invocation is not None:
            mutate_invocation(invocation_body)
        invocation = self_hashed(invocation_body)
        persist(paths.custodian_invocation_path, invocation)
        scenario = _scenario_document(output=output, global_freeze_hash=roots["freeze"], source_commit=G)
        persist(paths.intermediate.scenario_authority_path, scenario)
        scope = _load_json(paths.full_process_scope_path)
        persist(paths.intermediate.denominator_authority_path,
                _denominator_document(scenario=scenario, scope=scope, p1_custodian_hash=H))
        roots["invocation"] = invocation["self_hash"]

    def test_complete_raw_root_replay(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            primitive, flags = self._run(panel, paths, roots, asserted)
            self.assertEqual(primitive, asserted)
            self.assertTrue(all(flags.values()))

    def test_raw_source_projection_disconnect_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            paths.raw_physical_paths["F1"].write_bytes(b"changed\n")
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "RAW_PHYSICAL_SOURCE_BYTE_MISMATCH"):
                self._run(panel, paths, roots, asserted)

    def test_scenario_and_denominator_coherent_rehash_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            scenario = json.loads(paths.intermediate.scenario_authority_path.read_text())
            record = deepcopy(scenario["records"][0])
            record["closed_intervals"] = [["2026-01-01T00:00:01", "2026-01-01T00:00:02"]]
            record = self_hashed({k: v for k, v in record.items() if k != "self_hash"})
            scenario = self_hashed({**{k: v for k, v in scenario.items() if k != "self_hash"}, "records": [record]})
            persist(paths.intermediate.scenario_authority_path, scenario)
            scope = _load_json(paths.full_process_scope_path)
            denominator = _denominator_document(scenario=scenario, scope=scope, p1_custodian_hash=H)
            persist(paths.intermediate.denominator_authority_path, denominator)
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "SCENARIO_ROOT_REPLAY_FAILURE"):
                self._run(panel, paths, roots, asserted)

    def test_denominator_coherent_rehash_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            denominator = _load_json(paths.intermediate.denominator_authority_path)
            record = deepcopy(denominator["records"][0])
            record["primary_status"] = "OUT_OF_SCOPE"
            record = self_hashed({k: v for k, v in record.items() if k != "self_hash"})
            denominator = self_hashed({**{k: v for k, v in denominator.items() if k != "self_hash"}, "records": [record]})
            persist(paths.intermediate.denominator_authority_path, denominator)
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "DENOMINATOR_SCOPE_REPLAY_FAILURE"):
                self._run(panel, paths, roots, asserted)

    def test_raw_scenario_and_invocation_roots_reject_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            paths.raw_scenario_source_paths["SYNTHETIC-23.05"].write_bytes(b"{}\n")
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "RAW_SCENARIO_SOURCE_BYTE_MISMATCH"):
                self._run(panel, paths, roots, asserted)

    def test_coherently_rewritten_lease_state_chain_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            issued = _load_json(paths.lease_issued_state_path)
            issued = self_hashed({
                **{k: v for k, v in issued.items() if k != "self_hash"},
                "state": "COHERENTLY_REWRITTEN_STATE",
            })
            persist(paths.lease_issued_state_path, issued)
            request = _load_json(paths.custodian_request_path)
            request["predecessor_state_hash"] = issued["self_hash"]
            paths.custodian_request_path.write_bytes(canonical_bytes(request) + b"\n")
            consumed = _load_json(paths.lease_consumed_path)
            consumed = self_hashed({
                **{k: v for k, v in consumed.items() if k != "self_hash"},
                "predecessor_state_hash": issued["self_hash"],
            })
            persist(paths.lease_consumed_path, consumed)
            output = _load_json(paths.custodian_output_path)
            output = self_hashed({
                **{k: v for k, v in output.items() if k != "self_hash"},
                "predecessor_state_hash": issued["self_hash"],
                "lease_consumed_hash": consumed["self_hash"],
            })
            persist(paths.custodian_output_path, output)
            invocation = _load_json(paths.custodian_invocation_path)
            invocation = self_hashed({
                **{k: v for k, v in invocation.items() if k != "self_hash"},
                "predecessor_state_hash": issued["self_hash"],
                "request_byte_hash": sha256(paths.custodian_request_path.read_bytes()).hexdigest(),
                "consume_receipt_hash": consumed["self_hash"],
                "output_self_hash": output["self_hash"],
                "output_byte_hash": sha256(paths.custodian_output_path.read_bytes()).hexdigest(),
            })
            persist(paths.custodian_invocation_path, invocation)
            scenario = _scenario_document(output=output, global_freeze_hash=roots["freeze"], source_commit=G)
            persist(paths.intermediate.scenario_authority_path, scenario)
            scope = _load_json(paths.full_process_scope_path)
            persist(paths.intermediate.denominator_authority_path,
                    _denominator_document(scenario=scenario, scope=scope, p1_custodian_hash=H))
            roots["invocation"] = invocation["self_hash"]
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "CUSTODIAN_ROOT_REPLAY_FAILURE"):
                self._run(panel, paths, roots, asserted)

    def test_duplicate_and_non_unit_gap_rejected(self):
        cases = (
            (["2026-01-01T00:00:00", "2026-01-01T00:00:00"], "INVALID_TIMESTAMP_AUTHORITY_DUPLICATE"),
            (["2026-01-01T00:00:00", "2026-01-01T00:00:02"], "INVALID_TIMESTAMP_AUTHORITY_NON_UNIT_GAP"),
        )
        for timestamps, code in cases:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                panel, paths, roots, asserted = self._fixture(Path(raw), timestamps=timestamps)
                with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, code):
                    self._run(panel, paths, roots, asserted)

    def test_coherently_rehashed_unsafe_policy_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            self._rehash_custodian_chain(
                paths, roots, mutate_policy=lambda body: body.update(forbidden_roots=[]))
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "CUSTODIAN_RESOURCE_POLICY_SEMANTICS_MISMATCH"):
                self._run(panel, paths, roots, asserted)

    def test_forbidden_root_must_cover_prediction_namespace(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            unrelated = str((Path(raw) / "unrelated").resolve())
            self._rehash_custodian_chain(
                paths, roots, mutate_policy=lambda body: body.update(forbidden_roots=[unrelated]))
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "CUSTODIAN_FORBIDDEN_PREDICTION_ROOT_MISMATCH"):
                self._run(panel, paths, roots, asserted)

    def test_coherently_rehashed_invocation_semantics_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            self._rehash_custodian_chain(
                paths, roots,
                mutate_invocation=lambda body: body.update(isolation_mechanism="IN_PROCESS_TEST_DOUBLE"))
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "CUSTODIAN_ROOT_REPLAY_FAILURE"):
                self._run(panel, paths, roots, asserted)

    def test_coherently_rehashed_timestamp_contract_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            timestamp = _load_json(paths.timestamp_authority_paths["F1"])
            timestamp = self_hashed({
                **{k: v for k, v in timestamp.items() if k != "self_hash"},
                "timezone_contract": "UNAPPROVED_NORMALIZATION",
            })
            persist(paths.timestamp_authority_paths["F1"], timestamp)
            projection = _load_json(paths.projection_authority_paths["F1"])
            projection = self_hashed({
                **{k: v for k, v in projection.items() if k != "self_hash"},
                "timestamp_authority_hash": timestamp["self_hash"],
            })
            persist(paths.projection_authority_paths["F1"], projection)
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "RAW_TO_PROJECTION_LINEAGE_MISMATCH"):
                self._run(panel, paths, roots, asserted)

    def test_unexpected_raw_scenario_record_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            source_path = paths.raw_scenario_source_paths["SYNTHETIC-23.05"]
            source = _load_json(source_path)
            source["records"][0]["ignored_extra"] = "unsafe"
            persist(source_path, source)
            def update_source_hash(body):
                body["approved_sources"][0]["byte_hash"] = sha256(source_path.read_bytes()).hexdigest()
            self._rehash_custodian_chain(paths, roots, mutate_policy=update_source_hash)
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "RAW_SCENARIO_RECORD_SCHEMA_MISMATCH"):
                self._run(panel, paths, roots, asserted)

    def test_coherent_scope_swap_cannot_replace_release_root(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            scope = _load_json(paths.full_process_scope_path)
            scope["points"][0]["p1_membership"] = "NO"
            scope["points"][0]["official_process"] = "P2"
            scope = self_hashed({k: v for k, v in scope.items() if k != "self_hash"})
            persist(paths.full_process_scope_path, scope)
            scenario = _load_json(paths.intermediate.scenario_authority_path)
            persist(paths.intermediate.denominator_authority_path,
                    _denominator_document(scenario=scenario, scope=scope, p1_custodian_hash=H))
            roots["scope"] = scope["self_hash"]
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "RELEASE_NESTED_ROOT_BINDING_MISMATCH"):
                self._run(panel, paths, roots, asserted)

    def test_coherent_custodian_coordinate_disconnect_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            panel, paths, roots, asserted = self._fixture(Path(raw))
            fake_physical, fake_timestamp = "c" * 64, "d" * 64
            def mutate_request(request):
                request["allowed_scenario_bindings"][0]["physical_file_authority_hash"] = fake_physical
                request["allowed_scenario_bindings"][0]["timestamp_authority_hash"] = fake_timestamp
            def mutate_output(output):
                output["records"][0]["physical_file_authority_hash"] = fake_physical
                output["records"][0]["timestamp_authority_hash"] = fake_timestamp
                output["allowed_scenario_binding_hash"] = sha256(
                    canonical_bytes(_load_json(paths.custodian_request_path)["allowed_scenario_bindings"])
                ).hexdigest()
            self._rehash_custodian_chain(
                paths, roots, mutate_request=mutate_request, mutate_output=mutate_output)
            with self.assertRaisesRegex(DG05UpstreamVerifierV3Error, "CUSTODIAN_COORDINATE_ROOT_MISMATCH"):
                self._run(panel, paths, roots, asserted)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="ascii"))


if __name__ == "__main__":
    unittest.main()
