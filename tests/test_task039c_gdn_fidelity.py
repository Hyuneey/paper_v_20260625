from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.gdn.upstream_candidate_backend_v1 import (
    FROZEN_SEEDS,
    FROZEN_UPSTREAM_FILE_IDENTITIES,
    DependencyEnvironmentV1,
    FidelityClassificationV1,
    FidelityFieldAssessmentV1,
    UpstreamFileIdentityV1,
    UpstreamGDNDataBoundaryError,
    UpstreamGDNDependencyError,
    UpstreamGDNFidelityError,
    UpstreamGDNFidelityReceiptV1,
    UpstreamGDNTrainingConfigV1,
    assert_identical_seed_hyperparameters_v1,
    assert_upstream_source_observation_v1,
    authorize_gdn_data_request_v1,
    build_dependency_status_v1,
    build_fidelity_receipt_v1,
    default_fidelity_assessments_v1,
    verify_pinned_upstream_checkout_v1,
)
from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/v6/upstream_gdn_fidelity_receipt_v1_schema.json"
RECEIPT = ROOT / "docs/task_reports/TASK-039C_GDN_FIDELITY.json"


def dependency_status_unavailable():
    return build_dependency_status_v1(
        (
            DependencyEnvironmentV1(
                environment_id="synthetic_CP3_12",
                python_version="3.12.13",
                platform_id="windows-amd64",
                torch_version=None,
                torch_geometric_version=None,
            ),
        )
    )


def verified_source():
    return assert_upstream_source_observation_v1(
        repository="https://github.com/d-ailin/GDN",
        commit="9853899da860682669a134e4af315d036aab4eca",
        detached_head=True,
        clean_worktree=True,
        file_records=FROZEN_UPSTREAM_FILE_IDENTITIES,
    )


