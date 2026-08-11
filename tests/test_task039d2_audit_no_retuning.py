from __future__ import annotations

from dataclasses import replace
import unittest

from paperworks.profiling.task039d2_audit_accounting_v1 import (
    TASK039D2AuditPreparationError,
    verify_private_confirmation_ledger_v1,
)
from paperworks.profiling.task039d2_audit_reference_v1 import (
    AuditFrozenConfirmationPolicyV1,
)
from tests.task039d2_audit_support import (
    make_confirmation_ledger,
    make_input_set,
    rehash_ledger,
)


class AuditNoRetuningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.input_set = make_input_set()

    def test_source_threshold_and_stability_tolerance_cannot_change(self) -> None:
        source = self.input_set.source_parameters[0]
        for field_name, changed_value in (
            ("source_step_threshold", source.source_step_threshold + 0.1),
            (
                "source_stability_tolerance",
                source.source_stability_tolerance + 0.1,
            ),
        ):
            with self.subTest(field=field_name):
                with self.assertRaisesRegex(
                    TASK039D2AuditPreparationError, "record hash mismatch"
                ):
                    replace(source, **{field_name: changed_value})

    def test_target_scale_cannot_change(self) -> None:
        target = self.input_set.target_parameters[0]
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError, "record hash mismatch"
        ):
            replace(target, target_noise_scale=target.target_noise_scale + 0.1)

    def test_direction_and_horizon_must_equal_d1_bindings(self) -> None:
        mutations = (
            ("source_step_direction", "step_down"),
            ("target_response_direction", "decrease"),
            ("selected_horizon_seconds", 60),
        )
        for field_name, value in mutations:
            with self.subTest(field=field_name):
                ledger = make_confirmation_ledger(self.input_set)
                original = ledger["records"][0][field_name]
                if original == value:
                    value = {
                        "source_step_direction": "step_up",
                        "target_response_direction": "increase",
                        "selected_horizon_seconds": 30,
                    }[field_name]
                ledger["records"][0][field_name] = value
                rehash_ledger(ledger, record_index=0)
                with self.assertRaises(TASK039D2AuditPreparationError):
                    verify_private_confirmation_ledger_v1(
                        ledger, input_set=self.input_set
                    )

    def test_all_frozen_window_and_radius_values_reject_changes(self) -> None:
        mutations = (
            {"pre_window_seconds": 4},
            {"post_window_seconds": 6},
            {"minimum_stability_fraction": 0.79},
            {"response_window_seconds": 4},
            {"refractory_period_seconds": 9},
            {"isolation_radius_seconds": 3},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(
                    TASK039D2AuditPreparationError, "retuning is prohibited"
                ):
                    AuditFrozenConfirmationPolicyV1(**mutation)

    def test_alternative_search_and_fallback_are_rejected(self) -> None:
        for field_name in (
            "alternative_horizon_search_performed",
            "opposite_direction_search_performed",
            "lower_ranked_fallback_used",
        ):
            with self.subTest(field=field_name):
                ledger = make_confirmation_ledger(self.input_set)
                ledger["records"][0][field_name] = True
                rehash_ledger(ledger, record_index=0)
                with self.assertRaisesRegex(
                    TASK039D2AuditPreparationError, "retuning or search"
                ):
                    verify_private_confirmation_ledger_v1(
                        ledger, input_set=self.input_set
                    )

    def test_flip_after_failure_and_any_new_search_field_fail_closed(self) -> None:
        ledger = make_confirmation_ledger(self.input_set)
        ledger["records"][0]["target_direction_flipped_after_failure"] = True
        rehash_ledger(ledger, record_index=0)
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError, "fields are not closed"
        ):
            verify_private_confirmation_ledger_v1(
                ledger, input_set=self.input_set
            )

    def test_fit_parameter_reuse_false_is_rejected(self) -> None:
        ledger = make_confirmation_ledger(self.input_set)
        ledger["records"][0]["fit_parameters_reused_without_retuning"] = False
        rehash_ledger(ledger, record_index=0)
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError, "retuning or search"
        ):
            verify_private_confirmation_ledger_v1(
                ledger, input_set=self.input_set
            )


if __name__ == "__main__":
    unittest.main()
