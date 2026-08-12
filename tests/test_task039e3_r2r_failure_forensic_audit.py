from __future__ import annotations

import ast
from hashlib import sha256
import inspect
import json
from pathlib import Path
import subprocess
import textwrap
from typing import Any, Mapping
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    MockProviderResponseV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    ProviderCallSlotV1,
    TASK039E3PreparationError,
    execute_mock_provider_slot_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
    run_t1_v1,
    run_t1b_v1,
    run_t2_v1,
    run_direct_number_v1,
)
from paperworks.v6.task039e3_r2r_live_transport_v1 import (
    R2RLiveOpenAIChatCompletionsTransportV1,
)
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    R2RIntegrityGuardedTransportV1,
)
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    build_r2r_main_request_v1,
)
from paperworks.v6.task039e3_recovery_execution_v3 import (
    IntegrityGuardedTransportV3,
    TransactionalScientificProviderLedgerV3,
)
from paperworks.v6.task039e3_recovery_live_transport_v3 import (
    RecoveryLiveOpenAIChatCompletionsTransportV3,
    RecoveryProviderResponseV3,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    verify_public_artifact_v1,
)
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    reconstruct_transactional_ledger_v3,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    _proposal_document,
    _verify_self_hash,
    project_real_evidence_v1,
    run_real_t0_v1,
    validate_public_preflight_v1,
)


EXECUTION_COMMIT = "eb62b449e06ea5f6c4a2d445223f6ca98de3690c"
FAILURE_RECEIPT_HASH = (
    "7d60b8c5690f4f441377c5bdeae01c78452f0ad0b4eda96d9dbd8b1eb0a3c9c7"
)
EXPECTED_EXCEPTION_MESSAGE = (
    "TASK-039E3-PREP accepts MockProviderTransportV1 only"
)
EXPECTED_EXCEPTION_MESSAGE_SHA256 = sha256(
    EXPECTED_EXCEPTION_MESSAGE.encode("utf-8")
).hexdigest()

CONTROL_FLOW_PATHS = (
    "scripts/run_task039e3_r2r_scientific_execution_v1.py",
    "src/paperworks/v6/task039e3_r2r_precontact_v1.py",
    "src/paperworks/v6/task039e3_r2r_live_execution_v1.py",
    "src/paperworks/v6/task039e3_r2r_execution_v1.py",
    "src/paperworks/v6/task039e3_recovery_science_v2.py",
    "src/paperworks/v6/task039e3_scientific_execution_v1.py",
    "src/paperworks/v6/task039e3_orchestration_v1.py",
    "src/paperworks/v6/task039e3_r2r_request_contract_v1.py",
    "src/paperworks/v6/task039e3_execution_prep_v1.py",
    "src/paperworks/v6/task039e3_recovery_live_transport_v3.py",
    "src/paperworks/v6/task039e3_r2r_live_transport_v1.py",
    "src/paperworks/v6/task039e3_recovery_execution_v3.py",
    "src/paperworks/v6/task039e3_recovery_transactional_custody_v3.py",
)


class _NeverSendRawTransport:
    def __init__(self) -> None:
        self.send_calls = 0

    def send(self, _request: Any) -> Any:
        self.send_calls += 1
        raise AssertionError("never-send transport became reachable")


class _NeverSendIntegrityGuard:
    def __init__(self) -> None:
        self.invocations = 0

    def invoke_guarded_provider_attempt(self, callback: Any) -> Any:
        self.invocations += 1
        return callback()


class _HistoricalR2RIntegrityGuardedTransportV1:
    """Exact pre-remediation interface shape used by the forensic oracle."""

    def __init__(self, transport: Any, integrity_guard: Any) -> None:
        self.transport = transport
        self.integrity_guard = integrity_guard

    def send(self, request: Any) -> Any:
        return self.integrity_guard.invoke_guarded_provider_attempt(
            lambda: self.transport.send(request)
        )


def _git_output(repository: Path, *arguments: str, text: bool = False) -> Any:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    ).stdout


