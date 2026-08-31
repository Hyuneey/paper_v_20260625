from __future__ import annotations

import dataclasses
import copy
import inspect
import unittest
from unittest import mock

from paperworks.gdn.upstream_candidate_backend_v2 import (
    build_exp01_authorized_training_input_v2,
    build_exp01_run_authorization_v2,
    Exp01SeedRunReceiptV2,
    GDNNeighborPolicyV2,
    GDNV2NeighborError,
    select_self_excluded_neighbors_v2,
    train_authorized_upstream_aligned_seed_v2,
)
from paperworks.gdn.upstream_candidate_backend_v1 import (
    UpstreamGDNDependencyError,
    UpstreamGDNTrainingConfigV1,
    build_dependency_status_v1,
    inspect_current_dependency_environment_v1,
)
from paperworks.validation_v2.exp01_gdn_v1 import (
    Exp01ContractError,
    Exp01Disposition,
    build_exp01_analysis_receipt_v1,
    build_exp01_contribution_evidence_v1,
    build_exp01_preregistration_v1,
    compute_set_stability_v1,
    evaluate_graph_guided_inclusion_rule_v1,
    stable_seed_pairs_v1,
    unique_candidate_pairs_v1,
)
from paperworks.validation_v2.exp01_runner_v1 import execute_exp01_corrected_arm_v1
from paperworks.validation_v2.schema_registry_v1 import (
    ValidationV2SchemaRegistryError,
    validate_validation_v2_document_v1,
)
from paperworks.v6.common import stable_hash_v1


SHA = "a" * 64
COMMIT = "b" * 40


