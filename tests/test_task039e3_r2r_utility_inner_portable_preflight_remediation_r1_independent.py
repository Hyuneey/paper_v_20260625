"""Independent synthetic audit of the R2 portable preflight remediation.

The audit uses public documents and placeholder temporary files only.  It
does not load local bindings, private registries, HAI payloads, or labels and
never invokes the real one-attempt preflight.
"""

from __future__ import annotations

from dataclasses import fields, replace
import copy
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


def _self_hash(document: dict[str, object]) -> dict[str, object]:
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    payload["artifact_hash"] = stable_hash_v1(payload)
    return payload


def _write(path: Path, document: dict[str, object]) -> None:
    path.write_text(
        json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


class IndependentPortablePreflightRemediationR1Audit(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.main_a = self.root / "main-a.json"
        self.main_b = self.root / "main-b.json"
        self.supp_a = self.root / "supp-a.json"
        self.supp_b = self.root / "supp-b.json"
        for path in (self.main_a, self.main_b, self.supp_a, self.supp_b):
            path.write_text("{}\n", encoding="utf-8")
        self.main_authorization = (
            main_authority.load_committed_materialization_execution_authorization_r1(
                ROOT
            )
        )

    def _main(self, registry: Path) -> dict[str, object]:
        return main_authority.local_locator_manifest_document_v1(
            private_authority_path=registry,
            private_authority_hash=subject.MAIN_PRIVATE_REGISTRY_HASH,
            public_receipt_hash=subject.MAIN_MATERIALIZED_AUDIT_RECEIPT_HASH,
            created_at="2026-08-20T00:00:01+00:00",
            builder_commit=self.main_authorization.authorized_control_commit,
            builder_git_blob=self.main_authorization.authorized_control_source_blob,
            builder_source_sha256=(
                self.main_authorization.authorized_control_source_raw_sha256
            ),
            execution_authorization_hash=self.main_authorization.authorization_hash,
            materialization_authorized=True,
        )

    def _supp(self, registry: Path) -> dict[str, object]:
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
                "authorization_hash": subject.SUPPLEMENT_MATERIALIZATION_AUTHORIZATION_HASH,
                "created_at": "2026-08-20T00:00:01+00:00",
                "local_only": True,
                "must_not_be_committed": True,
            }
        )

    def _accepted(
        self,
        kind: str,
        document: dict[str, object],
        configured_registry: Path,
        name: str,
    ) -> bool:
        locator = self.root / name
        _write(locator, document)
        try:
            subject.validate_portable_private_locator_custody_v1(
                kind,
                locator_path=locator,
                registry_path=configured_registry,
            )
        except Exception:
            return False
        return True

    def test_root_cause_fix_supplies_two_independent_public_documents(self) -> None:
        original = main_authority.build_common42_authority_v1
        with patch.object(
            main_authority,
            "build_common42_authority_v1",
            wraps=original,
        ) as builder:
            authority = subject._build_main_registry_validation_authority_v1(ROOT)
        self.assertEqual(builder.call_count, 1)
        self.assertEqual(len(builder.call_args.args), 2)
        self.assertEqual(
            authority.authority_definition_hash,
            main_authority.CANONICAL_AUTHORITY_DEFINITION_HASH,
        )
        with self.assertRaises(TypeError):
            original()

    def test_root_cause_specific_public_input_bypasses_reject(self) -> None:
        attacks = (
            {"artifact_hash": main_authority.EXECUTABLE_EQUIVALENCE_HASH},
            {"artifact_hash": main_authority.E1_PUBLIC_MANIFEST_HASH},
        )
        accepted: list[int] = []
        for index, forged in enumerate(attacks):
            with patch.object(
                subject,
                "_load_public_self_hashed_v1",
                side_effect=(forged, forged),
            ):
                try:
                    subject._build_main_registry_validation_authority_v1(ROOT)
                except Exception:
                    continue
                accepted.append(index)
        self.assertEqual(accepted, [])

    def test_locator_cross_authority_and_self_rehash_attacks_reject(self) -> None:
        wrong = "0" * 64
        main_base = self._main(self.main_a)
        supp_base = self._supp(self.supp_a)
        cases = (
            (
                "MAIN",
                _self_hash({**main_base, "private_authority_hash": wrong}),
                self.main_a,
                "main-wrong-registry.json",
            ),
            (
                "MAIN",
                _self_hash({**main_base, "execution_authorization_hash": wrong}),
                self.main_a,
                "main-wrong-auth.json",
            ),
            ("MAIN", self._main(self.main_b), self.main_a, "main-wrong-target.json"),
            (
                "SUPPLEMENT",
                _self_hash({**supp_base, "private_registry_hash": wrong}),
                self.supp_a,
                "supp-wrong-registry.json",
            ),
            (
                "SUPPLEMENT",
                _self_hash({**supp_base, "authorization_hash": wrong}),
                self.supp_a,
                "supp-wrong-auth.json",
            ),
            (
                "SUPPLEMENT",
                self._supp(self.supp_b),
                self.supp_a,
                "supp-wrong-target.json",
            ),
            ("SUPPLEMENT", main_base, self.main_a, "cross-main-as-supp.json"),
            ("MAIN", supp_base, self.supp_a, "cross-supp-as-main.json"),
        )
        accepted = [
            name
            for kind, document, registry, name in cases
            if self._accepted(kind, document, registry, name)
        ]
        self.assertEqual(len(cases), 8)
        self.assertEqual(accepted, [])

    def test_historical_hash_replay_cannot_override_current_registry(self) -> None:
        main = self._main(self.main_b)
        main["artifact_hash"] = subject.MAIN_HISTORICAL_MATERIALIZATION_LOCATOR_HASH
        supp = self._supp(self.supp_b)
        supp["artifact_hash"] = (
            subject.SUPPLEMENT_HISTORICAL_MATERIALIZATION_LOCATOR_HASH
        )
        self.assertFalse(
            self._accepted("MAIN", main, self.main_a, "main-historical.json")
        )
        self.assertFalse(
            self._accepted(
                "SUPPLEMENT", supp, self.supp_a, "supp-historical.json"
            )
        )

    def test_receipt_and_authorization_forgery_scope_matrix_rejects(self) -> None:
        receipt = subject.build_synthetic_inner_execution_custody_preflight_receipt_v1()
        authorization = subject.issue_inner_execution_authorization_v1(receipt)
        candidates = (
            replace(authorization, d0_authorized=True),
            replace(authorization, d2_authorized=True),
            replace(authorization, detector_authorized=True),
            replace(authorization, outer_authorized=True),
            replace(authorization, test2_authorized=True),
            replace(authorization, authorization_scope="OUTER"),
            replace(authorization, main_private_registry_expected_hash="0" * 64),
            replace(authorization, supplement_private_registry_expected_hash="0" * 64),
            type(authorization)(
                **{
                    item.name: getattr(authorization, item.name)
                    for item in fields(authorization)
                }
            ),
            copy.deepcopy(authorization),
        )
        accepted: list[int] = []
        for index, candidate in enumerate(candidates):
            try:
                subject.validate_inner_execution_authorization_v1(
                    candidate,
                    receipt,
                )
            except Exception:
                continue
            accepted.append(index)
        forged_receipt = type(receipt)(
            **{item.name: getattr(receipt, item.name) for item in fields(receipt)}
        )
        try:
            subject.validate_inner_execution_custody_preflight_receipt_v1(
                forged_receipt
            )
        except Exception:
            pass
        else:
            accepted.append(len(candidates))
        self.assertEqual(len(candidates) + 1, 11)
        self.assertEqual(accepted, [])


if __name__ == "__main__":
    unittest.main()
