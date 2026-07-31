from __future__ import annotations

import copy
import unittest
from dataclasses import replace

from paperworks.data.adapters_v2 import (
    AdapterStatusV2,
    LegacySealedPolicyContextV2,
    adapt_data_view_manifest_v1,
    adapt_dataset_manifest_v1,
    adapt_split_manifest_v1,
)
from paperworks.data.contracts import SplitRole
from paperworks.data.contracts_v2 import (
    SealedAccessStatusV2,
    SplitRoleV2,
)
from paperworks.data.splits_v2 import (
    DataOperationV2,
    SplitPermissionV2Error,
    assert_operation_permitted_v2,
)
from tests.task039p1a_support import (
    creation_metadata,
    legacy_data_view_manifest,
    legacy_dataset_manifest,
    legacy_split_manifest,
)


class Task039P1AAdaptersV2Tests(unittest.TestCase):
    def test_dataset_adapter_preserves_hash_and_reports_information_loss(self) -> None:
        source = legacy_dataset_manifest()
        before = copy.deepcopy(source.to_dict())
        first = adapt_dataset_manifest_v1(
            source, creation_metadata=creation_metadata()
        )
        second = adapt_dataset_manifest_v1(
            source, creation_metadata=creation_metadata()
        )
        self.assertEqual(first.status, AdapterStatusV2.CREATED)
        self.assertEqual(first.source_artifact_hash, source.manifest_id)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertTrue(first.information_loss)
        self.assertEqual(source.to_dict(), before)
        self.assertIsNone(first.artifact.available_process_ids)

    def test_dataset_adapter_preserves_unlisted_legacy_file_hashes(self) -> None:
        source = legacy_dataset_manifest()
        source = replace(
            source,
            file_fingerprints={
                **source.file_fingerprints,
                "additional.csv": "e" * 64,
            },
        )
        result = adapt_dataset_manifest_v1(
            source, creation_metadata=creation_metadata()
        )
        self.assertEqual(result.status, AdapterStatusV2.CREATED)
        observed = {
            item.relative_local_path: item.sha256 for item in result.artifact.files
        }
        self.assertEqual(observed["legacy.csv"], "a" * 64)
        self.assertEqual(observed["additional.csv"], "e" * 64)

    def test_data_view_adapter_does_not_infer_process_or_calibration_fidelity(
        self,
    ) -> None:
        source = legacy_data_view_manifest()
        result = adapt_data_view_manifest_v1(
            source, creation_metadata=creation_metadata()
        )
        self.assertEqual(result.status, AdapterStatusV2.CREATED)
        self.assertIsNone(result.artifact.process_scope)
        self.assertFalse(result.artifact.second_level_rule_calibration_allowed)
        self.assertIsNone(
            result.artifact.aggregation.source_sampling_interval_seconds
        )

    def test_unambiguous_normal_roles_require_explicit_matching_target(self) -> None:
        cases = (
            (SplitRole.TRAIN_NORMAL, SplitRoleV2.NORMAL_CANDIDATE_FIT),
            (
                SplitRole.CALIBRATION_NORMAL,
                SplitRoleV2.NORMAL_RELATION_CALIBRATION,
            ),
        )
        for legacy_role, target_role in cases:
            source = legacy_split_manifest(legacy_role)
            with self.subTest(legacy_role=legacy_role.value):
                pending = adapt_split_manifest_v1(
                    source,
                    requested_target_role=None,
                    creation_metadata=creation_metadata(),
                    process_scope=("process_a",),
                )
                self.assertEqual(pending.status, AdapterStatusV2.PENDING_CONTEXT)
                created = adapt_split_manifest_v1(
                    source,
                    requested_target_role=target_role,
                    creation_metadata=creation_metadata(),
                    process_scope=("process_a",),
                )
                self.assertEqual(created.status, AdapterStatusV2.CREATED)
                self.assertEqual(created.artifact.role, target_role)
                self.assertEqual(created.source_artifact_hash, source.split_id)

    def test_legacy_validation_is_never_silently_mapped(self) -> None:
        source = legacy_split_manifest(SplitRole.VALIDATION)
        pending = adapt_split_manifest_v1(
            source,
            requested_target_role=None,
            creation_metadata=creation_metadata(),
            process_scope=("process_a",),
        )
        self.assertEqual(pending.status, AdapterStatusV2.PENDING_CONTEXT)
        for target in (
            SplitRoleV2.DEVELOPMENT,
            SplitRoleV2.INNER_UTILITY,
            SplitRoleV2.OUTER_VALIDATION,
        ):
            result = adapt_split_manifest_v1(
                source,
                requested_target_role=target,
                creation_metadata=creation_metadata(),
                process_scope=("process_a",),
            )
            self.assertEqual(result.status, AdapterStatusV2.CREATED)
            self.assertIn(
                "legacy_validation_semantics_supplied_by_external_context",
                result.information_loss,
            )

    def test_legacy_test_requires_policy_and_never_grants_sealed_access(self) -> None:
        source = legacy_split_manifest(SplitRole.TEST)
        pending = adapt_split_manifest_v1(
            source,
            requested_target_role=SplitRoleV2.SEALED_EVALUATION,
            creation_metadata=creation_metadata(),
            process_scope=("process_a",),
        )
        self.assertEqual(pending.status, AdapterStatusV2.PENDING_CONTEXT)
        exposed = adapt_split_manifest_v1(
            source,
            requested_target_role=SplitRoleV2.SEALED_EVALUATION,
            creation_metadata=creation_metadata(),
            process_scope=("process_a",),
            sealed_policy_context=LegacySealedPolicyContextV2(
                policy_reference="synthetic-policy",
                preregistered=True,
                explicit_approval_recorded=True,
                source_previously_exposed=True,
            ),
        )
        self.assertEqual(exposed.status, AdapterStatusV2.UNSUPPORTED_SOURCE)
        created = adapt_split_manifest_v1(
            source,
            requested_target_role=SplitRoleV2.SEALED_EVALUATION,
            creation_metadata=creation_metadata(),
            process_scope=("process_a",),
            sealed_policy_context=LegacySealedPolicyContextV2(
                policy_reference="synthetic-policy",
                preregistered=True,
                explicit_approval_recorded=True,
                source_previously_exposed=False,
            ),
        )
        self.assertEqual(created.status, AdapterStatusV2.CREATED)
        self.assertFalse(created.sealed_access_granted)
        self.assertEqual(
            created.artifact.sealed_access_status,
            SealedAccessStatusV2.APPROVAL_REQUIRED,
        )
        with self.assertRaises(SplitPermissionV2Error):
            assert_operation_permitted_v2(
                created.artifact, DataOperationV2.RUN_SEALED_EVALUATION
            )

    def test_split_adapter_never_infers_process_scope(self) -> None:
        source = legacy_split_manifest(SplitRole.TRAIN_NORMAL)
        result = adapt_split_manifest_v1(
            source,
            requested_target_role=SplitRoleV2.NORMAL_CANDIDATE_FIT,
            creation_metadata=creation_metadata(),
            process_scope=None,
        )
        self.assertEqual(result.status, AdapterStatusV2.PENDING_CONTEXT)
        self.assertIn("explicit_process_scope_required", result.information_loss)


if __name__ == "__main__":
    unittest.main()
