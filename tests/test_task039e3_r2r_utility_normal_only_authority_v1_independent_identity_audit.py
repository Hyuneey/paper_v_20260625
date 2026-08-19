from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
import math
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1
import paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
HISTORICAL_E1 = "0998c6600078b8a0aca7263b6e0b702808cc141b1cbcfe3d0026fddb98c408a7"
HISTORICAL_REGISTRY = "59e81b261801f28eefc917256dc628af704a14b4064161972d01545968555271"


def load(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def rehash_record(record: dict[str, object]) -> None:
    record["record_hash"] = stable_hash_v1(
        {key: value for key, value in record.items() if key != "record_hash"}
    )


def rehash_document(document: dict[str, object]) -> None:
    document["artifact_hash"] = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )


class IndependentIdentityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.equivalence = load("TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json")
        cls.manifest = load("TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json")
        cls.authority = subject.build_common42_authority_v1(cls.equivalence, cls.manifest)
        cls.values: dict[tuple[str, str], int | float] = {}
        windows: dict[str, int | float] = {
            "source_pre_window_seconds": 5,
            "source_post_window_seconds": 5,
            "minimum_source_stability_fraction": 0.8,
            "source_refractory_seconds": 10,
            "cross_source_isolation_radius_seconds": 2,
            "target_baseline_window_seconds": 5,
            "target_response_window_seconds": 3,
        }
        for relation in cls.authority.relations:
            for role in subject.UTILITY_NUMERIC_ROLES:
                if role == "source_step_threshold":
                    value: int | float = 2.5
                elif role == "source_stability_tolerance":
                    value = 0.25
                elif role == "target_noise_scale":
                    value = 0.125
                else:
                    value = windows[role]
                cls.values[(relation.relation_binding_hash, role)] = value
        cls.registry = subject.build_private_registry_document_v1(cls.authority, cls.values)

    def test_common42_identity_oracle_matches_all_fields(self) -> None:
        entries = {
            entry["relation_binding_hash"]: entry for entry in self.manifest["entries"]
        }
        expected: list[tuple[object, ...]] = []
        for record in self.equivalence["relation_records"]:
            signature = record["executable_signature"]
            binding = record["relation_binding_hash"]
            self.assertEqual(stable_hash_v1(signature), record["semantic_execution_hash"])
            self.assertEqual(tuple(record["common_arm_cells"]), ("T0", "T1", "T1-B"))
            entry = entries[binding]
            expected.append(
                (
                    entry["relation_identity"],
                    binding,
                    record["semantic_execution_hash"],
                    signature["source"],
                    signature["target"],
                    signature["source_step_direction"],
                    signature["target_response_direction"],
                    signature["selected_delay_horizon_seconds"],
                )
            )
        expected.sort(key=lambda row: row[1])
        observed = [
            (
                relation.relation_identity,
                relation.relation_binding_hash,
                relation.semantic_execution_hash,
                relation.source,
                relation.target,
                relation.source_direction,
                relation.target_direction,
                relation.selected_horizon_seconds,
            )
            for relation in self.authority.relations
        ]
        self.assertEqual(len(expected), 42)
        self.assertEqual(observed, expected)
        self.assertEqual(self.authority.authority_definition_hash, "6e7a286a37a5048a7887e8bea69f9ec0a9c3ff76c538cbb475e886fba276e4de")

    def test_reference_identities_match_independent_preimage(self) -> None:
        expected: list[str] = []
        for relation in self.authority.relations:
            for role in subject.UTILITY_NUMERIC_ROLES:
                preimage = {
                    "authority_version": "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1",
                    "relation_binding_hash": relation.relation_binding_hash,
                    "semantic_execution_hash": relation.semantic_execution_hash,
                    "numeric_role": role,
                    "calibration_policy_version": "TASK039D0_CONTINUOUS_STEP_CALIBRATION_V1",
                    "normal_input_identity_set": "cc502d87daf19a1511f868c1c767045a4457d505d195b0214f244d1910fe0cda",
                    "common42_authority_hash": "3bd07e1c2baf375bde86a2310b529dda40962e027edbd77485f431dc244730ff",
                }
                identity = f"TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1:{stable_hash_v1(preimage)}"
                expected.append(identity)
                self.assertEqual(subject.new_reference_identity_v1(relation, role), identity)
        self.assertEqual(tuple(expected), self.authority.reference_identities)
        self.assertEqual(len(expected), 420)
        self.assertEqual(len(set(expected)), 420)

    def test_reference_identity_changes_for_every_identity_field_but_not_value(self) -> None:
        relation = self.authority.relations[0]
        role = "source_step_threshold"
        base = {
            "authority_version": subject.AUTHORITY_VERSION,
            "relation_binding_hash": relation.relation_binding_hash,
            "semantic_execution_hash": relation.semantic_execution_hash,
            "numeric_role": role,
            "calibration_policy_version": subject.CALIBRATION_POLICY_VERSION,
            "normal_input_identity_set": subject.NORMAL_INPUT_IDENTITY_SET_HASH,
            "common42_authority_hash": subject.COMMON42_AUTHORITY_CHECK_HASH,
        }
        reference = f"{subject.AUTHORITY_VERSION}:{stable_hash_v1(base)}"
        mutations: dict[str, object] = {
            "authority_version": "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V2",
            "relation_binding_hash": "a" * 64,
            "semantic_execution_hash": "b" * 64,
            "numeric_role": "target_noise_scale",
            "calibration_policy_version": "OTHER_POLICY",
            "normal_input_identity_set": "c" * 64,
            "common42_authority_hash": "d" * 64,
        }
        for field, value in mutations.items():
            changed = dict(base)
            changed[field] = value
            with self.subTest(field=field):
                self.assertNotEqual(reference, f"{changed['authority_version']}:{stable_hash_v1(changed)}")

        first = deepcopy(self.registry["records"][0])
        changed_value = deepcopy(first)
        changed_value["numeric_value"] = float(first["numeric_value"]) + 1.0
        rehash_record(changed_value)
        self.assertEqual(first["new_reference_identity"], changed_value["new_reference_identity"])
        self.assertNotEqual(first["record_hash"], changed_value["record_hash"])

    def test_registry_has_exact_420_by_420_closure(self) -> None:
        records = self.registry["records"]
        keys = {(row["relation_binding_hash"], row["numeric_role"]) for row in records}
        references = {row["new_reference_identity"] for row in records}
        self.assertEqual(len(records), 420)
        self.assertEqual(len(keys), 420)
        self.assertEqual(len(references), 420)
        self.assertEqual(
            subject.validate_private_registry_document_v1(self.registry, self.authority),
            self.registry["artifact_hash"],
        )

    def test_registry_mutation_matrix_fails_closed(self) -> None:
        def mutate_record(field: str, value: object) -> dict[str, object]:
            document = deepcopy(self.registry)
            document["records"][0][field] = value
            rehash_record(document["records"][0])
            rehash_document(document)
            return document

        cases: list[tuple[str, dict[str, object]]] = []
        missing = deepcopy(self.registry)
        missing["records"].pop()
        rehash_document(missing)
        cases.append(("missing", missing))
        extra = deepcopy(self.registry)
        extra["records"].append(deepcopy(extra["records"][0]))
        rehash_document(extra)
        cases.append(("extra", extra))
        duplicate = deepcopy(self.registry)
        duplicate["records"][-1] = deepcopy(duplicate["records"][0])
        rehash_document(duplicate)
        cases.append(("duplicate", duplicate))
        cases.extend(
            (
                ("foreign_relation", mutate_record("relation_binding_hash", "a" * 64)),
                ("wrong_semantic", mutate_record("semantic_execution_hash", "b" * 64)),
                ("wrong_identity", mutate_record("relation_identity", "directional_relation:foreign")),
                ("wrong_role", mutate_record("numeric_role", "selected_delay_horizon_seconds")),
                ("wrong_train1", mutate_record("normal_train1_identity", "c" * 64)),
                ("wrong_train2", mutate_record("normal_train2_identity", "d" * 64)),
                ("wrong_policy", mutate_record("calibration_policy_version", "OTHER")),
                ("wrong_version", mutate_record("authority_version", "OTHER")),
                ("wrong_provenance", mutate_record("provenance_identity", "e" * 64)),
            )
        )
        tampered_record = deepcopy(self.registry)
        tampered_record["records"][0]["record_hash"] = "f" * 64
        rehash_document(tampered_record)
        cases.append(("record_hash", tampered_record))
        tampered_artifact = deepcopy(self.registry)
        tampered_artifact["artifact_hash"] = "f" * 64
        cases.append(("artifact_hash", tampered_artifact))
        for name, document in cases:
            with self.subTest(name=name), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.validate_private_registry_document_v1(document, self.authority)

    def test_strict_numeric_types_and_frozen_constant_types(self) -> None:
        binding = self.authority.relations[0].relation_binding_hash
        for role in ("source_step_threshold", "source_stability_tolerance", "target_noise_scale"):
            for value in (True, 1, "1", None, math.nan, math.inf, -math.inf, 1 + 0j):
                values = dict(self.values)
                values[(binding, role)] = value
                with self.subTest(role=role, value=repr(value)), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                    subject.build_private_registry_document_v1(self.authority, values)
        for role, wrong in (
            ("source_pre_window_seconds", 5.0),
            ("minimum_source_stability_fraction", 0),
            ("target_response_window_seconds", True),
        ):
            values = dict(self.values)
            values[(binding, role)] = wrong
            with self.subTest(role=role), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.build_private_registry_document_v1(self.authority, values)

    def test_historical_identity_collision_mutations_fail(self) -> None:
        relation = self.authority.relations[0]
        role = str(self.registry["records"][0]["numeric_role"])
        for collision in (
            relation.historical_reference(role),
            HISTORICAL_E1,
            HISTORICAL_REGISTRY,
        ):
            document = deepcopy(self.registry)
            document["records"][0]["new_reference_identity"] = collision
            rehash_record(document["records"][0])
            rehash_document(document)
            with self.subTest(collision=collision), self.assertRaises(subject.NormalOnlyAuthorityV1Error):
                subject.validate_private_registry_document_v1(document, self.authority)

    def test_claim_boundary_and_t2_exclusion_are_exact(self) -> None:
        snapshot = subject.authority_snapshot_v1()
        self.assertEqual(subject.AUTHORITY_LINEAGE, "NEW_VERSION_FROM_FROZEN_METHOD_AND_NORMAL_DATA")
        self.assertFalse(subject.HISTORICAL_E1_IDENTITY_RESTORED)
        self.assertFalse(subject.HISTORICAL_NUMERIC_IDENTITY_RESTORED)
        self.assertFalse(subject.T2_UTILITY_SCOPE_AUTHORIZED)
        self.assertFalse(snapshot["historical_e1_identity_restored"])
        self.assertFalse(snapshot["historical_numeric_identity_restored"])
        self.assertEqual(snapshot["common42"]["accepted"], 42)
        self.assertEqual(snapshot["common42"]["no_rule"], 0)
        source = (ROOT / "src/paperworks/v6/task039e3_r2r_utility_normal_only_authority_v1.py").read_text(encoding="utf-8")
        self.assertNotIn("T2 accepted relation", source)

    def test_common_relation_authority_must_not_be_caller_substitutable(self) -> None:
        """A fabricated authority must not validate merely because caller supplied it."""

        first = self.authority.relations[0]
        fabricated_relation = replace(
            first,
            relation_identity=first.relation_identity + ":fabricated",
            selected_horizon_seconds=first.selected_horizon_seconds + 1,
        )
        fabricated = replace(
            self.authority,
            relations=(fabricated_relation,) + self.authority.relations[1:],
        )
        fabricated_values = dict(self.values)
        with self.assertRaises(subject.NormalOnlyAuthorityV1Error):
            document = subject.build_private_registry_document_v1(fabricated, fabricated_values)
            subject.validate_private_registry_document_v1(document, fabricated)


if __name__ == "__main__":
    unittest.main()