class Exp01GDNV1Tests(unittest.TestCase):
    def test_self_is_removed_before_top5_and_ties_use_lowest_index(self) -> None:
        matrix = []
        for target in range(7):
            row = [1.0 for _ in range(7)]
            row[target] = 100.0
            matrix.append(row)
        selected = select_self_excluded_neighbors_v2(matrix)
        for target, neighbors in enumerate(selected):
            self.assertEqual(5, len(neighbors))
            self.assertNotIn(target, neighbors)
            self.assertEqual(tuple(index for index in range(7) if index != target)[:5], neighbors)

    def test_neighbor_contract_is_non_mutating_and_rejects_invalid_matrix(self) -> None:
        matrix = [[float(row == column) for column in range(6)] for row in range(6)]
        original = [row[:] for row in matrix]
        select_self_excluded_neighbors_v2(matrix)
        self.assertEqual(original, matrix)
        with self.assertRaises(GDNV2NeighborError):
            select_self_excluded_neighbors_v2([[1.0] * 5 for _ in range(5)])
        bad = [[0.0] * 6 for _ in range(6)]
        bad[0][1] = float("nan")
        with self.assertRaises(GDNV2NeighborError):
            select_self_excluded_neighbors_v2(bad)

    def test_neighbor_policy_rejects_changed_k_or_tie_policy(self) -> None:
        with self.assertRaises(GDNV2NeighborError):
            GDNNeighborPolicyV2(topk=4)
        with self.assertRaises(GDNV2NeighborError):
            GDNNeighborPolicyV2(tie_policy="UNSTABLE")

    def test_forward_and_extraction_both_call_same_v2_selector(self) -> None:
        source = inspect.getsource(__import__(
            "paperworks.gdn.upstream_candidate_backend_v2",
            fromlist=["train_upstream_aligned_seed_v2"],
        ))
        self.assertGreaterEqual(source.count("stable_torch_neighbors_v2(cosine"), 2)
        self.assertIn("fill_diagonal_(float(\"-inf\"))", source)

    def test_missing_exact_optional_dependency_fails_before_training(self) -> None:
        status = build_dependency_status_v1((inspect_current_dependency_environment_v1(),))
        if status.exact_backend_available:
            self.skipTest("exact optional GDN dependency is available")
        features = tuple(f"P1_F{index}" for index in range(6))
        config = UpstreamGDNTrainingConfigV1()
        registration = self._registration(config.hyperparameter_hash)
        authorization = build_exp01_run_authorization_v2(
            preregistration_hash=registration.preregistration_hash,
            data_authority_hash=registration.data_authority_hash,
            feature_contract_hash=registration.feature_contract_hash,
            candidate_universe_hash=registration.candidate_universe_hash,
            training_config_hash=config.hyperparameter_hash,
            neighbor_policy_hash=registration.neighbor_policy_hash,
            source_commit=registration.source_commit,
        )
        inputs = build_exp01_authorized_training_input_v2(
            segments=(((0.0,) * 6,) * 8,),
            feature_order=features,
            candidate_pairs=((features[0], features[1]),),
            data_authority_hash=registration.data_authority_hash,
            feature_contract_hash=registration.feature_contract_hash,
            candidate_universe_hash=registration.candidate_universe_hash,
        )
        with self.assertRaises(UpstreamGDNDependencyError):
            train_authorized_upstream_aligned_seed_v2(
                authorization=authorization,
                inputs=inputs,
                seed=11,
                config=config,
            )

    def _registration(self, training_config_hash: str = "f" * 64):
        return build_exp01_preregistration_v1(
            source_commit=COMMIT,
            protocol_hash=SHA,
            candidate_universe_hash="c" * 64,
            feature_contract_hash="d" * 64,
            data_authority_hash="e" * 64,
            training_config_hash=training_config_hash,
        )

    def _authorized_context(self):
        config = UpstreamGDNTrainingConfigV1()
        registration = self._registration(config.hyperparameter_hash)
        authorization = build_exp01_run_authorization_v2(
            preregistration_hash=registration.preregistration_hash,
            data_authority_hash=registration.data_authority_hash,
            feature_contract_hash=registration.feature_contract_hash,
            candidate_universe_hash=registration.candidate_universe_hash,
            training_config_hash=registration.training_config_hash,
            neighbor_policy_hash=registration.neighbor_policy_hash,
            source_commit=registration.source_commit,
        )
        features = tuple(f"P1_F{index}" for index in range(6))
        inputs = build_exp01_authorized_training_input_v2(
            segments=(((0.0,) * 6,) * 8,), feature_order=features,
            candidate_pairs=((features[0], features[1]),),
            data_authority_hash=registration.data_authority_hash,
            feature_contract_hash=registration.feature_contract_hash,
            candidate_universe_hash=registration.candidate_universe_hash,
        )
        return registration, authorization, inputs, config

    @staticmethod
    def _seed_receipt(seed, registration, authorization, inputs, config):
        graph_hash = stable_hash_v1({"selected_edges": (), "candidate_similarities": ()})
        internal_hash = stable_hash_v1({"neighbor_indices": ((1, 2, 3, 4, 5),)})
        provisional = Exp01SeedRunReceiptV2(
            seed=seed,
            preregistration_hash=registration.preregistration_hash,
            authorization_hash=authorization.authorization_hash,
            input_hash=inputs.input_hash,
            neighbor_policy_hash=registration.neighbor_policy_hash,
            training_config_hash=config.hyperparameter_hash,
            forward_internal_graph_hash=internal_hash,
            extraction_internal_graph_hash=internal_hash,
            selected_edges=(), candidate_similarities=(), epoch_count=1,
            best_validation_loss=0.5, graph_hash=graph_hash,
        )
        return Exp01SeedRunReceiptV2(
            **{**provisional.__dict__, "receipt_hash": stable_hash_v1(provisional.to_dict(include_hash=False))}
        )

    def test_preregistration_is_self_hashed_and_forbids_test_or_labels(self) -> None:
        registration = self._registration()
        self.assertEqual(
            registration.preregistration_hash,
            stable_hash_v1(registration.to_dict(include_hash=False)),
        )
        with self.assertRaises(Exp01ContractError):
            dataclasses.replace(registration, test1_authorized=True)
        with self.assertRaises(Exp01ContractError):
            dataclasses.replace(registration, heldout_authorized=True)
        with self.assertRaises(Exp01ContractError):
            dataclasses.replace(registration, primary_k=30)
        with self.assertRaises(Exp01ContractError):
            dataclasses.replace(registration, test2_authorized="no")
        self.assertIn("seed_stability_rule", registration.to_dict(include_hash=False))
        self.assertIn("intervention_rule", registration.to_dict(include_hash=False))

    def test_rehashed_modified_registration_still_fails_frozen_policy(self) -> None:
        registration = self._registration()
        document = registration.to_dict(include_hash=False)
        document["primary_k"] = 30
        document["preregistration_hash"] = stable_hash_v1(document)
        with self.assertRaises(Exp01ContractError):
            type(registration)(
                source_commit=document["source_commit"],
                protocol_hash=document["protocol_hash"],
                candidate_universe_hash=document["candidate_universe_hash"],
                feature_contract_hash=document["feature_contract_hash"],
                data_authority_hash=document["data_authority_hash"],
                neighbor_policy_hash=document["neighbor_policy_hash"],
                training_config_hash=document["training_config_hash"],
                primary_k=document["primary_k"],
                preregistration_hash=document["preregistration_hash"],
            )

    def test_stability_and_unique_provenance_are_exact_set_operations(self) -> None:
        a = (("s1", "t1"), ("s2", "t2"))
        b = (("s2", "t2"), ("s3", "t3"))
        metric = compute_set_stability_v1(a, b)
        self.assertEqual((1, 3), (metric.jaccard_numerator, metric.jaccard_denominator))
        self.assertAlmostEqual(1 / 3, metric.jaccard)
        stable = stable_seed_pairs_v1({11: a, 23: b, 37: (("s2", "t2"),)})
        self.assertEqual(frozenset({("s2", "t2")}), stable)
        unique = unique_candidate_pairs_v1(
            corrected_gdn=a,
            meta=(("s1", "t1"),),
            stat=(("s3", "t3"),),
        )
        self.assertEqual(frozenset({("s2", "t2")}), unique)

    def _evidence(self, **overrides):
        registration = self._registration()
        pair = (("s1", "t1"),)
        values = {
            "preregistration_hash": registration.preregistration_hash,
            "candidate_universe_hash": registration.candidate_universe_hash,
            "training_config_hash": registration.training_config_hash,
            "neighbor_policy_hash": registration.neighbor_policy_hash,
            "seed_run_receipt_hashes": ("1" * 64, "2" * 64, "3" * 64),
            "authority_complete": True,
            "execution_complete": True,
            "privacy_pass": True,
            "all_required_seeds_complete": True,
            "corrected_self_neighbor_count": 0,
            "forward_extraction_match": True,
            "corrected_top20_pairs": pair,
            "unique_pairs": pair,
            "seed_stable_pairs": pair,
            "split_stable_pairs": pair,
            "confirmed_pairs": pair,
            "primary_mask_pairs": pair,
            "masking_delta_by_seed": (1.0, 1.0, -0.1),
            "masking_baseline_by_seed": (2.0, 2.0, 2.0),
            "prohibited_input_used": False,
            "result_driven_change_used": False,
            "failure_reason": None,
        }
        values.update(overrides)
        common = {
            "preregistration_hash": values["preregistration_hash"],
            "candidate_universe_hash": values["candidate_universe_hash"],
            "training_config_hash": values["training_config_hash"],
            "neighbor_policy_hash": values["neighbor_policy_hash"],
        }
        values["checkpoint_receipt"] = build_exp01_analysis_receipt_v1(
            receipt_type="CHECKPOINT_SET",
            input_hashes=values["seed_run_receipt_hashes"],
            output_hash=stable_hash_v1({"seed_run_receipt_hashes": values["seed_run_receipt_hashes"]}),
            **common,
        )
        values["provenance_receipt"] = build_exp01_analysis_receipt_v1(
            receipt_type="PROVENANCE",
            input_hashes=(values["checkpoint_receipt"].receipt_hash,),
            output_hash=stable_hash_v1({
                "corrected_top20_pairs": values["corrected_top20_pairs"],
                "unique_pairs": values["unique_pairs"],
                "seed_stable_pairs": values["seed_stable_pairs"],
                "split_stable_pairs": values["split_stable_pairs"],
            }),
            **common,
        )
        values["confirmation_receipt"] = build_exp01_analysis_receipt_v1(
            receipt_type="CONFIRMATION",
            input_hashes=(values["provenance_receipt"].receipt_hash,),
            output_hash=stable_hash_v1({"confirmed_pairs": values["confirmed_pairs"]}),
            **common,
        )
        values["intervention_receipt"] = build_exp01_analysis_receipt_v1(
            receipt_type="INTERVENTION",
            input_hashes=(
                values["confirmation_receipt"].receipt_hash,
                values["checkpoint_receipt"].receipt_hash,
            ),
            output_hash=stable_hash_v1({
                "primary_mask_pairs": values["primary_mask_pairs"],
                "masking_delta_by_seed": values["masking_delta_by_seed"],
                "masking_baseline_by_seed": values["masking_baseline_by_seed"],
            }),
            **common,
        )
        return build_exp01_contribution_evidence_v1(**values)

    def test_inclusion_rule_retain_demote_and_fail_closed(self) -> None:
        passing = self._evidence()
        self.assertEqual(passing.evidence_hash, stable_hash_v1(passing.to_dict(include_hash=False)))
        self.assertEqual(
            Exp01Disposition.RETAIN_GRAPH_GUIDED_CONDITIONALLY,
            evaluate_graph_guided_inclusion_rule_v1(passing),
        )
        self.assertEqual(
            Exp01Disposition.DEMOTE_GDN_TO_ABLATION,
            evaluate_graph_guided_inclusion_rule_v1(self._evidence(
                corrected_top20_pairs=(), unique_pairs=(), seed_stable_pairs=(),
                split_stable_pairs=(), confirmed_pairs=(), primary_mask_pairs=(),
                masking_delta_by_seed=(0.0, 0.0, 0.0),
            )),
        )
        with self.assertRaises(Exp01ContractError):
            self._evidence(primary_mask_pairs=(("foreign", "target"),))
        failed = self._evidence(
            authority_complete=False, execution_complete=False,
            all_required_seeds_complete=False, forward_extraction_match=False,
            corrected_top20_pairs=(), unique_pairs=(), seed_stable_pairs=(),
            split_stable_pairs=(), confirmed_pairs=(), primary_mask_pairs=(),
            masking_delta_by_seed=(0.0, 0.0, 0.0),
            masking_baseline_by_seed=(0.0, 0.0, 0.0),
            failure_reason="OPTIONAL_DEPENDENCY_UNAVAILABLE",
        )
        self.assertEqual(
            Exp01Disposition.GDN_CONTRIBUTION_UNRESOLVED_FAIL_CLOSED,
            evaluate_graph_guided_inclusion_rule_v1(failed),
        )

    def test_incomplete_evidence_requires_reason(self) -> None:
        with self.assertRaises(Exp01ContractError):
            self._evidence(
                authority_complete=False, execution_complete=False,
                all_required_seeds_complete=False, forward_extraction_match=False,
            )

    def test_empty_or_foreign_mask_cannot_carry_positive_result(self) -> None:
        with self.assertRaises(Exp01ContractError):
            self._evidence(
                corrected_top20_pairs=(), unique_pairs=(), seed_stable_pairs=(),
                split_stable_pairs=(), confirmed_pairs=(), primary_mask_pairs=(),
                masking_delta_by_seed=(1.0, 0.0, 0.0),
                masking_baseline_by_seed=(1.0, 1.0, 1.0),
            )

    def test_adversarial_evidence_shapes_booleans_duplicates_and_overflow_fail(self) -> None:
        with self.assertRaises(Exp01ContractError):
            self._evidence(masking_delta_by_seed=(1.0, 1.0, 1.0, 1.0))
        with self.assertRaises(Exp01ContractError):
            self._evidence(masking_baseline_by_seed=(1.0, 1.0))
        with self.assertRaises(Exp01ContractError):
            self._evidence(authority_complete="yes")
        with self.assertRaises(Exp01ContractError):
            self._evidence(corrected_top20_pairs=(("s1", "t1"), ("s1", "t1")))
        overflow = tuple((f"s{index}", f"t{index}") for index in range(21))
        with self.assertRaises(Exp01ContractError):
            self._evidence(
                corrected_top20_pairs=overflow, unique_pairs=overflow,
                seed_stable_pairs=overflow, split_stable_pairs=overflow,
                confirmed_pairs=overflow, primary_mask_pairs=overflow,
            )

    def test_evidence_and_receipt_hashes_fail_closed_on_forgery(self) -> None:
        evidence = self._evidence()
        with self.assertRaises(Exp01ContractError):
            dataclasses.replace(evidence, evidence_hash="f" * 64)
        with self.assertRaises(Exp01ContractError):
            dataclasses.replace(evidence, seed_run_receipt_hashes=("1" * 64, "2" * 64))
        with self.assertRaises(Exp01ContractError):
            dataclasses.replace(
                evidence,
                intervention_receipt=dataclasses.replace(
                    evidence.intervention_receipt, output_hash="f" * 64, receipt_hash=""
                ),
                evidence_hash="",
            )

    def test_authority_gated_runner_rejects_mismatch_before_optional_backend(self) -> None:
        registration, authorization, inputs, config = self._authorized_context()
        forged = dataclasses.replace(authorization, data_authority_hash="9" * 64, authorization_hash="")
        forged = build_exp01_run_authorization_v2(**{
            name: value for name, value in forged.__dict__.items() if name != "authorization_hash"
        })
        with self.assertRaises(Exp01ContractError):
            execute_exp01_corrected_arm_v1(
                preregistration=registration, authorization=forged, inputs=inputs, config=config,
            )

    def test_authority_gated_runner_freezes_three_seed_bundle(self) -> None:
        registration, authorization, inputs, config = self._authorized_context()
        def fake_train(**values):
            return self._seed_receipt(
                values["seed"], registration, authorization, inputs, config
            )
        with mock.patch(
            "paperworks.validation_v2.exp01_runner_v1.train_authorized_upstream_aligned_seed_v2",
            side_effect=fake_train,
        ):
            receipts, bundle = execute_exp01_corrected_arm_v1(
                preregistration=registration, authorization=authorization,
                inputs=inputs, config=config,
            )
        self.assertEqual((11, 23, 37), tuple(receipt.seed for receipt in receipts))
        self.assertEqual(bundle.bundle_hash, stable_hash_v1(bundle.to_dict(include_hash=False)))
        evidence = self._evidence()
        documents = (
            ("exp01_preregistration_v1.schema.json", registration.to_dict()),
            ("exp01_run_authorization_v2.schema.json", authorization.to_dict()),
            ("exp01_authorized_training_input_v2.schema.json", inputs.to_dict()),
            ("exp01_seed_run_receipt_v2.schema.json", receipts[0].to_dict()),
            ("exp01_seed_bundle_receipt_v1.schema.json", bundle.to_dict()),
            ("exp01_analysis_receipt_v1.schema.json", evidence.checkpoint_receipt.to_dict()),
            ("exp01_contribution_evidence_v1.schema.json", evidence.to_dict()),
        )
        for filename, document in documents:
            with self.subTest(filename=filename):
                validate_validation_v2_document_v1(filename, document)

    def test_analysis_receipt_input_lineage_is_exact(self) -> None:
        evidence = self._evidence()
        forged = build_exp01_analysis_receipt_v1(
            receipt_type="PROVENANCE",
            preregistration_hash=evidence.preregistration_hash,
            candidate_universe_hash=evidence.candidate_universe_hash,
            training_config_hash=evidence.training_config_hash,
            neighbor_policy_hash=evidence.neighbor_policy_hash,
            input_hashes=("9" * 64,),
            output_hash=evidence.provenance_receipt.output_hash,
        )
        with self.assertRaises(Exp01ContractError):
            dataclasses.replace(evidence, provenance_receipt=forged, evidence_hash="")

    def test_runner_rejects_wrong_seed_receipt_policy_binding(self) -> None:
        registration, authorization, inputs, config = self._authorized_context()
        def fake_train(**values):
            receipt = self._seed_receipt(values["seed"], registration, authorization, inputs, config)
            provisional = dataclasses.replace(
                receipt, neighbor_policy_hash="9" * 64, receipt_hash=""
            )
            return dataclasses.replace(
                provisional,
                receipt_hash=stable_hash_v1(provisional.to_dict(include_hash=False)),
            )
        with mock.patch(
            "paperworks.validation_v2.exp01_runner_v1.train_authorized_upstream_aligned_seed_v2",
            side_effect=fake_train,
        ):
            with self.assertRaises(Exp01ContractError):
                execute_exp01_corrected_arm_v1(
                    preregistration=registration, authorization=authorization,
                    inputs=inputs, config=config,
                )

    def test_exp01_schemas_reject_material_type_and_safety_mutations(self) -> None:
        registration, authorization, inputs, config = self._authorized_context()
        receipt = self._seed_receipt(11, registration, authorization, inputs, config)
        evidence = self._evidence()
        mutations = (
            ("exp01_preregistration_v1.schema.json", registration.to_dict(), "test2_authorized", "YES"),
            ("exp01_preregistration_v1.schema.json", registration.to_dict(), "primary_k", "twenty"),
            ("exp01_preregistration_v1.schema.json", registration.to_dict(), "seeds", "not-array"),
            ("exp01_run_authorization_v2.schema.json", authorization.to_dict(), "labels_authorized", 0),
            ("exp01_authorized_training_input_v2.schema.json", inputs.to_dict(), "feature_order", "not-array"),
            ("exp01_seed_run_receipt_v2.schema.json", receipt.to_dict(), "seed", 99),
            ("exp01_analysis_receipt_v1.schema.json", evidence.checkpoint_receipt.to_dict(), "receipt_type", "UNKNOWN"),
            ("exp01_contribution_evidence_v1.schema.json", evidence.to_dict(), "authority_complete", "yes"),
        )
        for filename, original, field, bad_value in mutations:
            document = copy.deepcopy(original)
            document[field] = bad_value
            with self.subTest(filename=filename, field=field), self.assertRaises(
                ValidationV2SchemaRegistryError
            ):
                validate_validation_v2_document_v1(filename, document)


if __name__ == "__main__":
    unittest.main()
