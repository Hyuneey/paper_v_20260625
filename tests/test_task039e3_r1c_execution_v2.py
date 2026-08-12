from __future__ import annotations

import ast
from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_FIXTURE_ID,
    RECOVERY_CAPABILITY_TOKEN,
    build_recovery_capability_request_v1,
)
from paperworks.v6.task039e3_recovery_custody_v2 import (
    RecoveryCapabilityProviderLedgerV2,
    TypedProviderAccountingV2,
)
from paperworks.v6.task039e3_recovery_execution_v2 import (
    TASK039E3RecoveryExecutionV2Error,
    build_recovery_capability_receipt_v2,
    execute_recovery_capability_probe_v2,
    freeze_capability_custody_v2,
    run_capability_then_science_v2,
)
from paperworks.v6.task039e3_recovery_live_transport_v2 import (
    RecoveryLiveOpenAIChatCompletionsTransportV2,
)


_MODEL = "gpt-5.4-2026-03-05"
_HASH = "a" * 64


class _HTTPResponse:
    def __init__(self, document: object) -> None:
        self.status = 200
        self._body = json.dumps(document).encode("utf-8")

    def __enter__(self) -> "_HTTPResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def _provider_document(*, refusal: str | None = None) -> dict[str, object]:
    return {
        "id": "chatcmpl-r1c-execution-test",
        "model": _MODEL,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "fixture_id": RECOVERY_CAPABILITY_FIXTURE_ID,
                            "capability_token": RECOVERY_CAPABILITY_TOKEN,
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "refusal": refusal,
                },
            }
        ],
        "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
        "system_fingerprint": "fp-r1c-execution-test",
    }


@dataclass(frozen=True)
class _ScientificResult:
    scientific_logical_calls: int = 252

    def to_dict(self) -> dict[str, int]:
        return {"scientific_logical_calls": self.scientific_logical_calls}


