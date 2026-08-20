"""Independent synthetic audit of portable INNER private custody.

The suite creates only placeholder files in an ephemeral directory.  It does
not read environment bindings, real registries, HAI payloads, labels, or
private numeric values and never invokes the real custody preflight.
"""

from __future__ import annotations

import copy
from dataclasses import fields, replace
from hashlib import sha256
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

from paperworks.v6 import (  # noqa: E402
    task039e3_r2r_utility_inner_execution_authorization_v1 as subject,
)
from paperworks.v6 import (  # noqa: E402
    task039e3_r2r_utility_normal_only_authority_v1 as main_authority,
)
from paperworks.v6 import (  # noqa: E402
    task039e3_r2r_utility_source_census_supplement_v1 as supplement,
)


def _hash(document: dict[str, object]) -> str:
    return sha256(
        json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _self_hash(document: dict[str, object]) -> dict[str, object]:
    result = {key: value for key, value in document.items() if key != "artifact_hash"}
    result["artifact_hash"] = _hash(result)
    return result


def _write(path: Path, document: dict[str, object]) -> None:
    path.write_text(
        json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


class IndependentPortablePrivateCustodyAudit(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.main_registry_a = self.root / "main-a.json"
        self.main_registry_b = self.root / "main-b.json"
        self.supp_registry_a = self.root / "supp-a.json"
        self.supp_registry_b = self.root / "supp-b.json"
        for path in (
            self.main_registry_a,
            self.main_registry_b,
            self.supp_registry_a,
            self.supp_registry_b,
        ):
            path.write_text("{}\n", encoding="utf-8")
        self.main_auth = (
            main_authority.load_committed_materialization_execution_authorization_r1(
                ROOT
            )
        )

    def _main_document(
        self,
        registry: Path,
        *,
        timestamp: str = "2026-08-20T00:00:01+00:00",
    ) -> dict[str, object]:
        return _self_hash(
            {
                "artifact_type": (
                    "task039e3_r2r_utility_normal_only_local_locator_manifest_v1"
                ),
                "schema_version": main_authority.SCHEMA_VERSION,
                "authority_version": main_authority.AUTHORITY_VERSION,
                "absolute_private_authority_path": str(registry),
                "private_authority_hash": subject.MAIN_PRIVATE_REGISTRY_HASH,
                "public_receipt_hash": subject.MAIN_MATERIALIZED_AUDIT_RECEIPT_HASH,
                "created_at": timestamp,
                "builder_commit": self.main_auth.authorized_control_commit,
                "local_only": True,
                "must_not_be_committed": True,
                "control_revision": main_authority.NORMAL_ONLY_AUTHORITY_CONTROL_REVISION,
                "scientific_v1_commit": main_authority.SCIENTIFIC_V1_COMMIT,
                "control_source_commit": self.main_auth.authorized_control_commit,
                "control_source_git_blob": self.main_auth.authorized_control_source_blob,
                "control_source_raw_sha256": (
                    self.main_auth.authorized_control_source_raw_sha256
                ),
                "execution_authorization_hash": self.main_auth.authorization_hash,
                "materialization_authorized": True,
            }
        )

    def _supplement_document(
        self,
        registry: Path,
        *,
        timestamp: str = "2026-08-20T00:00:01+00:00",
    ) -> dict[str, object]:
        return _self_hash(
            {
                "artifact_type": (
                    "task039e3_r2r_utility_source_census_supplement_local_locator_v1"
                ),
                "schema_version": supplement.SCHEMA_VERSION,
                "authority_version": supplement.AUTHORITY_VERSION,
                "purpose": supplement.PURPOSE,
                "absolute_private_authority_path": str(registry),
                "private_registry_hash": subject.SUPPLEMENT_PRIVATE_REGISTRY_HASH,
                "supplement_descriptor_hash": supplement.SUPPLEMENT_DESCRIPTOR_HASH,
                "authorization_hash": (
                    subject.SUPPLEMENT_MATERIALIZATION_AUTHORIZATION_HASH
                ),
                "created_at": timestamp,
                "local_only": True,
                "must_not_be_committed": True,
            }
        )

    def _rejected(
        self,
        kind: str,
        document: dict[str, object],
        registry: Path,
        *,
        locator_name: str = "candidate.locator.json",
    ) -> bool:
        locator = self.root / locator_name
        _write(locator, document)
        try:
            subject.validate_portable_private_locator_custody_v1(
                kind,
                locator_path=locator,
                registry_path=registry,
            )
        except Exception:
            return True
        return False

    def test_current_valid_machine_locators_do_not_replay_historical_hash(self) -> None:
        cases = (
            ("MAIN", self._main_document(self.main_registry_a), self.main_registry_a),
            (
                "MAIN",
                self._main_document(
                    self.main_registry_b,
                    timestamp="2026-08-20T00:00:02+00:00",
                ),
                self.main_registry_b,
            ),
            (
                "SUPPLEMENT",
                self._supplement_document(self.supp_registry_a),
                self.supp_registry_a,
            ),
            (
                "SUPPLEMENT",
                self._supplement_document(
                    self.supp_registry_b,
                    timestamp="2026-08-20T00:00:02+00:00",
                ),
                self.supp_registry_b,
            ),
        )
        observed_hashes: list[str] = []
        portable_identities: dict[str, set[str]] = {"MAIN": set(), "SUPPLEMENT": set()}
        for index, (kind, document, registry) in enumerate(cases):
            locator = self.root / f"valid-{index}.locator.json"
            _write(locator, document)
            result = subject.validate_portable_private_locator_custody_v1(
                kind,
                locator_path=locator,
                registry_path=registry,
            )
            observed_hashes.append(str(document["artifact_hash"]))
            portable_identities[kind].add(result.portable_custody_identity)
        self.assertEqual(len(set(observed_hashes)), 4)
        self.assertNotIn(
            subject.MAIN_HISTORICAL_MATERIALIZATION_LOCATOR_HASH,
            observed_hashes,
        )
        self.assertNotIn(
            subject.SUPPLEMENT_HISTORICAL_MATERIALIZATION_LOCATOR_HASH,
            observed_hashes,
        )
        self.assertEqual({kind: len(values) for kind, values in portable_identities.items()}, {"MAIN": 1, "SUPPLEMENT": 1})

    def test_main_locator_attack_matrix_rejects_every_invalid(self) -> None:
        wrong = "0" * 64
        base = self._main_document(self.main_registry_a)
        attacks: list[tuple[str, dict[str, object], Path]] = []
        for name, changes in (
            ("wrong_registry_hash", {"private_authority_hash": wrong}),
            ("wrong_authorization", {"execution_authorization_hash": wrong}),
            ("wrong_version", {"authority_version": "UNFROZEN"}),
            ("wrong_control", {"control_source_git_blob": "0" * 40}),
            ("not_local", {"local_only": False}),
            ("committable", {"must_not_be_committed": False}),
            ("malformed_extra", {"unexpected": True}),
        ):
            attacks.append((name, _self_hash({**base, **changes}), self.main_registry_a))
        attacks.extend(
            (
                (
                    "wrong_target",
                    self._main_document(self.main_registry_b),
                    self.main_registry_a,
                ),
                (
                    "stale_target",
                    self._main_document(self.root / "missing.json"),
                    self.main_registry_a,
                ),
                (
                    "historical_hash_replay",
                    {
                        **self._main_document(self.main_registry_b),
                        "artifact_hash": subject.MAIN_HISTORICAL_MATERIALIZATION_LOCATOR_HASH,
                    },
                    self.main_registry_a,
                ),
            )
        )
        accepted = [
            name
            for index, (name, document, registry) in enumerate(attacks)
            if not self._rejected(
                "MAIN", document, registry, locator_name=f"main-{index}.json"
            )
        ]
        self.assertEqual(len(attacks), 10)
        self.assertEqual(accepted, [])

    def test_supplement_locator_attack_matrix_rejects_every_invalid(self) -> None:
        wrong = "0" * 64
        base = self._supplement_document(self.supp_registry_a)
        attacks: list[tuple[str, dict[str, object], Path]] = []
        for name, changes in (
            ("wrong_registry_hash", {"private_registry_hash": wrong}),
            ("wrong_authorization", {"authorization_hash": wrong}),
            ("wrong_version", {"authority_version": "UNFROZEN"}),
            ("wrong_purpose", {"purpose": "RELATION_AUTHORITY"}),
            ("wrong_descriptor", {"supplement_descriptor_hash": wrong}),
            ("not_local", {"local_only": False}),
            ("malformed_extra", {"unexpected": True}),
        ):
            attacks.append((name, _self_hash({**base, **changes}), self.supp_registry_a))
        attacks.extend(
            (
                (
                    "wrong_target",
                    self._supplement_document(self.supp_registry_b),
                    self.supp_registry_a,
                ),
                (
                    "stale_target",
                    self._supplement_document(self.root / "missing.json"),
                    self.supp_registry_a,
                ),
                (
                    "historical_hash_replay",
                    {
                        **self._supplement_document(self.supp_registry_b),
                        "artifact_hash": subject.SUPPLEMENT_HISTORICAL_MATERIALIZATION_LOCATOR_HASH,
                    },
                    self.supp_registry_a,
                ),
            )
        )
        accepted = [
            name
            for index, (name, document, registry) in enumerate(attacks)
            if not self._rejected(
                "SUPPLEMENT", document, registry, locator_name=f"supp-{index}.json"
            )
        ]
        self.assertEqual(len(attacks), 10)
        self.assertEqual(accepted, [])

    def test_path_and_file_type_attack_matrix_rejects_every_invalid(self) -> None:
        locator = self.root / "path.locator.json"
        _write(locator, self._main_document(self.main_registry_a))
        accepted: list[str] = []
        cases = (
            ("repo_internal", locator, ROOT / "AGENTS.md"),
            ("directory_registry", locator, self.root),
        )
        for name, locator_path, registry_path in cases:
            try:
                subject.validate_portable_private_locator_custody_v1(
                    "MAIN",
                    locator_path=locator_path,
                    registry_path=registry_path,
                )
            except Exception:
                continue
            accepted.append(name)
        with patch.object(Path, "is_symlink", return_value=True):
            try:
                subject.validate_portable_private_locator_custody_v1(
                    "MAIN",
                    locator_path=locator,
                    registry_path=self.main_registry_a,
                )
            except Exception:
                pass
            else:
                accepted.append("symlink")
        self.assertEqual(accepted, [])

    def test_preflight_and_authorization_forgery_matrix_rejects_every_invalid(self) -> None:
        receipt = subject.build_synthetic_inner_execution_custody_preflight_receipt_v1()
        authorization = subject.issue_inner_execution_authorization_v1(receipt)
        receipt_attacks = (
            {"main_locator_registry_binding_match": False},
            {"supplement_locator_registry_binding_match": False},
            {"main_registry_content_hash_match": False},
            {"supplement_registry_content_hash_match": False},
            {"portable_private_locator_policy_hash": "0" * 64},
            {"private_paths_exposed": 1},
        )
        authorization_attacks = (
            {"authorization_scope": "TEST2"},
            {"d0_authorized": True},
            {"d2_authorized": True},
            {"detector_authorized": True},
            {"outer_authorized": True},
            {"test2_authorized": True},
            {"threshold_recalibration_authorized": True},
            {"rule_regeneration_authorized": True},
            {"metric_modification_authorized": True},
            {"main_private_registry_expected_hash": "0" * 64},
            {"supplement_private_registry_expected_hash": "0" * 64},
        )
        accepted: list[str] = []
        for index, changes in enumerate(receipt_attacks):
            candidate = replace(receipt, **changes)
            candidate = replace(
                candidate,
                custody_preflight_hash=_hash(
                    {
                        item.name: getattr(candidate, item.name)
                        for item in fields(candidate)
                        if item.name != "custody_preflight_hash"
                    }
                ),
            )
            try:
                subject.validate_inner_execution_custody_preflight_receipt_v1(candidate)
            except Exception:
                continue
            accepted.append(f"receipt-{index}")
        for index, changes in enumerate(authorization_attacks):
            candidate = replace(authorization, **changes)
            candidate = replace(
                candidate,
                authorization_hash=_hash(
                    {
                        item.name: getattr(candidate, item.name)
                        for item in fields(candidate)
                        if not item.name.startswith("_")
                        and item.name != "authorization_hash"
                    }
                ),
            )
            try:
                subject.validate_inner_execution_authorization_v1(
                    candidate,
                    receipt,
                )
            except Exception:
                continue
            accepted.append(f"authorization-{index}")
        for name, candidate in (
            ("receipt-reconstruct", type(receipt)(**{item.name: getattr(receipt, item.name) for item in fields(receipt)})),
            ("receipt-deepcopy", copy.deepcopy(receipt)),
            ("authorization-reconstruct", type(authorization)(**{item.name: getattr(authorization, item.name) for item in fields(authorization)})),
            ("authorization-deepcopy", copy.deepcopy(authorization)),
        ):
            try:
                if name.startswith("receipt"):
                    subject.validate_inner_execution_custody_preflight_receipt_v1(candidate)  # type: ignore[arg-type]
                else:
                    subject.validate_inner_execution_authorization_v1(candidate, receipt)  # type: ignore[arg-type]
            except Exception:
                continue
            accepted.append(name)
        self.assertEqual(len(receipt_attacks) + len(authorization_attacks) + 4, 21)
        self.assertEqual(accepted, [])


if __name__ == "__main__":
    unittest.main()
