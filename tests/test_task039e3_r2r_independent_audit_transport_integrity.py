"""Independent offline audit of R2R transport custody and integrity gates."""

from __future__ import annotations

from base64 import b64decode
from dataclasses import asdict, replace
from hashlib import sha256
from io import BytesIO
import json
import socket
import unittest
from urllib.error import HTTPError

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_recovery_capability_v1 import (
    build_recovery_capability_request_v1,
)
from paperworks.v6.task039e3_execution_prep_v1 import TASK039E3PreparationError
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    DIRECT_NUMBER_PROMPT_HASH,
    DIRECT_NUMBER_SCHEMA_HASH,
    EXACT_ENDPOINT,
    EXACT_MODEL,
    MAIN_PROMPT_HASH,
    RECOVERY_SCHEMA_V2_HASH,
    RELATION_SCHEDULE_HASH,
    T2_FOLLOWUP_PROMPT_HASH,
)
from paperworks.v6.task039e3_r2r_live_transport_v1 import (
    HTTP_ERROR_BODY_READ_LIMIT_BYTES,
    MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES,
    R2RHTTPErrorCustodyPersistenceError,
    R2RLiveOpenAIChatCompletionsTransportV1,
)
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    R2RIntegrityGuardedTransportV1,
    R2RObservedIntegrityStateV1,
    R2RPostContactIntegrityGuardV1,
    R2RSourceBlobIdentityV1,
    R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
    TASK039E3R2RPrecontactError,
    capture_r2r_integrity_snapshot_v1,
)


class _ObservedStream(BytesIO):
    def __init__(self, body: bytes) -> None:
        super().__init__(body)
        self.read_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        return super().read(size)


class _ReadFailure(_ObservedStream):
    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        raise OSError("sensitive synthetic body-read detail")


class _ReturnedNon200:
    def __init__(self, status: int, stream: _ObservedStream, headers: dict[str, str]):
        self.status = status
        self._stream = stream
        self.headers = headers
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def close(self) -> None:
        self.closed = True


def _error(status: int, stream: BytesIO, headers: dict[str, str]) -> HTTPError:
    return HTTPError(
        "https://offline.invalid",
        status,
        "offline synthetic HTTP error",
        headers,
        stream,
    )


def _assert_self_hash(test: unittest.TestCase, document: dict[str, object]) -> None:
    content = dict(document)
    observed = content.pop("record_hash")
    test.assertEqual(observed, stable_hash_v1(content))


def _integrity_state() -> R2RObservedIntegrityStateV1:
    return R2RObservedIntegrityStateV1(
        execution_commit="a" * 40,
        source_manifest_hash="1" * 64,
        source_blobs=(
            R2RSourceBlobIdentityV1(
                "scripts/run_task039e3_r2r_scientific_execution_v1.py",
                "b" * 40,
                "2" * 64,
            ),
        ),
        authorization_hash="3" * 64,
        recovery_main_provider_schema_v2_hash=RECOVERY_SCHEMA_V2_HASH,
        main_prompt_hash=MAIN_PROMPT_HASH,
        t2_followup_prompt_hash=T2_FOLLOWUP_PROMPT_HASH,
        direct_number_prompt_hash=DIRECT_NUMBER_PROMPT_HASH,
        direct_number_schema_hash=DIRECT_NUMBER_SCHEMA_HASH,
        exact_model=EXACT_MODEL,
        endpoint=EXACT_ENDPOINT,
        sampling_configuration_hash="4" * 64,
        timeout_seconds=30.0,
        retry_policy_hash="5" * 64,
        relation_schedule_hash=RELATION_SCHEDULE_HASH,
        scientific_concurrency=1,
        scientific_call_budget_hash="6" * 64,
        scientific_accounting_behavior_hash=(
            R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1
        ),
        recovery_execution_configuration_hash="7" * 64,
    )


