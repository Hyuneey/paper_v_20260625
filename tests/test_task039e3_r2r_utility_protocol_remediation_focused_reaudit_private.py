from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
EQUIVALENCE = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
EXPECTED_E1 = "0998c6600078b8a0aca7263b6e0b702808cc141b1cbcfe3d0026fddb98c408a7"
EXPECTED_REGISTRY = "59e81b261801f28eefc917256dc628af704a14b4064161972d01545968555271"
EXPECTED_COHORT = "4eb4da843a61a9c72aba59edcdf90e49766fc571af7eade14d500b3d04d363d4"
EXPECTED_MATERIALIZATION = "2831f175f777bc0544513c35926269e05b6360c17e13f70b89d1768f1c7aa164"


def _load_private(name: str) -> dict[str, object]:
    value = os.environ.get(name)
    if not value:
        raise unittest.SkipTest(f"explicit private input {name} is not configured")
    return json.loads(Path(value).read_text(encoding="utf-8"))


def _self_hash(value: dict[str, object]) -> str:
    observed = value.get("artifact_hash")
    payload = {key: item for key, item in value.items() if key != "artifact_hash"}
    if observed != stable_hash_v1(payload):
        raise AssertionError("artifact self-hash differs")
    assert isinstance(observed, str)
    return observed


def _authorized_specs(equivalence: dict[str, object]) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    direct_fields = {
        "source_threshold_reference": "source_step_threshold",
        "source_stability_reference": "source_stability_tolerance",
        "target_scale_reference": "target_noise_scale",
    }
    for item in equivalence["relation_records"]:  # type: ignore[index]
        relation_hash = item["relation_binding_hash"]
        signature = item["executable_signature"]
        pairs = [(signature[field], role) for field, role in direct_fields.items()]
        pairs.extend((reference, role) for role, reference in signature["window_constant_references"].items())
        for reference, role in pairs:
            if reference in result:
                raise AssertionError("authorized reference is duplicated")
            result[reference] = (role, relation_hash)
    return result


