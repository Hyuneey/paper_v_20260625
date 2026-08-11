from __future__ import annotations

from io import BytesIO
import json
import unittest
from urllib.error import HTTPError

from paperworks.v6.task039e3_execution_prep_v1 import build_capability_probe_request_v1
from paperworks.v6.task039e3_live_transport_v1 import (
    CALL_TIMEOUT_SECONDS,
    LiveOpenAIChatCompletionsTransportV1,
    parse_retry_after_seconds_v1,
)


class _Response:
    def __init__(self, document: dict[str, object], status: int = 200) -> None:
        self.status = status
        self._raw = json.dumps(document).encode("utf-8")

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._raw


def _success(model: str = "gpt-5.4-2026-03-05") -> dict[str, object]:
    return {
        "id": "resp_test",
        "model": model,
        "system_fingerprint": "fp_test",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "model_snapshot": "gpt-5.4-2026-03-05",
                            "structured_output_supported": True,
                        }
                    ),
                    "refusal": None,
                },
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


class LiveTransportTests(unittest.TestCase):
    def test_exact_success_mapping_and_no_header_custody(self) -> None:
        observed: dict[str, object] = {}

        def opener(request: object, *, timeout: int) -> _Response:
            observed["timeout"] = timeout
            observed["has_auth"] = bool(request.get_header("Authorization"))
            return _Response(_success())

        transport = LiveOpenAIChatCompletionsTransportV1(
            api_key="test-only-secret", opener=opener, sleeper=lambda _seconds: None
        )
        response = transport.send(build_capability_probe_request_v1())
        self.assertTrue(response.response_present)
        self.assertEqual(response.model, "gpt-5.4-2026-03-05")
        self.assertEqual(observed, {"timeout": CALL_TIMEOUT_SECONDS, "has_auth": True})
        custody = transport.attempt_custody[0].to_dict()
        serialized = json.dumps(custody)
        self.assertNotIn("test-only-secret", serialized)
        self.assertNotIn("Authorization", serialized)
        self.assertEqual(custody["system_fingerprint"], "fp_test")

    def test_returned_model_mismatch_fails_closed_without_fallback(self) -> None:
        transport = LiveOpenAIChatCompletionsTransportV1(
            api_key="test", opener=lambda *_args, **_kwargs: _Response(_success("gpt-other")),
            sleeper=lambda _seconds: None,
        )
        response = transport.send(build_capability_probe_request_v1())
        self.assertFalse(response.response_present)
        self.assertEqual(response.outcome, "model_identity_integrity")

    def test_retry_after_overrides_fixed_wait(self) -> None:
        calls = 0
        waits: list[float] = []

        def opener(*_args: object, **_kwargs: object) -> _Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise HTTPError("https://example", 429, "rate", {"Retry-After": "7"}, BytesIO())
            return _Response(_success())

        transport = LiveOpenAIChatCompletionsTransportV1(
            api_key="test", opener=opener, sleeper=waits.append
        )
        first = transport.send(build_capability_probe_request_v1())
        second = transport.send(build_capability_probe_request_v1())
        self.assertEqual(first.outcome, "http_429")
        self.assertTrue(second.response_present)
        self.assertEqual(waits, [7.0])

    def test_retry_after_parser_rejects_invalid(self) -> None:
        self.assertEqual(parse_retry_after_seconds_v1("2"), 2.0)
        self.assertIsNone(parse_retry_after_seconds_v1("not-a-date"))
        self.assertIsNone(parse_retry_after_seconds_v1("-1"))


if __name__ == "__main__":
    unittest.main()
