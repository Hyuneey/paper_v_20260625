from __future__ import annotations

import dataclasses
from hashlib import sha256
import inspect
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paperworks.validation_v2.evaluation_custody_v1 import (
    DenseBooleanPredictionArtifactV1, DenseBooleanPredictionRecordV1,
    PredictionFreezeReferenceV1, persist_dense_prediction_before_label_v1,
)
from paperworks.validation_v2.exp04_protocol_v1 import (
    EXP04_FUSION_POLICY_ID, EXP04_METHOD_IDS, Exp04ProtocolError,
    RuleOutcomeEvidenceV1, build_exp04_preregistration_v1,
    build_rule_outcome_authority_v1, exp04_opportunity_id_v1,
    fuse_detector_with_rules_v1,
)
from paperworks.validation_v2.formal_v4_authority_v1 import canonical_document_hash_v1
from paperworks.validation_v2.prediction_custody_v1 import (
    D1PredictionArtifactV2, D1PredictionRecordV2, persist_prediction_before_label_v1,
)
from paperworks.validation_v2.runtime_v1 import FORMAL_V4_RUNTIME_VERSION, FormalV4RuntimeTraceV1
from tests.test_validation_v2_formal_v4_authority_v1 import V2Fixture


H = "a" * 64
POLICY = sha256(b"policy").hexdigest()
METRIC = sha256(b"metric").hexdigest()


