from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import unittest
from unittest import mock

from paperworks.validation_v2 import formal_v4_authority_v1 as authority_module
from paperworks.validation_v2.formal_v4_authority_v1 import (
    FormalV4AuthorityError,
    load_formal_v4_numeric_value_map_v1,
)
from paperworks.validation_v2.runtime_v1 import (
    FormalV4ObservationWindowV1,
    execute_formal_v4_batch_v1,
    execute_formal_v4_rule_v1,
    execute_prepared_formal_v4_rule_v1,
    finalize_formal_v4_runtime_session_v1,
    prepare_formal_v4_runtime_session_v1,
    validate_formal_v4_prepared_runtime_finalization_receipt_v1,
)
from tests.test_validation_v2_formal_v4_authority_v1 import V2Fixture


class FormalV4PreparedRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = V2Fixture()

    def tearDown(self) -> None:
        self.fx.close()

    def window(self, **overrides) -> FormalV4ObservationWindowV1:
        values = {
            "opportunity_id": "OP-1",
            "relation_id": "REL-1",
            "feature_contract_hash": self.fx.feature_binding.content_sha256,
            "file_contract_hash": self.fx.file_binding.content_sha256,
            "sampling_contract_hash": self.fx.sampling_binding.content_sha256,
            "event_index": 100,
            "target_response_start_index": 105,
            "source_pre_values": (0.0, 0.0),
            "source_post_values": (2.0, 2.0),
            "target_baseline_values": (10.0, 10.0),
            "target_response_values": (11.0, 11.0),
            "seconds_since_previous_source_trigger": None,
            "seconds_to_nearest_other_source_trigger": None,
            "future_window_complete": True,
        }
        values.update(overrides)
        return FormalV4ObservationWindowV1(**values)

    def test_prepared_and_direct_traces_are_bit_identical(self) -> None:
        windows = (
            self.window(opportunity_id="PASS"),
            self.window(
                opportunity_id="FAIL",
                target_response_values=(10.0, 10.0),
            ),
            self.window(
                opportunity_id="ABSTAIN-SOURCE",
                source_post_values=(0.0, 0.0),
            ),
            self.window(
                opportunity_id="ABSTAIN-TARGET",
                future_window_complete=False,
            ),
            self.window(
                opportunity_id="REL-2-PASS",
                relation_id="REL-2",
                target_response_start_index=160,
                source_pre_values=(2.0, 2.0),
                source_post_values=(0.0, 0.0),
                target_response_values=(9.0, 9.0),
            ),
        )
        direct = tuple(
            execute_formal_v4_rule_v1(
                self.fx.bundle,
                execution_context=self.fx.context,
                repository_root=self.fx.root,
                window=window,
            )
            for window in windows
        )
        session = prepare_formal_v4_runtime_session_v1(
            self.fx.bundle,
            execution_context=self.fx.context,
            repository_root=self.fx.root,
        )
        prepared = tuple(
            execute_prepared_formal_v4_rule_v1(session, window=window)
            for window in windows
        )
        self.assertEqual(
            [item.to_dict() for item in prepared],
            [item.to_dict() for item in direct],
        )
        self.assertEqual(
            [(item.final_outcome, item.reason) for item in prepared],
            [
                ("PASS", "expected_response_observed"),
                ("FAIL", "expected_response_not_observed"),
                ("ABSTAIN", "source_not_triggered"),
                ("ABSTAIN", "incomplete_target_response_window"),
                ("PASS", "expected_response_observed"),
            ],
        )
        receipt = finalize_formal_v4_runtime_session_v1(session)
        self.assertEqual(receipt.evaluated_window_count, len(windows))
        self.assertEqual(receipt.numeric_cache_document_loads, 1)
        self.assertTrue(receipt.bound_bytes_unchanged)

    def test_numeric_batch_loader_reads_document_once(self) -> None:
        original = authority_module._read_exact_json_object_v1
        with mock.patch.object(
            authority_module,
            "_read_exact_json_object_v1",
            wraps=original,
        ) as reader:
            rows = load_formal_v4_numeric_value_map_v1(
                descriptors=self.fx.descriptors,
                numeric_authority_binding=self.fx.numeric_binding,
                repository_root=self.fx.root,
            )
        self.assertEqual(reader.call_count, 1)
        self.assertEqual(
            tuple(relation_id for relation_id, _values in rows),
            tuple(item.relation_id for item in self.fx.descriptors),
        )

    def test_windows_do_not_read_bound_files_after_prepare(self) -> None:
        session = prepare_formal_v4_runtime_session_v1(
            self.fx.bundle,
            execution_context=self.fx.context,
            repository_root=self.fx.root,
        )
        with mock.patch.object(
            Path,
            "read_bytes",
            side_effect=AssertionError("window execution performed bound-file I/O"),
        ):
            for index in range(25):
                trace = execute_prepared_formal_v4_rule_v1(
                    session,
                    window=self.window(opportunity_id=f"OP-{index}"),
                )
                self.assertEqual(trace.final_outcome, "PASS")
        receipt = finalize_formal_v4_runtime_session_v1(session)
        self.assertEqual(receipt.evaluated_window_count, 25)

    def test_safe_batch_returns_only_finalized_complete_result(self) -> None:
        windows = tuple(
            self.window(opportunity_id=f"BATCH-{index}") for index in range(12)
        )
        traces, receipt = execute_formal_v4_batch_v1(
            self.fx.bundle,
            execution_context=self.fx.context,
            repository_root=self.fx.root,
            windows=windows,
        )
        self.assertEqual(len(traces), 12)
        self.assertEqual(receipt.evaluated_window_count, 12)
        self.assertEqual(
            validate_formal_v4_prepared_runtime_finalization_receipt_v1(receipt),
            receipt.receipt_hash,
        )
        with self.assertRaisesRegex(
            FormalV4AuthorityError, "WINDOW_BATCH_INVALID"
        ):
            execute_formal_v4_batch_v1(
                self.fx.bundle,
                execution_context=self.fx.context,
                repository_root=self.fx.root,
                windows=list(windows),  # type: ignore[arg-type]
            )

    def test_batch_bound_file_reads_do_not_scale_with_window_count(self) -> None:
        windows = tuple(
            self.window(opportunity_id=f"READ-{index}") for index in range(8)
        )
        original = Path.read_bytes
        direct_reads = 0

        def count_direct(path):
            nonlocal direct_reads
            direct_reads += 1
            return original(path)

        with mock.patch.object(Path, "read_bytes", new=count_direct):
            for window in windows:
                execute_formal_v4_rule_v1(
                    self.fx.bundle,
                    execution_context=self.fx.context,
                    repository_root=self.fx.root,
                    window=window,
                )

        batch_reads = 0

        def count_batch(path):
            nonlocal batch_reads
            batch_reads += 1
            return original(path)

        with mock.patch.object(Path, "read_bytes", new=count_batch):
            traces, receipt = execute_formal_v4_batch_v1(
                self.fx.bundle,
                execution_context=self.fx.context,
                repository_root=self.fx.root,
                windows=windows,
            )
        self.assertEqual(len(traces), 8)
        self.assertEqual(receipt.evaluated_window_count, 8)
        self.assertGreater(direct_reads, batch_reads)

    def test_finalize_detects_mutation_and_disables_session(self) -> None:
        session = prepare_formal_v4_runtime_session_v1(
            self.fx.bundle,
            execution_context=self.fx.context,
            repository_root=self.fx.root,
        )
        execute_prepared_formal_v4_rule_v1(session, window=self.window())
        numeric_path = self.fx.root / self.fx.numeric_binding.relative_path
        numeric_path.write_bytes(numeric_path.read_bytes() + b" ")
        with self.assertRaises(FormalV4AuthorityError):
            finalize_formal_v4_runtime_session_v1(session)
        with self.assertRaisesRegex(
            FormalV4AuthorityError, "PREPARED_RUNTIME_CAPABILITY_MISSING"
        ):
            execute_prepared_formal_v4_rule_v1(
                session, window=self.window(opportunity_id="AFTER-MUTATION")
            )

    def test_finalized_or_forged_session_rejects(self) -> None:
        session = prepare_formal_v4_runtime_session_v1(
            self.fx.bundle,
            execution_context=self.fx.context,
            repository_root=self.fx.root,
        )
        receipt = finalize_formal_v4_runtime_session_v1(session)
        self.assertEqual(receipt.test1_label_accesses, 0)
        self.assertEqual(receipt.test2_accesses, 0)
        self.assertEqual(receipt.heldout_accesses, 0)
        self.assertEqual(
            validate_formal_v4_prepared_runtime_finalization_receipt_v1(receipt),
            receipt.receipt_hash,
        )
        with self.assertRaisesRegex(
            FormalV4AuthorityError, "RECEIPT_HASH_MISMATCH"
        ):
            validate_formal_v4_prepared_runtime_finalization_receipt_v1(
                replace(receipt, test2_accesses=1)
            )
        with self.assertRaisesRegex(
            FormalV4AuthorityError, "PREPARED_RUNTIME_CAPABILITY_MISSING"
        ):
            execute_prepared_formal_v4_rule_v1(session, window=self.window())
        forged = replace(session, _capability=None)
        with self.assertRaises(FormalV4AuthorityError):
            execute_prepared_formal_v4_rule_v1(forged, window=self.window())


if __name__ == "__main__":
    unittest.main()
