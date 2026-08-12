from __future__ import annotations

"""Independent audit oracle for R1B recovery serialization and writes."""

from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from types import MappingProxyType
import unittest
from unittest.mock import patch

from paperworks.v6 import task039e3_recovery_serialization_v1 as serializer
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    RecoverySerializationError,
    finalize_public_artifact_v1,
    normalize_plain_json_v1,
    public_artifact_hash_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)


def _independent_hash(document: dict[str, object]) -> str:
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _assert_plain_json(test: unittest.TestCase, value: object) -> None:
    if isinstance(value, dict):
        test.assertIs(type(value), dict)
        for key, item in value.items():
            test.assertIs(type(key), str)
            _assert_plain_json(test, item)
        return
    if isinstance(value, list):
        test.assertIs(type(value), list)
        for item in value:
            _assert_plain_json(test, item)
        return
    test.assertIn(type(value), {type(None), str, bool, int, float})


class _WriteFailureHandle:
    def __init__(self, handle: object) -> None:
        self._handle = handle

    def __enter__(self) -> "_WriteFailureHandle":
        return self

    def __exit__(self, *_args: object) -> None:
        self._handle.close()

    def write(self, _value: bytes) -> int:
        raise OSError("synthetic write failure")

    def flush(self) -> None:
        self._handle.flush()

    def fileno(self) -> int:
        return self._handle.fileno()


