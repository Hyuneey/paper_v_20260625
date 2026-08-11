from dataclasses import FrozenInstanceError, replace
import unittest

from paperworks.v6.task039e2_audit_prep_v1 import (
    EXPECTED_MODEL_SNAPSHOT,
    IndependentFreezeHashBindingsV1,
    TASK039E2AuditPreparationError,
)
from task039e2_audit_support import make_configuration, make_hash_bindings, synthetic_hash


class Task039E2AuditConfigTests(unittest.TestCase):
    def test_exact_provider_configuration_and_all_hash_bindings(self) -> None:
        configuration = make_configuration()
        bindings = make_hash_bindings()
        self.assertEqual(configuration.model, EXPECTED_MODEL_SNAPSHOT)
        self.assertIsNone(configuration.seed)
        self.assertFalse(configuration.stream)
        self.assertFalse(configuration.store)
        self.assertFalse(configuration.model_fallback)
        bindings.assert_matches_configuration(configuration)
        self.assertEqual(
            configuration.to_dict()["artifact_hash"], configuration.artifact_hash
        )

    def test_exact_config_drift_rejected(self) -> None:
        cases = (
            ("provider", "azure-openai"),
            ("endpoint", "/v1/responses"),
            ("model", "gpt-5.4"),
            ("model", "gpt-5.4-2026-03-06"),
            ("reasoning", "low"),
            ("temperature", 0.0),
            ("top_p", 0.9),
            ("top_p", 1),
            ("max_completion_tokens", 2048),
            ("max_completion_tokens", 1024.0),
            ("seed", 7),
            ("stream", True),
            ("stream", 0),
            ("store", True),
            ("store", 0),
            ("model_fallback", True),
            ("model_fallback", 0),
        )
        for field_name, bad_value in cases:
            with self.subTest(field_name=field_name, bad_value=bad_value):
                with self.assertRaises(TASK039E2AuditPreparationError):
                    make_configuration(**{field_name: bad_value})

    def test_missing_prompt_family_or_hash_binding_mismatch_rejected(self) -> None:
        bindings = make_hash_bindings()
        with self.assertRaises(TASK039E2AuditPreparationError):
            IndependentFreezeHashBindingsV1(
                prompt_family_hashes=bindings.prompt_family_hashes[:-1],
                structured_schema_hash=bindings.structured_schema_hash,
                rendering_policy_hash=bindings.rendering_policy_hash,
                retrieval_policy_hash=bindings.retrieval_policy_hash,
                t0_template_hash=bindings.t0_template_hash,
                schedule_hash=bindings.schedule_hash,
                retry_policy_hash=bindings.retry_policy_hash,
                direct_number_role_policy_hash=bindings.direct_number_role_policy_hash,
            )
        bad_configuration = make_configuration(schedule_hash=synthetic_hash("other"))
        with self.assertRaises(TASK039E2AuditPreparationError):
            bindings.assert_matches_configuration(bad_configuration)

    def test_configuration_is_immutable(self) -> None:
        configuration = make_configuration()
        with self.assertRaises(FrozenInstanceError):
            configuration.model = "gpt-5.4"  # type: ignore[misc]
        with self.assertRaises(TASK039E2AuditPreparationError):
            replace(configuration, execution_started=True)


if __name__ == "__main__":
    unittest.main()
