from __future__ import annotations

import copy
from dataclasses import replace
import unittest

from paperworks.v6 import task039e3_r2r_d2_inner_execution_v1 as subject


class IndependentD2InnerExecutionV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        empty_sources = tuple(() for _ in range(subject.EXPECTED_ROW_COUNT))
        false_rows = tuple(False for _ in range(subject.EXPECTED_ROW_COUNT))
        none_rows = tuple("NONE" for _ in range(subject.EXPECTED_ROW_COUNT))
        evidence = subject.D2FusionEvidenceV1(
            subject.AUTHORIZATION_HASH,
            subject.D2_DESIGN_HASH,
            subject.D0_PREDICTION_HASH,
            subject.D1_PREDICTION_HASH,
            subject.SOURCE_MAP_HASH,
            subject.EXPECTED_ROW_COUNT,
            0,
            0,
            "0" * 64,
            empty_sources,
            false_rows,
            none_rows,
            false_rows,
        )
        cls.valid_combined = subject._build_combined_prediction_v1(evidence).to_public_dict()
        subject.validate_scientific_combined_prediction_document_v1(cls.valid_combined)

    def test_01_exactly_32_independent_attacks_accept_zero_invalid(self) -> None:
        rejected = 0
        accepted_invalid = 0

        grant = subject.issue_committed_d2_inner_execution_grant_v1()

        def rehash_grant(field: str, value: object) -> subject.CommittedD2InnerExecutionGrantV1:
            forged = replace(grant, **{field: value}, grant_hash="")
            return replace(forged, grant_hash=subject.stable_hash_v1(forged._payload()))

        grant_attacks = (
            ("authorization_hash", "0" * 64),
            ("d2_design_hash", "0" * 64),
            ("d0_prediction_hash", "0" * 64),
            ("d1_prediction_hash", "0" * 64),
            ("source_map_hash", "0" * 64),
            ("required_distinct_source_count", 1),
        )
        for field, value in grant_attacks:
            try:
                subject.validate_committed_d2_inner_execution_grant_v1(
                    rehash_grant(field, value)
                )
            except subject.D2InnerExecutionV1Error:
                rejected += 1
            else:
                accepted_invalid += 1

        reconstructed = subject.CommittedD2InnerExecutionGrantV1(**grant.__dict__)
        try:
            subject.validate_committed_d2_inner_execution_grant_v1(reconstructed)
        except subject.D2InnerExecutionV1Error:
            rejected += 1
        else:
            accepted_invalid += 1

        label_state = subject.D2ExecutionStateMachineV1()
        try:
            label_state.require_label_access()
        except subject.D2InnerExecutionV1Error:
            rejected += 1
        else:
            accepted_invalid += 1
        try:
            copy.deepcopy(grant)
        except subject.D2InnerExecutionV1Error:
            rejected += 1
        else:
            accepted_invalid += 1

        try:
            subject.fuse_synthetic_timeline_v1(
                (False,), ((0, True, "missing"),), {}
            )
        except subject.D2InnerExecutionV1Error:
            rejected += 1
        else:
            accepted_invalid += 1

        behavioral_attacks = (
            # Same-source duplicates must not be counted twice.
            subject.fuse_synthetic_timeline_v1(
                (False,), ((0, True, "r1"), (0, True, "r2")),
                {"r1": "SOURCE_A", "r2": "SOURCE_A"},
            )[0][0] is True,
            # A caller-changed one-source threshold must not corroborate.
            subject.fuse_synthetic_timeline_v1(
                (False,), ((0, True, "r1"),), {"r1": "SOURCE_A"}
            )[0][0] is True,
            # Adjacent seconds must not be treated as a temporal window.
            any(
                row[0]
                for row in subject.fuse_synthetic_timeline_v1(
                    (False, False), ((0, True, "r1"), (1, True, "r2")),
                    {"r1": "SOURCE_A", "r2": "SOURCE_B"},
                )
            ),
            # Raw OR-any-rule substitution must not produce a recovery.
            subject.fuse_synthetic_timeline_v1(
                (False,), ((0, True, "r1"),), {"r1": "SOURCE_A"}
            )[0] != (False, "NONE", ("SOURCE_A",)),
            # AND fusion must not suppress a frozen D0 alarm.
            subject.fuse_synthetic_timeline_v1((True,), (), {})[0][0] is False,
            # No other D0 suppression is permitted.
            subject.fuse_point_v1(True, frozenset())[1:] != (True, "D0_ONLY"),
        )
        for accepted in behavioral_attacks:
            if accepted:
                accepted_invalid += 1
            else:
                rejected += 1

        prohibited = (
            "d0_score_access",
            "d1_rule_reevaluation",
            "d1_metric_read",
            "d0_rerun",
            "d1_rerun",
            "test1_feature_access",
            "test2",
            "retry",
            "fusion_change",
            "fusion_candidate_search",
            "result_driven_change",
            "outer",
        )
        for operation in prohibited:
            try:
                subject.reject_prohibited_operation_v1(operation)
            except subject.D2InnerExecutionV1Error:
                rejected += 1
            else:
                accepted_invalid += 1

        def rehash_document(document: dict[str, object]) -> dict[str, object]:
            payload = dict(document)
            payload.pop("artifact_hash", None)
            payload["artifact_hash"] = subject.stable_hash_v1(payload)
            return payload

        inserted_label = dict(self.valid_combined)
        inserted_label["label"] = 1

        trigger_mutation = dict(self.valid_combined)
        trigger_records = list(trigger_mutation["prediction_records"])
        trigger_records[0] = dict(trigger_records[0], trigger_class="RULE_RECOVERY")
        trigger_mutation["prediction_records"] = trigger_records

        identity_mutation = dict(self.valid_combined)
        identity_records = list(identity_mutation["prediction_records"])
        identity_records[0] = dict(identity_records[0], combined_decision_identity="f" * 64)
        identity_mutation["prediction_records"] = identity_records

        private_source_leak = dict(self.valid_combined)
        private_source_leak["distinct_sources_by_row"] = []

        for mutation in (
            inserted_label,
            trigger_mutation,
            identity_mutation,
            private_source_leak,
        ):
            try:
                subject.validate_scientific_combined_prediction_document_v1(
                    rehash_document(mutation)
                )
            except subject.D2InnerExecutionV1Error:
                rejected += 1
            else:
                accepted_invalid += 1

        self.assertEqual(rejected, subject.EXPECTED_INDEPENDENT_ATTACKS)
        self.assertEqual(accepted_invalid, 0)

    def test_02_execution_entry_has_no_caller_scientific_knobs(self) -> None:
        import inspect

        self.assertEqual(
            list(inspect.signature(subject.execute_authorized_d2_inner_v1).parameters),
            [],
        )

    def test_03_source_has_no_forbidden_scientific_or_remote_dependency(self) -> None:
        source = inspect_source = __import__("inspect").getsource(subject)
        self.assertNotIn("hai-test1.csv", inspect_source)
        self.assertNotIn("D1_METRICS_V1.json", source)
        self.assertNotIn("git push", source)
        self.assertNotIn("requests.", source)
        self.assertNotIn("urllib.", source)


if __name__ == "__main__":
    unittest.main()
