from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import pickle
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from paperworks.validation_v2 import hai_feature_adapter_v1 as adapter
from paperworks.validation_v2.hai_shared_feature_session_v1 import (
    HAISharedFeatureConsumerV1,
    HAISharedFeatureSessionError,
    HAISharedFeatureSessionV1,
)
from paperworks.validation_v2.protocol_v1 import (
    ProtocolExecutionGuardV1,
    ProtocolOperationV1,
    build_policy_freeze_receipt_v1,
    build_validation_protocol_v1,
)
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


class HAISharedFeatureSessionV1Tests(unittest.TestCase):
    def _fixture(self, root: Path, *, split_id: str = "train1") -> adapter.HAIFeatureFileSpecV1:
        edition = root / "hai-23.05"
        edition.mkdir()
        path = edition / "synthetic.csv"
        filler = tuple(f"X{index:02d}" for index in range(49))
        header = ("timestamp",) + tuple(P1_FEATURE_ORDER) + filler
        start = datetime(2025, 1, 1)
        lines = [",".join(header)]
        for row_index in range(5):
            timestamp = (start + timedelta(seconds=row_index)).isoformat()
            values = [str(row_index + column / 100) for column in range(37)]
            lines.append(",".join((timestamp, *values, *("0" for _ in filler))))
        payload = ("\n".join(lines) + "\n").encode("utf-8")
        path.write_bytes(payload)
        roles = {
            "train1": "NORMAL_FIT_PRIMARY",
            "train3": "NORMAL_CONFIRMATION_CALIBRATION",
            "test1": "DEVELOPMENT_ONLY",
        }
        return adapter.HAIFeatureFileSpecV1(
            split_id=split_id,
            role=roles[split_id],
            relative_path="hai-23.05/synthetic.csv",
            sha256_hex=sha256(payload).hexdigest(),
            byte_size=len(payload),
            row_count=5,
            raw_header_sha256=sha256(lines[0].encode("utf-8")).hexdigest(),
            header_field_count=87,
        )

    def _capability(self, repository: Path, root: Path) -> adapter.HAIFeatureRootCapabilityV1:
        with patch.dict(os.environ, {"HAI_DATA_ROOT": str(root)}, clear=False):
            return adapter.resolve_hai_feature_root_capability_v1(repository)

    def _guard(self) -> ProtocolExecutionGuardV1:
        return ProtocolExecutionGuardV1(build_validation_protocol_v1(source_commit="1" * 40))

    def _frozen_guard(self) -> ProtocolExecutionGuardV1:
        protocol = build_validation_protocol_v1(source_commit="1" * 40)
        guard = ProtocolExecutionGuardV1(protocol)
        guard.freeze_policies(
            build_policy_freeze_receipt_v1(
                protocol=protocol,
                candidate_set_hash="2" * 64,
                selection_objective="SYNTHETIC_FIXED_OBJECTIVE",
                tie_break_rule="SYNTHETIC_FIXED_TIE_BREAK",
                selected_config_hash="3" * 64,
                authority_hash="4" * 64,
                method_policy_hashes=("5" * 64,),
                metric_contract_hash="6" * 64,
            )
        )
        return guard

    def test_three_consumers_share_one_parse_and_one_immutable_projection(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            spec = self._fixture(root)
            session = HAISharedFeatureSessionV1(
                experiment_id="SYNTHETIC-SHARED-SESSION",
                capability=self._capability(repository, root),
                protocol_guard=self._guard(),
            )
            consumers = (
                HAISharedFeatureConsumerV1("D0.PCA", ProtocolOperationV1.DETECTOR_FIT),
                HAISharedFeatureConsumerV1("DETECTOR.IFOREST", ProtocolOperationV1.DETECTOR_FIT),
                HAISharedFeatureConsumerV1("D1.RELATION", ProtocolOperationV1.RELATION_FIT),
            )
            original = adapter._load_feature_file_from_spec_v1
            with patch.dict(adapter._SPECS, {"train1": spec}, clear=False), patch.object(
                adapter,
                "_load_feature_file_from_spec_v1",
                wraps=original,
            ) as loader:
                source_receipt = session.open_split(split_id="train1", consumers=consumers)
            self.assertEqual(loader.call_count, 1)
            self.assertEqual(source_receipt.to_dict()["file_open_count"], 1)

            d0 = session.numeric_matrix(split_id="train1", consumer_id="D0.PCA")
            iforest = session.numeric_matrix(split_id="train1", consumer_id="DETECTOR.IFOREST")
            relation = session.numeric_matrix(split_id="train1", consumer_id="D1.RELATION")
            self.assertIsNot(d0, iforest)
            self.assertIsNot(iforest, relation)
            self.assertTrue(np.shares_memory(d0, relation))
            self.assertFalse(d0.flags.writeable)
            with self.assertRaises(ValueError):
                d0[0, 0] = 99.0
            with self.assertRaises(ValueError):
                d0.setflags(write=True)

            document = session.public_document()
            self.assertEqual(document["feature_file_open_count"], 1)
            self.assertEqual(document["unique_projection_count"], 1)
            self.assertEqual(document["test1_feature_accesses"], 0)
            self.assertEqual(document["test2_accesses"], 0)
            self.assertFalse(document["persistent_cache_created"])
            self.assertFalse(document["private_paths_embedded"])
            self.assertNotIn(str(root), repr(document))
            body = {key: value for key, value in document.items() if key != "receipt_hash"}
            expected = sha256(
                json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
            ).hexdigest()
            self.assertEqual(document["receipt_hash"], expected)

    def test_subset_projection_is_computed_once_and_shared(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            spec = self._fixture(root)
            session = HAISharedFeatureSessionV1(
                experiment_id="SYNTHETIC-SUBSET-SESSION",
                capability=self._capability(repository, root),
                protocol_guard=self._guard(),
            )
            consumers = (
                HAISharedFeatureConsumerV1("CONSUMER.A", ProtocolOperationV1.RELATION_FIT),
                HAISharedFeatureConsumerV1("CONSUMER.B", ProtocolOperationV1.RELATION_FIT),
            )
            with patch.dict(adapter._SPECS, {"train1": spec}, clear=False):
                session.open_split(split_id="train1", consumers=consumers)
            subset = tuple(P1_FEATURE_ORDER[:3])
            first = session.numeric_matrix(
                split_id="train1", consumer_id="CONSUMER.A", feature_ids=subset
            )
            second = session.numeric_matrix(
                split_id="train1", consumer_id="CONSUMER.B", feature_ids=subset
            )
            self.assertIsNot(first, second)
            self.assertTrue(np.shares_memory(first, second))
            self.assertEqual(first.shape, (5, 3))
            self.assertFalse(first.flags.writeable)
            with self.assertRaises(ValueError):
                first.setflags(write=True)
            self.assertEqual(session.public_document()["unique_projection_count"], 1)

    def test_three_development_consumers_authorize_test1_once_after_policy_freeze(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            spec = self._fixture(root, split_id="test1")
            session = HAISharedFeatureSessionV1(
                experiment_id="SYNTHETIC-EXP04-SHARED",
                capability=self._capability(repository, root),
                protocol_guard=self._frozen_guard(),
            )
            consumers = tuple(
                HAISharedFeatureConsumerV1(
                    consumer_id,
                    ProtocolOperationV1.DEVELOPMENT_PREDICTION,
                )
                for consumer_id in ("D0.PCA", "DETECTOR.IFOREST", "D1.FORMALV4")
            )
            original = adapter._load_feature_file_from_spec_v1
            with patch.dict(adapter._SPECS, {"test1": spec}, clear=False), patch.object(
                adapter,
                "_load_feature_file_from_spec_v1",
                wraps=original,
            ) as loader:
                session.open_split(split_id="test1", consumers=consumers)
            self.assertEqual(loader.call_count, 1)
            document = session.public_document()
            self.assertEqual(document["feature_file_open_count"], 1)
            self.assertEqual(document["test1_feature_accesses"], 1)
            self.assertFalse(document["labels_accessed"])
            self.assertEqual(document["test2_accesses"], 0)

    def test_invalid_operation_and_unregistered_consumer_fail_before_use(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            spec = self._fixture(root, split_id="train3")
            session = HAISharedFeatureSessionV1(
                experiment_id="SYNTHETIC-FAIL-CLOSED",
                capability=self._capability(repository, root),
                protocol_guard=self._guard(),
            )
            consumers = (
                HAISharedFeatureConsumerV1("D0.PCA", ProtocolOperationV1.DETECTOR_FIT),
            )
            original = adapter._load_feature_file_from_spec_v1
            with patch.dict(adapter._SPECS, {"train3": spec}, clear=False), patch.object(
                adapter,
                "_load_feature_file_from_spec_v1",
                wraps=original,
            ) as loader, self.assertRaisesRegex(
                adapter.HAIFeatureAdapterError,
                "^SPLIT_OPERATION_REJECTED$",
            ):
                session.open_split(split_id="train3", consumers=consumers)
            self.assertEqual(loader.call_count, 0)
            self.assertEqual(session.public_document()["feature_file_open_count"], 0)
            with self.assertRaisesRegex(
                HAISharedFeatureSessionError,
                "^SHARED_CONSUMER_NOT_AUTHORIZED$",
            ):
                session.numeric_matrix(split_id="train3", consumer_id="D0.PCA")

    def test_duplicate_open_consumer_forgery_serialization_and_close_fail_closed(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            spec = self._fixture(root)
            session = HAISharedFeatureSessionV1(
                experiment_id="SYNTHETIC-LIFECYCLE",
                capability=self._capability(repository, root),
                protocol_guard=self._guard(),
            )
            consumer = HAISharedFeatureConsumerV1(
                "D0.PCA", ProtocolOperationV1.DETECTOR_FIT
            )
            with patch.dict(adapter._SPECS, {"train1": spec}, clear=False):
                session.open_split(split_id="train1", consumers=(consumer,))
                with self.assertRaisesRegex(
                    HAISharedFeatureSessionError,
                    "^SHARED_SPLIT_ALREADY_OPEN$",
                ):
                    session.open_split(split_id="train1", consumers=(consumer,))
            with self.assertRaisesRegex(
                HAISharedFeatureSessionError,
                "^SHARED_CONSUMER_NOT_AUTHORIZED$",
            ):
                session.numeric_matrix(split_id="train1", consumer_id="D1.UNKNOWN")
            with self.assertRaisesRegex(
                HAISharedFeatureSessionError,
                "^SHARED_SESSION_SERIALIZATION_REJECTED$",
            ):
                pickle.dumps(session)
            session.close()
            self.assertEqual(session.public_document()["state"], "CLOSED")
            with self.assertRaisesRegex(
                HAISharedFeatureSessionError,
                "^SHARED_SESSION_CLOSED$",
            ):
                session.numeric_matrix(split_id="train1", consumer_id="D0.PCA")

    def test_heldout_alias_and_duplicate_consumer_are_rejected_without_open(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            session = HAISharedFeatureSessionV1(
                experiment_id="SYNTHETIC-BOUNDARY",
                capability=self._capability(repository, root),
                protocol_guard=self._guard(),
            )
            consumer = HAISharedFeatureConsumerV1(
                "D0.PCA", ProtocolOperationV1.DETECTOR_FIT
            )
            with self.assertRaisesRegex(
                adapter.HAIFeatureAdapterError,
                "^HELDOUT_OR_TEST2_ALIAS_REJECTED$",
            ):
                session.open_split(split_id="test2", consumers=(consumer,))
            with self.assertRaisesRegex(
                HAISharedFeatureSessionError,
                "^SHARED_CONSUMER_DUPLICATE_REJECTED$",
            ):
                session.open_split(split_id="train1", consumers=(consumer, consumer))
            self.assertEqual(session.public_document()["feature_file_open_count"], 0)


if __name__ == "__main__":
    unittest.main()