def frozen_source_identities(repository: Path) -> tuple[dict[str, str], ...]:
    identities: list[dict[str, str]] = []
    for relative in CONTROL_FLOW_PATHS:
        blob = _git_output(
            repository, "rev-parse", f"{EXECUTION_COMMIT}:{relative}", text=True
        ).strip()
        content = _git_output(repository, "show", f"{EXECUTION_COMMIT}:{relative}")
        identities.append(
            {
                "repository_path": relative,
                "git_blob_sha": blob,
                "sha256": sha256(content).hexdigest(),
            }
        )
    return tuple(identities)


def verify_public_failure_receipt(path: Path) -> dict[str, Any]:
    document = verify_public_artifact_v1(json.loads(path.read_text(encoding="utf-8")))
    expected = {
        "artifact_hash": FAILURE_RECEIPT_HASH,
        "status": "failed_task039e3_r2r_scientific_execution",
        "execution_commit": EXECUTION_COMMIT,
        "source_manifest_hash": (
            "01c8e23f2eb15f321295bf0163dcbd81df67ed0179817acb725614a45bfede1d"
        ),
        "authorization_hash": (
            "674d314c42d672dfdd847e5552a310f938fb44b7a55c4bd49fa968d3aa746c91"
        ),
        "capability_reuse_status": "PASS_REUSED",
        "completed_r2r_scientific_logical_calls": 0,
        "r2r_scientific_transport_attempts": 0,
        "proposal_committed_count": 1,
        "outcome_committed_count": 1,
        "direct_number_committed_count": 0,
        "postcontact_integrity_status": "not_started",
        "scientific_provider_ledger_head_hash": None,
        "failure_classification": "TASK039E3PreparationError",
        "failure_stage": "r2r_scientific_execution_or_finalization",
        "last_attempted_scientific_slot": None,
    }
    for key, value in expected.items():
        if document.get(key) != value:
            raise AssertionError(f"public failure receipt differs: {key}")
    for key in (
        "rule_v2_authorized",
        "runtime_authority",
        "utility_evaluation_authorized",
        "winner_selected",
        "provider_recontact_authorized",
        "automatic_resume_authorized",
        "patch_and_continue_authorized",
        "historical_partial_results_reused",
    ):
        if document.get(key) is not False:
            raise AssertionError(f"failure receipt prohibition differs: {key}")
    return document


def _stream_private_relation_record(
    ledger_path: Path, target_relation_identity: str
) -> tuple[dict[str, Any], int, int]:
    """Decode records only until the requested relation is reached."""

    decoder = json.JSONDecoder()
    buffer = ""
    bytes_read = 0
    records_start: int | None = None
    position = 0
    decoded_count = 0
    with ledger_path.open("r", encoding="utf-8") as handle:
        while True:
            if records_start is None:
                marker = buffer.find('"records"')
                if marker >= 0:
                    bracket = buffer.find("[", marker)
                    if bracket >= 0:
                        records_start = bracket + 1
                        position = records_start
            if records_start is not None:
                while position < len(buffer) and buffer[position] in " \t\r\n,":
                    position += 1
                if position < len(buffer):
                    try:
                        item, end = decoder.raw_decode(buffer, position)
                    except json.JSONDecodeError:
                        pass
                    else:
                        if not isinstance(item, dict):
                            raise AssertionError("private E1 record is not an object")
                        decoded_count += 1
                        if item.get("relation_identity") == target_relation_identity:
                            return item, decoded_count, bytes_read
                        position = end
                        continue
            chunk = handle.read(4096)
            if not chunk:
                raise AssertionError("relation zero is absent from private E1 ledger")
            buffer += chunk
            bytes_read += len(chunk.encode("utf-8"))


