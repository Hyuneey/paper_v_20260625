from __future__ import annotations

"""Independent cross-module boundary oracle for TASK-039E3-R1B.

This suite deliberately avoids exercising the internal unit details owned by
the capability, serialization, and authorization lanes.  It checks the seams
between those components and the still-frozen E3 scientific orchestration.
All authority, credential, provider, and private-root inputs are synthetic and
dependency injected.

Requirements matrix:

* authority / credential ordering: tests 1 and 2;
* timeout, retry, and logical-probe accounting: test 3;
* corrected capability observations and strict request: test 4;
* source preservation and schedule / T1-B / T2 fairness: tests 5 and 6;
* root separation: test 7;
* capability custody before E1 and no science on BLOCK: tests 8 and 9;
* recovery-source public leakage boundary: test 10.
"""

from pathlib import Path
import json
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1, thaw_json
from paperworks.v6.task039e3_execution_prep_v1 import (
    MAXIMUM_SCIENTIFIC_SLOTS,
    MAXIMUM_TRANSPORT_RETRIES,
    TRANSPORT_RETRY_DELAYS_SECONDS,
    MockProviderResponseV1,
    build_mock_336_slot_schedule_v1,
)
from paperworks.v6.task039e3_live_transport_v1 import (
    CALL_TIMEOUT_SECONDS,
    RETRY_DELAYS_SECONDS,
)
from paperworks.v6.task039e3_recovery_authorization_v1 import (
    ARTIFACT_TYPE,
    AUTHORIZATION_STATUS,
    EXACT_MODEL,
    HISTORICAL_CAPABILITY_PROBE_COUNT,
    HISTORICAL_CAPABILITY_RECEIPT_HASH,
    HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
    MAXIMUM_ADDITIONAL_RECOVERY_PROBES,
    MAXIMUM_CUMULATIVE_CAPABILITY_PROBES,
    R0_BUNDLE_HASH,
    R0_COMMIT,
    R1A_COMMIT,
    R1A_RECEIPT_HASH,
    R1A_TIMEOUT_AUTHORITY_HASH,
    SCHEMA_VERSION,
    TASK_ID,
    URLOPEN_TIMEOUT_SECONDS,
    GitExecutionStateV1,
    PriorAuthorityStateV1,
    RecoveryProbeAccountingV1,
    TASK039E3RecoveryAuthorizationError,
    run_ordered_precontact_guards_v1,
    validate_recovery_private_roots_v1,
)
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_FIXTURE_ID,
    RECOVERY_CAPABILITY_TOKEN,
    build_recovery_capability_request_v1,
    evaluate_recovery_capability_response_v1,
)
from paperworks.v6.task039e3_recovery_execution_v1 import (
    run_recovery_capability_phase_v1,
)


_SYNTHETIC_COMMIT = "a" * 40
_SYNTHETIC_MANIFEST_HASH = stable_hash_v1({"synthetic": "source-manifest"})
_HISTORICAL_COMMIT_A = "48b79643088ce1a0179191d7ddae4c97dc8dece9"


def _r2_authorization() -> dict[str, object]:
    content: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "task_id": TASK_ID,
        "authorization_status": AUTHORIZATION_STATUS,
        "r0_commit": R0_COMMIT,
        "r0_bundle_hash": R0_BUNDLE_HASH,
        "r1a_commit": R1A_COMMIT,
        "r1a_timeout_authority_hash": R1A_TIMEOUT_AUTHORITY_HASH,
        "r1a_receipt_hash": R1A_RECEIPT_HASH,
        "historical_capability_receipt_hash": (
            HISTORICAL_CAPABILITY_RECEIPT_HASH
        ),
        "historical_provider_ledger_head_hash": (
            HISTORICAL_PROVIDER_LEDGER_HEAD_HASH
        ),
        "r1b_commit_a": _SYNTHETIC_COMMIT,
        "r1b_source_manifest_hash": _SYNTHETIC_MANIFEST_HASH,
        "exact_model": EXACT_MODEL,
        "urlopen_timeout_seconds": URLOPEN_TIMEOUT_SECONDS,
        "historical_capability_probe_count": HISTORICAL_CAPABILITY_PROBE_COUNT,
        "maximum_additional_recovery_probes": (
            MAXIMUM_ADDITIONAL_RECOVERY_PROBES
        ),
        "maximum_cumulative_capability_probes": (
            MAXIMUM_CUMULATIVE_CAPABILITY_PROBES
        ),
        "provider_contact_authorized": True,
        "recovery_probe_authorized": True,
        "scientific_execution_after_capability_pass_authorized": True,
        "rule_v2_authorized": False,
        "runtime_authority": False,
        "utility_evaluation_authorized": False,
        "winner_selected": False,
    }
    return {**content, "self_hash": stable_hash_v1(content)}


