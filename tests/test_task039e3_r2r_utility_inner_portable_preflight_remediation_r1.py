"""Focused synthetic tests for the R2 portable preflight remediation.

No real registry, HAI payload, label, environment binding, private path, or
private numeric value is read.  Placeholder files exercise locator custody;
the canonical MAIN authority is rebuilt from frozen public documents only.
"""

from __future__ import annotations

from dataclasses import fields, replace
import inspect
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


def _self_hash(document: dict[str, object]) -> dict[str, object]:
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    payload["artifact_hash"] = stable_hash_v1(payload)
    return payload


def _write(path: Path, document: dict[str, object]) -> None:
    path.write_text(
        json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


class PortablePreflightRemediationR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.main_registry = self.root / "main.registry.json"
        self.other_registry = self.root / "other.registry.json"
        self.supplement_registry = self.root / "supplement.registry.json"
        for path in (
            self.main_registry,
            self.other_registry,
            self.supplement_registry,
        ):
            path.write_text("{}\n", encoding="utf-8")
        self.main_authorization = (
            main_authority.load_committed_materialization_execution_authorization_r1(
                ROOT
            )
        )

    def _main_locator(self, registry: Path | None = None) -> dict[str, object]:
        return main_authority.local_locator_manifest_document_v1(
            private_authority_path=registry or self.main_registry,
            private_authority_hash=subject.MAIN_PRIVATE_REGISTRY_HASH,
            public_receipt_hash=subject.MAIN_MATERIALIZED_AUDIT_RECEIPT_HASH,
            created_at=TIMESTAMP,
            builder_commit=self.main_authorization.authorized_control_commit,
            builder_git_blob=self.main_authorization.authorized_control_source_blob,
            builder_source_sha256=(
                self.main_authorization.authorized_control_source_raw_sha256
            ),
            execution_authorization_hash=self.main_authorization.authorization_hash,
            materialization_authorized=True,
        )

    def _supplement_locator(
        self, registry: Path | None = None
    ) -> dict[str, object]:
        return _self_hash(
            {
                "artifact_type": (
                    "task039e3_r2r_utility_source_census_supplement_local_locator_v1"
                ),
                "schema_version": supplement.SCHEMA_VERSION,
                "authority_version": supplement.AUTHORITY_VERSION,
                "purpose": supplement.PURPOSE,
                "absolute_private_authority_path": str(
                    registry or self.supplement_registry
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
        )

    def _validate(
        self,
        kind: str,
        document: dict[str, object],
        registry: Path,
        name: str,
    ):
        locator = self.root / name
        _write(locator, document)
        return subject.validate_portable_private_locator_custody_v1(
            kind,
            locator_path=locator,
            registry_path=registry,
        )

    def test_main_registry_authority_replays_both_frozen_public_inputs(self) -> None:
        authority = subject._build_main_registry_validation_authority_v1(ROOT)
        self.assertEqual(
            authority.authority_definition_hash,
            main_authority.CANONICAL_AUTHORITY_DEFINITION_HASH,
        )
        source = inspect.getsource(subject.perform_inner_execution_custody_preflight_v1)
        self.assertIn("_build_main_registry_validation_authority_v1", source)
        self.assertNotIn("build_common42_authority_v1()", source)
        self.assertEqual(
            subject.INNER_AUTHORIZATION_CONTROL_REVISION,
            "R2_PORTABLE_PREFLIGHT",
        )

    def test_fresh_main_and_supplement_locators_pass_without_historical_hash(self) -> None:
        main_document = self._main_locator()
        supplement_document = self._supplement_locator()
        self.assertNotEqual(
            main_document["artifact_hash"],
            subject.MAIN_HISTORICAL_MATERIALIZATION_LOCATOR_HASH,
        )
        self.assertNotEqual(
            supplement_document["artifact_hash"],
            subject.SUPPLEMENT_HISTORICAL_MATERIALIZATION_LOCATOR_HASH,
        )
        main_result = self._validate(
            "MAIN", main_document, self.main_registry, "main-valid.json"
        )
        supplement_result = self._validate(
            "SUPPLEMENT",
            supplement_document,
            self.supplement_registry,
            "supp-valid.json",
        )
        self.assertTrue(main_result.locator_registry_binding_match)
        self.assertTrue(supplement_result.locator_registry_binding_match)

    def test_main_locator_invalid_matrix_rejects_all(self) -> None:
        base = self._main_locator()
        wrong_hash = _self_hash({**base, "private_authority_hash": "0" * 64})
        wrong_auth = _self_hash(
            {**base, "execution_authorization_hash": "0" * 64}
        )
        malformed = _self_hash({**base, "unexpected": True})
        wrong_target = self._main_locator(self.other_registry)
        historical_wrong = {
            **wrong_target,
            "artifact_hash": subject.MAIN_HISTORICAL_MATERIALIZATION_LOCATOR_HASH,
        }
        attacks = (
            ("wrong-hash", wrong_hash, self.main_registry),
            ("wrong-auth", wrong_auth, self.main_registry),
            ("malformed", malformed, self.main_registry),
            ("wrong-target", wrong_target, self.main_registry),
            ("historical-wrong", historical_wrong, self.main_registry),
        )
        accepted: list[str] = []
        for name, document, registry in attacks:
            try:
                self._validate("MAIN", document, registry, f"main-{name}.json")
            except Exception:
                continue
            accepted.append(name)
        repo_locator = self.root / "repo-main.json"
        _write(repo_locator, self._main_locator(ROOT / "AGENTS.md"))
        try:
            subject.validate_portable_private_locator_custody_v1(
                "MAIN",
                locator_path=repo_locator,
                registry_path=ROOT / "AGENTS.md",
            )
        except Exception:
            pass
        else:
            accepted.append("repo-internal")
        locator = self.root / "main-symlink.json"
        _write(locator, base)
        with patch.object(Path, "is_symlink", return_value=True):
            try:
                subject.validate_portable_private_locator_custody_v1(
                    "MAIN",
                    locator_path=locator,
                    registry_path=self.main_registry,
                )
            except Exception:
                pass
            else:
                accepted.append("symlink")
        self.assertEqual(len(attacks) + 2, 7)
        self.assertEqual(accepted, [])

    def test_supplement_locator_invalid_matrix_rejects_all(self) -> None:
        base = self._supplement_locator()
        attacks = (
            (
                "wrong-hash",
                _self_hash({**base, "private_registry_hash": "0" * 64}),
                self.supplement_registry,
            ),
            (
                "wrong-auth",
                _self_hash({**base, "authorization_hash": "0" * 64}),
                self.supplement_registry,
            ),
            (
                "malformed",
                _self_hash({**base, "unexpected": True}),
                self.supplement_registry,
            ),
            (
                "wrong-target",
                self._supplement_locator(self.other_registry),
                self.supplement_registry,
            ),
        )
        accepted: list[str] = []
        for name, document, registry in attacks:
            try:
                self._validate(
                    "SUPPLEMENT", document, registry, f"supp-{name}.json"
                )
            except Exception:
                continue
            accepted.append(name)
        locator = self.root / "supp-symlink.json"
        _write(locator, base)
        with patch.object(Path, "is_symlink", return_value=True):
            try:
                subject.validate_portable_private_locator_custody_v1(
                    "SUPPLEMENT",
                    locator_path=locator,
                    registry_path=self.supplement_registry,
                )
            except Exception:
                pass
            else:
                accepted.append("symlink")
        self.assertEqual(len(attacks) + 1, 5)
        self.assertEqual(accepted, [])

    def test_receipt_authorization_reconstruction_and_scope_escalation_reject(self) -> None:
        receipt = subject.build_synthetic_inner_execution_custody_preflight_receipt_v1()
        issued = subject.issue_inner_execution_authorization_v1(receipt)
        reconstructed_receipt = type(receipt)(
            **{item.name: getattr(receipt, item.name) for item in fields(receipt)}
        )
        reconstructed_authorization = type(issued)(
            **{item.name: getattr(issued, item.name) for item in fields(issued)}
        )
        escalated = replace(issued, d2_authorized=True)
        for candidate, candidate_receipt in (
            (reconstructed_authorization, receipt),
            (issued, reconstructed_receipt),
            (escalated, receipt),
        ):
            with self.assertRaises(Exception):
                subject.validate_inner_execution_authorization_v1(
                    candidate,
                    candidate_receipt,
                )


if __name__ == "__main__":
    unittest.main()