def replay_relation_zero_never_send(
    *, execution_repository: Path, e1_private_ledger_path: Path
) -> dict[str, Any]:
    public = validate_public_preflight_v1(execution_repository)
    schedule = tuple(public["schedule"]["relation_identities"])
    target = schedule[0]
    private, decoded_count, bytes_read = _stream_private_relation_record(
        e1_private_ledger_path, target
    )
    _verify_self_hash(private)
    cohort = public["cohort"]
    primitives = {
        item["relation_identity"]: item
        for item in cohort["confirmed_relation_primitives"]
    }
    bundles = {
        item["relation_binding_hash"]: item
        for item in cohort["approved_numeric_evidence_bundles"]
    }
    manifests = {
        item["relation_identity"]: item for item in cohort["public_manifest_entries"]
    }
    evidence = project_real_evidence_v1(
        private_record=private,
        public_primitive=primitives[target],
        public_bundle=bundles[private["relation_binding_hash"]],
        public_manifest=manifests[target],
    )

    proposals = ConstructionProposalLedgerV1()
    outcomes = ConstructionOutcomeLedgerV1()
    t0_outcome = run_real_t0_v1(
        evidence=evidence, proposal_ledger=proposals, outcome_ledger=outcomes
    )
    if len(proposals.records) != 1 or len(outcomes.records) != 1:
        raise AssertionError("relation-zero deterministic T0 replay differs")

    request = build_r2r_main_request_v1(evidence.render_view())
    slot = ProviderCallSlotV1(
        0, evidence.relation.binding_hash, "T1", 1, True
    )
    raw = _NeverSendRawTransport()
    integrity = _NeverSendIntegrityGuard()
    guarded = R2RIntegrityGuardedTransportV1(raw, integrity)  # type: ignore[arg-type]
    try:
        execute_mock_provider_slot_v1(
            slot=slot,
            request=request,
            transport=guarded,
            ledger=ProviderCallLedgerV1(),
            parse_kind="proposal",
        )
    except TASK039E3PreparationError as exc:
        message = str(exc)
        exception_class = type(exc).__name__
    else:
        raise AssertionError("frozen first T1 slot unexpectedly became reachable")

    proposal = proposals.records[0]
    return {
        "relation_schedule_index": 0,
        "relation_identity_hash": sha256(target.encode("utf-8")).hexdigest(),
        "private_e1_records_decoded": decoded_count,
        "private_e1_bytes_read_upper_bound": bytes_read,
        "request_build_succeeded": True,
        "request_hash": request.request_hash,
        "slot_hash": slot.slot_hash,
        "exception_class": exception_class,
        "exception_message": message,
        "exception_message_sha256": sha256(message.encode("utf-8")).hexdigest(),
        "sentinel_send_calls": raw.send_calls,
        "integrity_wrapper_invocations": integrity.invocations,
        "t0_proposal_record_hash": proposal.record_hash,
        "t0_outcome_artifact_hash": t0_outcome.artifact_hash,
        "t0_outcome": t0_outcome.outcome,
    }


def reconstruct_failed_private_custody(
    *, recovery_private_root: Path, replay: Mapping[str, Any]
) -> dict[str, Any]:
    scientific = recovery_private_root / "scientific_r2r_v1"
    provider = reconstruct_transactional_ledger_v3(
        scientific / "provider", ledger_kind="scientific_provider"
    )
    http_error = reconstruct_transactional_ledger_v3(
        scientific / "http_error_attempts", ledger_kind="http_error_custody"
    )

    def jsonl(path: Path) -> tuple[dict[str, Any], ...]:
        with path.open("r", encoding="utf-8") as handle:
            return tuple(json.loads(line) for line in handle if line.strip())

    proposals = jsonl(scientific / "proposals_working.jsonl")
    outcomes = jsonl(scientific / "outcomes_working.jsonl")
    direct = jsonl(scientific / "direct_working.jsonl")
    if provider.authoritative_record_count != 0 or provider.head_record_hash is not None:
        raise AssertionError("scientific provider custody is not empty")
    if http_error.authoritative_record_count != 0 or http_error.head_record_hash is not None:
        raise AssertionError("HTTP-error custody is not empty")
    if provider.orphan_record_hashes or provider.pending_files:
        raise AssertionError("scientific provider custody contains ambiguous state")
    if http_error.orphan_record_hashes or http_error.pending_files:
        raise AssertionError("HTTP-error custody contains ambiguous state")
    if (len(proposals), len(outcomes), len(direct)) != (1, 1, 0):
        raise AssertionError("failed private partial counts differ")
    proposal = proposals[0]
    outcome = outcomes[0]
    if (
        proposal.get("arm") != "T0"
        or proposal.get("call_number") != 0
        or proposal.get("record_hash") != replay["t0_proposal_record_hash"]
    ):
        raise AssertionError("T0 proposal custody differs from deterministic replay")
    outcome_content = {key: value for key, value in outcome.items() if key != "artifact_hash"}
    if (
        outcome.get("arm") != "T0"
        or stable_hash_v1(outcome_content) != outcome.get("artifact_hash")
        or outcome.get("artifact_hash") != replay["t0_outcome_artifact_hash"]
    ):
        raise AssertionError("T0 outcome custody differs from deterministic replay")
    proposal_relation_hash = sha256(
        str(proposal["relation_identity"]).encode("utf-8")
    ).hexdigest()
    outcome_relation_hash = sha256(
        str(outcome["relation_identity"]).encode("utf-8")
    ).hexdigest()
    if not (
        proposal_relation_hash
        == outcome_relation_hash
        == replay["relation_identity_hash"]
    ):
        raise AssertionError("T0 private relation identity differs")
    return {
        "scientific_provider_record_count": provider.authoritative_record_count,
        "scientific_provider_ledger_hash": provider.ledger_hash,
        "scientific_provider_ledger_head_hash": provider.head_record_hash,
        "http_error_record_count": http_error.authoritative_record_count,
        "http_error_ledger_hash": http_error.ledger_hash,
        "http_error_ledger_head_hash": http_error.head_record_hash,
        "proposal_record_count": len(proposals),
        "outcome_record_count": len(outcomes),
        "direct_number_record_count": len(direct),
        "relation_identity_hash": proposal_relation_hash,
        "proposal_arm": proposal["arm"],
        "proposal_record_hash": proposal["record_hash"],
        "outcome_arm": outcome["arm"],
        "outcome_artifact_hash": outcome["artifact_hash"],
        "t0_replay_exact_match": True,
        "all_transactional_chains_valid": True,
    }


