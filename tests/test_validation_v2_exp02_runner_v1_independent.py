from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.exp02_runner_v1 import (
    EXP02_REQUIRED_BINDING_IDS,
    Exp02RunnerError,
    atomic_persist_selected_policy_v1,
    build_frozen_scientific_binding_v1,
    validate_scientific_binding_bundle_v1,
)


COMMIT = "2" * 40


def h(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def independent_hash(document: dict) -> str:
    payload = json.dumps(
        document, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")
    return sha256(payload).hexdigest()


class Exp02RunnerV1IndependentTests(unittest.TestCase):
    def test_binding_hashes_and_bundle_hash_match_independent_oracle(self) -> None:
        bindings = tuple(
            build_frozen_scientific_binding_v1(
                binding_id=binding_id, contract_id=f"oracle-{index}",
                specification_hash=h(f"spec-{index}"),
                implementation_hash=h(f"impl-{index}"),
                configuration_hash=h(f"config-{index}"),
                source_commit=COMMIT,
            )
            for index, binding_id in enumerate(EXP02_REQUIRED_BINDING_IDS)
        )
        for binding in bindings:
            self.assertEqual(binding.self_hash, independent_hash(binding.body_dict()))
        bundle = validate_scientific_binding_bundle_v1(
            bindings,
            expected_binding_hashes={item.binding_id: item.self_hash for item in bindings},
            source_commit=COMMIT,
        )
        self.assertEqual(bundle.self_hash, independent_hash(bundle.body_dict()))
        self.assertEqual(
            tuple(name for name, _ in bundle.binding_hashes),
            EXP02_REQUIRED_BINDING_IDS,
        )

    def test_external_expectation_must_be_complete_even_for_valid_objects(self) -> None:
        bindings = tuple(
            build_frozen_scientific_binding_v1(
                binding_id=binding_id, contract_id=f"oracle-{index}",
                specification_hash=h(f"spec-{index}"),
                implementation_hash=h(f"impl-{index}"),
                configuration_hash=h(f"config-{index}"),
                source_commit=COMMIT,
            )
            for index, binding_id in enumerate(EXP02_REQUIRED_BINDING_IDS)
        )
        expectations = {item.binding_id: item.self_hash for item in bindings[:-1]}
        with self.assertRaisesRegex(Exp02RunnerError, "BINDING_EXPECTATION_INCOMPLETE"):
            validate_scientific_binding_bundle_v1(
                bindings, expected_binding_hashes=expectations,
                source_commit=COMMIT,
            )

    def test_atomic_adapter_order_and_public_receipt_are_independently_observable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory).resolve() / "private-policy.json"
            order: list[str] = []

            def writer(handle, payload):
                order.append("write")
                return handle.write(payload)

            def file_fsync(descriptor):
                order.append("file_fsync")

            def replace_file(source, destination):
                order.append("replace")
                source.replace(destination)

            def directory_fsync(_directory):
                order.append("directory_fsync")

            def reopen(path):
                order.append("reopen")
                return path.read_bytes()

            evidence, receipt = atomic_persist_selected_policy_v1(
                artifact_id="independent-oracle", payload=b"selected-policy",
                target_path=target, write_payload=writer,
                file_fsync=file_fsync, atomic_replace=replace_file,
                directory_fsync=directory_fsync, reopen_reader=reopen,
            )
            self.assertEqual(
                order,
                ["write", "file_fsync", "replace", "directory_fsync", "reopen"],
            )
            expected_payload_hash = sha256(b"selected-policy").hexdigest()
            self.assertEqual(evidence.payload_bytes_sha256, expected_payload_hash)
            self.assertEqual(receipt.payload_sha256, expected_payload_hash)
            self.assertEqual(receipt.self_hash, independent_hash(receipt.body_dict()))
            serialized = json.dumps(receipt.to_dict(), sort_keys=True)
            self.assertNotIn(str(target), serialized)
            self.assertNotIn(str(target.parent), serialized)


if __name__ == "__main__":
    unittest.main()
