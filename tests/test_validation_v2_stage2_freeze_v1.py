from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paperworks.validation_v2.stage2_freeze_v1 import (
    Stage2FreezeError,
    bind_stage2_file_v1,
    build_stage2_commit_a_manifest_v1,
    persist_stage2_commit_a_manifest_v1,
    validate_stage2_preregistration_document_v1,
)


BASE = "4fcc4ec501711a3f3a3335183ecd5f80fc4b39bd"


def registration(experiment_id: str = "EXP-01") -> dict[str, object]:
    body: dict[str, object] = {
        "schema": "paperworks.validation_v2.stage2_preregistration_v1",
        "schema_version": "1.0.0",
        "experiment_id": experiment_id,
        "status": "FROZEN_BEFORE_NORMAL_DATA_ACCESS",
        "prohibited_inputs": ["test1", "labels", "test2", "heldout"],
        "test2_authorized": False,
    }
    body["preregistration_hash"] = sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")).hexdigest()
    return body


class Stage2FreezeV1Tests(unittest.TestCase):
    def write_required(self, root: Path) -> None:
        (root / "research_control_center/validation_v2/reports").mkdir(parents=True)
        (root / "src/paperworks/validation_v2/schemas").mkdir(parents=True)
        (root / "research_control_center/validation_v2/PILOT_V1_PRESERVATION_MANIFEST.json").write_text("{}")
        (root / "research_control_center/validation_v2/reports/V2_PROTOCOL_001_EVIDENCE.json").write_text(json.dumps({
            "implementation": {"protocol_hash": "a" * 64},
        }))
        (root / "research_control_center/validation_v2/reports/GAP_FIX_METRIC_001_EVIDENCE.json").write_text(json.dumps({
            "implementation": {"protocol_hash": "a" * 64, "metric_contract_hash": "b" * 64},
        }))
        (root / "src/paperworks/validation_v2/formal_v4_authority_v1.py").write_text("authority = 1\n")
        (root / "src/paperworks/validation_v2/schemas/a.schema.json").write_text("{}")

    def bindings(self, registration_path: str) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
        shared = ("EXP-01",)
        return (
            (registration_path, "PREREGISTRATION", shared),
            ("research_control_center/validation_v2/PILOT_V1_PRESERVATION_MANIFEST.json", "GOVERNANCE", shared),
            ("research_control_center/validation_v2/reports/V2_PROTOCOL_001_EVIDENCE.json", "GOVERNANCE", shared),
            ("research_control_center/validation_v2/reports/GAP_FIX_METRIC_001_EVIDENCE.json", "GOVERNANCE", shared),
            ("src/paperworks/validation_v2/formal_v4_authority_v1.py", "SOURCE", shared),
            ("src/paperworks/validation_v2/schemas/a.schema.json", "SCHEMA", shared),
        )

    def test_preregistration_self_hash_and_forbidden_authority_fail_closed(self) -> None:
        document = registration()
        self.assertEqual(document["preregistration_hash"], validate_stage2_preregistration_document_v1(document))
        changed = dict(document)
        changed["status"] = "FROZEN_BEFORE_TEST1"
        with self.assertRaises(Stage2FreezeError):
            validate_stage2_preregistration_document_v1(changed)
        authorized = registration()
        authorized["test2_authorized"] = True
        body = dict(authorized)
        body.pop("preregistration_hash")
        authorized["preregistration_hash"] = sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode()).hexdigest()
        with self.assertRaisesRegex(Stage2FreezeError, "FORBIDDEN"):
            validate_stage2_preregistration_document_v1(authorized)

    def test_exact_files_bind_bytes_and_git_blob_identity(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_required(root)
            (root / "src").mkdir(exist_ok=True)
            path = root / "src" / "contract.py"
            path.write_bytes(b"value = 1\n")
            record = bind_stage2_file_v1(
                root, path="src/contract.py", role="SOURCE", experiment_ids=("EXP-01",),
            )
            self.assertEqual(10, record.byte_count)
            self.assertEqual(64, len(record.sha256))
            self.assertEqual(40, len(record.git_blob_oid))
            with self.assertRaises(Stage2FreezeError):
                bind_stage2_file_v1(root, path="../escape", role="SOURCE", experiment_ids=("EXP-01",))

    def test_manifest_requires_sorted_unique_explicit_bindings_and_rejects_mutation(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_required(root)
            (root / "pre").mkdir()
            (root / "src").mkdir(exist_ok=True)
            (root / "pre" / "exp.json").write_text(json.dumps(registration()), encoding="utf-8")
            (root / "src" / "code.py").write_text("x = 1\n", encoding="utf-8")
            manifest = build_stage2_commit_a_manifest_v1(
                root, source_base_commit=BASE,
                file_bindings=self.bindings("pre/exp.json") + (("src/code.py", "SOURCE", ("EXP-01",)),),
            )
            self.assertEqual(7, len(manifest.tracked_files))
            self.assertEqual(("EXP-01", registration()["preregistration_hash"]), manifest.preregistration_hashes[0])
            with self.assertRaises(Stage2FreezeError):
                replace(manifest, authority_mode="CANONICAL_RUNTIME")
            (root / "src" / "code.py").write_text("x = 2\n", encoding="utf-8")
            changed = build_stage2_commit_a_manifest_v1(
                root, source_base_commit=BASE,
                file_bindings=self.bindings("pre/exp.json") + (("src/code.py", "SOURCE", ("EXP-01",)),),
            )
            self.assertNotEqual(manifest.manifest_hash, changed.manifest_hash)

    def test_no_overwrite_persistence(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_required(root)
            (root / "pre").mkdir()
            (root / "pre" / "exp.json").write_text(json.dumps(registration()), encoding="utf-8")
            manifest = build_stage2_commit_a_manifest_v1(
                root, source_base_commit=BASE, file_bindings=self.bindings("pre/exp.json"),
            )
            output = root / "freeze" / "manifest.json"
            persist_stage2_commit_a_manifest_v1(manifest, output)
            self.assertEqual(manifest.manifest_hash, json.loads(output.read_text())["manifest_hash"])
            with self.assertRaisesRegex(Stage2FreezeError, "ALREADY_EXISTS"):
                persist_stage2_commit_a_manifest_v1(manifest, output)


if __name__ == "__main__":
    unittest.main()