class R1CRecoveryExecutionV2Tests(unittest.TestCase):
    def _transport(self, opener: object) -> RecoveryLiveOpenAIChatCompletionsTransportV2:
        return RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic-only",
            opener=opener,
            sleeper=lambda _seconds: None,
        )

    def test_one_logical_probe_retains_one_two_three_attempt_accounting(self) -> None:
        for success_attempt in (1, 2, 3):
            with self.subTest(success_attempt=success_attempt):
                calls = 0

                def opener(*_args: object, **_kwargs: object) -> _HTTPResponse:
                    nonlocal calls
                    calls += 1
                    if calls < success_attempt:
                        raise TimeoutError("synthetic timeout")
                    return _HTTPResponse(_provider_document())

                execution = execute_recovery_capability_probe_v2(
                    self._transport(opener)
                )
                self.assertEqual(execution.accounting.current_recovery_probe_count, 1)
                self.assertEqual(execution.accounting.cumulative_probe_count, 2)
                self.assertEqual(execution.transport_attempts, success_attempt)
                self.assertEqual(execution.transport_retries, success_attempt - 1)

    def test_probe_rejects_preused_transport(self) -> None:
        transport = self._transport(
            lambda *_args, **_kwargs: _HTTPResponse(_provider_document())
        )
        transport.send(build_recovery_capability_request_v1())
        with self.assertRaisesRegex(TASK039E3RecoveryExecutionV2Error, "unused"):
            execute_recovery_capability_probe_v2(transport)

    def test_capability_custody_and_receipt_are_separate_and_self_hashed(self) -> None:
        transport = self._transport(
            lambda *_args, **_kwargs: _HTTPResponse(_provider_document())
        )
        execution = execute_recovery_capability_probe_v2(transport)
        ledger = RecoveryCapabilityProviderLedgerV2()
        binding = freeze_capability_custody_v2(
            execution=execution, transport=transport, ledger=ledger
        )
        receipt = build_recovery_capability_receipt_v2(
            execution=execution,
            execution_commit="b" * 40,
            source_manifest_hash=_HASH,
            r2_authorization_hash="c" * 64,
            custody_binding=binding,
        )
        self.assertEqual(len(ledger.records), 1)
        self.assertEqual(ledger.records[0].logical_call_kind, "recovery_capability")
        self.assertEqual(receipt["local_compatibility_slots"], 0)
        self.assertEqual(receipt["system_fingerprint"], "fp-r1c-execution-test")
        self.assertEqual(len(receipt["artifact_hash"]), 64)

    def test_capability_block_freezes_custody_and_never_creates_science(self) -> None:
        transport = self._transport(
            lambda *_args, **_kwargs: _HTTPResponse(
                _provider_document(refusal="synthetic refusal")
            )
        )
        with TemporaryDirectory() as temp:
            root = Path(temp)
            result = run_capability_then_science_v2(
                execution_commit="b" * 40,
                source_manifest_hash=_HASH,
                r2_authorization_hash="c" * 64,
                e1_private_root=root / "unread-e1",
                recovery_private_root=root,
                public_cohort={},
                relation_identities=tuple(f"r-{index}" for index in range(42)),
                transport=transport,
                progress=lambda _message: None,
            )
            self.assertEqual(result["status"], "blocked_task039e3_recovery_capability_gate")
            self.assertEqual(result["scientific_calls"], 0)
            self.assertEqual(result["local_compatibility_slots"], 0)
            self.assertFalse((root / "scientific").exists())
            self.assertTrue((root / "recovery_capability_provider_v2.jsonl").is_file())
            self.assertTrue((root / "recovery_capability_receipt_v2.json").is_file())

    def test_pass_reaches_science_only_after_durable_receipt(self) -> None:
        transport = self._transport(
            lambda *_args, **_kwargs: _HTTPResponse(_provider_document())
        )
        observed: dict[str, bool] = {}
        with TemporaryDirectory() as temp:
            root = Path(temp)

            def scientific(**kwargs: object) -> _ScientificResult:
                authority = kwargs["authority"]
                observed["receipt_exists"] = (
                    root / "recovery_capability_receipt_v2.json"
                ).is_file()
                observed["custody_frozen"] = authority.capability_custody_frozen
                observed["receipt_durable"] = authority.capability_receipt_durable
                return _ScientificResult()

            accounting = TypedProviderAccountingV2(
                historical_capability_probes=1,
                current_recovery_capability_logical_calls=1,
                current_recovery_capability_transport_attempts=1,
                current_recovery_capability_transport_retries=0,
                cumulative_real_provider_capability_probes=2,
                scientific_logical_calls=252,
                scientific_transport_attempts=252,
                scientific_transport_retries=0,
                local_compatibility_slots=0,
            )
            with patch(
                "paperworks.v6.task039e3_recovery_execution_v2.run_post_capability_scientific_execution_v2",
                side_effect=scientific,
            ), patch(
                "paperworks.v6.task039e3_recovery_execution_v2.build_typed_provider_accounting_v2",
                return_value=accounting,
            ):
                result = run_capability_then_science_v2(
                    execution_commit="b" * 40,
                    source_manifest_hash=_HASH,
                    r2_authorization_hash="c" * 64,
                    e1_private_root=root / "synthetic-e1",
                    recovery_private_root=root,
                    public_cohort={},
                    relation_identities=tuple(f"r-{index}" for index in range(42)),
                    transport=transport,
                    progress=lambda _message: None,
                )
        self.assertTrue(observed["receipt_exists"])
        self.assertTrue(observed["custody_frozen"])
        self.assertTrue(observed["receipt_durable"])
        self.assertEqual(result["typed_accounting"]["local_compatibility_slots"], 0)

    def test_active_v2_files_exclude_legacy_bridge_and_legacy_payload(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        paths = (
            repository / "src/paperworks/v6/task039e3_recovery_execution_v2.py",
            repository / "src/paperworks/v6/task039e3_recovery_science_v2.py",
            repository / "scripts/run_task039e3_recovery_execution_v2.py",
        )
        forbidden = (
            "RecoveryScientificCompatibilityTransportV1",
            "model_snapshot",
            "structured_output_supported",
        )
        for path in paths:
            source = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, source, f"{token} in {path.name}")

    def test_active_runner_import_closure_cannot_reach_v1_recovery_execution(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        pending = [
            repository / "scripts/run_task039e3_recovery_execution_v2.py"
        ]
        visited: set[Path] = set()
        imported_modules: set[str] = set()
        while pending:
            path = pending.pop()
            if path in visited:
                continue
            visited.add(path)
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or node.level != 0:
                    continue
                module = node.module or ""
                if not module.startswith("paperworks.v6."):
                    continue
                imported_modules.add(module)
                relative = Path("src") / Path(*module.split("."))
                candidate = repository / relative.with_suffix(".py")
                if candidate.is_file():
                    pending.append(candidate)
        self.assertNotIn(
            "paperworks.v6.task039e3_recovery_execution_v1", imported_modules
        )

    def test_runner_has_exactly_one_future_credential_lookup(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        source = (
            repository / "scripts/run_task039e3_recovery_execution_v2.py"
        ).read_text(encoding="utf-8")
        self.assertEqual(source.count('os.environ.get("OPENAI_API_KEY")'), 1)
        self.assertLess(
            source.index("run_ordered_precontact_guards_v2("),
            source.index("RecoveryLiveOpenAIChatCompletionsTransportV2("),
        )


if __name__ == "__main__":
    unittest.main()
