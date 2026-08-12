"""Independent post-contact integrity oracle for TASK-039E3-R1C-AUDIT.

No environment credential or network resource is touched.  The synthetic
capability response marks the contact boundary, after which this oracle
mutates in-memory active execution/configuration state and proves that the
current V2 coordinator can still report scientific PASS.  That observed
behavior is a BLOCKING audit finding, not an endorsed implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_FIXTURE_ID,
    RECOVERY_CAPABILITY_TOKEN,
)
from paperworks.v6.task039e3_recovery_custody_v2 import TypedProviderAccountingV2
from paperworks.v6 import task039e3_recovery_execution_v2 as execution_v2
from paperworks.v6.task039e3_recovery_live_transport_v2 import (
    RecoveryLiveOpenAIChatCompletionsTransportV2,
)


_MODEL = "gpt-5.4-2026-03-05"
_HASH = "a" * 64


class _HTTPResponse:
    status = 200

    def __init__(self) -> None:
        document = {
            "id": "chatcmpl-postcontact-audit",
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
                        "refusal": None,
                    },
                }
            ],
            "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
            "system_fingerprint": "fp-postcontact-audit",
        }
        self._body = json.dumps(document).encode("utf-8")

    def __enter__(self) -> "_HTTPResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


@dataclass(frozen=True)
class _SyntheticScientificResult:
    scientific_logical_calls: int = 252

    def to_dict(self) -> dict[str, int]:
        return {"scientific_logical_calls": self.scientific_logical_calls}


def _complete_accounting() -> TypedProviderAccountingV2:
    return TypedProviderAccountingV2(
        historical_capability_probes=1,
        current_recovery_capability_logical_calls=1,
        current_recovery_capability_transport_attempts=1,
        current_recovery_capability_transport_retries=0,
        scientific_logical_calls=252,
        scientific_transport_attempts=252,
        scientific_transport_retries=0,
        local_compatibility_slots=0,
        cumulative_real_provider_capability_probes=2,
        full_scientific_run_complete=True,
    )


class R1CAuditPostContactIntegrityTests(unittest.TestCase):
    def test_coordinator_has_no_postcontact_git_or_manifest_recheck(self) -> None:
        source = inspect.getsource(execution_v2.run_capability_then_science_v2)
        forbidden_missing_checks = (
            "collect_git_execution_state_v2",
            "validate_git_and_source_state_v2",
            "source_blobs_match_manifest",
            "worktree_clean",
            "index_clean",
        )
        for name in forbidden_missing_checks:
            self.assertNotIn(name, source)

    def test_source_and_timeout_mutation_after_contact_can_still_return_pass(self) -> None:
        contacted = False

        def opener(*_args: object, **_kwargs: object) -> _HTTPResponse:
            nonlocal contacted
            contacted = True
            return _HTTPResponse()

        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic-only",
            opener=opener,
            sleeper=lambda _seconds: None,
        )
        original_science = execution_v2.run_post_capability_scientific_execution_v2
        original_accounting = execution_v2.build_typed_provider_accounting_v2
        original_timeout = transport._timeout_seconds

        with TemporaryDirectory() as raw:
            root = Path(raw)
            source_copy = root / "active_scientific_source.py"
            source_copy.write_bytes(
                Path(original_science.__code__.co_filename).read_bytes()
            )
            initial_source = source_copy.read_bytes()

            def mutated_science(**_kwargs: object) -> _SyntheticScientificResult:
                self.assertTrue(contacted)
                source_copy.write_bytes(initial_source + b"\n# post-contact mutation\n")
                transport._timeout_seconds = 31.0
                execution_v2.build_typed_provider_accounting_v2 = (
                    lambda **_values: _complete_accounting()
                )
                return _SyntheticScientificResult()

            execution_v2.run_post_capability_scientific_execution_v2 = mutated_science
            try:
                result = execution_v2.run_capability_then_science_v2(
                    execution_commit="b" * 40,
                    source_manifest_hash=_HASH,
                    r2_authorization_hash="c" * 64,
                    e1_private_root=root / "synthetic-e1",
                    recovery_private_root=root / "synthetic-recovery",
                    public_cohort={},
                    relation_identities=tuple(f"r-{index}" for index in range(42)),
                    transport=transport,
                    progress=lambda _message: None,
                )
            finally:
                execution_v2.run_post_capability_scientific_execution_v2 = original_science
                execution_v2.build_typed_provider_accounting_v2 = original_accounting
                transport._timeout_seconds = original_timeout

            self.assertNotEqual(source_copy.read_bytes(), initial_source)
            self.assertEqual(result["status"], "passed_task039e3_rule_construction_scientific_execution")
            self.assertEqual(result["typed_accounting"]["scientific_logical_calls"], 252)
            self.assertTrue(contacted)


if __name__ == "__main__":
    unittest.main()