class Task039CGDNFidelityTests(unittest.TestCase):
    def test_pinned_upstream_checkout_and_all_frozen_blobs(self) -> None:
        observed = verify_pinned_upstream_checkout_v1(ROOT / "external/gdn")
        self.assertEqual(observed, verified_source())
        self.assertEqual(len(observed.file_records), 7)

    def test_pinned_upstream_commit_mismatch_blocks(self) -> None:
        with self.assertRaisesRegex(UpstreamGDNFidelityError, "commit mismatch"):
            assert_upstream_source_observation_v1(
                repository="https://github.com/d-ailin/GDN",
                commit="0" * 40,
                detached_head=True,
                clean_worktree=True,
                file_records=FROZEN_UPSTREAM_FILE_IDENTITIES,
            )

    def test_required_file_hash_mismatch_blocks(self) -> None:
        changed = list(FROZEN_UPSTREAM_FILE_IDENTITIES)
        original = changed[0]
        changed[0] = UpstreamFileIdentityV1(original.path, original.git_blob_sha, "0" * 64)
        with self.assertRaisesRegex(UpstreamGDNFidelityError, "file identity mismatch"):
            assert_upstream_source_observation_v1(
                repository="https://github.com/d-ailin/GDN",
                commit="9853899da860682669a134e4af315d036aab4eca",
                detached_head=True,
                clean_worktree=True,
                file_records=changed,
            )

    def test_smoke_backend_cannot_claim_scientific_gdn(self) -> None:
        receipt = build_fidelity_receipt_v1(
            source_verification=verified_source(),
            dependency_status=dependency_status_unavailable(),
            implementation_path=ROOT / "src/paperworks/gdn/upstream_candidate_backend_v1.py",
            created_at="2026-08-10T00:00:00+00:00",
        )
        payload = receipt.__dict__.copy()
        payload["backend_id"] = "torch_pyg_cpu_smoke"
        with self.assertRaisesRegex(UpstreamGDNFidelityError, "smoke"):
            UpstreamGDNFidelityReceiptV1(**payload)

    def test_unresolved_material_field_blocks_fidelity(self) -> None:
        assessments = list(default_fidelity_assessments_v1())
        first = assessments[0]
        assessments[0] = FidelityFieldAssessmentV1(
            field_name=first.field_name,
            classification=FidelityClassificationV1.UNRESOLVED,
            upstream_sources=first.upstream_sources,
            implementation_evidence=first.implementation_evidence,
            rationale="Synthetic unresolved-field guard test.",
        )
        receipt = build_fidelity_receipt_v1(
            source_verification=verified_source(),
            dependency_status=dependency_status_unavailable(),
            implementation_path=ROOT / "src/paperworks/gdn/upstream_candidate_backend_v1.py",
            created_at="2026-08-10T00:00:00+00:00",
            assessments=assessments,
        )
        self.assertEqual(receipt.status, "blocked_upstream_gdn_backend_unresolved")
        self.assertEqual(receipt.backend_classification, "upstream_aligned_unverified")
        self.assertEqual(receipt.unresolved_fields, (first.field_name,))

    def test_dependency_unavailable_is_fail_closed(self) -> None:
        status = dependency_status_unavailable()
        self.assertFalse(status.exact_backend_available)
        self.assertEqual(status.dependency_status, "blocked_optional_dependency")
        with self.assertRaises(UpstreamGDNDependencyError):
            type(status)(
                environments=status.environments,
                required_versions=status.required_versions,
                exact_backend_available=True,
                selected_environment_id=status.environments[0].environment_id,
                dependency_status="available",
            )

    def test_exact_seeds_and_no_per_seed_hyperparameter_variation(self) -> None:
        config = UpstreamGDNTrainingConfigV1()
        self.assertEqual(config.seeds, (11, 23, 37))
        assert_identical_seed_hyperparameters_v1({seed: config for seed in FROZEN_SEEDS})
        changed = copy.copy(config)
        object.__setattr__(changed, "batch_size", 31)
        with self.assertRaisesRegex(UpstreamGDNFidelityError, "variation"):
            assert_identical_seed_hyperparameters_v1({11: config, 23: changed, 37: config})

    def test_train3_train4_test_and_br2_pair_inputs_rejected(self) -> None:
        for prohibited in (
            "hai-23.05/hai-train3.csv",
            "hai-23.05/hai-train4.csv",
            "hai-23.05/hai-test1.csv",
        ):
            with self.subTest(prohibited=prohibited):
                with self.assertRaises(UpstreamGDNDataBoundaryError):
                    authorize_gdn_data_request_v1(
                        process_id="P1",
                        split_role="NORMAL_CANDIDATE_FIT",
                        relative_files=("hai-23.05/hai-train1.csv", prohibited),
                        requested_feature_names=("P1_A",),
                    )
        with self.assertRaisesRegex(UpstreamGDNDataBoundaryError, "BR2"):
            authorize_gdn_data_request_v1(
                process_id="P1",
                split_role="NORMAL_CANDIDATE_FIT",
                relative_files=(
                    "hai-23.05/hai-train1.csv",
                    "hai-23.05/hai-train2.csv",
                ),
                requested_feature_names=("P1_A",),
                prohibited_inputs=("BR2_private_relation_ledger",),
            )

    def test_phase_a_receipt_schema_self_hash_and_no_raw_access(self) -> None:
        payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
        Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(payload)
        observed = payload.pop("artifact_hash")
        self.assertEqual(stable_hash_v1(payload), observed)
        self.assertEqual(payload["status"], "passed_upstream_gdn_fidelity")
        self.assertFalse(payload["smoke_backend_used"])
        self.assertFalse(payload["real_hai_feature_values_accessed"])
        self.assertEqual(payload["unresolved_fields"], [])

    def test_public_receipt_contains_no_private_path_or_checkpoint_path(self) -> None:
        text = RECEIPT.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]", text))
        self.assertNotIn("checkpoint_path", text.lower())


if __name__ == "__main__":
    unittest.main()
