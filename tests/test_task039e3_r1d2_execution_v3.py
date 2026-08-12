from __future__ import annotations

import ast
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_FIXTURE_ID,
    RECOVERY_CAPABILITY_TOKEN,
)
from paperworks.v6.task039e3_recovery_execution_v3 import (
    IntegrityGuardedTransportV3,
    TASK039E3RecoveryScientificAbortV3Error,
    TransactionalScientificProviderLedgerV3,
    build_typed_accounting_v3,
    execute_recovery_capability_probe_v3,
    freeze_capability_custody_v3,
    run_capability_then_science_v3,
    validate_execution_roots_v3,
)
from paperworks.v6.task039e3_recovery_integrity_v3 import (
    FrozenSourceBlobV3,
    PostContactIntegrityGuardV3,
    build_frozen_execution_integrity_state_v3,
    capture_execution_integrity_snapshot_v3,
)
from paperworks.v6.task039e3_recovery_live_transport_v3 import (
    RecoveryLiveOpenAIChatCompletionsTransportV3,
)
from paperworks.v6.task039e3_recovery_result_finalizer_v3 import (
    FinalizedScientificResultV3,
    PUBLIC_ARTIFACT_NAMES_V3,
    SUCCESS_STATUS,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    finalize_public_artifact_v1,
)
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalHashChainCustodyV3,
)


ROOT = Path(__file__).resolve().parents[1]
HASH = "a" * 64
COMMIT = "b" * 40


class _HTTPResponse:
    status = 200

    def __init__(self, document: object) -> None:
        self._raw = json.dumps(document).encode("utf-8")

    def __enter__(self) -> "_HTTPResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._raw


def _provider_document(*, content: object | None = None) -> dict[str, object]:
    if content is None:
        content = json.dumps(
            {
                "fixture_id": RECOVERY_CAPABILITY_FIXTURE_ID,
                "capability_token": RECOVERY_CAPABILITY_TOKEN,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    return {
        "id": "chatcmpl-r1d2-execution",
        "model": "gpt-5.4-2026-03-05",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": content, "refusal": None},
            }
        ],
        "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
        "system_fingerprint": "fp-r1d2-execution",
    }


def _guard() -> PostContactIntegrityGuardV3:
    state = build_frozen_execution_integrity_state_v3(
        head_commit=COMMIT,
        source_manifest_hash=HASH,
        source_blobs=(FrozenSourceBlobV3.from_bytes("src/synthetic.py", b"x = 1\n"),),
        scientific_accounting_behavior_hash="c" * 64,
        r2_authorization_hash="d" * 64,
    )
    return PostContactIntegrityGuardV3(
        snapshot=capture_execution_integrity_snapshot_v3(state),
        observed_state_loader=lambda: state,
    )


def _transport(document: object) -> RecoveryLiveOpenAIChatCompletionsTransportV3:
    return RecoveryLiveOpenAIChatCompletionsTransportV3(
        api_key="synthetic-only",
        opener=lambda *_args, **_kwargs: _HTTPResponse(document),
        sleeper=lambda _seconds: None,
    )


@dataclass(frozen=True)
class _ScientificResult:
    def to_dict(self) -> dict[str, int]:
        return {
            "relation_count": 42,
            "t0_outcomes": 42,
            "t1_logical_calls": 42,
            "t1b_logical_calls": 126,
            "t2_logical_calls": 42,
            "direct_number_logical_calls": 42,
            "scientific_logical_calls": 252,
            "scientific_concurrency": 1,
            "scientific_generation_retries": 0,
            "local_compatibility_slots": 0,
        }