class Exp04ProtocolV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = V2Fixture()
        self.custody = TemporaryDirectory()
        self.custody_root = Path(self.custody.name).resolve()
        self.serial = 0

    def tearDown(self) -> None:
        self.custody.cleanup()
        self.fx.close()

    def evidence(self, descriptor_index: int, row: int, outcome: str, *, source: str | None = None):
        descriptor = self.fx.descriptors[descriptor_index]
        rule = descriptor.relation_id
        source = descriptor.source if source is None else source
        reason = {"PASS": "expected_response_observed", "FAIL": "expected_response_not_observed", "ABSTAIN": "source_not_triggered"}[outcome]
        payload = {
            "alarm_emitted": outcome == "FAIL", "authorization_hash": self.fx.bundle.receipt.authorization_hash,
            "descriptor_hash": descriptor.descriptor_hash, "execution_context_hash": self.fx.context.context_hash,
            "final_outcome": outcome, "opportunity_id": exp04_opportunity_id_v1(file_id="test1", row_index=row, rule_id=rule),
            "reason": reason, "relation_id": rule, "runtime_version": FORMAL_V4_RUNTIME_VERSION,
        }
        trace = FormalV4RuntimeTraceV1(
            opportunity_id=payload["opportunity_id"], relation_id=rule, descriptor_hash=descriptor.descriptor_hash,
            authorization_hash=self.fx.bundle.receipt.authorization_hash, execution_context_hash=self.fx.context.context_hash,
            final_outcome=outcome, reason=reason, alarm_emitted=outcome == "FAIL",
            trace_hash=canonical_document_hash_v1(payload),
        )
        return RuleOutcomeEvidenceV1(
            "test1", H, row, rule, source, outcome, descriptor.descriptor_hash, trace.trace_hash,
            self.fx.bundle.authority.authority_hash, self.fx.bundle.receipt.authorization_hash, trace,
        )

    def frozen_inputs(self, alarms: tuple[bool, ...], outcomes: tuple[RuleOutcomeEvidenceV1, ...]):
        self.serial += 1
        prefix = f"case-{self.serial}"
        base = DenseBooleanPredictionArtifactV1(
            artifact_id=f"BASE-{self.serial}", method_id="V2_D0_PCA_SPE_NORMAL_ONLY_V1",
            config_id="D0-CONFIG", experiment_id="EXP-04", dataset_id="HAI-P1", split_role="DEVELOPMENT_TEST1",
            authority_hash=sha256(b"base-authority").hexdigest(), evaluation_policy_hash=POLICY,
            metric_contract_hash=METRIC, file_contract_hash=self.fx.context.file_contract_binding.content_sha256,
            source_commit=self.fx.commit,
            records=tuple(DenseBooleanPredictionRecordV1("test1", H, row, alarm) for row, alarm in enumerate(alarms)),
        )
        base_receipt = persist_dense_prediction_before_label_v1(
            base, artifact_root=self.custody_root, prediction_relative_path=f"{prefix}/base.json",
            receipt_relative_path=f"{prefix}/base.receipt.json",
        )
        base_reference = PredictionFreezeReferenceV1(
            base.method_id, f"{prefix}/base.json", f"{prefix}/base.receipt.json", base_receipt,
        )
        by_row: dict[int, list[RuleOutcomeEvidenceV1]] = {}
        for item in outcomes:
            if item.outcome == "FAIL" and 0 <= item.row_index < len(alarms):
                by_row.setdefault(item.row_index, []).append(item)
        d1 = D1PredictionArtifactV2(
            method_id="V2_VERIFIED_RELATIONAL_RULE_ONLY_V1", config_id="D1-CONFIG", experiment_id="EXP-04",
            dataset_id="HAI-P1", split_role="DEVELOPMENT_TEST1",
            authority_hash=self.fx.bundle.authority.authority_hash,
            runtime_authorization_hash=self.fx.bundle.receipt.authorization_hash,
            execution_context_hash=self.fx.context.context_hash, source_commit=self.fx.commit,
            portfolio_hash=self.fx.bundle.authority.authority_hash,
            file_contract_hash=self.fx.context.file_contract_binding.content_sha256,
            records=tuple(D1PredictionRecordV2(
                "test1", H, row, bool(by_row.get(row)),
                tuple(sorted(item.rule_id for item in by_row.get(row, []))),
                tuple(sorted(item.trace_hash for item in by_row.get(row, []))),
            ) for row in range(len(alarms))),
        )
        d1_receipt = persist_prediction_before_label_v1(
            d1, artifact_root=self.custody_root, prediction_relative_path=f"{prefix}/d1.json",
            receipt_relative_path=f"{prefix}/d1.receipt.json",
        )
        return base_reference, d1_receipt, f"{prefix}/d1.receipt.json"

    def fuse(self, alarms, outcomes, *, frozen_outcomes=None, frozen=None):
        base_reference, d1_receipt, d1_path = frozen or self.frozen_inputs(
            alarms, outcomes if frozen_outcomes is None else frozen_outcomes,
        )
        return fuse_detector_with_rules_v1(
            base_custody_root=self.custody_root, base_prediction_reference=base_reference,
            expected_evaluation_policy_hash=POLICY, expected_metric_contract_hash=METRIC,
            d1_custody_root=self.custody_root, d1_receipt_relative_path=d1_path,
            d1_freeze_receipt=d1_receipt, rule_outcomes=outcomes,
            authorized_runtime=self.fx.bundle, execution_context=self.fx.context,
            repository_root=self.fx.root,
        )

    def preregistration(self):
        return build_exp04_preregistration_v1(
            source_commit=self.fx.commit, validation_protocol_hash="1" * 64, metric_contract_hash="2" * 64,
            d0_authority_contract_hash="3" * 64, isolation_forest_contract_hash="4" * 64,
            rule_portfolio_contract_hash="5" * 64, evaluation_custody_contract_hash="6" * 64,
        )

    def test_preregistration_and_scientific_fusion_api_are_frozen(self) -> None:
        prereg = self.preregistration()
        self.assertEqual(EXP04_METHOD_IDS, prereg.method_ids)
        self.assertEqual("DEVELOPMENT_TEST1", prereg.split_role)
        self.assertFalse(prereg.test2_authorized)
        self.assertNotIn("base_predictions", inspect.signature(fuse_detector_with_rules_v1).parameters)
        self.assertNotIn("rule_authority", inspect.signature(fuse_detector_with_rules_v1).parameters)

    def test_preregistration_rejects_policy_mutation(self) -> None:
        with self.assertRaises(Exp04ProtocolError):
            dataclasses.replace(self.preregistration(), fusion_min_distinct_sources=1, preregistration_hash="")

    def test_fusion_preserves_base_and_requires_two_distinct_sources(self) -> None:
        evidence = (self.evidence(0, 1, "FAIL"), self.evidence(1, 1, "FAIL"), self.evidence(0, 2, "FAIL"), self.evidence(1, 2, "FAIL"))
        decisions = self.fuse((True, False, False), evidence)
        self.assertEqual((True, True, True), tuple(item.final_alarm for item in decisions))
        self.assertEqual((False, True, True), tuple(item.rule_addition for item in decisions))
        self.assertTrue(all(item.fusion_policy_id == EXP04_FUSION_POLICY_ID for item in decisions))

    def test_foreign_coordinate_source_and_relocation_are_rejected(self) -> None:
        with self.assertRaises(Exp04ProtocolError):
            self.fuse((False,), (self.evidence(0, 1, "FAIL"),))
        forged_source = (self.evidence(0, 0, "FAIL"), self.evidence(1, 0, "FAIL", source=self.fx.descriptors[0].source))
        with self.assertRaisesRegex(Exp04ProtocolError, "source or descriptor authority mismatch"):
            self.fuse((False,), forged_source)
        with self.assertRaisesRegex(Exp04ProtocolError, "replay its runtime trace"):
            dataclasses.replace(self.evidence(0, 0, "FAIL"), row_index=1)

    def test_omitted_added_or_substituted_fail_evidence_is_rejected(self) -> None:
        full = (self.evidence(0, 0, "FAIL"), self.evidence(1, 0, "FAIL"))
        for observed, frozen in ((full[:1], full), (full, full[:1]), ((full[0], self.evidence(1, 0, "PASS")), full)):
            with self.subTest(observed=len(observed), frozen=len(frozen)), self.assertRaisesRegex(Exp04ProtocolError, "FAIL evidence census mismatch"):
                self.fuse((False,), observed, frozen_outcomes=frozen)

    def test_forged_base_or_d1_freeze_receipt_is_rejected(self) -> None:
        evidence = (self.evidence(0, 0, "FAIL"),)
        base_ref, d1_receipt, path = self.frozen_inputs((False,), evidence)
        forged_base = dataclasses.replace(base_ref, receipt=dataclasses.replace(base_ref.receipt, self_hash="f" * 64))
        with self.assertRaisesRegex(Exp04ProtocolError, "durable upstream prediction replay failed"):
            self.fuse((False,), evidence, frozen=(forged_base, d1_receipt, path))
        with self.assertRaisesRegex(Exp04ProtocolError, "durable upstream prediction replay failed"):
            self.fuse((False,), evidence, frozen=(base_ref, dataclasses.replace(d1_receipt, self_hash="f" * 64), path))

    def test_descriptor_authority_is_replayed_from_formal_v4(self) -> None:
        authority = build_rule_outcome_authority_v1(
            authorized_runtime=self.fx.bundle, execution_context=self.fx.context, repository_root=self.fx.root,
        )
        self.assertEqual(len(self.fx.descriptors), len(authority.bindings))
        self.assertEqual(self.fx.bundle.authority.descriptor_set_hash, authority.descriptor_set_hash)

    def test_grouped_fusion_matches_independent_policy_reference(self) -> None:
        alarms = (False, False, False, False, True, False)
        evidence = (
            self.evidence(0, 0, "FAIL"),
            self.evidence(1, 0, "FAIL"),
            self.evidence(0, 1, "FAIL"),
            self.evidence(0, 2, "PASS"),
            self.evidence(1, 2, "FAIL"),
            self.evidence(0, 3, "ABSTAIN"),
            self.evidence(0, 5, "FAIL"),
            self.evidence(1, 5, "FAIL"),
        )
        observed = self.fuse(alarms, evidence)

        sources_by_row: dict[int, set[str]] = {}
        for item in evidence:
            if item.outcome == "FAIL":
                sources_by_row.setdefault(item.row_index, set()).add(item.source_id)
        expected = tuple(
            (
                row,
                alarm,
                tuple(sorted(sources_by_row.get(row, set()))),
                len(sources_by_row.get(row, set())) >= 2,
                alarm or len(sources_by_row.get(row, set())) >= 2,
            )
            for row, alarm in enumerate(alarms)
        )
        actual = tuple(
            (
                item.row_index,
                item.base_alarm,
                item.distinct_fail_sources,
                item.rule_addition,
                item.final_alarm,
            )
            for item in observed
        )
        self.assertEqual(expected, actual)

    def test_fusion_source_keeps_one_rule_pass_and_no_repeated_coordinate_sort(self) -> None:
        source = inspect.getsource(fuse_detector_with_rules_v1)
        self.assertEqual(source.count("for item in rule_outcomes:"), 1)
        self.assertEqual(source.count("for base_prediction, d1_record in zip"), 1)
        self.assertEqual(source.count("for base_prediction, record, coordinate in dense_rows:"), 1)
        self.assertNotIn("tuple(sorted(set(coordinates)))", source)
        self.assertNotIn("by_coordinate.get", source)


if __name__ == "__main__":
    unittest.main()
