"""Offline tests for bounded R2R HTTP-error custody."""

from __future__ import annotations

import ast
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import unittest
from urllib.error import HTTPError

from paperworks.v6.task039e3_recovery_capability_v1 import (
    build_recovery_capability_request_v1,
)
from paperworks.v6.task039e3_r2r_live_transport_v1 import (
    HTTP_ERROR_BODY_READ_LIMIT_BYTES,
    MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES,
    R2RLiveOpenAIChatCompletionsTransportV1,
)


class _BoundedBytesIO(BytesIO):
    def __init__(self, body: bytes) -> None:
        super().__init__(body)
        self.read_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        return super().read(size)


class _Non200Handle:
    def __init__(self, *, status: int, body: bytes, headers: dict[str, str]) -> None:
        self.status = status
        self.headers = headers
        self._stream = _BoundedBytesIO(body)
        self.closed_by_transport = False

    @property
    def read_sizes(self) -> list[int]:
        return self._stream.read_sizes

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def close(self) -> None:
        self.closed_by_transport = True


def _error_opener(
    *, status: int, body: bytes, headers: dict[str, str] | None = None
):
    stream = _BoundedBytesIO(body)
    error = HTTPError(
        "https://offline.invalid",
        status,
        "offline fixture",
        headers or {},
        stream,
    )

    def opener(*_args: object, **_kwargs: object) -> object:
        raise error

    return opener, stream


def _one_error_attempt(
    *, status: int, body: bytes, headers: dict[str, str] | None = None
):
    opener, stream = _error_opener(status=status, body=body, headers=headers)
    transport = R2RLiveOpenAIChatCompletionsTransportV1(
        api_key="synthetic-test-only",
        opener=opener,
        sleeper=lambda _delay: None,
    )
    response = transport.send(build_recovery_capability_request_v1())
    return response, transport.attempt_custody[0], stream


