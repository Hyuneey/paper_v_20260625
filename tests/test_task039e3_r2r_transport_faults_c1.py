"""C1 offline fault injection for R2R HTTP-error custody and retries."""

from __future__ import annotations

from io import BytesIO
import json
import socket
import unittest
from urllib.error import HTTPError, URLError

from paperworks.v6.task039e3_recovery_capability_v1 import (
    build_recovery_capability_request_v1,
)
from paperworks.v6.task039e3_execution_prep_v1 import TASK039E3PreparationError
from paperworks.v6.task039e3_r2r_live_transport_v1 import (
    HTTP_ERROR_BODY_READ_LIMIT_BYTES,
    MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES,
    R2RHTTPErrorCustodyPersistenceError,
    R2RLiveOpenAIChatCompletionsTransportV1,
)


class _ObservedBody(BytesIO):
    def __init__(self, body: bytes) -> None:
        super().__init__(body)
        self.read_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        return super().read(size)


class _ReadFailure(BytesIO):
    def __init__(self) -> None:
        super().__init__(b"provider body must not escape")
        self.read_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        raise OSError("synthetic private body read failure")


def _http_error(status: int, stream: BytesIO, **headers: str) -> HTTPError:
    return HTTPError(
        "https://offline.invalid",
        status,
        "synthetic offline HTTP error",
        headers,
        stream,
    )


