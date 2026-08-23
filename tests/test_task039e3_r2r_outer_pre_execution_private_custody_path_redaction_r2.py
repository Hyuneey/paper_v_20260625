from __future__ import annotations

import inspect
import unittest

from scripts import remediate_task039e3_r2r_outer_pre_execution_private_custody_path_redaction_r2 as mod


def binding(**changes: str) -> mod.LocalBindingDocumentR2:
    values = {name: f"SYNTHETIC_LOCATOR_{index}" for index, name in enumerate(mod.CANONICAL_FIELDS)}
    values.update(changes)
    return mod.LocalBindingDocumentR2(mod.OuterLocalBindingSchemaAdapterR2.schema_version, values)


def artifact(**changes: object) -> mod.PrivateArtifactCandidateR2:
    values: dict[str, object] = {
        "role": "task039e3_r2r_d0_pca_model_artifact_v1",
        "expected_role": "task039e3_r2r_d0_pca_model_artifact_v1",
        "expected_hash": "a" * 64,
        "observed_hash": "a" * 64,
    }
    values.update(changes)
    return mod.PrivateArtifactCandidateR2(**values)


class OuterPreExecutionCustodyR2Tests(unittest.TestCase):
    def rejected(self, call) -> None:
        with self.assertRaises(mod.OuterR2Error):
            call()

    def test_01_exact_canonical_schema_accepted(self) -> None:
        self.assertEqual(set(mod.OuterLocalBindingSchemaAdapterR2.adapt(binding())), set(mod.CANONICAL_FIELDS))

    def test_02_obsolete_r1_schema_rejected(self) -> None:
        value = binding()
        fields = dict(value.fields)
        fields.pop(mod.MAIN_REGISTRY)
        fields["TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_REGISTRY_V1"] = "SYNTHETIC"
        self.rejected(lambda: mod.OuterLocalBindingSchemaAdapterR2.adapt(
            mod.LocalBindingDocumentR2(value.schema_version, fields)))

    def test_03_wrong_schema_version_rejected(self) -> None:
        self.rejected(lambda: mod.OuterLocalBindingSchemaAdapterR2.adapt(
            mod.LocalBindingDocumentR2("WRONG", dict(binding().fields))))

    def test_04_wrong_field_name_rejected(self) -> None:
        fields = dict(binding().fields); fields["UNKNOWN"] = fields.pop(mod.MODEL)
        self.rejected(lambda: mod.OuterLocalBindingSchemaAdapterR2.adapt(
            mod.LocalBindingDocumentR2(mod.OuterLocalBindingSchemaAdapterR2.schema_version, fields)))

    def test_05_wrong_binding_object_type_rejected(self) -> None:
        self.rejected(lambda: mod.OuterLocalBindingSchemaAdapterR2.adapt(dict(binding().fields)))

    def test_06_environment_locator_separate_from_hash(self) -> None:
        self.assertEqual(mod.validate_private_artifact_candidate_r2(artifact()), "a" * 64)

    def test_07_missing_required_field_rejected(self) -> None:
        fields = dict(binding().fields); fields.pop(mod.THRESHOLD)
        self.rejected(lambda: mod.OuterLocalBindingSchemaAdapterR2.adapt(
            mod.LocalBindingDocumentR2(mod.OuterLocalBindingSchemaAdapterR2.schema_version, fields)))

    def test_08_optional_unknown_environment_field_rejected(self) -> None:
        fields = dict(binding().fields); fields["OPTIONAL_UNPROVEN"] = "SYNTHETIC"
        self.rejected(lambda: mod.OuterLocalBindingSchemaAdapterR2.adapt(
            mod.LocalBindingDocumentR2(mod.OuterLocalBindingSchemaAdapterR2.schema_version, fields)))

    def test_09_fuzzy_alias_rejected(self) -> None:
        fields = dict(binding().fields); fields[mod.MODEL + "_PATH"] = fields.pop(mod.MODEL)
        self.rejected(lambda: mod.OuterLocalBindingSchemaAdapterR2.adapt(
            mod.LocalBindingDocumentR2(mod.OuterLocalBindingSchemaAdapterR2.schema_version, fields)))

    def test_10_model_exact_hash_required(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(artifact(observed_hash="b" * 64)))

    def test_11_wrong_model_role_rejected(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(artifact(role="WRONG")))

    def test_12_threshold_exact_authority_required(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(artifact(
            role="task039e3_r2r_d0_threshold_artifact_v1",
            expected_role="task039e3_r2r_d0_threshold_artifact_v1", observed_hash="c" * 64)))

    def test_13_threshold_storage_assumption_rejected(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(artifact(storage_type="EMBEDDED")))

    def test_14_exact_namespaces_accepted(self) -> None:
        self.assertEqual(mod.validate_namespaces_r2(dict(mod.NAMESPACE_BINDINGS)), "PASS")

    def test_15_unknown_namespace_rejected(self) -> None:
        changed = dict(mod.NAMESPACE_BINDINGS); changed["UNKNOWN"] = "UNKNOWN"
        self.rejected(lambda: mod.validate_namespaces_r2(changed))

    def test_16_inside_git_rejected(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(artifact(outside_git=False)))

    def test_17_symlink_rejected(self) -> None:
        self.rejected(lambda: mod.validate_private_artifact_candidate_r2(artifact(symlink=True)))

    def test_18_unwritable_root_rejected(self) -> None:
        self.rejected(lambda: mod.validate_sentinel_candidate_r2(mod.SentinelCandidateR2(writable=False)))

    def test_19_sentinel_residue_rejected(self) -> None:
        self.rejected(lambda: mod.validate_sentinel_candidate_r2(mod.SentinelCandidateR2(residue_count=1)))

    def test_20_raw_path_stdout_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/stdout"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(token, (token,)))

    def test_21_raw_path_stderr_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/stderr"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(f"stderr={token}", (token,)))

    def test_22_raw_path_exception_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/exception"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(f"Exception {token}", (token,)))

    def test_23_public_json_path_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/json"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(f'{{"path":"{token}"}}', (token,)))

    def test_24_public_markdown_path_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/markdown"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(f"`{token}`", (token,)))

    def test_25_continuity_path_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/continuity"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(f"HANDOFF {token}", (token,)))

    def test_26_diagnostic_assignment_output_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/assignment"
        self.rejected(lambda: mod.OuterPrivatePathRedactionR2.require_clean(f"PRIVATE_LOCATOR='{token}'", (token,)))

    def test_27_test2_feature_access_rejected(self) -> None:
        self.rejected(lambda: mod.reject_operation_r2("test2_feature_access"))

    def test_28_test2_label_access_rejected(self) -> None:
        self.rejected(lambda: mod.reject_operation_r2("test2_label_access"))

    def test_29_scientific_attempt_increment_rejected(self) -> None:
        self.rejected(lambda: mod.validate_attempt_accounting_r2(1, 0, 0, 0, 0))

    def test_30_private_copy_rejected(self) -> None:
        self.rejected(lambda: mod.reject_operation_r2("private_copy"))

    def test_31_threshold_recalculation_rejected(self) -> None:
        self.rejected(lambda: mod.reject_operation_r2("threshold_recalculation"))

    def test_32_duplicate_json_key_rejected(self) -> None:
        self.rejected(lambda: mod.strict_json(b'{"a":1,"a":2}'))

    def test_33_self_hash_collision_rejected(self) -> None:
        self.rejected(lambda: mod.seal({"artifact_hash": "x"}))

    def test_34_real_path_has_no_scientific_controller(self) -> None:
        source = inspect.getsource(mod.remediate_once_r2)
        for forbidden in ("execute_authorized_outer_v1", "compute_spe_float64_v1", "_evaluate_d1", "metric_values"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