def _provider_response(*, content: object, model: str = EXACT_MODEL) -> MockProviderResponseV1:
    return MockProviderResponseV1(
        response_present=True,
        outcome="synthetic_recovery_capability",
        status_code=200,
        model=model,
        content=content if isinstance(content, str) else json.dumps(content),
        finish_reason="stop",
        response_id="SYNTHETIC_RECOVERY_RESPONSE",
        token_usage={"prompt_tokens": 1, "completion_tokens": 1},
    )


def _passing_gate():
    return evaluate_recovery_capability_response_v1(
        _provider_response(
            content={
                "fixture_id": RECOVERY_CAPABILITY_FIXTURE_ID,
                "capability_token": RECOVERY_CAPABILITY_TOKEN,
            }
        )
    )


def _blocking_gate():
    return evaluate_recovery_capability_response_v1(
        _provider_response(
            content={
                "fixture_id": RECOVERY_CAPABILITY_FIXTURE_ID,
                "capability_token": "SYNTHETIC_WRONG_TOKEN",
            }
        )
    )


class RecoveryBoundaryTests(unittest.TestCase):
    def test_precontact_guard_order_reaches_injected_credential_only_last(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "synthetic-repository"
            e1 = root / "synthetic-e1"
            historical = root / "synthetic-historical-e3"
            recovery = root / "synthetic-recovery-e3"
            for directory in (repository, e1, historical, recovery):
                directory.mkdir()

            observed: list[str] = []
            bootstrap = run_ordered_precontact_guards_v1(
                authorization_document=_r2_authorization(),
                prior_authority_state_loader=lambda: PriorAuthorityStateV1(
                    r0_commit=R0_COMMIT,
                    r0_bundle_hash=R0_BUNDLE_HASH,
                    r1a_commit=R1A_COMMIT,
                    r1a_timeout_authority_hash=R1A_TIMEOUT_AUTHORITY_HASH,
                    r1a_receipt_hash=R1A_RECEIPT_HASH,
                ),
                git_state_loader=lambda: GitExecutionStateV1(
                    head_commit=_SYNTHETIC_COMMIT,
                    worktree_clean=True,
                    index_clean=True,
                    source_manifest_hash=_SYNTHETIC_MANIFEST_HASH,
                    source_blobs_match_manifest=True,
                ),
                repository_root=repository,
                e1_private_value=str(e1),
                historical_e3_private_value=str(historical),
                recovery_e3_private_value=str(recovery),
                historical_capability_receipt_hash=(
                    HISTORICAL_CAPABILITY_RECEIPT_HASH
                ),
                historical_provider_ledger_head_hash=(
                    HISTORICAL_PROVIDER_LEDGER_HEAD_HASH
                ),
                scientific_preflight_loader=lambda: {"synthetic": True},
                credential_loader=lambda: observed.append("credential") or "synthetic",
                event_sink=observed.append,
            )
            self.assertEqual(observed[-1], "credential_loaded")
            self.assertEqual(observed.count("credential"), 1)
            self.assertEqual(
                bootstrap.completed_guard_order[-2:],
                ("scientific_public_preflight_validated", "credential_loaded"),
            )

    def test_authorization_failure_never_reaches_credential_or_git_loader(self) -> None:
        document = _r2_authorization()
        document["r0_bundle_hash"] = "0" * 64
        reached: list[str] = []
        with self.assertRaises(TASK039E3RecoveryAuthorizationError):
            run_ordered_precontact_guards_v1(
                authorization_document=document,
                prior_authority_state_loader=lambda: reached.append("authority") or None,  # type: ignore[return-value]
                git_state_loader=lambda: reached.append("git") or None,  # type: ignore[return-value]
                repository_root=Path("SYNTHETIC_UNUSED"),
                e1_private_value="SYNTHETIC_UNUSED",
                historical_e3_private_value="SYNTHETIC_UNUSED",
                recovery_e3_private_value="SYNTHETIC_UNUSED",
                historical_capability_receipt_hash="0" * 64,
                historical_provider_ledger_head_hash="0" * 64,
                scientific_preflight_loader=lambda: reached.append("preflight"),
                credential_loader=lambda: reached.append("credential"),
            )
        self.assertEqual(reached, [])

    def test_timeout_retry_and_probe_accounting_are_separate(self) -> None:
        self.assertEqual(URLOPEN_TIMEOUT_SECONDS, 30.0)
        self.assertEqual(float(CALL_TIMEOUT_SECONDS), URLOPEN_TIMEOUT_SECONDS)
        self.assertEqual(MAXIMUM_TRANSPORT_RETRIES, 2)
        self.assertEqual(TRANSPORT_RETRY_DELAYS_SECONDS, (2, 4))
        self.assertEqual(RETRY_DELAYS_SECONDS, (2, 4))

        probes = RecoveryProbeAccountingV1().allocate_recovery_probe()
        self.assertEqual(probes.current_recovery_probe_count, 1)
        self.assertEqual(probes.cumulative_probe_count, 2)
        self.assertIs(probes.with_transport_attempts(3), probes)
        self.assertEqual(probes.cumulative_probe_count, 2)
        with self.assertRaisesRegex(Exception, "third capability probe"):
            probes.allocate_recovery_probe()

    def test_corrected_request_is_strict_stateless_and_self_report_free(self) -> None:
        request = build_recovery_capability_request_v1()
        body = thaw_json(request.request_body)
        self.assertEqual(body["model"], EXACT_MODEL)
        self.assertEqual(body["reasoning_effort"], "none")
        self.assertEqual(body["temperature"], 0.7)
        self.assertEqual(body["top_p"], 1.0)
        self.assertEqual(body["max_completion_tokens"], 1024)
        self.assertEqual(body["n"], 1)
        self.assertEqual(body["presence_penalty"], 0)
        self.assertEqual(body["frequency_penalty"], 0)
        self.assertFalse(body["stream"])
        self.assertFalse(body["store"])
        # E2's frozen Chat Completions builder represents "no tools" by
        # omitting the optional field rather than adding a new API parameter.
        self.assertEqual(body.get("tools", []), [])
        self.assertNotIn("seed", body)
        self.assertEqual(body["response_format"]["type"], "json_schema")
        self.assertTrue(body["response_format"]["json_schema"]["strict"])
        serialized = json.dumps(body, sort_keys=True)
        self.assertNotIn("model_snapshot", serialized)
        self.assertNotIn("structured_output_supported", serialized)

    def test_historical_scientific_sources_remain_byte_identical(self) -> None:
        # The source-freeze oracle intentionally uses the current repository's
        # Git object store rather than line-ending-sensitive worktree commands.
        import subprocess

        repository = Path(__file__).resolve().parents[1]
        frozen_paths = (
            "src/paperworks/v6/task039e3_execution_prep_v1.py",
            "src/paperworks/v6/task039e3_live_transport_v1.py",
            "src/paperworks/v6/task039e3_scientific_execution_v1.py",
        )
        for relative in frozen_paths:
            expected = subprocess.run(
                ["git", "show", f"{_HISTORICAL_COMMIT_A}:{relative}"],
                cwd=repository,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout
            observed = subprocess.run(
                ["git", "show", f"HEAD:{relative}"],
                cwd=repository,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout
            self.assertEqual(observed, expected, relative)

    def test_schedule_and_fairness_source_remain_frozen(self) -> None:
        relation_hashes = tuple(
            stable_hash_v1({"synthetic_relation": index}) for index in range(42)
        )
        schedule = build_mock_336_slot_schedule_v1(relation_hashes)
        counts = {
            arm: sum(slot.arm == arm for slot in schedule)
            for arm in ("T1", "T1-B", "T2", "T1-DIRECT-NUMBER")
        }
        self.assertEqual(
            counts,
            {"T1": 42, "T1-B": 126, "T2": 126, "T1-DIRECT-NUMBER": 42},
        )
        self.assertEqual(len(schedule), MAXIMUM_SCIENTIFIC_SLOTS)
        for relation_index in range(42):
            relation_slots = [
                slot for slot in schedule if slot.relation_schedule_index == relation_index
            ]
            self.assertEqual(
                [slot.arm_local_call_number for slot in relation_slots if slot.arm == "T1-B"],
                [1, 2, 3],
            )
            self.assertEqual(
                [slot.arm_local_call_number for slot in relation_slots if slot.arm == "T2"],
                [1, 2, 3],
            )

    def test_root_boundary_requires_three_distinct_synthetic_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "repo"
            outside = root / "outside"
            repository.mkdir()
            outside.mkdir()
            with self.assertRaisesRegex(Exception, "distinct"):
                validate_recovery_private_roots_v1(
                    repository_root=repository,
                    e1_private_value=str(outside),
                    historical_e3_private_value=str(outside),
                    recovery_e3_private_value=str(outside),
                )

    def test_capability_block_freezes_custody_without_e1_access(self) -> None:
        events: list[str] = []
        result = run_recovery_capability_phase_v1(
            precontact_guard_runner=lambda: events.append("precontact") or "bootstrap",
            probe_executor=lambda bootstrap: events.append(f"probe:{bootstrap}") or _blocking_gate(),
            custody_writer=lambda gate: events.append(f"custody:{gate.gate_status}") or "custody-hash",
            e1_loader=lambda bootstrap: events.append(f"e1:{bootstrap}"),
        )
        self.assertEqual(result.gate_status, "BLOCK")
        self.assertEqual(events, ["precontact", "probe:bootstrap", "custody:BLOCK"])

    def test_capability_pass_opens_e1_only_after_durable_custody(self) -> None:
        events: list[str] = []
        result = run_recovery_capability_phase_v1(
            precontact_guard_runner=lambda: events.append("precontact") or "bootstrap",
            probe_executor=lambda bootstrap: events.append(f"probe:{bootstrap}") or _passing_gate(),
            custody_writer=lambda gate: events.append(f"custody:{gate.gate_status}") or "custody-hash",
            e1_loader=lambda bootstrap: events.append(f"e1:{bootstrap}") or "evidence",
        )
        self.assertEqual(result.gate_status, "PASS")
        self.assertEqual(
            events,
            ["precontact", "probe:bootstrap", "custody:PASS", "e1:bootstrap"],
        )

    def test_recovery_sources_contain_no_embedded_secret_or_real_payload(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        paths = sorted(
            (repository / "src/paperworks/v6").glob("task039e3_recovery_*_v1.py")
        )
        paths.extend(
            sorted((repository / "schemas/v6").glob("task039e3_recovery_*_v1_schema.json"))
        )
        self.assertTrue(paths)
        prohibited_literals = (
            "sk-proj-",
            "Bearer sk-",
            "raw_hai",
            "real_provider_response_content",
            "chain_of_thought",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for prohibited in prohibited_literals:
                self.assertNotIn(prohibited, text, f"{prohibited} in {path.name}")


if __name__ == "__main__":
    unittest.main()
