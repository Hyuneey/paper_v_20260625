from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.gdn_sidecar_v1 import VIEWS, SEEDS, project_gdn_evidence_v1, seal, annotate_explanation_v1
from paperworks.validation_v2.private_vault_v1 import preserve_private_artifact_v1, public_artifact_record_v1


class SidecarTests(unittest.TestCase):
    def fixture(self):
        relation = dict(relation_id="ref-r", source="S", target="T", source_direction="step_up", target_direction="increase", selected_horizon_seconds=5)
        descriptor = {**relation, "relation_id":"rule-r", "descriptor_hash":"a"*64}
        evidence = []
        for view in VIEWS:
            for seed in SEEDS:
                row = dict(view=view, seed=seed, event_edge_mask=[dict(relation_id="ref-r", value=1.0)], checkpoint_unchanged=True, attention_invariance_passed=True)
                row["evidence_hash"] = seal(row)["self_hash"]
                evidence.append(row)
        return relation, descriptor, evidence

    def project(self, relation, descriptor, evidence):
        return project_gdn_evidence_v1(reference={"confirmed_directional_relations":[relation]}, portfolio={"descriptors":[descriptor]}, evidence=evidence, expected_stable_count=1, bindings={"functional_receipt_hash":"b"*64,"portfolio_hash":"c"*64})

    def test_exact_and_pair_only_horizon_projection(self):
        relation, descriptor, evidence = self.fixture()
        mapping, sidecar = self.project(relation, descriptor, evidence)
        self.assertEqual(mapping["pairs"][0]["classification"], "PAIR_AND_HORIZON_CORROBORATION")
        descriptor["selected_horizon_seconds"] = 60
        mapping, sidecar = self.project(relation, descriptor, evidence)
        self.assertEqual(sidecar["rows"][0]["learned_graph_status"], "CORROBORATED_PAIR_ONLY")
        self.assertEqual(sidecar["rows"][0]["gdn_supported_horizons"], [5])

    def test_corrupt_or_incomplete_evidence_fails(self):
        relation, descriptor, evidence = self.fixture()
        with self.assertRaises(ValueError):
            self.project(relation, descriptor, evidence[:-1])
        evidence[0]["event_edge_mask"][0]["value"] = -3.0
        with self.assertRaises(ValueError):
            self.project(relation, descriptor, evidence)

    def test_annotation_cannot_change_runtime_outcome(self):
        relation, descriptor, evidence = self.fixture()
        _, sidecar = self.project(relation, descriptor, evidence)
        for outcome in ("PASS", "FAIL", "ABSTAIN"):
            base = {"final_outcome":outcome, "alarm_emitted":outcome == "FAIL", "portfolio_authority_hash":"c"*64,
                    **{k:descriptor[k] for k in ("descriptor_hash","source","target","source_direction","target_direction","selected_horizon_seconds")}}
            base["artifact_hash"] = seal(base)["self_hash"]
            before = deepcopy(base)
            annotated = annotate_explanation_v1(base, row=sidecar["rows"][0], descriptor=descriptor, sidecar=sidecar, expected_sidecar_hash=sidecar["self_hash"])
            self.assertEqual(base, before)
            self.assertEqual(annotated["base_explanation"], before)
            self.assertFalse(annotated["affects_outcome"])
        row = {**sidecar["rows"][0], "learned_graph_status":"NOT_EVALUABLE"}
        with self.assertRaises(ValueError):
            annotate_explanation_v1(base, row=row, descriptor=descriptor, sidecar=sidecar, expected_sidecar_hash=sidecar["self_hash"])
        with self.assertRaises(ValueError):
            annotate_explanation_v1(base, row=sidecar["rows"][0], descriptor=descriptor, sidecar=sidecar, expected_sidecar_hash="x")
        altered = {**base, "source":"OTHER"}
        with self.assertRaises(ValueError):
            annotate_explanation_v1(altered, row=sidecar["rows"][0], descriptor=descriptor, sidecar=sidecar, expected_sidecar_hash=sidecar["self_hash"])
        altered["artifact_hash"] = seal({k:v for k,v in altered.items() if k!="artifact_hash"})["self_hash"]
        with self.assertRaises(ValueError):
            annotate_explanation_v1(altered, row=sidecar["rows"][0], descriptor=descriptor, sidecar=sidecar, expected_sidecar_hash=sidecar["self_hash"])


class VaultTests(unittest.TestCase):
    def test_copy_restore_replay_no_overwrite_and_redaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.write_bytes(b"synthetic")
            expected = sha256(b"synthetic").hexdigest()
            record = preserve_private_artifact_v1(source=source, vault=root/"vault", artifact_id="TEST", expected_hash=expected, restore_target=root/"restored")
            self.assertEqual((root/"restored").read_bytes(), source.read_bytes())
            self.assertEqual(record["backup_status"], "SINGLE_COPY_LOCAL_ONLY")
            self.assertFalse(any(k.startswith("private_") for k in public_artifact_record_v1(record)))
            with self.assertRaises(ValueError):
                preserve_private_artifact_v1(source=source, vault=root/"vault", artifact_id="TEST", expected_hash="a"*64)
            (root/"restored").write_bytes(b"mutation")
            with self.assertRaises(ValueError):
                preserve_private_artifact_v1(source=source, vault=root/"vault", artifact_id="TEST", expected_hash=expected, restore_target=root/"restored")


if __name__ == "__main__":
    unittest.main()
