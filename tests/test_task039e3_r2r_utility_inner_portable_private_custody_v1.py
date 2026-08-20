"""Synthetic/static tests for portable private-locator custody.

No real registry, environment binding, HAI file, label, or private numeric
value is opened.  Temporary files contain only synthetic placeholder bytes.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paperworks.v6.common import stable_hash_v1  # noqa: E402
from paperworks.v6 import (  # noqa: E402
    task039e3_r2r_utility_inner_execution_authorization_v1 as subject,
)
from paperworks.v6 import (  # noqa: E402
    task039e3_r2r_utility_normal_only_authority_v1 as main_authority,
)
from paperworks.v6 import (  # noqa: E402
    task039e3_r2r_utility_source_census_supplement_v1 as supplement,
)


TIMESTAMP = "2026-08-20T00:00:00+00:00"


def _write_json(path: Path, document: dict[str, object]) -> None:
    path.write_text(
        json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


class PortablePrivateCustodyV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.main_registry = self.root / "main.registry.json"
        self.supplement_registry = self.root / "supplement.registry.json"
        self.main_registry.write_text("{}\n", encoding="utf-8")
        self.supplement_registry.write_text("{}\n", encoding="utf-8")

    def _main_locator(self, registry_path: Path | None = None) -> dict[str, object]:
        authorization = (
            main_authority.load_committed_materialization_execution_authorization_r1(
                ROOT
            )
        )
        return main_authority.local_locator_manifest_document_v1(
            private_authority_path=(registry_path or self.main_registry),
            private_authority_hash=subject.MAIN_PRIVATE_REGISTRY_HASH,
            public_receipt_hash=subject.MAIN_MATERIALIZED_AUDIT_RECEIPT_HASH,
            created_at=TIMESTAMP,
            builder_commit=authorization.authorized_control_commit,
            builder_git_blob=authorization.authorized_control_source_blob,
            builder_source_sha256=authorization.authorized_control_source_raw_sha256,
            execution_authorization_hash=authorization.authorization_hash,
            materialization_authorized=True,
        )

    def _supplement_locator(
        self, registry_path: Path | None = None
    ) -> dict[str, object]:
        document: dict[str, object] = {
            "artifact_type": (
                "task039e3_r2r_utility_source_census_supplement_local_locator_v1"
            ),
            "schema_version": supplement.SCHEMA_VERSION,
            "authority_version": supplement.AUTHORITY_VERSION,
            "purpose": supplement.PURPOSE,
            "absolute_private_authority_path": str(
                registry_path or self.supplement_registry
            ),
            "private_registry_hash": subject.SUPPLEMENT_PRIVATE_REGISTRY_HASH,
            "supplement_descriptor_hash": supplement.SUPPLEMENT_DESCRIPTOR_HASH,
            "authorization_hash": (
                subject.SUPPLEMENT_MATERIALIZATION_AUTHORIZATION_HASH
            ),
            "created_at": TIMESTAMP,
            "local_only": True,
            "must_not_be_committed": True,
        }
        document["artifact_hash"] = stable_hash_v1(document)
        return document

    def _validate(
        self,
        authority_kind: str,
        document: dict[str, object],
        registry_path: Path,
    ) -> subject.PortablePrivateLocatorCustodyV1:
        locator_path = self.root / f"{authority_kind.lower()}.locator.json"
        _write_json(locator_path, document)
        return subject.validate_portable_private_locator_custody_v1(
            authority_kind,
            locator_path=locator_path,
            registry_path=registry_path,
        )

    def test_fresh_main_locator_hash_may_differ_from_historical(self) -> None:
        document = self._main_locator()
        self.assertNotEqual(
            document["artifact_hash"],
            subject.MAIN_HISTORICAL_MATERIALIZATION_LOCATOR_HASH,
        )
        result = self._validate("MAIN", document, self.main_registry)
        self.assertTrue(result.locator_schema_valid)
        self.assertTrue(result.locator_local_only)
        self.assertTrue(result.locator_registry_binding_match)
        self.assertTrue(result.locator_materialization_authority_match)
        self.assertNotIn(str(self.root), repr(result))

    def test_fresh_supplement_locator_hash_may_differ_from_historical(self) -> None:
        document = self._supplement_locator()
        self.assertNotEqual(
            document["artifact_hash"],
            subject.SUPPLEMENT_HISTORICAL_MATERIALIZATION_LOCATOR_HASH,
        )
        result = self._validate(
            "SUPPLEMENT", document, self.supplement_registry
        )
        self.assertTrue(result.locator_schema_valid)
        self.assertTrue(result.locator_registry_binding_match)
        self.assertTrue(result.locator_materialization_authority_match)
        self.assertNotIn(str(self.root), repr(result))

    def test_historical_locator_hash_with_wrong_current_registry_is_rejected(self) -> None:
        document = self._main_locator(self.supplement_registry)
        document["artifact_hash"] = (
            subject.MAIN_HISTORICAL_MATERIALIZATION_LOCATOR_HASH
        )
        with self.assertRaises(Exception):
            self._validate("MAIN", document, self.main_registry)

    def test_locator_target_substitution_is_rejected(self) -> None:
        document = self._main_locator(self.supplement_registry)
        with self.assertRaises(subject.InnerExecutionAuthorizationV1Error):
            self._validate("MAIN", document, self.main_registry)

    def test_main_locator_registry_hash_substitution_is_rejected(self) -> None:
        document = self._main_locator()
        document["private_authority_hash"] = "0" * 64
        document["artifact_hash"] = stable_hash_v1(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        with self.assertRaises(subject.InnerExecutionAuthorizationV1Error):
            self._validate("MAIN", document, self.main_registry)

    def test_supplement_locator_registry_hash_substitution_is_rejected(self) -> None:
        document = self._supplement_locator()
        document["private_registry_hash"] = "0" * 64
        document["artifact_hash"] = stable_hash_v1(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        with self.assertRaises(subject.InnerExecutionAuthorizationV1Error):
            self._validate("SUPPLEMENT", document, self.supplement_registry)

    def test_supplement_materialization_authority_substitution_is_rejected(self) -> None:
        document = self._supplement_locator()
        document["authorization_hash"] = "0" * 64
        document["artifact_hash"] = stable_hash_v1(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        with self.assertRaises(subject.InnerExecutionAuthorizationV1Error):
            self._validate("SUPPLEMENT", document, self.supplement_registry)

    def test_repo_internal_registry_is_rejected(self) -> None:
        repo_file = ROOT / "AGENTS.md"
        document = self._main_locator(repo_file)
        locator_path = self.root / "main.locator.json"
        _write_json(locator_path, document)
        with self.assertRaises(subject.InnerExecutionAuthorizationV1Error):
            subject.validate_portable_private_locator_custody_v1(
                "MAIN",
                locator_path=locator_path,
                registry_path=repo_file,
            )

    def test_locator_symlink_is_rejected(self) -> None:
        locator_path = self.root / "main.locator.json"
        _write_json(locator_path, self._main_locator())
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaises(subject.InnerExecutionAuthorizationV1Error):
                subject.validate_portable_private_locator_custody_v1(
                    "MAIN",
                    locator_path=locator_path,
                    registry_path=self.main_registry,
                )

    def test_malformed_registry_documents_are_rejected_by_canonical_validators(self) -> None:
        with self.assertRaises(Exception):
            main_authority.validate_private_registry_document_v1(
                {"artifact_hash": subject.MAIN_PRIVATE_REGISTRY_HASH},
                main_authority.build_common42_authority_v1(),
            )
        with self.assertRaises(Exception):
            supplement.validate_supplement_private_registry_document_v1(
                {"artifact_hash": subject.SUPPLEMENT_PRIVATE_REGISTRY_HASH}
            )

    def test_authority_kind_swap_and_caller_hash_selection_are_rejected(self) -> None:
        document = self._main_locator()
        with self.assertRaises(Exception):
            self._validate("SUPPLEMENT", document, self.main_registry)
        locator_path = self.root / "main-extra.locator.json"
        _write_json(locator_path, document)
        with self.assertRaises(TypeError):
            subject.validate_portable_private_locator_custody_v1(
                "MAIN",
                locator_path=locator_path,
                registry_path=self.main_registry,
                expected_registry_hash="0" * 64,  # type: ignore[call-arg]
            )


if __name__ == "__main__":
    unittest.main()