def _independent_errors(
    e1: dict[str, object], registry: dict[str, object], equivalence: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    try:
        if _self_hash(e1) != EXPECTED_E1:
            errors.append("wrong_e1_hash")
        if _self_hash(registry) != EXPECTED_REGISTRY:
            errors.append("wrong_registry_hash")
        if _self_hash(equivalence) != "3efdce159bc5ac39825d4e4654428237e47205307f83aae7a133db6c5789f60f":
            errors.append("wrong_equivalence_hash")
    except AssertionError as exc:
        errors.append(str(exc))
    specs = _authorized_specs(equivalence)
    if len(specs) != 420:
        errors.append("authorized_reference_count")

    e1_index: dict[str, list[tuple[dict[str, object], dict[str, object]]]] = {}
    for parent in e1.get("records", []):  # type: ignore[union-attr]
        try:
            _self_hash(parent)
        except AssertionError:
            errors.append("e1_parent_self_hash")
        for binding in parent["numeric_bindings"]:
            preimage = {key: value for key, value in binding.items() if key != "numeric_reference"}
            if stable_hash_v1(preimage) != binding["numeric_reference"]:
                errors.append("e1_reference_preimage")
            e1_index.setdefault(binding["numeric_reference"], []).append((parent, binding))

    registry_index: dict[str, list[dict[str, object]]] = {}
    for record in registry.get("records", []):  # type: ignore[union-attr]
        payload = {key: value for key, value in record.items() if key != "record_hash"}
        if stable_hash_v1(payload) != record.get("record_hash"):
            errors.append("registry_record_self_hash")
        registry_index.setdefault(record["reference"], []).append(record)

    if len(registry.get("records", [])) != 420 or len(registry_index) != 420:  # type: ignore[arg-type]
        errors.append("registry_record_count_or_duplicate")
    if registry.get("e1_private_ledger_hash") != EXPECTED_E1:
        errors.append("registry_e1_authority")
    if registry.get("e1_cohort_hash") != EXPECTED_COHORT:
        errors.append("registry_cohort_authority")
    if registry.get("e1_materialization_result_hash") != EXPECTED_MATERIALIZATION:
        errors.append("registry_materialization_authority")

    for reference, (expected_role, expected_relation) in specs.items():
        e1_matches = e1_index.get(reference, [])
        registry_matches = registry_index.get(reference, [])
        if len(e1_matches) != 1:
            errors.append("missing_or_ambiguous_e1")
            continue
        if len(registry_matches) != 1:
            errors.append("missing_or_ambiguous_registry")
            continue
        parent, binding = e1_matches[0]
        record = registry_matches[0]
        value = binding["numeric_value"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            errors.append("nonfinite_or_non_numeric")
        if binding["numeric_role"] != expected_role or record["numeric_role"] != expected_role:
            errors.append("role_mismatch")
        if parent["relation_binding_hash"] != expected_relation or record["relation_binding_hash"] != expected_relation:
            errors.append("relation_mismatch")
        if record["numeric_value"] != value:
            errors.append("value_mismatch")
        preimage = {key: value for key, value in binding.items() if key != "numeric_reference"}
        if record["authoritative_e1_binding_preimage"] != preimage:
            errors.append("binding_preimage_mismatch")
        if record["authoritative_e1_binding_hash"] != stable_hash_v1(binding):
            errors.append("binding_hash_mismatch")
        if record["authoritative_e1_record_hash"] != parent["artifact_hash"]:
            errors.append("parent_record_mismatch")
        provenance_text = json.dumps(
            {
                "origin": binding["value_origin"],
                "authority": binding["evidence_authority"],
                "llm_generated": binding["llm_generated"],
                "runtime_authority": binding["runtime_authority"],
            },
            sort_keys=True,
        ).lower()
        if (
            binding["evidence_authority"] != "approved_construction_evidence"
            or binding["llm_generated"] is not False
            or binding["runtime_authority"] is not False
            or "direct_number" in provenance_text
            or "test_provenance" in provenance_text
            or "label_provenance" in provenance_text
        ):
            errors.append("provenance_violation")
    return errors


class IndependentPrivateAuthorityReauditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.e1 = _load_private("TASK039E3_E1_PRIVATE_LEDGER")
        cls.registry = _load_private("TASK039E3_UTILITY_NUMERIC_REGISTRY_V2")
        cls.equivalence = json.loads(EQUIVALENCE.read_text(encoding="utf-8"))

    def test_all_420_registry_records_match_exact_e1_authority(self) -> None:
        self.assertEqual(_independent_errors(self.e1, self.registry, self.equivalence), [])

    def test_private_authority_counts_and_public_safe_flags(self) -> None:
        self.assertEqual((self.e1["record_count"], self.e1["numeric_binding_count"]), (42, 462))
        self.assertEqual(
            (self.registry["references_requested"], self.registry["unique_resolutions"], self.registry["record_count"]),
            (420, 420, 420),
        )
        self.assertEqual(
            (self.registry["missing"], self.registry["ambiguous"], self.registry["nonfinite"]),
            (0, 0, 0),
        )
        self.assertEqual(
            (self.registry["test_provenance"], self.registry["label_provenance"], self.registry["direct_number_provenance"]),
            (0, 0, 0),
        )

    def test_registry_mutations_are_independently_detected(self) -> None:
        for kind in ("value", "role", "reference", "duplicate", "missing", "wrong_e1"):
            changed = copy.deepcopy(self.registry)
            if kind == "value":
                changed["records"][0]["numeric_value"] += 1
                changed["records"][0]["record_hash"] = stable_hash_v1(
                    {k: v for k, v in changed["records"][0].items() if k != "record_hash"}
                )
            elif kind == "role":
                changed["records"][0]["numeric_role"] = "target_noise_scale"
                changed["records"][0]["record_hash"] = stable_hash_v1(
                    {k: v for k, v in changed["records"][0].items() if k != "record_hash"}
                )
            elif kind == "reference":
                changed["records"][0]["reference"] = "0" * 64
                changed["records"][0]["record_hash"] = stable_hash_v1(
                    {k: v for k, v in changed["records"][0].items() if k != "record_hash"}
                )
            elif kind == "duplicate":
                changed["records"].append(copy.deepcopy(changed["records"][0]))
            elif kind == "missing":
                changed["records"].pop()
            else:
                changed["e1_private_ledger_hash"] = "0" * 64
            changed["artifact_hash"] = stable_hash_v1(
                {key: value for key, value in changed.items() if key != "artifact_hash"}
            )
            self.assertTrue(_independent_errors(self.e1, changed, self.equivalence), kind)


if __name__ == "__main__":
    unittest.main()
