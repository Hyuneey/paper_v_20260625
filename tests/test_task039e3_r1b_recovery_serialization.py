from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    RecoverySerializationError,
    canonical_json_v1,
    finalize_public_artifact_v1,
    normalize_plain_json_v1,
    public_artifact_hash_v1,
    serialize_public_artifact_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)


class Task039E3R1BRecoverySerializationTests(unittest.TestCase):
    def test_nested_immutable_containers_become_plain_json(self) -> None:
        value = MappingProxyType(
            {
                "receipt": MappingProxyType(
                    {"items": (1, MappingProxyType({"ok": True}), [None, "x"])}
                )
            }
        )
        normalized = normalize_plain_json_v1(value)
        self.assertEqual(
            normalized,
            {"receipt": {"items": [1, {"ok": True}, [None, "x"]]}},
        )
        self.assertIs(type(normalized), dict)
        self.assertIs(type(normalized["receipt"]), dict)
        self.assertIs(type(normalized["receipt"]["items"]), list)

    def test_deeply_nested_tuple_mapping_and_list(self) -> None:
        value = {"a": ({"b": (MappingProxyType({"c": [1, (2,)]}),)},)}
        self.assertEqual(
            normalize_plain_json_v1(value),
            {"a": [{"b": [{"c": [1, [2]]}]}]},
        )

    def test_unsupported_value_is_rejected_without_string_fallback(self) -> None:
        class SecretObject:
            def __str__(self) -> str:
                raise AssertionError("generic string fallback must not be called")

            def __repr__(self) -> str:
                raise AssertionError("generic repr fallback must not be called")

        with self.assertRaisesRegex(
            RecoverySerializationError,
            r"unsupported JSON value at \$\.secret: SecretObject",
        ):
            normalize_plain_json_v1({"secret": SecretObject()})

    def test_non_string_mapping_key_and_nonfinite_float_are_rejected(self) -> None:
        with self.assertRaisesRegex(RecoverySerializationError, "mapping key"):
            normalize_plain_json_v1({1: "not allowed"})
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaisesRegex(RecoverySerializationError, "non-finite"):
                normalize_plain_json_v1({"value": value})

    def test_canonical_json_matches_repository_convention(self) -> None:
        value = MappingProxyType({"z": (2, 3), "a": "\N{SNOWMAN}"})
        normalized = {"z": [2, 3], "a": "\N{SNOWMAN}"}
        self.assertEqual(
            canonical_json_v1(value),
            json.dumps(
                normalized,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ),
        )
        self.assertEqual(public_artifact_hash_v1(value), stable_hash_v1(normalized))

    def test_finalize_hash_is_stable_and_ignores_container_mutability(self) -> None:
        immutable = MappingProxyType({"task": "R1B", "values": (1, 2, 3)})
        mutable = {"values": [1, 2, 3], "task": "R1B"}
        first = finalize_public_artifact_v1(immutable)
        second = finalize_public_artifact_v1(mutable)
        self.assertEqual(first, second)
        self.assertEqual(first["artifact_hash"], stable_hash_v1(mutable))
        self.assertEqual(finalize_public_artifact_v1(first), first)

    def test_mismatched_or_missing_self_hash_is_rejected(self) -> None:
        valid = finalize_public_artifact_v1({"task": "R1B"})
        invalid = {**valid, "artifact_hash": "0" * 64}
        with self.assertRaisesRegex(RecoverySerializationError, "does not match"):
            finalize_public_artifact_v1(invalid)
        no_hash = {key: value for key, value in valid.items() if key != "artifact_hash"}
        with self.assertRaisesRegex(RecoverySerializationError, "is required"):
            verify_public_artifact_v1(no_hash)

    def test_serialization_round_trip_and_hash_verification(self) -> None:
        document = MappingProxyType(
            {"task": "R1B", "nested": MappingProxyType({"values": (1, 2)})}
        )
        encoded = serialize_public_artifact_v1(document)
        parsed = json.loads(encoded)
        self.assertEqual(parsed, verify_public_artifact_v1(parsed))
        self.assertEqual(parsed["nested"]["values"], [1, 2])

    def test_atomic_write_creates_verified_destination_and_no_temp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "artifact.json"
            observed = write_public_artifact_atomic_v1(
                destination,
                MappingProxyType({"task": "R1B", "nested": ({"ok": True},)}),
            )
            self.assertEqual(json.loads(destination.read_text("utf-8")), observed)
            self.assertEqual(list(Path(directory).glob(".*.tmp")), [])

    def test_failure_before_temp_creation_leaves_no_partial_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "artifact.json"
            with self.assertRaises(RecoverySerializationError):
                write_public_artifact_atomic_v1(destination, {"bad": object()})
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_replace_failure_preserves_previous_valid_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "artifact.json"
            original = write_public_artifact_atomic_v1(destination, {"version": 1})
            original_bytes = destination.read_bytes()
            with patch(
                "paperworks.v6.task039e3_recovery_serialization_v1.os.replace",
                side_effect=OSError("synthetic replace failure"),
            ):
                with self.assertRaisesRegex(
                    RecoverySerializationError, "atomic public artifact write failed"
                ):
                    write_public_artifact_atomic_v1(destination, {"version": 2})
            self.assertEqual(destination.read_bytes(), original_bytes)
            self.assertEqual(json.loads(original_bytes), original)
            self.assertEqual(list(Path(directory).glob(".*.tmp")), [])

    def test_private_custody_is_untouched_when_public_serialization_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            private = Path(directory) / "private-ledger.json"
            public = Path(directory) / "public.json"
            private.write_bytes(b'{"custody":"preserved"}\n')
            before = private.read_bytes()
            with self.assertRaises(RecoverySerializationError):
                write_public_artifact_atomic_v1(public, {"unsupported": object()})
            self.assertEqual(private.read_bytes(), before)
            self.assertFalse(public.exists())

    def test_missing_parent_fails_without_creating_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "missing"
            with self.assertRaisesRegex(RecoverySerializationError, "parent directory"):
                write_public_artifact_atomic_v1(parent / "artifact.json", {"ok": True})
            self.assertFalse(parent.exists())


if __name__ == "__main__":
    unittest.main()