def _integrity_mutations() -> dict[str, object]:
    return {
        "execution_commit": "c" * 40,
        "source_manifest_hash": "8" * 64,
        "source_blobs": (
            R2RSourceBlobIdentityV1(
                "scripts/run_task039e3_r2r_scientific_execution_v1.py",
                "b" * 40,
                "9" * 64,
            ),
        ),
        "authorization_hash": "a" * 64,
        "recovery_main_provider_schema_v2_hash": "b" * 64,
        "main_prompt_hash": "c" * 64,
        "t2_followup_prompt_hash": "d" * 64,
        "direct_number_prompt_hash": "e" * 64,
        "direct_number_schema_hash": "f" * 64,
        "exact_model": "unexpected-model",
        "endpoint": "https://offline.invalid/v1/chat/completions",
        "sampling_configuration_hash": "0" * 64,
        "timeout_seconds": 31.0,
        "retry_policy_hash": "1" * 64,
        "relation_schedule_hash": "2" * 64,
        "scientific_concurrency": 2,
        "scientific_call_budget_hash": "3" * 64,
        "scientific_accounting_behavior_hash": "4" * 64,
        "recovery_execution_configuration_hash": "5" * 64,
    }


class R2RIndependentAuditTransportIntegrityTests(unittest.TestCase):
    def _transport(
        self,
        opener: object,
        *,
        sleeper: object | None = None,
        committer: object | None = None,
    ) -> R2RLiveOpenAIChatCompletionsTransportV1:
        return R2RLiveOpenAIChatCompletionsTransportV1(
            api_key="offline-synthetic-only",
            opener=opener,  # type: ignore[arg-type]
            sleeper=(sleeper if sleeper is not None else lambda _delay: None),  # type: ignore[arg-type]
            http_error_custody_committer=(
                committer if committer is not None else lambda _attempt: None
            ),  # type: ignore[arg-type]
            require_durable_http_error_custody=True,
        )

    def test_exact_body_boundaries_on_both_non200_paths(self) -> None:
        request = build_recovery_capability_request_v1()
        for path_kind in ("http_error", "returned_non200"):
            for size in (0, 1, 65535, 65536, 65537):
                with self.subTest(path=path_kind, size=size):
                    body = bytes((index % 251 for index in range(size)))
                    stream = _ObservedStream(body)
                    headers = {
                        "Content-Length": str(size),
                        "Content-Type": "application/octet-stream",
                        "X-Request-Id": "request-private-value",
                        "X-Client-Request-Id": "client-private-value",
                    }
                    returned: _ReturnedNon200 | None = None
                    if path_kind == "http_error":
                        def opener(*_args: object, **_kwargs: object) -> object:
                            raise _error(400, stream, headers)
                    else:
                        returned = _ReturnedNon200(400, stream, headers)

                        def opener(*_args: object, **_kwargs: object) -> object:
                            return returned

                    committed: list[object] = []
                    transport = self._transport(opener, committer=committed.append)
                    response = transport.send(request)
                    attempt = transport.attempt_custody[0]
                    custody = attempt.private_http_error
                    assert custody is not None

                    retained = body[:MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES]
                    truncated = size == HTTP_ERROR_BODY_READ_LIMIT_BYTES
                    self.assertEqual(response.outcome, "http_400")
                    self.assertEqual(stream.read_sizes, [65537])
                    self.assertEqual(custody.retained_error_body, retained)
                    self.assertEqual(custody.retained_body_byte_length, len(retained))
                    self.assertEqual(custody.observed_body_byte_length, size)
                    self.assertEqual(custody.original_body_byte_length_if_known, size)
                    self.assertEqual(custody.retained_body_sha256, sha256(retained).hexdigest())
                    self.assertEqual(custody.body_truncated, truncated)
                    self.assertEqual(
                        custody.body_read_status,
                        "truncated" if truncated else "complete",
                    )
                    self.assertEqual(
                        custody.full_body_sha256,
                        None if truncated else sha256(body).hexdigest(),
                    )
                    self.assertEqual(custody.content_type, "application/octet-stream")
                    self.assertEqual(custody.x_request_id, "request-private-value")
                    self.assertEqual(custody.x_client_request_id, "client-private-value")
                    self.assertEqual(custody.provider_error_payload_received, size > 0)
                    self.assertFalse(custody.provider_error_object_parseable)
                    self.assertFalse(attempt.retry_eligible)
                    self.assertEqual(len(committed), 1)
                    if returned is not None:
                        self.assertTrue(returned.closed)

    def test_error_fields_hashes_and_private_public_separation(self) -> None:
        message = "private provider diagnostic"
        error_type = "invalid_request_error"
        error_code = "invalid_schema"
        error_param = "response_format"
        request_id = "request-id-private"
        client_request_id = "client-request-id-private"
        body = json.dumps(
            {
                "error": {
                    "message": message,
                    "type": error_type,
                    "code": error_code,
                    "param": error_param,
                }
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        stream = _ObservedStream(body)
        headers = {
            "Content-Length": str(len(body)),
            "Content-Type": "application/json; charset=utf-8",
            "X-Request-Id": request_id,
            "X-Client-Request-Id": client_request_id,
        }

        def opener(*_args: object, **_kwargs: object) -> object:
            raise _error(422, stream, headers)

        transport = self._transport(opener)
        transport.send(build_recovery_capability_request_v1())
        attempt = transport.attempt_custody[0]
        custody = attempt.private_http_error
        assert custody is not None
        self.assertTrue(custody.provider_error_object_parseable)
        self.assertEqual(custody.provider_error_type, error_type)
        self.assertEqual(custody.provider_error_code, error_code)
        self.assertEqual(custody.provider_error_param, error_param)
        self.assertEqual(
            custody.provider_error_message_hash,
            sha256(message.encode("utf-8")).hexdigest(),
        )

        private_custody = custody.to_private_dict()
        public_custody = custody.to_public_dict()
        private_attempt = attempt.to_dict()
        public_attempt = attempt.to_public_dict()
        for document in (
            private_custody,
            public_custody,
            private_attempt,
            public_attempt,
        ):
            _assert_self_hash(self, document)

        self.assertEqual(
            b64decode(str(private_custody["retained_error_body_base64"])), body
        )
        public_text = json.dumps(public_attempt, sort_keys=True)
        for prohibited in (
            message,
            error_type,
            error_code,
            error_param,
            request_id,
            client_request_id,
            "retained_error_body_base64",
        ):
            self.assertNotIn(prohibited, public_text)
        self.assertEqual(
            public_custody["provider_error_message_hash"],
            sha256(message.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            public_custody["provider_error_type_hash"],
            sha256(error_type.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            public_custody["provider_error_code_hash"],
            sha256(error_code.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            public_custody["provider_error_param_hash"],
            sha256(error_param.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            public_custody["x_request_id_hash"],
            sha256(request_id.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            public_custody["x_client_request_id_hash"],
            sha256(client_request_id.encode("utf-8")).hexdigest(),
        )

    def test_body_read_failure_is_sanitized_on_both_paths(self) -> None:
        for path_kind in ("http_error", "returned_non200"):
            with self.subTest(path=path_kind):
                stream = _ReadFailure(b"unread")
                headers = {"Content-Type": "application/json"}
                returned: _ReturnedNon200 | None = None
                if path_kind == "http_error":
                    def opener(*_args: object, **_kwargs: object) -> object:
                        raise _error(429, stream, headers)
                else:
                    returned = _ReturnedNon200(429, stream, headers)

                    def opener(*_args: object, **_kwargs: object) -> object:
                        return returned

                committed: list[object] = []
                transport = self._transport(opener, committer=committed.append)
                response = transport.send(build_recovery_capability_request_v1())
                attempt = transport.attempt_custody[0]
                custody = attempt.private_http_error
                assert custody is not None
                self.assertEqual(response.outcome, "http_429")
                self.assertTrue(attempt.retry_eligible)
                self.assertEqual(custody.body_read_status, "read_failed")
                self.assertEqual(custody.body_read_error_class, "OSError")
                self.assertEqual(custody.retained_error_body, b"")
                self.assertEqual(custody.retained_body_sha256, sha256(b"").hexdigest())
                self.assertIsNone(custody.full_body_sha256)
                self.assertEqual(custody.observed_body_byte_length, 0)
                self.assertFalse(custody.provider_error_payload_received)
                self.assertEqual(stream.read_sizes, [65537])
                self.assertEqual(len(committed), 1)
                public = json.dumps(attempt.to_public_dict(), sort_keys=True)
                self.assertNotIn("sensitive synthetic body-read detail", public)
                if returned is not None:
                    self.assertTrue(returned.closed)

    def test_http400_nonretryable_and_429_5xx_exact_retry_budget(self) -> None:
        request = build_recovery_capability_request_v1()

        calls_400: list[int] = []

        def opener_400(*_args: object, **_kwargs: object) -> object:
            calls_400.append(1)
            raise _error(400, _ObservedStream(b"{}"), {})

        transport_400 = self._transport(opener_400)
        response_400 = transport_400.send(request)
        self.assertEqual(response_400.outcome, "http_400")
        self.assertFalse(transport_400.attempt_custody[0].retry_eligible)
        self.assertEqual(
            transport_400.attempt_custody[0].terminal_classification,
            "completed_nonretryable_transport_failure",
        )

        for status, expected in ((429, "http_429"), (503, "http_5xx")):
            with self.subTest(status=status):
                calls: list[int] = []
                delays: list[float] = []
                commits: list[object] = []

                def opener(*_args: object, **_kwargs: object) -> object:
                    calls.append(len(calls) + 1)
                    raise _error(status, _ObservedStream(b"{}"), {})

                transport = self._transport(
                    opener,
                    sleeper=delays.append,
                    committer=commits.append,
                )
                for _ in range(3):
                    response = transport.send(request)
                    self.assertEqual(response.outcome, expected)
                self.assertEqual(calls, [1, 2, 3])
                self.assertEqual(delays, [2.0, 4.0])
                self.assertEqual(len(commits), 3)
                self.assertEqual(
                    [item.attempt_number for item in transport.attempt_custody],
                    [1, 2, 3],
                )
                self.assertTrue(
                    all(item.retry_eligible for item in transport.attempt_custody)
                )
                with self.assertRaisesRegex(
                    TASK039E3PreparationError, "transport retry budget exceeded"
                ):
                    transport.send(request)
                self.assertEqual(calls, [1, 2, 3])
                self.assertEqual(delays, [2.0, 4.0])

    def test_durable_persistence_failure_seals_before_sleep_or_recontact(self) -> None:
        opener_calls: list[int] = []
        delays: list[float] = []
        commit_calls: list[int] = []

        def opener(*_args: object, **_kwargs: object) -> object:
            opener_calls.append(1)
            raise _error(503, _ObservedStream(b"private"), {})

        def failing_commit(_attempt: object) -> None:
            commit_calls.append(1)
            raise OSError("sensitive persistence detail")

        transport = self._transport(
            opener,
            sleeper=delays.append,
            committer=failing_commit,
        )
        request = build_recovery_capability_request_v1()
        with self.assertRaises(R2RHTTPErrorCustodyPersistenceError) as first:
            transport.send(request)
        self.assertEqual(
            str(first.exception), "required HTTP-error custody persistence failed"
        )
        self.assertIsNone(first.exception.__cause__)
        self.assertTrue(transport.http_error_custody_persistence_failed)
        self.assertEqual(transport.calls, 1)
        self.assertEqual(opener_calls, [1])
        self.assertEqual(commit_calls, [1])
        self.assertEqual(delays, [])

        with self.assertRaisesRegex(
            R2RHTTPErrorCustodyPersistenceError, "transport sealed"
        ):
            transport.send(request)
        self.assertEqual(transport.calls, 1)
        self.assertEqual(opener_calls, [1])
        self.assertEqual(commit_calls, [1])
        self.assertEqual(delays, [])

    def test_timeout_retry_semantics_remain_frozen(self) -> None:
        calls: list[int] = []
        delays: list[float] = []

        def opener(*_args: object, **_kwargs: object) -> object:
            calls.append(1)
            raise socket.timeout("offline")

        transport = self._transport(opener, sleeper=delays.append)
        request = build_recovery_capability_request_v1()
        for _ in range(3):
            response = transport.send(request)
            self.assertEqual(response.outcome, "timeout_before_response")
        self.assertEqual(calls, [1, 1, 1])
        self.assertEqual(delays, [2.0, 4.0])
        self.assertTrue(
            all(item.retry_eligible for item in transport.attempt_custody)
        )

    def test_every_integrity_mutation_blocks_before_first_contact(self) -> None:
        baseline = _integrity_state()
        request = build_recovery_capability_request_v1()
        for field, mutation in _integrity_mutations().items():
            with self.subTest(field=field):
                mutable = {"state": replace(baseline, **{field: mutation})}
                raw_calls: list[int] = []

                def opener(*_args: object, **_kwargs: object) -> object:
                    raw_calls.append(1)
                    raise AssertionError("integrity gate allowed first contact")

                raw = self._transport(opener)
                guard = R2RPostContactIntegrityGuardV1(
                    capture_r2r_integrity_snapshot_v1(baseline),
                    lambda: mutable["state"],
                )
                guarded = R2RIntegrityGuardedTransportV1(raw, guard)
                with self.assertRaises(TASK039E3R2RPrecontactError):
                    guarded.send(request)
                self.assertTrue(guard.blocked)
                self.assertEqual(raw.calls, 0)
                self.assertEqual(raw_calls, [])

                mutable["state"] = baseline
                with self.assertRaisesRegex(
                    TASK039E3R2RPrecontactError, "permanently blocked"
                ):
                    guarded.send(request)
                self.assertEqual(raw.calls, 0)
                self.assertEqual(raw_calls, [])

    def test_every_integrity_mutation_after_first_contact_blocks_recontact(self) -> None:
        baseline = _integrity_state()
        request = build_recovery_capability_request_v1()
        for field, mutation in _integrity_mutations().items():
            with self.subTest(field=field):
                mutable = {"state": baseline}
                raw_calls: list[int] = []

                def opener(*_args: object, **_kwargs: object) -> object:
                    raw_calls.append(1)
                    raise _error(400, _ObservedStream(b"{}"), {})

                raw = self._transport(opener)
                guard = R2RPostContactIntegrityGuardV1(
                    capture_r2r_integrity_snapshot_v1(baseline),
                    lambda: mutable["state"],
                )
                guarded = R2RIntegrityGuardedTransportV1(raw, guard)
                self.assertEqual(guarded.send(request).outcome, "http_400")
                self.assertEqual(raw.calls, 1)
                self.assertEqual(raw_calls, [1])

                mutable["state"] = replace(baseline, **{field: mutation})
                with self.assertRaises(TASK039E3R2RPrecontactError):
                    guarded.send(request)
                self.assertTrue(guard.blocked)
                self.assertEqual(raw.calls, 1)
                self.assertEqual(raw_calls, [1])

                mutable["state"] = baseline
                with self.assertRaisesRegex(
                    TASK039E3R2RPrecontactError, "permanently blocked"
                ):
                    guarded.send(request)
                self.assertEqual(raw.calls, 1)
                self.assertEqual(raw_calls, [1])

    def test_snapshot_fingerprint_binds_the_complete_observed_state(self) -> None:
        baseline = _integrity_state()
        snapshot = capture_r2r_integrity_snapshot_v1(baseline)
        self.assertEqual(snapshot.fingerprint, stable_hash_v1(asdict(baseline)))
        self.assertEqual(
            set(_integrity_mutations()),
            set(R2RObservedIntegrityStateV1.__dataclass_fields__),
        )


if __name__ == "__main__":
    unittest.main()