class R2RFailureForensicAuditTests(unittest.TestCase):
    def test_never_send_reproduces_exact_mock_only_guard(self) -> None:
        raw = _NeverSendRawTransport()
        integrity = _NeverSendIntegrityGuard()
        guarded = _HistoricalR2RIntegrityGuardedTransportV1(raw, integrity)
        slot = ProviderCallSlotV1(0, "0" * 64, "T1", 1, True)
        request = unittest.mock.MagicMock() if hasattr(unittest, "mock") else None
        # The type guard precedes all request use, so a sentinel object is sufficient.
        with self.assertRaisesRegex(
            TASK039E3PreparationError,
            "TASK-039E3-PREP accepts MockProviderTransportV1 only",
        ):
            execute_mock_provider_slot_v1(
                slot=slot,
                request=request,  # type: ignore[arg-type]
                transport=guarded,
                ledger=ProviderCallLedgerV1(),
                parse_kind="proposal",
            )
        self.assertEqual(raw.send_calls, 0)
        self.assertEqual(integrity.invocations, 0)
        self.assertEqual(
            EXPECTED_EXCEPTION_MESSAGE_SHA256,
            sha256(EXPECTED_EXCEPTION_MESSAGE.encode("utf-8")).hexdigest(),
        )

    def test_exact_control_flow_symbols_remain_frozen(self) -> None:
        sources = {
            "precontact": inspect.getsource(R2RIntegrityGuardedTransportV1),
            "t1": inspect.getsource(run_t1_v1),
            "t1b": inspect.getsource(run_t1b_v1),
            "t2": inspect.getsource(run_t2_v1),
            "direct": inspect.getsource(run_direct_number_v1),
            "slot": inspect.getsource(execute_mock_provider_slot_v1),
        }
        self.assertIn("R2RIntegrityGuardedTransportV1(raw_transport, snapshot)", (
            Path(inspect.getsourcefile(R2RIntegrityGuardedTransportV1) or "")
            .with_name("task039e3_r2r_precontact_v1.py")
            .read_text(encoding="utf-8")
        ))
        self.assertIn("execute_mock_provider_slot_v1", sources["t1"])
        self.assertIn("execute_mock_provider_slot_v1", sources["t1b"])
        self.assertIn("execute_mock_provider_slot_v1", sources["t2"])
        self.assertIn("execute_mock_provider_slot_v1", sources["direct"])
        self.assertIn("isinstance(transport, MockProviderTransportV1)", sources["slot"])

    def test_r1d2_adapter_and_historical_r2r_interfaces_differ(self) -> None:
        self.assertTrue(issubclass(IntegrityGuardedTransportV3, MockProviderTransportV1))
        historical = _git_output(
            Path(__file__).resolve().parents[1],
            "show",
            f"{EXECUTION_COMMIT}:src/paperworks/v6/task039e3_r2r_precontact_v1.py",
            text=True,
        )
        self.assertIn("class R2RIntegrityGuardedTransportV1:", historical)
        self.assertNotIn(
            "class R2RIntegrityGuardedTransportV1(MockProviderTransportV1):",
            historical,
        )
        for name in ("calls", "request_hashes", "attempt_custody", "send"):
            self.assertTrue(hasattr(IntegrityGuardedTransportV3, name))
        self.assertTrue(hasattr(_HistoricalR2RIntegrityGuardedTransportV1, "send"))
        for name in ("calls", "request_hashes", "attempt_custody"):
            self.assertFalse(
                hasattr(_HistoricalR2RIntegrityGuardedTransportV1, name)
            )

    def test_t1b_has_a_follow_on_request_hashes_dependency(self) -> None:
        source = inspect.getsource(run_t1b_v1)
        self.assertIn("transport.request_hashes[-3:]", source)
        guarded = _HistoricalR2RIntegrityGuardedTransportV1(
            _NeverSendRawTransport(), _NeverSendIntegrityGuard()
        )
        with self.assertRaises(AttributeError):
            _ = guarded.request_hashes  # type: ignore[attr-defined]

    def test_response_and_transactional_ledger_seams_are_otherwise_compatible(self) -> None:
        self.assertTrue(
            issubclass(R2RLiveOpenAIChatCompletionsTransportV1, MockProviderTransportV1)
        )
        self.assertTrue(issubclass(RecoveryProviderResponseV3, MockProviderResponseV1))
        append_parameters = tuple(
            inspect.signature(TransactionalScientificProviderLedgerV3.append).parameters
        )
        for required in (
            "slot",
            "request_hash",
            "response_present",
            "provider_response_metadata",
            "transport_attempts",
            "parse_status",
            "proposal_core_hash",
            "terminal_slot_state",
        ):
            self.assertIn(required, append_parameters)

    def test_retry_ownership_is_one_caller_loop_plus_one_attempt_transport(self) -> None:
        slot_tree = ast.parse(inspect.getsource(execute_mock_provider_slot_v1))
        slot_loops = [node for node in ast.walk(slot_tree) if isinstance(node, ast.For)]
        self.assertEqual(len(slot_loops), 1)
        transport_tree = ast.parse(
            textwrap.dedent(
                inspect.getsource(RecoveryLiveOpenAIChatCompletionsTransportV3.send)
            )
        )
        self.assertFalse(any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(transport_tree)))
        self.assertTrue(hasattr(RecoveryLiveOpenAIChatCompletionsTransportV3, "_before_attempt"))

    def test_historical_audits_did_not_cross_the_exact_live_arm_seam(self) -> None:
        tests_root = Path(__file__).parent
        science = (tests_root / "test_task039e3_r2r_independent_audit_science.py").read_text(encoding="utf-8")
        runner = (tests_root / "test_task039e3_r2r_live_runner_v1.py").read_text(encoding="utf-8")
        source = (tests_root / "test_task039e3_r2r_independent_audit_source_precontact.py").read_text(encoding="utf-8")
        self.assertIn("MockProviderTransportV1", science)
        self.assertIn('step("science", "science-result")', runner)
        self.assertIn('step("science", "synthetic-science")', source)
        self.assertNotIn(
            "R2RIntegrityGuardedTransportV1", science
        )

    def test_source_identity_inventory_is_complete(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        identities = frozen_source_identities(repository)
        self.assertEqual(len(identities), len(CONTROL_FLOW_PATHS))
        self.assertEqual(
            tuple(item["repository_path"] for item in identities), CONTROL_FLOW_PATHS
        )
        for item in identities:
            self.assertRegex(item["git_blob_sha"], r"^[0-9a-f]{40}$")
            self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
