from __future__ import annotations

import unittest
from dataclasses import replace

from paperworks.v6.task039e2_execution_freeze_prep_v1 import (
    ConstructionExecutionConfigurationV1,
    ConstructionEvidenceRenderingPolicyV1,
    TASK039E2PreparationError,
)
from tests.task039e2_support import (
    synthetic_capability_receipt,
    synthetic_configuration_and_schedule,
)


class ExecutionConfigurationTests(unittest.TestCase):
    def test_synthetic_configuration_cross_binds_capability_and_schedule(self) -> None:
        receipt = synthetic_capability_receipt()
        configuration, schedule = synthetic_configuration_and_schedule()
        configuration.assert_capability_receipt(receipt)
        configuration.assert_schedule(schedule)
        self.assertFalse(configuration.provider_selected)
        self.assertFalse(configuration.model_selected)
        self.assertFalse(configuration.provider_contacted)
        self.assertFalse(configuration.execution_authorized)
        self.assertEqual(
            configuration.construction_evidence_rendering_policy_hash,
            ConstructionEvidenceRenderingPolicyV1().artifact_hash,
        )

    def test_missing_capability_is_disclosed_and_fails_execution_check(self) -> None:
        receipt = replace(
            synthetic_capability_receipt(),
            structured_schema_output_supported=False,
            unsupported_capabilities=("structured_schema_output",),
        )
        self.assertEqual(
            receipt.missing_required_capabilities(),
            ("structured_schema_output",),
        )
        with self.assertRaisesRegex(
            TASK039E2PreparationError, "provider capability missing"
        ):
            receipt.assert_execution_capable()

    def test_undisclosed_missing_capability_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            TASK039E2PreparationError, "explicitly and exactly disclosed"
        ):
            replace(
                synthetic_capability_receipt(),
                stateless_independent_calls_supported=False,
            )

    def test_real_provider_or_model_configuration_is_rejected_in_prep(self) -> None:
        configuration, _ = synthetic_configuration_and_schedule()
        for field_name, value in (
            ("provider_identifier", "SYNTHETIC-PROVIDER-UNAUTHORIZED"),
            ("exact_model_identifier", "SYNTHETIC-MODEL-UNAUTHORIZED"),
        ):
            with self.subTest(field=field_name):
                with self.assertRaisesRegex(
                    TASK039E2PreparationError, "SYNTHETIC_"
                ):
                    replace(configuration, **{field_name: value})

    def test_configuration_rejects_invalid_seed_and_decoding_controls(self) -> None:
        configuration, _ = synthetic_configuration_and_schedule()
        with self.assertRaisesRegex(TASK039E2PreparationError, "fixed seed"):
            replace(configuration, seed_value=None)
        with self.assertRaisesRegex(TASK039E2PreparationError, "top_p"):
            replace(configuration, top_p=1.5)
        with self.assertRaisesRegex(TASK039E2PreparationError, "stateless"):
            replace(configuration, stateless_calls_required=False)

    def test_configuration_seed_policy_must_match_capability_receipt(self) -> None:
        configuration, _ = synthetic_configuration_and_schedule()
        receipt = replace(
            synthetic_capability_receipt(),
            deterministic_decoding_supported=True,
            exposed_seed_control_supported=False,
        )
        configuration = replace(
            configuration, model_capability_receipt_hash=receipt.artifact_hash
        )
        with self.assertRaisesRegex(TASK039E2PreparationError, "fixed seed"):
            configuration.assert_capability_receipt(receipt)


if __name__ == "__main__":
    unittest.main()