class R1D2ExecutionV3Tests(unittest.TestCase):
    def test_malformed_http200_capability_is_transactionally_present_not_exhausted(self) -> None:
        malformed = _provider_document(content={"wrong": True})
        transport = IntegrityGuardedTransportV3(_transport(malformed), _guard())
        execution = execute_recovery_capability_probe_v3(transport)
        with tempfile.TemporaryDirectory() as temporary:
            custody = TransactionalHashChainCustodyV3(
                Path(temporary) / "capability",
                ledger_kind="recovery_capability",
                allowed_logical_call_kind="recovery_capability",
            )
            binding = freeze_capability_custody_v3(
                execution=execution, transport=transport, custody=custody
            )
            payload = custody.records[0]["payload"]
        self.assertTrue(payload["response_present"])
        self.assertTrue(payload["provider_authored_response"])
        self.assertEqual(payload["parse_status"], "schema_invalid_response")
        self.assertEqual(
            payload["terminal_slot_state"], "completed_schema_invalid_response"
        )
        self.assertEqual(binding["terminal_slot_state"], "completed_schema_invalid_response")

    def test_model_mismatch_survives_logical_custody_and_terminal_failure_receipt(self) -> None:
        unexpected_model = "gpt-unexpected-r1d2"
        unexpected_id = "chatcmpl-unexpected-r1d2"
        document = _provider_document()
        document["model"] = unexpected_model
        document["id"] = unexpected_id
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            recovery = base / "recovery"
            e1 = base / "e1"
            historical = base / "historical"
            public = base / "public"
            for root in (recovery, e1, historical):
                root.mkdir()
            result = run_capability_then_science_v3(
                repository_root=ROOT,
                execution_commit=COMMIT,
                source_manifest_hash=HASH,
                r2_authorization_hash="d" * 64,
                authority_bindings={},
                scientific_source_hashes={},
                e1_private_root=e1,
                historical_e3_private_root=historical,
                recovery_private_root=recovery,
                public_output_root=public,
                public_cohort={},
                relation_identities=tuple(f"relation-{index}" for index in range(42)),
                transport=_transport(document),
                integrity_guard=_guard(),
                progress=lambda _message: None,
            )
            payload = json.loads(next((recovery / "capability_provider_v3" / "records").glob("*.json")).read_text(encoding="utf-8"))["payload"]
            failure = result["failure_receipt"]
        self.assertEqual(payload["returned_model"], unexpected_model)
        self.assertEqual(payload["response_id"], unexpected_id)
        self.assertEqual(payload["terminal_slot_state"], "completed_model_identity_mismatch")
        self.assertEqual(failure["actual_returned_model"], unexpected_model)
        self.assertEqual(failure["actual_response_id"], unexpected_id)
        self.assertEqual(failure["terminal_slot_state"], "completed_model_identity_mismatch")

    def test_scientific_malformed_response_is_durable_before_abort(self) -> None:
        transport = _transport(_provider_document(content={"wrong": True}))
        guarded = IntegrityGuardedTransportV3(transport, _guard())
        from paperworks.v6.task039e3_recovery_capability_v1 import build_recovery_capability_request_v1
        response = guarded.send(build_recovery_capability_request_v1())
        with tempfile.TemporaryDirectory() as temporary:
            custody = TransactionalHashChainCustodyV3(
                Path(temporary) / "science",
                ledger_kind="scientific_provider",
                allowed_logical_call_kind="scientific",
            )
            ledger = TransactionalScientificProviderLedgerV3(
                custody, attempt_supplier=lambda: guarded.attempt_custody
            )
            from paperworks.v6.task039e3_execution_prep_v1 import ProviderCallSlotV1
            slot = ProviderCallSlotV1(0, "e" * 64, "T1", 1, True)
            with self.assertRaises(TASK039E3RecoveryScientificAbortV3Error):
                ledger.append(
                    slot=slot,
                    request_hash="f" * 64,
                    response_present=response.response_present,
                    provider_response_metadata={"outcome": response.outcome},
                    transport_attempts=(object(),),
                    parse_status="schema_parse_failure",
                    proposal_core_hash=None,
                    terminal_slot_state="completed_invalid_response",
                )
            reconstructed = custody.reconstruct()
            payload = reconstructed.reachable_records[0]["payload"]
        self.assertEqual(reconstructed.authoritative_record_count, 1)
        self.assertTrue(payload["response_present"])
        self.assertEqual(payload["terminal_slot_state"], "completed_schema_invalid_response")

    def test_typed_accounting_never_cancels_counter_families(self) -> None:
        for attempts in (1, 2, 3):
            accounting = build_typed_accounting_v3(
                capability_attempts=attempts,
                scientific_result=_ScientificResult(),
                scientific_transport_attempts=254,
            )
            self.assertEqual(accounting["current_recovery_capability_transport_retries"], attempts - 1)
            self.assertEqual(accounting["scientific_transport_retries"], 2)
            self.assertEqual(accounting["local_compatibility_slots"], 0)

    def test_public_root_is_external_distinct_and_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            roots = [base / name for name in ("e1", "historical", "recovery")]
            for root in roots:
                root.mkdir()
            public = base / "public"
            guarded = validate_execution_roots_v3(
                repository_root=ROOT,
                e1_private_value=str(roots[0]),
                historical_e3_private_value=str(roots[1]),
                recovery_e3_private_value=str(roots[2]),
                public_output_value=str(public),
            )
            self.assertEqual(guarded.public_output_root, public.resolve())
            nested = roots[2] / "public"
            with self.assertRaisesRegex(Exception, "distinct"):
                validate_execution_roots_v3(
                    repository_root=ROOT,
                    e1_private_value=str(roots[0]),
                    historical_e3_private_value=str(roots[1]),
                    recovery_e3_private_value=str(roots[2]),
                    public_output_value=str(nested),
                )

    def test_capability_pass_precedes_science_and_verified_receipt_is_terminal_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            recovery = base / "recovery"
            e1 = base / "e1"
            historical = base / "historical"
            public = base / "public"
            for root in (recovery, e1, historical):
                root.mkdir()
            observed: dict[str, bool] = {}

            def science(**kwargs: object) -> _ScientificResult:
                authority = kwargs["authority"]
                observed["custody"] = authority.capability_custody_frozen
                observed["receipt"] = authority.capability_receipt_durable
                from paperworks.v6.task039e3_recovery_capability_v1 import (
                    build_recovery_capability_request_v1,
                )
                synthetic_transport = kwargs["transport"]
                for _ in range(252):
                    synthetic_transport.send(build_recovery_capability_request_v1())
                return _ScientificResult()

            def finalizer(**kwargs: object) -> FinalizedScientificResultV3:
                observed["finalizer"] = True
                writer = kwargs["artifact_writer"]
                receipt = finalize_public_artifact_v1(
                    {"artifact_type": "synthetic_terminal_receipt", "status": SUCCESS_STATUS}
                )
                written = writer(public / PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"], receipt)
                return FinalizedScientificResultV3(
                    status=SUCCESS_STATUS,
                    public_artifact_hashes={"execution_receipt": written["artifact_hash"]},
                    private_artifact_hashes={},
                    execution_receipt_hash=written["artifact_hash"],
                    public_artifact_order=("execution_receipt",),
                )

            result = run_capability_then_science_v3(
                repository_root=ROOT,
                execution_commit=COMMIT,
                source_manifest_hash=HASH,
                r2_authorization_hash="d" * 64,
                authority_bindings={},
                scientific_source_hashes={},
                e1_private_root=e1,
                historical_e3_private_root=historical,
                recovery_private_root=recovery,
                public_output_root=public,
                public_cohort={},
                relation_identities=tuple(f"relation-{index}" for index in range(42)),
                transport=_transport(_provider_document()),
                integrity_guard=_guard(),
                progress=lambda _message: None,
                scientific_runner=science,
                success_finalizer=finalizer,
            )
            self.assertEqual(result["status"], SUCCESS_STATUS)
            self.assertTrue(observed["custody"])
            self.assertTrue(observed["receipt"])
            self.assertTrue(observed["finalizer"])
            self.assertTrue((public / PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"]).is_file())

    def test_active_runner_closure_excludes_legacy_execution_and_bridge(self) -> None:
        pending = [ROOT / "scripts/run_task039e3_recovery_execution_v3.py"]
        visited: set[Path] = set()
        modules: set[str] = set()
        while pending:
            path = pending.pop()
            if path in visited:
                continue
            visited.add(path)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or node.level:
                    continue
                module = node.module or ""
                if not module.startswith("paperworks.v6."):
                    continue
                modules.add(module)
                candidate = ROOT / "src" / Path(*module.split("."))
                candidate = candidate.with_suffix(".py")
                if candidate.is_file():
                    pending.append(candidate)
        self.assertNotIn("paperworks.v6.task039e3_recovery_execution_v1", modules)
        self.assertNotIn("paperworks.v6.task039e3_recovery_execution_v2", modules)
        active_text = "\n".join(path.read_text(encoding="utf-8") for path in visited)
        self.assertNotIn("RecoveryScientificCompatibilityTransportV1", active_text)

    def test_runner_has_one_credential_lookup_after_guards_and_external_outputs(self) -> None:
        source = (ROOT / "scripts/run_task039e3_recovery_execution_v3.py").read_text(encoding="utf-8")
        self.assertEqual(source.count('os.environ.get("OPENAI_API_KEY")'), 1)
        self.assertIn('--public-output-root', source)
        self.assertIn('--final-audit-receipt', source)
        self.assertLess(
            source.index("run_ordered_precontact_guards_v3("),
            source.index("RecoveryLiveOpenAIChatCompletionsTransportV3("),
        )


if __name__ == "__main__":
    unittest.main()
