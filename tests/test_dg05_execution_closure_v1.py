from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.dg05_execution_closure_v1 import *
from paperworks.validation_v2.dg05_execution_closure_v1 import STATE_ORDER_V3
from paperworks.validation_v2.dg05_label_custodian_v1 import (
    CustodianIsolationError, consume_and_extract_v1, validate_request_v1,
)
from paperworks.validation_v2.multipanel_custody_v1 import (
    FROZEN_ATTACK_FILE_IDS_V2, FROZEN_AUTHORITY_SOURCE_COMMIT_V2,
    FROZEN_DETECTOR_AUTHORITY_HASHES_V2, FROZEN_FEATURE_IDS_V2,
    FROZEN_FUSION_POLICY_HASH_V2, FROZEN_METHOD_BUNDLE_HASH_V2,
    FROZEN_PANEL_ORDER_V2, FROZEN_PORTFOLIO_HASHES_V2,
    FROZEN_ATTACK_FILE_CENSUS_HASH_V2,
    PhysicalFileIdentityV2, FrozenPhysicalFileAuthorityV2,
    frozen_feature_allowlist_authorities_v2,
)


H = "a" * 64
G = "a" * 40


def detector_registry() -> DetectorSubauthorityRegistryV1:
    entries = []
    for panel in FROZEN_PANEL_ORDER_V2:
        for detector in ("PCA_SPE", "ISOLATION_FOREST"):
            salt = digest([panel, detector])
            entries.append(DetectorSubauthorityV1(panel, detector, FROZEN_DETECTOR_AUTHORITY_HASHES_V2[panel], salt, salt, salt, salt, salt, salt, salt))
    return DetectorSubauthorityRegistryV1(tuple(sorted(entries)), G)


def dispatch_registry(detectors: DetectorSubauthorityRegistryV1) -> MethodDispatchRegistryV1:
    entries = []
    methods = {
        "M0_PCA_SPE": ("PCA", "PCA_SPE", "PCA"),
        "M1_T0_RULE_ONLY": ("RULE", None, "T0"),
        "M2_T2_RULE_ONLY": ("RULE", None, "T2"),
        "M3_PCA_PLUS_T0": ("FUSION", "PCA_SPE", "T0"),
        "M4_PCA_PLUS_T2": ("FUSION", "PCA_SPE", "T2"),
        "ISOLATION_FOREST": ("IF", "ISOLATION_FOREST", "IF"),
        "ISOLATION_FOREST_PLUS_T2": ("FUSION", "ISOLATION_FOREST", "T2"),
    }
    for panel in FROZEN_PANEL_ORDER_V2:
        local = dict(methods)
        if panel == FROZEN_PANEL_ORDER_V2[0]:
            local["V2A_RULE_ONLY_REFERENCE"] = ("RULE", None, "V2A")
            local["HISTORICAL_PCA_PLUS_V2A_CONTINUITY"] = ("FUSION", "PCA_SPE", "V2A")
        for method, (kind, detector, portfolio) in local.items():
            components = []
            if detector:
                components.append(digest(detectors.lookup(panel, detector).document()))
            if portfolio in ("T0", "T2", "V2A"):
                components.append(FROZEN_PORTFOLIO_HASHES_V2[panel][portfolio])
            if kind == "FUSION":
                components.append(FROZEN_FUSION_POLICY_HASH_V2)
            entries.append(MethodDispatchEntryV1(panel, method, kind, tuple(components), detector))
    return MethodDispatchRegistryV1(tuple(sorted(entries)), detectors.document()["self_hash"], FROZEN_METHOD_BUNDLE_HASH_V2, G)


def full_scope() -> FullProcessScopeAuthorityV1:
    points = []
    for version in ("21.03", "22.04", "23.05"):
        points.extend((
            FullProcessPointV1(version, "P1_EXACT", "P1", "YES", H),
            FullProcessPointV1(version, "P2_EXACT", "P2", "NO", H),
        ))
    return FullProcessScopeAuthorityV1(tuple(sorted(points)), H, tuple((v, H) for v in ("21.03", "22.04", "23.05")), G,
        version_counts=tuple((v, 2) for v in ("21.03", "22.04", "23.05")), authority_mode="SYNTHETIC_REHEARSAL")


