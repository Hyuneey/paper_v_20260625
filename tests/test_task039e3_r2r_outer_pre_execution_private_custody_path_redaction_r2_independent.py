from __future__ import annotations

import inspect
import unittest

from scripts import remediate_task039e3_r2r_outer_pre_execution_private_custody_path_redaction_r2 as mod


def valid(**changes: object) -> mod.PrivateArtifactCandidateR2:
    values: dict[str, object] = {
        "role": "task039e3_r2r_d0_pca_model_artifact_v1",
        "expected_role": "task039e3_r2r_d0_pca_model_artifact_v1",
        "expected_hash": "d" * 64,
        "observed_hash": "d" * 64,
    }
    values.update(changes)
    return mod.PrivateArtifactCandidateR2(**values)


class OuterPreExecutionCustodyR2IndependentTests(unittest.TestCase):
    def rejected(self, call) -> None:
        with self.assertRaises(mod.OuterR2Error):
            call()

    def canonical(self) -> dict[str, str]:
        return {name: f"SYNTHETIC_{index}" for index, name in enumerate(mod.CANONICAL_FIELDS)}

    def adapt(self, fields: dict[str, str]) -> dict[str, str]:
        return mod.OuterLocalBindingSchemaAdapterR2.adapt(
            mod.LocalBindingDocumentR2(mod.OuterLocalBindingSchemaAdapterR2.schema_version, fields))

    def test_01_r1_expected_schema_substitution_rejected(self) -> None:
        fields = self.canonical(); fields.pop(mod.MAIN_LOCATOR); fields[next(iter(mod.LEGACY_TO_CANONICAL))] = "X"
        self.rejected(lambda: self.adapt(fields))

    def test_02_unproven_alias_rejected(self) -> None:
        fields = self.canonical(); fields["MODEL_LOCATOR"] = fields.pop(mod.MODEL)
        self.rejected(lambda: self.adapt(fields))

    def test_03_flattened_nested_binding_rejected(self) -> None:
        fields = self.canonical(); fields[mod.MODEL] = {"path": "X"}
        self.rejected(lambda: self.adapt(fields))

    def test_04_path_object_confusion_rejected(self) -> None:
        fields = self.canonical(); fields[mod.MODEL] = object()
        self.rejected(lambda: self.adapt(fields))

    def test_05_hash_replaced_by_path_rejected(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(valid(observed_hash="SYNTHETIC_PATH")))

    def test_06_filename_only_validation_rejected(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(valid(observed_hash="e" * 64)))

    def test_07_size_only_validation_rejected(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(valid(observed_hash="f" * 64)))

    def test_08_threshold_recomputation_rejected(self) -> None:
        self.rejected(lambda: mod.reject_operation_r2("threshold_recalculation"))

    def test_09_guessed_environment_variable_rejected(self) -> None:
        fields = self.canonical(); fields["GUESSED_D0_MODEL"] = fields.pop(mod.MODEL)
        self.rejected(lambda: self.adapt(fields))

    def test_10_directory_glob_discovery_rejected(self) -> None:
        self.rejected(lambda: mod.reject_operation_r2("glob_discovery"))

    def test_11_diagnostic_search_leak_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/search"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(f"MATCH={token}", (token,)))

    def test_12_traceback_leak_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/traceback"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(f'File "{token}", line 1', (token,)))

    def test_13_exception_path_repr_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/repr"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(f"WindowsPath('{token}')", (token,)))

    def test_14_readiness_json_path_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/readiness"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(f'{{"root":"{token}"}}', (token,)))

    def test_15_continuity_path_leak_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/state"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(f"CURRENT_STATE={token}", (token,)))

    def test_16_fallback_root_rejected(self) -> None:
        self.rejected(lambda: mod.reject_operation_r2("fallback_root"))

    def test_17_private_copy_workaround_rejected(self) -> None:
        self.rejected(lambda: mod.reject_operation_r2("private_copy"))

    def test_18_symlink_artifact_rejected(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(valid(symlink=True)))

    def test_19_nested_git_artifact_rejected(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(valid(outside_git=False)))

    def test_20_test2_feature_access_rejected(self) -> None:
        self.rejected(lambda: mod.validate_attempt_accounting_r2(0, 1, 0, 1, 0))

    def test_21_test2_label_access_rejected(self) -> None:
        self.rejected(lambda: mod.validate_attempt_accounting_r2(0, 1, 0, 0, 1))

    def test_22_premature_attempt_consumption_rejected(self) -> None:
        self.rejected(lambda: mod.reject_operation_r2("scientific_attempt_increment"))

    def test_23_tracked_copy_rejected(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(valid(tracked_copy_count=1)))

    def test_24_no_prohibited_runtime_tokens_in_real_entry(self) -> None:
        source = inspect.getsource(mod.remediate_once_r2)
        for forbidden in ("execute_authorized_outer_v1", "label-test2", "hai-test2", "metric_values"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