class R1BSerializationAuditTests(unittest.TestCase):
    def test_closed_recursive_domain_preserves_json_scalar_types(self) -> None:
        document = MappingProxyType(
            {
                "nested": MappingProxyType(
                    {
                        "tuple": (
                            MappingProxyType({"boolean": True, "integer": 1}),
                            [False, 0, None],
                        ),
                        "finite": [-7.5, 0.0, 3.25],
                        "text": "snowman:\N{SNOWMAN}",
                    }
                )
            }
        )
        observed = normalize_plain_json_v1(document)
        _assert_plain_json(self, observed)
        self.assertIs(type(observed["nested"]["tuple"][0]["boolean"]), bool)
        self.assertIs(type(observed["nested"]["tuple"][0]["integer"]), int)
        self.assertEqual(
            observed["nested"]["tuple"][1],
            [False, 0, None],
        )

    def test_nonfinite_nonstring_key_and_arbitrary_object_fail_closed(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaisesRegex(
                RecoverySerializationError, "non-finite"
            ):
                normalize_plain_json_v1({"numeric": value})

        with self.assertRaisesRegex(RecoverySerializationError, "mapping key"):
            normalize_plain_json_v1(MappingProxyType({1: "not-json"}))

        class NoFallback:
            def __str__(self) -> str:
                raise AssertionError("str fallback called")

            def __repr__(self) -> str:
                raise AssertionError("repr fallback called")

        with self.assertRaisesRegex(
            RecoverySerializationError, r"unsupported JSON value at \$\.secret: NoFallback"
        ):
            normalize_plain_json_v1({"secret": NoFallback()})

    def test_canonical_self_hash_is_reproduced_without_serializer_hash_helper(self) -> None:
        source = MappingProxyType(
            {
                "z": (3, MappingProxyType({"enabled": True})),
                "a": "\N{SNOWMAN}",
                "numeric": 2.5,
            }
        )
        finalized = finalize_public_artifact_v1(source)
        expected_hash = _independent_hash(finalized)
        self.assertEqual(finalized["artifact_hash"], expected_hash)
        self.assertEqual(public_artifact_hash_v1(finalized), expected_hash)
        self.assertEqual(verify_public_artifact_v1(finalized), finalized)
        decoded = json.loads(json.dumps(finalized, ensure_ascii=True, allow_nan=False))
        self.assertEqual(decoded, finalized)
        self.assertEqual(_independent_hash(decoded), expected_hash)

    def test_success_atomically_replaces_existing_artifact_and_cleans_temp(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "artifact.json"
            target.write_text('{"historical":true}\n', encoding="utf-8")

            written = write_public_artifact_atomic_v1(
                target,
                MappingProxyType(
                    {"version": 2, "nested": (MappingProxyType({"ok": True}),)}
                ),
            )
            observed = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(observed, written)
            self.assertEqual(observed["artifact_hash"], _independent_hash(observed))
            self.assertEqual(list(root.glob(".artifact.json.*.tmp")), [])

    def test_normalization_failure_happens_before_temp_and_preserves_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "artifact.json"
            target.write_bytes(b"AUTHORITATIVE_PRIOR_BYTES")
            with patch.object(serializer.tempfile, "mkstemp") as mkstemp:
                with self.assertRaises(RecoverySerializationError):
                    write_public_artifact_atomic_v1(target, {"invalid": object()})
            mkstemp.assert_not_called()
            self.assertEqual(target.read_bytes(), b"AUTHORITATIVE_PRIOR_BYTES")
            self.assertEqual(list(root.glob(".artifact.json.*.tmp")), [])

    def test_temp_creation_failure_preserves_target_and_creates_no_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "artifact.json"
            target.write_bytes(b"AUTHORITATIVE_PRIOR_BYTES")
            with patch.object(
                serializer.tempfile,
                "mkstemp",
                side_effect=OSError("synthetic temp creation failure"),
            ):
                with self.assertRaisesRegex(RecoverySerializationError, "atomic"):
                    write_public_artifact_atomic_v1(target, {"version": 2})
            self.assertEqual(target.read_bytes(), b"AUTHORITATIVE_PRIOR_BYTES")
            self.assertEqual(list(root.glob(".artifact.json.*.tmp")), [])

    def test_write_failure_removes_temp_and_preserves_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "artifact.json"
            target.write_bytes(b"AUTHORITATIVE_PRIOR_BYTES")
            real_fdopen = os.fdopen

            def failing_fdopen(descriptor: int, mode: str) -> _WriteFailureHandle:
                return _WriteFailureHandle(real_fdopen(descriptor, mode))

            with patch.object(serializer.os, "fdopen", side_effect=failing_fdopen):
                with self.assertRaisesRegex(RecoverySerializationError, "atomic"):
                    write_public_artifact_atomic_v1(target, {"version": 2})
            self.assertEqual(target.read_bytes(), b"AUTHORITATIVE_PRIOR_BYTES")
            self.assertEqual(list(root.glob(".artifact.json.*.tmp")), [])

    def test_file_fsync_failure_removes_temp_and_preserves_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "artifact.json"
            target.write_bytes(b"AUTHORITATIVE_PRIOR_BYTES")
            with patch.object(
                serializer.os,
                "fsync",
                side_effect=OSError("synthetic file fsync failure"),
            ):
                with self.assertRaisesRegex(RecoverySerializationError, "atomic"):
                    write_public_artifact_atomic_v1(target, {"version": 2})
            self.assertEqual(target.read_bytes(), b"AUTHORITATIVE_PRIOR_BYTES")
            self.assertEqual(list(root.glob(".artifact.json.*.tmp")), [])

    def test_replace_failure_removes_temp_and_preserves_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "artifact.json"
            target.write_bytes(b"AUTHORITATIVE_PRIOR_BYTES")
            with patch.object(
                serializer.os,
                "replace",
                side_effect=OSError("synthetic replace failure"),
            ):
                with self.assertRaisesRegex(RecoverySerializationError, "atomic"):
                    write_public_artifact_atomic_v1(target, {"version": 2})
            self.assertEqual(target.read_bytes(), b"AUTHORITATIVE_PRIOR_BYTES")
            self.assertEqual(list(root.glob(".artifact.json.*.tmp")), [])

    def test_failures_without_existing_target_leave_no_authoritative_partial(self) -> None:
        failure_patches = (
            patch.object(
                serializer.tempfile,
                "mkstemp",
                side_effect=OSError("synthetic temp creation failure"),
            ),
            patch.object(
                serializer.os,
                "replace",
                side_effect=OSError("synthetic replace failure"),
            ),
        )
        for failure_patch in failure_patches:
            with self.subTest(failure_patch=failure_patch), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                target = root / "artifact.json"
                with failure_patch, self.assertRaises(RecoverySerializationError):
                    write_public_artifact_atomic_v1(target, {"version": 2})
                self.assertFalse(target.exists())
                self.assertEqual(list(root.glob(".artifact.json.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