def manifest(registry: MethodDispatchRegistryV1, detectors: DetectorSubauthorityRegistryV1, scope: FullProcessScopeAuthorityV1) -> DG05ExecutableAuthorityManifestV1:
    implementations = tuple(sorted((name, digest(name)) for name in (
        "state_machine", "projection_adapter", "prediction_adapter", "timestamp_builder",
        "scenario_builder", "denominator_builder", "global_manifest_builder", "global_freeze_builder",
        "label_custodian", "result_builder", "result_verifier",
    )))
    portfolios = tuple(sorted(v for values in FROZEN_PORTFOLIO_HASHES_V2.values() for v in values.values()))
    return DG05ExecutableAuthorityManifestV1(tuple(FROZEN_SCIENTIFIC_AUTHORITIES_V1.items()), detectors.document()["self_hash"], registry.document()["self_hash"], portfolios, scope.document()["self_hash"], digest("p1-custodian-v3"), implementations, G)


def physical() -> FrozenPhysicalFileAuthorityV2:
    files = []
    for panel in FROZEN_PANEL_ORDER_V2:
        for file_id in FROZEN_ATTACK_FILE_IDS_V2[panel]:
            files.append(PhysicalFileIdentityV2(panel, file_id, digest([panel, file_id, "raw"]), digest([panel, file_id, "header"]), digest([panel, file_id, "official"])))
    return FrozenPhysicalFileAuthorityV2(tuple(files), FROZEN_ATTACK_FILE_CENSUS_HASH_V2, H, FROZEN_AUTHORITY_SOURCE_COMMIT_V2)


