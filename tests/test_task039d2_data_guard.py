from __future__ import annotations

import inspect
import unittest
from pathlib import Path
from unittest.mock import patch

from paperworks.profiling import task039d2_confirmation_v1 as d2


class TASK039D2DataGuardTests(unittest.TestCase):
    def test_current_real_execution_status_is_false(self) -> None:
        self.assertFalse(d2.D2_REAL_EXECUTION_AUTHORIZED)
        receipt = d2.build_synthetic_preparation_execution_receipt_v1()
        self.assertFalse(receipt["real_hai_files_accessed"])
        self.assertFalse(receipt["d1_private_ledgers_accessed"])
        self.assertFalse(receipt["d2_authorization_present"])
        self.assertFalse(receipt["real_d2_execution_possible"])
        self.assertFalse(receipt["rule_v2_authorized"])

    def test_missing_authorization_stops_before_any_file_open(self) -> None:
        with patch.object(Path, "open", autospec=True) as mocked_open:
            with self.assertRaisesRegex(
                d2.TASK039D2PreparationError,
                "blocked_task039d2_authorization_absent",
            ):
                d2.run_future_real_confirmation_from_file_v1(
                    Path("hai-23.05/hai-train3.csv")
                )
            mocked_open.assert_not_called()

    def test_raw_mapping_or_boolean_cannot_bypass_authorization_contract(self) -> None:
        for invalid in ({"real_hai_train3_access_authorized": True}, True, object()):
            with self.subTest(invalid_type=type(invalid).__name__):
                with self.assertRaisesRegex(
                    d2.TASK039D2PreparationError,
                    "blocked_task039d2_authorization_invalid",
                ):
                    d2.require_real_execution_authorization_v1(invalid)  # type: ignore[arg-type]

    def test_no_real_loader_cli_or_bypass_flag_exists(self) -> None:
        module_source = inspect.getsource(d2)
        engine_source = inspect.getsource(d2.confirm_synthetic_relations_v1)
        self.assertNotIn("argparse", module_source)
        self.assertNotIn("bypass", module_source.lower())
        self.assertNotIn(".open(", engine_source)
        self.assertNotIn("read_csv", engine_source)
        self.assertNotIn("hai-train", engine_source)
        authorization_instances = [
            value
            for value in vars(d2).values()
            if isinstance(value, d2.TASK039D2AuthorizationV1)
        ]
        self.assertEqual(authorization_instances, [])

    def test_synthetic_wrapper_rejects_unmarked_or_non_synthetic_values(self) -> None:
        values = {"x": tuple(0.0 for _ in range(10))}
        with self.assertRaisesRegex(d2.TASK039D2PreparationError, "marked synthetic"):
            d2.SyntheticTrain3ValueMapV1(fixture_id="train3", values=values)
        with self.assertRaisesRegex(d2.TASK039D2PreparationError, "synthetic values only"):
            d2.SyntheticTrain3ValueMapV1(
                fixture_id="synthetic_guard",
                values=values,
                synthetic_only=False,
            )


if __name__ == "__main__":
    unittest.main()
