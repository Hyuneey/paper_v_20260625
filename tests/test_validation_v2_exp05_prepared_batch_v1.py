from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import unittest
from unittest import mock

from paperworks.validation_v2 import exp05_runner_v1 as runner
from paperworks.validation_v2 import runtime_v1 as runtime_module
from paperworks.validation_v2.formal_v4_authority_v1 import (
    FormalV4AuthorityError,
    canonical_document_hash_v1,
)
from paperworks.validation_v2.runtime_v1 import FormalV4ObservationWindowV1
from paperworks.validation_v2.schema_registry_v1 import (
    validate_validation_v2_document_v1,
)
from tests.test_validation_v2_exp05_runner_v1 import h
from tests.test_validation_v2_formal_v4_authority_v1 import V2Fixture


class Exp05PreparedBatchV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = V2Fixture()
        descriptor = self.fx.descriptors[0]
        self.base_window = FormalV4ObservationWindowV1(
            opportunity_id="OP-EXP05-BATCH-0",
            relation_id=descriptor.relation_id,
            feature_contract_hash=self.fx.feature_binding.content_sha256,
            file_contract_hash=self.fx.file_binding.content_sha256,
            sampling_contract_hash=self.fx.sampling_binding.content_sha256,
            event_index=100,
            target_response_start_index=105,
            source_pre_values=(0.0, 0.0),
            source_post_values=(2.0, 2.0),
            target_baseline_values=(10.0, 10.0),
            target_response_values=(11.0, 11.0),
            seconds_since_previous_source_trigger=None,
            seconds_to_nearest_other_source_trigger=None,
            future_window_complete=True,
        )
        self.authorization = runner.authorize_exp05_execution_v1(
            execution_scope="SYNTHETIC_CONFORMANCE",
            preregistration_hash=h("exp05-preregistration"),
            source_commit=self.fx.commit,
            bundle=self.fx.bundle,
        )

    def tearDown(self) -> None:
        self.fx.close()

    def windows(self, count: int) -> tuple[FormalV4ObservationWindowV1, ...]:
        return tuple(
            replace(self.base_window, opportunity_id=f"OP-EXP05-BATCH-{index}")
            for index in range(count)
        )

    def execute_batch(
        self, windows: tuple[FormalV4ObservationWindowV1, ...]
    ) -> runner.EvaluatedFormalV4ExplanationBatchV1:
        return runner.execute_and_materialize_formal_v4_batch_v1(
            self.fx.bundle,
            authorization=self.authorization,
            execution_context=self.fx.context,
            repository_root=self.fx.root,
            windows=windows,
        )

    def test_batch_units_are_bit_identical_to_existing_single_path(self) -> None:
        windows = self.windows(5)
        direct = tuple(
            runner.execute_and_materialize_formal_v4_rule_v1(
                self.fx.bundle,
                authorization=self.authorization,
                execution_context=self.fx.context,
                repository_root=self.fx.root,
                window=window,
            )
            for window in windows
        )
        batch = self.execute_batch(windows)
        self.assertEqual(
            [unit.to_dict() for unit in batch.units],
            [unit.to_dict() for unit in direct],
        )
        self.assertEqual(
            batch.prepared_runtime_finalization_receipt.evaluated_window_count,
            len(windows),
        )
        self.assertEqual(
            runner.validate_evaluated_formal_v4_explanation_batch_v1(batch),
            batch.batch_hash,
        )
        validate_validation_v2_document_v1(
            "exp05_evaluated_batch_v1.schema.json", batch.to_dict()
        )
        self.assertTrue(all(unit.fidelity_result.all_checks_passed for unit in batch.units))

    def test_bound_file_reads_are_constant_with_batch_size(self) -> None:
        original = Path.read_bytes

        def count_for(size: int) -> int:
            observed = 0

            def counted(path: Path) -> bytes:
                nonlocal observed
                observed += 1
                return original(path)

            with mock.patch.object(Path, "read_bytes", new=counted):
                batch = self.execute_batch(self.windows(size))
            self.assertEqual(len(batch.units), size)
            return observed

        small_reads = count_for(2)
        large_reads = count_for(20)
        self.assertEqual(small_reads, large_reads)

    def test_batch_avoids_repeated_single_window_authority_replay(self) -> None:
        windows = self.windows(8)
        original = Path.read_bytes
        direct_reads = 0

        def count_direct(path: Path) -> bytes:
            nonlocal direct_reads
            direct_reads += 1
            return original(path)

        with mock.patch.object(Path, "read_bytes", new=count_direct):
            for window in windows:
                runner.execute_and_materialize_formal_v4_rule_v1(
                    self.fx.bundle,
                    authorization=self.authorization,
                    execution_context=self.fx.context,
                    repository_root=self.fx.root,
                    window=window,
                )

        batch_reads = 0

        def count_batch(path: Path) -> bytes:
            nonlocal batch_reads
            batch_reads += 1
            return original(path)

        with mock.patch.object(Path, "read_bytes", new=count_batch):
            batch = self.execute_batch(windows)
        self.assertEqual(len(batch.units), len(windows))
        self.assertGreater(direct_reads, batch_reads)

    def test_authority_mutation_before_end_replay_releases_no_batch(self) -> None:
        original = runtime_module.execute_prepared_formal_v4_rule_v1
        calls = 0

        def mutate_after_first(session, *, window):
            nonlocal calls
            trace = original(session, window=window)
            calls += 1
            if calls == 1:
                numeric_path = self.fx.root / self.fx.numeric_binding.relative_path
                numeric_path.write_bytes(numeric_path.read_bytes() + b" ")
            return trace

        with mock.patch.object(
            runtime_module,
            "execute_prepared_formal_v4_rule_v1",
            side_effect=mutate_after_first,
        ):
            with self.assertRaises(FormalV4AuthorityError):
                self.execute_batch(self.windows(3))

    def test_batch_rejects_empty_non_tuple_and_substitution(self) -> None:
        with self.assertRaisesRegex(runner.Exp05RunnerError, "WINDOW_BATCH_INVALID"):
            self.execute_batch(())
        with self.assertRaisesRegex(runner.Exp05RunnerError, "WINDOW_BATCH_INVALID"):
            runner.execute_and_materialize_formal_v4_batch_v1(
                self.fx.bundle,
                authorization=self.authorization,
                execution_context=self.fx.context,
                repository_root=self.fx.root,
                windows=list(self.windows(1)),  # type: ignore[arg-type]
            )
        batch = self.execute_batch(self.windows(2))
        forged = replace(batch, units=tuple(reversed(batch.units)))
        with self.assertRaisesRegex(runner.Exp05RunnerError, "REPLAY_MISMATCH"):
            runner.validate_evaluated_formal_v4_explanation_batch_v1(forged)
        bad_receipt = replace(
            batch.prepared_runtime_finalization_receipt,
            test2_accesses=1,
            receipt_hash="0" * 64,
        )
        bad_receipt = replace(
            bad_receipt,
            receipt_hash=canonical_document_hash_v1(bad_receipt.body_dict()),
        )
        forged = replace(batch, prepared_runtime_finalization_receipt=bad_receipt)
        with self.assertRaisesRegex(runner.Exp05RunnerError, "FINALIZATION_REJECTED"):
            runner.validate_evaluated_formal_v4_explanation_batch_v1(forged)


if __name__ == "__main__":
    unittest.main()