class DG05ExecutionClosureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.detectors = detector_registry()
        self.dispatch = dispatch_registry(self.detectors)
        self.scope = full_scope()
        self.manifest = manifest(self.dispatch, self.detectors, self.scope)
        self.manifest.validate()

    def test_b1_constant_bound_state_and_negative_authorities(self) -> None:
        mh = self.manifest.document()["self_hash"]
        state = initialize_dg05_execution_v1(self.manifest, approved_manifest_hash=mh, execution_id="SYNTHETIC")
        self.assertEqual(state["executable_approval_manifest_hash"], mh)
        with self.assertRaises(DG05ClosureError):
            initialize_dg05_execution_v1(self.manifest, approved_manifest_hash=H, execution_id="SYNTHETIC")
        changed = replace(self.manifest, scientific_authorities=tuple((k, H if k == "metric" else v) for k, v in self.manifest.scientific_authorities))
        with self.assertRaises(DG05ClosureError):
            changed.validate()
        with self.assertRaises(DG05ClosureError):
            advance_dg05_state_v1(state, self.manifest, next_state="GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED", evidence=StateTransitionEvidenceV1("GLOBAL_FREEZE", H, 72, self_hashed({"schema":"fake"})))

    def test_b4_p1_known_non_p1_unresolved_and_cross_process(self) -> None:
        self.assertEqual(self.scope.classify("23.05", "P1_EXACT"), "P1")
        self.assertEqual(self.scope.classify("23.05", "P2_EXACT"), "KNOWN_NON_P1")
        self.assertEqual(self.scope.classify("23.05", "UNKNOWN"), "UNRESOLVED")

    def test_b8_method_specific_subauthorities(self) -> None:
        self.detectors.validate()
        self.dispatch.validate()
        pca = self.dispatch.lookup(FROZEN_PANEL_ORDER_V2[0], "M0_PCA_SPE")
        isolation = self.dispatch.lookup(FROZEN_PANEL_ORDER_V2[0], "ISOLATION_FOREST")
        self.assertEqual(pca.detector_id, "PCA_SPE")
        self.assertEqual(isolation.detector_id, "ISOLATION_FOREST")
        with self.assertRaises(DG05ClosureError):
            replace(pca, detector_id="ISOLATION_FOREST").validate()

    def _write_synthetic_csv(self, path: Path, authority: FrozenFeatureAllowlistAuthorityV2, label: bytes = b"0") -> None:
        header = [authority.timestamp_id, *authority.feature_ids, "Attack", "unknown_field"]
        lines = [b",".join(v.encode() for v in header)]
        for index in range(2):
            timestamp = f"2026-01-01T00:00:0{index}".encode()
            values = [b"1.0"] * len(authority.feature_ids)
            lines.append(b",".join([timestamp, *values, label, b"opaque"]))
        path.write_bytes(b"\n".join(lines) + b"\n")

    def test_b7_projection_non_interference_invalid_utf8_and_reserved_exclusion(self) -> None:
        authority = frozen_feature_allowlist_authorities_v2()[FROZEN_PANEL_ORDER_V2[0]]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            a, b = root / "a.csv", root / "b.csv"
            self._write_synthetic_csv(a, authority, b"0")
            self._write_synthetic_csv(b, authority, b"\xff")
            fa = PhysicalFileIdentityV2(authority.panel_id, "hai-test2.csv", file_sha256(a), H, H)
            fb = PhysicalFileIdentityV2(authority.panel_id, "hai-test2.csv", file_sha256(b), H, H)
            pa, ta = project_attack_feature_file_v1(source=a, destination=root / "pa.jsonl", physical_file=fa, panel_authority=authority, file_id="hai-test2.csv", adapter_implementation_hash=H, source_commit=G)
            pb, tb = project_attack_feature_file_v1(source=b, destination=root / "pb.jsonl", physical_file=fb, panel_authority=authority, file_id="hai-test2.csv", adapter_implementation_hash=H, source_commit=G)
            self.assertEqual((pa.projection_hash, ta.timestamp_vector_hash), (pb.projection_hash, tb.timestamp_vector_hash))
            payload = (root / "pa.jsonl").read_text("ascii").lower()
            self.assertNotIn("attack", payload)
            self.assertNotIn("unknown_field", payload)

    def test_cell_census_is_derived_and_equals_72(self) -> None:
        census = build_expected_prediction_cell_census_v1(physical=physical(), dispatch=self.dispatch)
        self.assertEqual(census["count"], 72)
        self.assertEqual(len({v["cell_id"] for v in census["cells"]}), 72)

    def test_b6_isolated_custodian_consumes_before_read_and_denies_prediction_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            incoming, outgoing, predictions = root / "labels", root / "custodian", root / "predictions"
            incoming.mkdir(); outgoing.mkdir(); predictions.mkdir()
            source = incoming / "scenarios.json"
            source.write_text(json.dumps({"schema": "approved_official_scenario_source_v1", "records": []}), encoding="utf-8")
            source_hash = file_sha256(source)
            token = "opaque"
            lease_body = {"schema": "single_use_label_scenario_lease_v3", "token_hash": __import__("hashlib").sha256(token.encode()).hexdigest(), "global_freeze_hash": H, "state_hash": H, "executable_manifest_hash": H, "issue_count": 1, "consume_limit": 1}
            lease_receipt = self_hashed(lease_body)
            policy_body = {"input_root": str(incoming.resolve()), "output_root": str(outgoing.resolve()), "forbidden_roots": [str(predictions.resolve())]}
            resource_policy = self_hashed(policy_body)
            binding = {"panel_id": FROZEN_PANEL_ORDER_V2[0], "dataset_version": "23.05", "file_id": "hai-test2.csv", "physical_file_authority_hash": H, "timestamp_authority_hash": H, "official_source_hash": source_hash}
            request = {"schema": "isolated_label_scenario_custodian_request_v1", "opaque_lease": token,
                       "lease_receipt": lease_receipt, "global_freeze_hash": H, "executable_manifest_hash": H,
                       "approved_input": str(source), "approved_output": str(outgoing / "out.json"),
                       "public_authority_hashes": [H], "consumed_receipt": str(outgoing / "consumed.json"),
                       "resource_policy": resource_policy, "allowed_scenario_bindings": [binding],
                       "approved_source_byte_hash": source_hash, "authority_mode": "SYNTHETIC_REHEARSAL",
                       "nominal_counts": {FROZEN_PANEL_ORDER_V2[0]: 0}}
            result = consume_and_extract_v1(request, input_root=incoming, output_root=outgoing, forbidden_roots=[predictions])
            self.assertTrue((outgoing / "consumed.json").exists())
            self.assertEqual(len(result["output_byte_hash"]), 64)
            with self.assertRaises(CustodianIsolationError):
                consume_and_extract_v1(request, input_root=incoming, output_root=outgoing, forbidden_roots=[predictions])
            tainted = dict(request); tainted["prediction_path"] = str(predictions / "x")
            with self.assertRaises(CustodianIsolationError):
                validate_request_v1(tainted, input_root=incoming, output_root=outgoing, forbidden_roots=[predictions])

    def test_b3_denominator_five_fixtures_method_blind(self) -> None:
        timestamp_hash = H
        rows = (
            ScenarioRecordV1(FROZEN_PANEL_ORDER_V2[0], "23.05", "hai-test2.csv", "A", (("2026-01-01T00:00:00", "2026-01-01T00:00:01"),), ("P1_EXACT",), (), H, timestamp_hash, H),
            ScenarioRecordV1(FROZEN_PANEL_ORDER_V2[0], "23.05", "hai-test2.csv", "B", (("2026-01-01T00:00:00", "2026-01-01T00:00:01"),), ("P2_EXACT",), (), H, timestamp_hash, H),
            ScenarioRecordV1(FROZEN_PANEL_ORDER_V2[0], "23.05", "hai-test2.csv", "C", (("2026-01-01T00:00:00", "2026-01-01T00:00:01"),), ("P2_EXACT", "UNKNOWN"), (), H, timestamp_hash, H),
            ScenarioRecordV1(FROZEN_PANEL_ORDER_V2[0], "23.05", "hai-test2.csv", "D", (("2026-01-01T00:00:00", "2026-01-01T00:00:01"),), ("P1_EXACT", "UNKNOWN"), (), H, timestamp_hash, H),
            ScenarioRecordV1(FROZEN_PANEL_ORDER_V2[0], "23.05", "hai-test2.csv", "E", (("2026-01-01T00:00:00", "2026-01-01T00:00:01"),), ("P2_EXACT",), ("P1",), H, timestamp_hash, H),
        )
        scenario = build_scenario_authority_v1(records=rows, lease_completion_hash=H, global_freeze_hash=H, source_commit=G,
            nominal_counts={FROZEN_PANEL_ORDER_V2[0]: 5, FROZEN_PANEL_ORDER_V2[1]: 0, FROZEN_PANEL_ORDER_V2[2]: 0}, authority_mode="SYNTHETIC_REHEARSAL")
        denominator = build_denominator_authority_v1(scenario_authority=scenario, full_scope=self.scope, p1_custodian_v3_hash=H)
        states = {r["scenario_id"]: (r["primary_status"], r["secondary_cross_process_p1_relevant"]) for r in denominator["records"]}
        self.assertEqual(states, {"A": ("P1_ELIGIBLE", False), "B": ("OUT_OF_SCOPE", False), "C": ("UNRESOLVED", False), "D": ("P1_ELIGIBLE", False), "E": ("OUT_OF_SCOPE", True)})
        self.assertFalse(denominator["prediction_inputs"])
        with self.assertRaises(DG05ClosureError):
            build_scenario_authority_v1(records=rows, lease_completion_hash=H, global_freeze_hash=H, source_commit=G,
                nominal_counts={FROZEN_PANEL_ORDER_V2[0]: 5, FROZEN_PANEL_ORDER_V2[1]: 0, FROZEN_PANEL_ORDER_V2[2]: 0})

    def test_b2_b5_result_bytes_coordinate_and_nested_replay(self) -> None:
        panel = FROZEN_PANEL_ORDER_V2[0]
        timestamps = ("2026-01-01T00:00:00", "2026-01-01T00:00:01")
        timestamp_vector_hash = __import__("hashlib").sha256(b"".join(v.encode() + b"\n" for v in timestamps)).hexdigest()
        ta = TimestampCoordinateAuthorityV1(panel, "23.05", "hai-test2.csv", H, H, "timestamp", 2, timestamp_vector_hash,
            "UTF8_ISO8601_BYTES", "NAIVE_AS_RECORDED_NO_CONVERSION", "STRICT_FILE_ORDER", "PRESERVE_DUPLICATES_IN_ROW_ORDER", H, G)
        row = ScenarioRecordV1(panel, "23.05", "hai-test2.csv", "A", ((timestamps[0], timestamps[1]),), ("P1_EXACT",), (), H, ta.document()["self_hash"], H)
        scenario = build_scenario_authority_v1(records=(row,), lease_completion_hash=H, global_freeze_hash=H, source_commit=G,
            nominal_counts={panel: 1, FROZEN_PANEL_ORDER_V2[1]: 0, FROZEN_PANEL_ORDER_V2[2]: 0}, authority_mode="SYNTHETIC_REHEARSAL")
        denominator = build_denominator_authority_v1(scenario_authority=scenario, full_scope=self.scope, p1_custodian_v3_hash=H)
        result = compute_bound_panel_method_result_v1(panel_id=panel, method_id="M0_PCA_SPE", method_authority_hash=H,
            prediction_manifest_hash=H, predictions={"hai-test2.csv": (ta, timestamps, (False, True), H, H)},
            scenario_authority=scenario, denominator_authority=denominator, metric_authority_hash=FROZEN_SCIENTIFIC_AUTHORITIES_V1["metric"],
            p1_custodian_hash=H, etapr_authority_hash=FROZEN_SCIENTIFIC_AUTHORITIES_V1["etapr"], normal_burden_hash=H, source_commit=G)
        self.assertEqual((result["hit_count"], result["eligible_count"], result["scenario_recall"]), (1, 1, 1.0))
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "result.json"
            receipt = persist_result_authority_v1(path, result)
            audit = verify_result_authority_v1(path=path, receipt=receipt, expected_bindings={"scenario_authority_hash": scenario["self_hash"], "denominator_authority_hash": denominator["self_hash"]})
            self.assertEqual(audit["status"], "PASS")
            mutated = dict(result); mutated["hit_count"] = 0
            path.write_bytes(canonical_bytes(mutated) + b"\n")
            with self.assertRaises(DG05ClosureError):
                verify_result_authority_v1(path=path, receipt=receipt, expected_bindings={})
        wrong = replace(ta, file_id="other")
        with self.assertRaises(DG05ClosureError):
            compute_bound_panel_method_result_v1(panel_id=panel, method_id="M0", method_authority_hash=H,
                prediction_manifest_hash=H, predictions={"hai-test2.csv": (wrong, timestamps, (False, True), H, H)},
                scenario_authority=scenario, denominator_authority=denominator, metric_authority_hash=H, p1_custodian_hash=H,
                etapr_authority_hash=H, normal_burden_hash=H, source_commit=G)

    def test_full_72_cell_production_adapter_synthetic_rehearsal(self) -> None:
        mh = self.manifest.document()["self_hash"]
        projections = {}
        timestamps = {}
        artifacts = {}
        receipts = []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            authorities = frozen_feature_allowlist_authorities_v2()
            synthetic_files = []
            for panel in FROZEN_PANEL_ORDER_V2:
                for file_id in FROZEN_ATTACK_FILE_IDS_V2[panel]:
                    source = root / f"{panel}-{file_id}.csv"
                    self._write_synthetic_csv(source, authorities[panel])
                    synthetic_files.append(PhysicalFileIdentityV2(panel, file_id, file_sha256(source), digest([panel, file_id, "header"]), digest([panel, file_id, "official"])))
            phy = FrozenPhysicalFileAuthorityV2(tuple(synthetic_files), FROZEN_ATTACK_FILE_CENSUS_HASH_V2, H, FROZEN_AUTHORITY_SOURCE_COMMIT_V2)
            census = build_expected_prediction_cell_census_v1(physical=phy, dispatch=self.dispatch)
            for item in phy.files:
                source = root / f"{item.panel_id}-{item.file_id}.csv"
                projection, timestamp = project_attack_feature_file_v1(source=source, destination=root / f"{item.panel_id}-{item.file_id}.projection",
                    physical_file=item, panel_authority=authorities[item.panel_id], file_id=item.file_id,
                    adapter_implementation_hash=H, source_commit=G)
                projections[(item.panel_id, item.file_id)] = (projection, root / f"{item.panel_id}-{item.file_id}.projection")
                timestamps[(item.panel_id, item.file_id)] = timestamp
            def detector(path: Path, entry: MethodDispatchEntryV1):
                return (False, True), None
            def rule(path: Path, entry: MethodDispatchEntryV1):
                return (False, True), {"opportunities": [], "pass": 0, "fail": 1, "abstain": 0, "system_errors": 0, "rule_ids": ["R"], "physical_source_ids": ["P1_EXACT"]}
            executor_classes = {"PCA": detector, "IF": detector, "RULE": rule, "FUSION": rule}
            executors = {digest(entry.document()): executor_classes[entry.executor_class] for entry in self.dispatch.entries}
            for cell in census["cells"]:
                projection, path = projections[(cell["panel_id"], cell["file_id"])]
                receipt = execute_prediction_cell_v1(cell=cell, dispatch=self.dispatch, projection=projection,
                    timestamp=timestamps[(cell["panel_id"], cell["file_id"])], executable_manifest_hash=mh,
                    executors=executors, projection_path=path, output_directory=root / "predictions", source_commit=G)
                receipts.append(receipt)
                artifacts[receipt.cell_id] = (root / "predictions" / f"{receipt.cell_id}.prediction.json",
                    None if receipt.trace_status == "NOT_APPLICABLE" else root / "predictions" / f"{receipt.cell_id}.trace.json")
            global_manifest = build_global_prediction_manifest_v1(census=census, receipts=receipts, executable_manifest_hash=mh, dispatch=self.dispatch)
            state = initialize_dg05_execution_v1(self.manifest, approved_manifest_hash=mh, execution_id="SYNTHETIC72")
            evidence = (("PHYSICAL_FILE_AUTHORITY", 10), ("PROJECTION_CENSUS", 10), ("EXECUTION_START", 1))
            for next_state, (kind, count) in zip(STATE_ORDER_V3[1:4], evidence):
                document = self_hashed({"schema": kind.lower(), "count": count})
                state = advance_dg05_state_v1(state, self.manifest, next_state=next_state, evidence=StateTransitionEvidenceV1(kind, document["self_hash"], count, document))
            freeze = freeze_global_predictions_v1(manifest=global_manifest, census=census, receipt_artifacts=artifacts, predecessor_state=state)
            state = advance_dg05_state_v1(state, self.manifest, next_state=STATE_ORDER_V3[4], evidence=StateTransitionEvidenceV1("GLOBAL_FREEZE", freeze["self_hash"], 72, freeze))
            lease = issue_label_lease_v3(freeze=freeze, state=state, executable_manifest_hash=mh)
            self.assertEqual((global_manifest["success_count"], global_manifest["failure_count"], freeze["status"], lease["receipt"]["issue_count"]), (72, 0, "GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED", 1))
            # After label lease, manifest/method replacement cannot advance the same chain.
            with self.assertRaises(DG05ClosureError):
                advance_dg05_state_v1(state, replace(self.manifest, dispatch_registry_hash=H), next_state=STATE_ORDER_V3[5], evidence=StateTransitionEvidenceV1("LEASE_ISSUE", lease["receipt"]["self_hash"], 1, lease["receipt"]))

    def test_failure_is_terminal_and_not_prediction(self) -> None:
        entry = self.dispatch.lookup(FROZEN_PANEL_ORDER_V2[0], "M0_PCA_SPE")
        self.assertEqual(entry.detector_id, "PCA_SPE")
        # Exact adapter behavior is exercised by omitting the registered class.
        authority = frozen_feature_allowlist_authorities_v2()[FROZEN_PANEL_ORDER_V2[0]]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); source = root / "a.csv"; self._write_synthetic_csv(source, authority)
            file_identity = PhysicalFileIdentityV2(authority.panel_id, "hai-test2.csv", file_sha256(source), H, H)
            projection, timestamp = project_attack_feature_file_v1(source=source, destination=root / "projection", physical_file=file_identity,
                panel_authority=authority, file_id="hai-test2.csv", adapter_implementation_hash=H, source_commit=G)
            census = build_expected_prediction_cell_census_v1(physical=physical(), dispatch=self.dispatch)
            cell = next(v for v in census["cells"] if v["panel_id"] == FROZEN_PANEL_ORDER_V2[0] and v["method_id"] == "M0_PCA_SPE")
            receipt = execute_prediction_cell_v1(cell=cell, dispatch=self.dispatch, projection=projection, timestamp=timestamp,
                executable_manifest_hash=self.manifest.document()["self_hash"], executors={}, projection_path=root / "projection",
                output_directory=root / "predictions", source_commit=G)
            self.assertEqual((receipt.status, receipt.prediction_artifact_hash, receipt.failure_code), ("METHOD_FAILURE", None, "EXECUTOR_NOT_REGISTERED"))


if __name__ == "__main__":
    unittest.main()
