from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_execution_v1 import (
    HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS,
    HISTORICAL_PARTIAL_R2R_SCIENTIFIC_LOGICAL_CALLS,
    HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL,
    HISTORICAL_ZERO_CONTACT_R2R_SCIENTIFIC_LOGICAL_CALLS,
    build_lifetime_accounting_v1,
)
from paperworks.v6.task039e3_r2r_failure_finalizer_v1 import (
    write_terminal_failure_receipt_r2r_v1,
)
from paperworks.v6.task039e3_r2r_live_execution_v1 import _typed_accounting
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    R2RObservedIntegrityStateV1,
    R2RPostContactIntegrityGuardV1,
    R2RSourceBlobIdentityV1,
    R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
    TASK039E3R2RPrecontactError,
    capture_r2r_integrity_snapshot_v1,
)
from paperworks.v6.task039e3_r2r_result_finalizer_v1 import (
    TASK039E3R2RResultFinalizationError,
    _validate_completed_r2r_science,
)
from tests.test_task039e3_r2r_finalization_v1 import _accounting, _direct, _outcomes


ROOT = Path(__file__).resolve().parents[1]
BEHAVIOR_HASH = "0e18526c8dbcaec26d67385b89c60826dc4388cac08727cd61a2c60b1b812ae2"


def _self_hashed(path: str) -> dict[str, object]:
    document = json.loads((ROOT / path).read_text(encoding="utf-8"))
    supplied = document.pop("artifact_hash")
    calculated = hashlib.sha256(
        json.dumps(
            document,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    if supplied != calculated:
        raise AssertionError(f"tracked evidence self-hash differs: {path}")
    return {"artifact_hash": supplied, **document}


def _integrity_state(accounting_hash: str) -> R2RObservedIntegrityStateV1:
    return R2RObservedIntegrityStateV1(
        execution_commit="5dca2d0431d60ef2f2bdfc907ebfe3fe18521f16",
        source_manifest_hash="9037fda0bc7694fd643058a9779fb919c75664824f2f11c49dde9f4be1b209b8",
        source_blobs=(R2RSourceBlobIdentityV1("src/synthetic.py", "1" * 40, "2" * 64),),
        authorization_hash="3" * 64,
        recovery_main_provider_schema_v2_hash="bcbc9debc32ec9e4b02d5781c7f8b512023752ccb90f60154648bb5d9de67aa1",
        main_prompt_hash="a251e4b9da31c33e72d14dd81da6b2b1d0d1437fdf37ca311330eccce226f1ba",
        t2_followup_prompt_hash="a633067a7c9927be158f68ce714236f4c18c09433d49c903dac941a9774eeca5",
        direct_number_prompt_hash="fb01d8990ee3a7affe540dfdf3556b46d7bd744cd1e3a04d6fd9d79772dd2769",
        direct_number_schema_hash="b1b91bf27fd191da57984be625a2547e4e5ee96a0aca52535df071af92bfd6ca",
        exact_model="gpt-5.4-2026-03-05",
        endpoint="https://api.openai.com/v1/chat/completions",
        sampling_configuration_hash="4" * 64,
        timeout_seconds=30.0,
        retry_policy_hash="5" * 64,
        relation_schedule_hash="6db63485387924b28e9ce498aae46412a127ba69055a28e72880e1afffa4c4ca",
        scientific_concurrency=1,
        scientific_call_budget_hash="6" * 64,
        scientific_accounting_behavior_hash=accounting_hash,
        recovery_execution_configuration_hash="7" * 64,
    )


class DirectRenderingAccountingIndependentAudit(unittest.TestCase):
    def test_historical_components_derive_from_frozen_public_evidence(self) -> None:
        original = _self_hashed(
            "docs/task_reports/TASK-039E3_R2_FAILURE_FORENSIC_PARTIAL_SCIENCE.json"
        )
        zero_contact = _self_hashed(
            "docs/task_reports/TASK-039E3_R2R_FAILURE_FORENSIC_EXECUTION.json"
        )
        partial = _self_hashed(
            "docs/task_reports/TASK-039E3_R2R_DIRECT_FAILURE_EXECUTION.json"
        )
        self.assertEqual(original["scientific_logical_calls"], 1)
        self.assertEqual(zero_contact["scientific_logical_calls"], 0)
        self.assertEqual(partial["scientific_call_counts"]["fresh_r2r_total"], 5)
        self.assertEqual(
            (HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS,
             HISTORICAL_ZERO_CONTACT_R2R_SCIENTIFIC_LOGICAL_CALLS,
             HISTORICAL_PARTIAL_R2R_SCIENTIFIC_LOGICAL_CALLS,
             HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL),
            (1, 0, 5, 6),
        )
        self.assertTrue(partial["authorization_consumed"])
        self.assertFalse(partial["authorization_reusable"])
        self.assertEqual(partial["scientific_result_classification"], "ABORTED_NON_EVALUABLE_PARTIAL_R2R_EXECUTION")

    def test_pure_and_live_accounting_keep_historical_calls_separate(self) -> None:
        for fresh, expected in ((252, 258), (336, 342)):
            with self.subTest(fresh=fresh):
                lifetime = build_lifetime_accounting_v1(fresh)
                self.assertEqual(lifetime.historical_scientific_logical_calls_total, 6)
                self.assertEqual(lifetime.recovery_cohort_scientific_logical_calls, fresh)
                self.assertEqual(lifetime.lifetime_scientific_logical_call_attempts, expected)
                result = SimpleNamespace(
                    t1_logical_calls=42,
                    t1b_logical_calls=126,
                    t2_logical_calls=fresh - 210,
                    direct_number_logical_calls=42,
                    scientific_logical_calls=fresh,
                )
                transport = SimpleNamespace(attempt_custody=(object(),) * fresh)
                accounting = _typed_accounting(result, transport)
                self.assertEqual(accounting["historical_scientific_logical_calls_total"], 6)
                self.assertEqual(accounting["r2r_scientific_logical_calls"], fresh)
                self.assertEqual(accounting["lifetime_scientific_logical_call_attempts"], expected)
                self.assertEqual(accounting["historical_partial_records_reused"], 0)

    def test_success_validator_accepts_new_namespace_and_rejects_old_lifetime(self) -> None:
        calls, fresh, accounting = _validate_completed_r2r_science(
            _outcomes(), _direct(), _accounting()
        )
        self.assertEqual((calls["T1"], calls["T1-B"], calls["T2"], calls["T1-DIRECT-NUMBER"]), (42, 126, 42, 42))
        self.assertEqual(fresh, 252)
        self.assertEqual(accounting["historical_scientific_logical_calls_total"], 6)
        self.assertEqual(accounting["lifetime_scientific_logical_call_attempts"], 258)
        stale = _accounting()
        stale["lifetime_scientific_logical_call_attempts"] = 253
        with self.assertRaises(TASK039E3R2RResultFinalizationError):
            _validate_completed_r2r_science(_outcomes(), _direct(), stale)

    def test_failure_receipt_is_six_plus_current_fresh_without_double_counting(self) -> None:
        base = {
            "execution_commit": "1" * 40,
            "source_manifest_hash": "2" * 64,
            "authorization_hash": "3" * 64,
            "configuration_fingerprint": "4" * 64,
            "capability_reuse_status": "PASS_REUSED",
            "capability_provider_ledger_head_hash": "5" * 64,
            "scientific_provider_ledger_head_hash": "6" * 64,
            "last_attempted_scientific_slot": "T2:relation-00:1",
            "r2r_scientific_transport_attempts": 0,
            "proposal_committed_count": 0,
            "outcome_committed_count": 0,
            "direct_number_committed_count": 0,
            "postcontact_integrity_status": "verified_unchanged",
        }
        for current in (0, 5, 17):
            context = {**base, "completed_r2r_scientific_logical_calls": current}
            with patch(
                "paperworks.v6.task039e3_r2r_failure_finalizer_v1."
                "write_public_artifact_atomic_v1",
                side_effect=lambda _destination, document: document,
            ):
                receipt = write_terminal_failure_receipt_r2r_v1(
                    destination=Path("synthetic-never-written.json"),
                    failure_stage="scientific_execution",
                    failure=RuntimeError("synthetic"),
                    context=context,
                )
            self.assertEqual(receipt["historical_scientific_logical_calls_total"], 6)
            self.assertEqual(receipt["completed_r2r_scientific_logical_calls"], current)
            self.assertEqual(receipt["lifetime_scientific_logical_call_attempts"], 6 + current)
            self.assertFalse(receipt["historical_partial_results_reused"])

    def test_behavior_hash_reconstructs_and_is_integrity_bound(self) -> None:
        expected = stable_hash_v1(
            {
                "historical_aborted_r2_scientific_logical_calls": 1,
                "historical_original_r2_scientific_logical_calls": 1,
                "historical_zero_contact_r2r_scientific_logical_calls": 0,
                "historical_partial_r2r_scientific_logical_calls": 5,
                "historical_scientific_logical_calls_total": 6,
                "historical_partial_records_reused": 0,
                "relations": 42,
                "t1_logical_calls": 42,
                "t1b_logical_calls": 126,
                "t2_logical_calls_minimum": 42,
                "t2_logical_calls_maximum": 126,
                "direct_number_logical_calls": 42,
                "r2r_scientific_logical_calls_minimum": 252,
                "r2r_scientific_logical_calls_maximum": 336,
                "lifetime_accounting": "6_plus_actual_r2r_scientific_logical_calls",
                "scientific_concurrency": 1,
                "scientific_generation_retries": 0,
            }
        )
        self.assertEqual(expected, BEHAVIOR_HASH)
        self.assertEqual(R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1, expected)
        state = _integrity_state(expected)
        snapshot = capture_r2r_integrity_snapshot_v1(state)
        guard = R2RPostContactIntegrityGuardV1(snapshot, lambda: state)
        guard.assert_unchanged_before_provider_attempt()
        stale_state = replace(state, scientific_accounting_behavior_hash="e" * 64)
        stale_guard = R2RPostContactIntegrityGuardV1(snapshot, lambda: stale_state)
        with self.assertRaises(TASK039E3R2RPrecontactError):
            stale_guard.assert_unchanged_before_provider_attempt()
        self.assertTrue(stale_guard.blocked)

    def test_active_source_manifest_contains_no_stale_lifetime_assumption(self) -> None:
        manifest = _self_hashed(
            "docs/task_reports/"
            "TASK-039E3_R2R_DIRECT_NUMBER_RENDERING_REMEDIATION_SOURCE_FREEZE.json"
        )
        active = "\n".join(
            (ROOT / item["repository_path"]).read_text(encoding="utf-8")
            for item in manifest["source_records"]
            if item["repository_path"].endswith(".py")
        )
        for stale in (
            "1_plus_actual_r2r_scientific_logical_calls",
            "lifetime_scientific_logical_call_attempts\": 1 +",
            "lifetime_scientific_logical_call_attempts = 1 +",
        ):
            self.assertNotIn(stale, active)


if __name__ == "__main__":
    unittest.main()