class R2RLiveTransportV1Tests(unittest.TestCase):
    def test_small_http_400_body_is_retained_privately_and_parsed(self) -> None:
        body = json.dumps(
            {
                "error": {
                    "message": "sensitive provider diagnostic",
                    "type": "invalid_request_error",
                    "code": "invalid_schema",
                    "param": "response_format",
                }
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "X-Request-Id": "req-offline-1",
            "X-Client-Request-Id": "client-offline-1",
        }
        response, attempt, stream = _one_error_attempt(
            status=400, body=body, headers=headers
        )

        self.assertEqual(stream.read_sizes, [HTTP_ERROR_BODY_READ_LIMIT_BYTES])
        self.assertEqual(response.outcome, "http_400")
        self.assertTrue(response.transport_response_received)
        self.assertFalse(response.provider_payload_received)
        self.assertFalse(response.provider_authored_response)
        self.assertFalse(response.response_present)
        self.assertFalse(attempt.retry_eligible)
        self.assertEqual(
            attempt.terminal_classification,
            "completed_nonretryable_transport_failure",
        )
        custody = attempt.private_http_error
        assert custody is not None
        self.assertEqual(custody.retained_error_body, body)
        self.assertEqual(custody.full_body_sha256, sha256(body).hexdigest())
        self.assertFalse(custody.body_truncated)
        self.assertTrue(custody.provider_error_payload_received)
        self.assertTrue(custody.provider_error_object_parseable)
        self.assertEqual(custody.provider_error_type, "invalid_request_error")
        self.assertEqual(custody.provider_error_code, "invalid_schema")
        self.assertEqual(custody.provider_error_param, "response_format")
        self.assertEqual(custody.x_request_id, "req-offline-1")
        self.assertEqual(custody.x_client_request_id, "client-offline-1")
        self.assertEqual(
            custody.provider_error_message_hash,
            sha256(b"sensitive provider diagnostic").hexdigest(),
        )

    def test_empty_and_invalid_bodies_remain_unparsed(self) -> None:
        for name, body in (("empty", b""), ("invalid_utf8", b"\xff"), ("invalid_json", b"{")):
            with self.subTest(name=name):
                _response, attempt, _stream = _one_error_attempt(
                    status=400, body=body
                )
                custody = attempt.private_http_error
                assert custody is not None
                self.assertFalse(custody.provider_error_object_parseable)
                self.assertIsNone(custody.provider_error_message_hash)
                self.assertEqual(
                    custody.provider_error_payload_received, bool(body)
                )
                self.assertEqual(custody.full_body_sha256, sha256(body).hexdigest())

    def test_exactly_64k_is_complete_and_64k_plus_one_is_truncated(self) -> None:
        exact = b"a" * MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES
        _response, attempt, stream = _one_error_attempt(status=400, body=exact)
        custody = attempt.private_http_error
        assert custody is not None
        self.assertEqual(stream.read_sizes, [HTTP_ERROR_BODY_READ_LIMIT_BYTES])
        self.assertEqual(custody.retained_body_byte_length, 65536)
        self.assertEqual(custody.observed_body_byte_length, 65536)
        self.assertFalse(custody.body_truncated)
        self.assertEqual(custody.full_body_sha256, sha256(exact).hexdigest())

        oversized = b"b" * HTTP_ERROR_BODY_READ_LIMIT_BYTES
        _response, attempt, stream = _one_error_attempt(
            status=400,
            body=oversized,
            headers={"Content-Length": str(len(oversized))},
        )
        custody = attempt.private_http_error
        assert custody is not None
        self.assertEqual(stream.read_sizes, [HTTP_ERROR_BODY_READ_LIMIT_BYTES])
        self.assertEqual(custody.retained_error_body, oversized[:65536])
        self.assertEqual(custody.observed_body_byte_length, 65537)
        self.assertEqual(custody.original_body_byte_length_if_known, 65537)
        self.assertTrue(custody.body_truncated)
        self.assertEqual(custody.body_read_status, "truncated")
        self.assertIsNone(custody.full_body_sha256)
        self.assertFalse(custody.provider_error_object_parseable)

    def test_nonexception_non200_handle_is_also_bounded_and_closed(self) -> None:
        handle = _Non200Handle(
            status=422,
            body=b"z" * (HTTP_ERROR_BODY_READ_LIMIT_BYTES + 100),
            headers={"Content-Type": "text/plain"},
        )
        transport = R2RLiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-test-only",
            opener=lambda *_args, **_kwargs: handle,
            sleeper=lambda _delay: None,
        )
        response = transport.send(build_recovery_capability_request_v1())
        attempt = transport.attempt_custody[0]

        self.assertEqual(response.outcome, "http_422")
        self.assertFalse(attempt.retry_eligible)
        self.assertEqual(handle.read_sizes, [HTTP_ERROR_BODY_READ_LIMIT_BYTES])
        self.assertTrue(handle.closed_by_transport)
        assert attempt.private_http_error is not None
        self.assertTrue(attempt.private_http_error.body_truncated)

    def test_http_429_and_5xx_retry_semantics_are_unchanged(self) -> None:
        for status, expected in ((429, "http_429"), (503, "http_5xx")):
            with self.subTest(status=status):
                headers = {"Retry-After": "3"} if status == 429 else {}
                response, attempt, _stream = _one_error_attempt(
                    status=status, body=b"{}", headers=headers
                )
                self.assertEqual(response.outcome, expected)
                self.assertTrue(attempt.retry_eligible)
                self.assertEqual(
                    attempt.terminal_classification, "retryable_transport_failure"
                )
                self.assertEqual(
                    attempt.retry_after_seconds_observed,
                    3.0 if status == 429 else None,
                )

        delays: list[float] = []
        errors = [
            HTTPError(
                "https://offline.invalid",
                429,
                "offline",
                {"Retry-After": "3"},
                _BoundedBytesIO(b"{}"),
            ),
            HTTPError(
                "https://offline.invalid",
                503,
                "offline",
                {},
                _BoundedBytesIO(b"{}"),
            ),
        ]

        def opener(*_args: object, **_kwargs: object) -> object:
            raise errors.pop(0)

        transport = R2RLiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-test-only", opener=opener, sleeper=delays.append
        )
        request = build_recovery_capability_request_v1()
        transport.send(request)
        transport.send(request)
        self.assertEqual(delays, [3.0])
        self.assertEqual(
            [attempt.attempt_number for attempt in transport.attempt_custody],
            [1, 2],
        )
        self.assertTrue(all(
            attempt.retry_eligible for attempt in transport.attempt_custody
        ))

    def test_public_projection_contains_no_raw_error_body_or_message(self) -> None:
        secret = "provider diagnostic must remain private"
        body = json.dumps({"error": {"message": secret}}).encode("utf-8")
        request_id = "req-private-correlation-id"
        client_request_id = "client-private-correlation-id"
        _response, attempt, _stream = _one_error_attempt(
            status=400,
            body=body,
            headers={
                "X-Request-Id": request_id,
                "X-Client-Request-Id": client_request_id,
            },
        )
        private = json.dumps(attempt.to_dict(), sort_keys=True)
        public = json.dumps(attempt.to_public_dict(), sort_keys=True)

        self.assertIn("retained_error_body_base64", private)
        self.assertNotIn("retained_error_body_base64", public)
        self.assertNotIn(secret, public)
        self.assertNotIn('"provider_error_type":', public)
        self.assertNotIn('"provider_error_code":', public)
        self.assertNotIn('"provider_error_param":', public)
        self.assertNotIn(request_id, public)
        self.assertNotIn(client_request_id, public)
        self.assertIn(request_id, private)
        self.assertIn(client_request_id, private)
        self.assertIn('"x_request_id_hash":', public)
        self.assertIn('"x_client_request_id_hash":', public)
        self.assertIn("provider_error_message_hash", public)
        self.assertIn('"model_completion_response_present": false', public)
        self.assertIn('"scientific_response_present": false', public)

    def test_source_has_no_import_time_or_hidden_network_call(self) -> None:
        source_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "paperworks"
            / "v6"
            / "task039e3_r2r_live_transport_v1.py"
        )
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        urlopen_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "urlopen"
        ]
        self.assertEqual(urlopen_calls, [])
        self.assertNotIn("requests", source)
        self.assertNotIn("httpx", source)
        self.assertNotIn("os.environ", source)
        self.assertNotIn("OPENAI_API_KEY", source)


if __name__ == "__main__":
    unittest.main()