class R2RTransportFaultsC1Tests(unittest.TestCase):
    def test_required_committer_must_exist_before_transport_construction(self) -> None:
        opener_calls: list[object] = []

        with self.assertRaisesRegex(ValueError, "requires an injected committer"):
            R2RLiveOpenAIChatCompletionsTransportV1(
                api_key="synthetic-test-only",
                opener=lambda *_args, **_kwargs: opener_calls.append(object()),
                require_durable_http_error_custody=True,
            )

        self.assertEqual(opener_calls, [])

    def test_body_read_failure_is_bounded_metadata_and_can_commit_before_retry(self) -> None:
        streams = [_ReadFailure(), _ReadFailure()]
        opener_calls: list[int] = []
        committed: list[dict[str, object]] = []
        delays: list[float] = []

        def opener(*_args: object, **_kwargs: object) -> object:
            index = len(opener_calls)
            opener_calls.append(index)
            raise _http_error(429, streams[index])

        transport = R2RLiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-test-only",
            opener=opener,
            sleeper=delays.append,
            http_error_custody_committer=lambda attempt: committed.append(
                attempt.to_dict()
            ),
            require_durable_http_error_custody=True,
        )
        request = build_recovery_capability_request_v1()

        first = transport.send(request)
        self.assertEqual(first.outcome, "http_429")
        first_attempt = transport.attempt_custody[0]
        custody = first_attempt.private_http_error
        assert custody is not None
        self.assertEqual(streams[0].read_sizes, [HTTP_ERROR_BODY_READ_LIMIT_BYTES])
        self.assertEqual(custody.body_read_status, "read_failed")
        self.assertEqual(custody.body_read_error_class, "OSError")
        self.assertEqual(custody.retained_error_body, b"")
        self.assertFalse(custody.provider_error_payload_received)
        self.assertTrue(first_attempt.retry_eligible)
        self.assertEqual(len(committed), 1)

        # Retry only becomes reachable after the injected durable committer
        # returned successfully for the first attempt.
        second = transport.send(request)
        self.assertEqual(second.outcome, "http_429")
        self.assertEqual(opener_calls, [0, 1])
        self.assertEqual(delays, [2.0])
        self.assertEqual(len(committed), 2)

        public = json.dumps(first_attempt.to_public_dict(), sort_keys=True)
        self.assertNotIn("provider body must not escape", public)
        self.assertNotIn("synthetic private body read failure", public)
        self.assertNotIn("retained_error_body_base64", public)

    def test_custody_persistence_failure_latches_transport_before_retry(self) -> None:
        stream = _ObservedBody(b'{"error":{"message":"private"}}')
        opener_calls: list[int] = []
        delays: list[float] = []
        commit_calls: list[int] = []

        def opener(*_args: object, **_kwargs: object) -> object:
            opener_calls.append(len(opener_calls) + 1)
            raise _http_error(503, stream)

        def fail_commit(_attempt: object) -> None:
            commit_calls.append(1)
            raise OSError("synthetic fsync failure")

        transport = R2RLiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-test-only",
            opener=opener,
            sleeper=delays.append,
            http_error_custody_committer=fail_commit,
            require_durable_http_error_custody=True,
        )
        request = build_recovery_capability_request_v1()

        with self.assertRaisesRegex(
            R2RHTTPErrorCustodyPersistenceError,
            "custody persistence failed",
        ):
            transport.send(request)

        self.assertTrue(transport.http_error_custody_persistence_failed)
        self.assertEqual(transport.calls, 1)
        self.assertEqual(opener_calls, [1])
        self.assertEqual(commit_calls, [1])
        self.assertEqual(delays, [])
        self.assertEqual(len(transport.attempt_custody), 1)
        self.assertTrue(transport.attempt_custody[0].retry_eligible)

        # Even an erroneous caller retry cannot reach sleep or the opener.
        with self.assertRaisesRegex(
            R2RHTTPErrorCustodyPersistenceError,
            "transport sealed",
        ):
            transport.send(request)
        self.assertEqual(transport.calls, 1)
        self.assertEqual(opener_calls, [1])
        self.assertEqual(commit_calls, [1])
        self.assertEqual(delays, [])

    def test_http_status_retry_semantics_survive_successful_custody_commit(self) -> None:
        expected = (
            (400, "http_400", False, "completed_nonretryable_transport_failure"),
            (429, "http_429", True, "retryable_transport_failure"),
            (503, "http_5xx", True, "retryable_transport_failure"),
        )
        for status, outcome, retryable, terminal in expected:
            with self.subTest(status=status):
                committed: list[object] = []
                stream = _ObservedBody(b"{}")

                def opener(*_args: object, **_kwargs: object) -> object:
                    raise _http_error(status, stream)

                transport = R2RLiveOpenAIChatCompletionsTransportV1(
                    api_key="synthetic-test-only",
                    opener=opener,
                    sleeper=lambda _delay: None,
                    http_error_custody_committer=committed.append,
                    require_durable_http_error_custody=True,
                )
                response = transport.send(build_recovery_capability_request_v1())
                attempt = transport.attempt_custody[0]
                self.assertEqual(response.outcome, outcome)
                self.assertEqual(attempt.retry_eligible, retryable)
                self.assertEqual(attempt.terminal_classification, terminal)
                self.assertEqual(len(committed), 1)
                self.assertEqual(
                    stream.read_sizes, [HTTP_ERROR_BODY_READ_LIMIT_BYTES]
                )

    def test_successful_custody_preserves_three_attempt_retry_ceiling(self) -> None:
        opener_calls: list[int] = []
        committed: list[object] = []
        delays: list[float] = []

        def opener(*_args: object, **_kwargs: object) -> object:
            opener_calls.append(len(opener_calls) + 1)
            raise _http_error(503, _ObservedBody(b"{}"))

        transport = R2RLiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-test-only",
            opener=opener,
            sleeper=delays.append,
            http_error_custody_committer=committed.append,
            require_durable_http_error_custody=True,
        )
        request = build_recovery_capability_request_v1()
        for _ in range(3):
            self.assertEqual(transport.send(request).outcome, "http_5xx")

        self.assertEqual(opener_calls, [1, 2, 3])
        self.assertEqual(delays, [2.0, 4.0])
        self.assertEqual(
            [attempt.attempt_number for attempt in transport.attempt_custody],
            [1, 2, 3],
        )
        self.assertEqual(len(committed), 3)

        with self.assertRaisesRegex(
            TASK039E3PreparationError, "transport retry budget exceeded"
        ):
            transport.send(request)
        self.assertEqual(opener_calls, [1, 2, 3])
        self.assertEqual(delays, [2.0, 4.0])

    def test_timeout_and_connection_failures_keep_frozen_retry_semantics(self) -> None:
        failures = (
            (socket.timeout("offline"), "timeout_before_response"),
            (ConnectionResetError("offline"), "connection_reset"),
            (URLError("offline"), "connection_failure"),
        )
        for failure, outcome in failures:
            with self.subTest(outcome=outcome):
                commit_calls: list[object] = []

                def opener(*_args: object, **_kwargs: object) -> object:
                    raise failure

                transport = R2RLiveOpenAIChatCompletionsTransportV1(
                    api_key="synthetic-test-only",
                    opener=opener,
                    sleeper=lambda _delay: None,
                    http_error_custody_committer=commit_calls.append,
                    require_durable_http_error_custody=True,
                )
                response = transport.send(build_recovery_capability_request_v1())
                attempt = transport.attempt_custody[0]
                self.assertEqual(response.outcome, outcome)
                self.assertTrue(attempt.retry_eligible)
                self.assertIsNone(attempt.private_http_error)
                self.assertEqual(commit_calls, [])

    def test_body_bound_and_public_projection_remain_frozen(self) -> None:
        self.assertEqual(MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES, 65536)
        self.assertEqual(HTTP_ERROR_BODY_READ_LIMIT_BYTES, 65537)
        body = json.dumps(
            {"error": {"message": "private provider error message"}}
        ).encode("utf-8") + b"x" * 70000
        stream = _ObservedBody(body)
        committed: list[object] = []

        def opener(*_args: object, **_kwargs: object) -> object:
            raise _http_error(400, stream)

        transport = R2RLiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-test-only",
            opener=opener,
            http_error_custody_committer=committed.append,
            require_durable_http_error_custody=True,
        )
        transport.send(build_recovery_capability_request_v1())
        attempt = transport.attempt_custody[0]
        custody = attempt.private_http_error
        assert custody is not None
        self.assertEqual(custody.retained_body_byte_length, 65536)
        self.assertEqual(custody.observed_body_byte_length, 65537)
        self.assertTrue(custody.body_truncated)
        self.assertEqual(stream.read_sizes, [65537])

        public = json.dumps(attempt.to_public_dict(), sort_keys=True)
        self.assertNotIn("private provider error message", public)
        self.assertNotIn("retained_error_body_base64", public)


if __name__ == "__main__":
    unittest.main()
