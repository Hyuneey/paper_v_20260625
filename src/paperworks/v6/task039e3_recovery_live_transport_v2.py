"""Recovery-specific OpenAI transport with forensic provider custody.

This additive TASK-039E3-R1C transport preserves provider observations before
performing model-identity validation.  In particular, an HTTP-200 response
from an unexpected model remains a present provider response and retains its
exact model and response identifier.  Credentials are dependency-injected and
are never included in request hashes or custody records.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import socket
import time
from types import MappingProxyType
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from paperworks.v6.common import stable_hash_v1, thaw_json
from paperworks.v6.task039e2_execution_configuration_v1 import EXACT_MODEL
from paperworks.v6.task039e3_execution_prep_v1 import (
    FrozenProviderRequestV1,
    MockProviderResponseV1,
    MockProviderTransportV1,
    TASK039E3PreparationError,
)
from paperworks.v6.task039e3_live_transport_v1 import parse_retry_after_seconds_v1


URLOPEN_TIMEOUT_SECONDS = 30.0
MAXIMUM_TRANSPORT_RETRIES = 2
MAXIMUM_TRANSPORT_ATTEMPTS = 3
RETRY_DELAYS_SECONDS = (2.0, 4.0)
RESPONSE_ORIGIN = "provider"

_RETRYABLE_OUTCOMES = frozenset(
    {
        "connection_failure",
        "connection_reset",
        "timeout_before_response",
        "http_429",
        "http_5xx",
    }
)


@dataclass(frozen=True)
class RecoveryLiveTransportAttemptCustodyV2:
    """One actual provider transport attempt; never a local synthetic slot."""

    sequence_index: int
    attempt_number: int
    request_hash: str
    response_origin: str
    provider_contacted: bool
    provider_authored_response: bool
    outcome: str
    terminal_classification: str
    status_code: int | None
    response_present: bool
    returned_model: str | None
    response_id: str | None
    finish_reason: str | None
    token_usage: Mapping[str, int] | None
    system_fingerprint: str | None
    retry_eligible: bool
    actual_retry_delay_before_attempt_seconds: float | None
    retry_after_seconds_observed: float | None

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "sequence_index": self.sequence_index,
            "attempt_number": self.attempt_number,
            "request_hash": self.request_hash,
            "response_origin": self.response_origin,
            "provider_contacted": self.provider_contacted,
            "provider_authored_response": self.provider_authored_response,
            "outcome": self.outcome,
            "terminal_classification": self.terminal_classification,
            "status_code": self.status_code,
            "response_present": self.response_present,
            "returned_model": self.returned_model,
            "response_id": self.response_id,
            "finish_reason": self.finish_reason,
            "token_usage": (
                dict(self.token_usage) if self.token_usage is not None else None
            ),
            "system_fingerprint": self.system_fingerprint,
            "retry_eligible": self.retry_eligible,
            "actual_retry_delay_before_attempt_seconds": (
                self.actual_retry_delay_before_attempt_seconds
            ),
            "retry_after_seconds_observed": self.retry_after_seconds_observed,
        }
        document["record_hash"] = stable_hash_v1(document)
        return document


def _usage_from_document(document: Mapping[str, Any]) -> Mapping[str, int] | None:
    usage = document.get("usage")
    if not isinstance(usage, Mapping):
        return None
    return MappingProxyType(
        {
            str(key): int(value)
            for key, value in usage.items()
            if isinstance(value, int) and not isinstance(value, bool)
        }
    )


def _first_choice_metadata(document: Mapping[str, Any]) -> tuple[str | None, Any]:
    choices = document.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        return None, None
    choice = choices[0]
    if not isinstance(choice, Mapping):
        return None, None
    finish_reason = choice.get("finish_reason")
    return (
        str(finish_reason) if finish_reason is not None else None,
        choice.get("message"),
    )


def _terminal_classification(response: MockProviderResponseV1) -> str:
    if response.outcome == "model_identity_integrity":
        return "completed_model_identity_mismatch"
    if not response.response_present and response.outcome in _RETRYABLE_OUTCOMES:
        return "retryable_transport_failure"
    if response.outcome == "provider_refusal":
        return "completed_provider_refusal"
    if response.outcome == "schema_invalid_response":
        return "completed_schema_invalid_response"
    if response.response_present:
        return "completed_provider_response"
    return "completed_nonretryable_transport_failure"


class RecoveryLiveOpenAIChatCompletionsTransportV2(MockProviderTransportV1):
    """Stateless Chat Completions transport for a future authorized R2 run.

    ``send`` performs exactly one HTTP attempt.  The frozen caller controls
    logical-call retries by invoking ``send`` again for retryable outcomes.
    Attempt two and three receive the fixed 2/4 second waits (or an authorized
    Retry-After override for HTTP 429).  A fourth attempt is fail-closed.
    """

    def __init__(
        self,
        *,
        api_key: str,
        opener: Callable[..., Any] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
        timeout_seconds: float = URLOPEN_TIMEOUT_SECONDS,
    ) -> None:
        if not isinstance(api_key, str) or not api_key:
            raise TASK039E3PreparationError(
                "blocked_task039e3_credential_unavailable"
            )
        if float(timeout_seconds) != URLOPEN_TIMEOUT_SECONDS:
            raise TASK039E3PreparationError(
                "recovery timeout differs from frozen R1A authority"
            )
        self._api_key = api_key
        self._opener = opener
        self._sleeper = sleeper
        self._timeout_seconds = URLOPEN_TIMEOUT_SECONDS
        self._calls = 0
        self._request_hashes: list[str] = []
        self._attempt_custody: list[RecoveryLiveTransportAttemptCustodyV2] = []
        self._retry_pending = False
        self._retry_ordinal = 0
        self._next_delay_seconds: float | None = None

    @property
    def calls(self) -> int:
        """Actual provider transport-attempt count."""

        return self._calls

    @property
    def request_hashes(self) -> tuple[str, ...]:
        return tuple(self._request_hashes)

    @property
    def attempt_custody(self) -> tuple[RecoveryLiveTransportAttemptCustodyV2, ...]:
        return tuple(self._attempt_custody)

    def _before_attempt(self) -> tuple[int, float | None]:
        if not self._retry_pending:
            self._retry_ordinal = 0
            return 1, None
        self._retry_ordinal += 1
        if self._retry_ordinal > MAXIMUM_TRANSPORT_RETRIES:
            raise TASK039E3PreparationError("transport retry budget exceeded")
        delay = self._next_delay_seconds
        if delay is None:
            delay = RETRY_DELAYS_SECONDS[self._retry_ordinal - 1]
        self._sleeper(delay)
        return self._retry_ordinal + 1, delay

    def _finish_attempt(
        self,
        *,
        request_hash: str,
        attempt_number: int,
        response: MockProviderResponseV1,
        actual_delay: float | None,
        retry_after: float | None,
        returned_model: str | None = None,
        response_id: str | None = None,
        finish_reason: str | None = None,
        token_usage: Mapping[str, int] | None = None,
        system_fingerprint: str | None = None,
        provider_authored_response: bool | None = None,
    ) -> MockProviderResponseV1:
        retryable = not response.response_present and response.outcome in _RETRYABLE_OUTCOMES
        observed_model = returned_model if returned_model is not None else response.model
        observed_response_id = response_id if response_id is not None else response.response_id
        observed_finish_reason = (
            finish_reason if finish_reason is not None else response.finish_reason
        )
        observed_usage = token_usage if token_usage is not None else response.token_usage
        self._attempt_custody.append(
            RecoveryLiveTransportAttemptCustodyV2(
                sequence_index=len(self._attempt_custody),
                attempt_number=attempt_number,
                request_hash=request_hash,
                response_origin=RESPONSE_ORIGIN,
                provider_contacted=True,
                provider_authored_response=(
                    response.response_present
                    if provider_authored_response is None
                    else provider_authored_response
                ),
                outcome=response.outcome,
                terminal_classification=_terminal_classification(response),
                status_code=response.status_code,
                response_present=response.response_present,
                returned_model=observed_model,
                response_id=observed_response_id,
                finish_reason=observed_finish_reason,
                token_usage=observed_usage,
                system_fingerprint=system_fingerprint,
                retry_eligible=retryable,
                actual_retry_delay_before_attempt_seconds=actual_delay,
                retry_after_seconds_observed=retry_after,
            )
        )
        self._retry_pending = retryable
        self._next_delay_seconds = retry_after if response.outcome == "http_429" else None
        if not retryable:
            self._retry_ordinal = 0
            self._next_delay_seconds = None
        return response

    def send(self, request: FrozenProviderRequestV1) -> MockProviderResponseV1:
        if not isinstance(request, FrozenProviderRequestV1):
            raise TASK039E3PreparationError(
                "recovery live transport requires frozen request"
            )
        attempt_number, actual_delay = self._before_attempt()
        self._calls += 1
        self._request_hashes.append(request.request_hash)
        payload = json.dumps(
            thaw_json(request.request_body),
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        outbound = Request(
            request.endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        retry_after: float | None = None
        try:
            with self._opener(outbound, timeout=self._timeout_seconds) as handle:
                status = int(getattr(handle, "status", 200))
                raw = handle.read()
            if status != 200:
                outcome = "http_5xx" if status >= 500 else f"http_{status}"
                response = MockProviderResponseV1(False, outcome, status, None, None)
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                    provider_authored_response=False,
                )

            try:
                decoded = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                response = MockProviderResponseV1(
                    False, "schema_invalid_response", 200, None, None
                )
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                    provider_authored_response=True,
                )

            if not isinstance(decoded, Mapping):
                response = MockProviderResponseV1(
                    False, "schema_invalid_response", 200, None, None
                )
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                    provider_authored_response=True,
                )

            document = decoded
            raw_model = document.get("model")
            raw_response_id = document.get("id")
            returned_model = raw_model if isinstance(raw_model, str) else None
            response_id = raw_response_id if isinstance(raw_response_id, str) else None
            finish_reason, raw_message = _first_choice_metadata(document)
            usage = _usage_from_document(document)
            raw_fingerprint = document.get("system_fingerprint")
            system_fingerprint = (
                str(raw_fingerprint) if raw_fingerprint is not None else None
            )

            # Model identity comes solely from provider response metadata and
            # is evaluated before accepting message content as scientific.
            if returned_model is not None and returned_model != EXACT_MODEL:
                if response_id is None:
                    response = MockProviderResponseV1(
                        False, "schema_invalid_response", 200, None, None
                    )
                else:
                    response = MockProviderResponseV1(
                        True,
                        "model_identity_integrity",
                        200,
                        returned_model,
                        None,
                        finish_reason=finish_reason,
                        response_id=response_id,
                        token_usage=usage,
                    )
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                    returned_model=returned_model,
                    response_id=response_id,
                    finish_reason=finish_reason,
                    token_usage=usage,
                    system_fingerprint=system_fingerprint,
                    provider_authored_response=True,
                )

            if (
                returned_model != EXACT_MODEL
                or response_id is None
                or not isinstance(raw_message, Mapping)
            ):
                response = MockProviderResponseV1(
                    False, "schema_invalid_response", 200, None, None
                )
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                    returned_model=returned_model,
                    response_id=response_id,
                    finish_reason=finish_reason,
                    token_usage=usage,
                    system_fingerprint=system_fingerprint,
                    provider_authored_response=True,
                )

            refusal_value = raw_message.get("refusal")
            refusal = isinstance(refusal_value, str) and bool(refusal_value.strip())
            content = None if refusal else raw_message.get("content")
            if content is not None and not isinstance(content, str):
                response = MockProviderResponseV1(
                    True,
                    "schema_invalid_response",
                    200,
                    returned_model,
                    None,
                    finish_reason=finish_reason,
                    response_id=response_id,
                    token_usage=usage,
                )
            else:
                response = MockProviderResponseV1(
                    True,
                    "provider_refusal" if refusal else "successful_response",
                    200,
                    returned_model,
                    content,
                    refusal=refusal,
                    finish_reason=finish_reason,
                    response_id=response_id,
                    token_usage=usage,
                )
            return self._finish_attempt(
                request_hash=request.request_hash,
                attempt_number=attempt_number,
                response=response,
                actual_delay=actual_delay,
                retry_after=None,
                returned_model=returned_model,
                response_id=response_id,
                finish_reason=finish_reason,
                token_usage=usage,
                system_fingerprint=system_fingerprint,
                provider_authored_response=True,
            )
        except HTTPError as exc:
            status = int(exc.code)
            if status == 429:
                outcome = "http_429"
                retry_after = parse_retry_after_seconds_v1(
                    exc.headers.get("Retry-After")
                )
            elif status >= 500:
                outcome = "http_5xx"
            else:
                outcome = f"http_{status}"
            response = MockProviderResponseV1(False, outcome, status, None, None)
        except (TimeoutError, socket.timeout):
            response = MockProviderResponseV1(
                False, "timeout_before_response", None, None, None
            )
        except (ConnectionResetError, BrokenPipeError):
            response = MockProviderResponseV1(
                False, "connection_reset", None, None, None
            )
        except URLError as exc:
            reason = exc.reason
            outcome = (
                "timeout_before_response"
                if isinstance(reason, (TimeoutError, socket.timeout))
                else "connection_reset"
                if isinstance(reason, ConnectionResetError)
                else "connection_failure"
            )
            response = MockProviderResponseV1(False, outcome, None, None, None)
        return self._finish_attempt(
            request_hash=request.request_hash,
            attempt_number=attempt_number,
            response=response,
            actual_delay=actual_delay,
            retry_after=retry_after,
            provider_authored_response=False,
        )


__all__ = [
    "MAXIMUM_TRANSPORT_ATTEMPTS",
    "MAXIMUM_TRANSPORT_RETRIES",
    "RESPONSE_ORIGIN",
    "RETRY_DELAYS_SECONDS",
    "RecoveryLiveOpenAIChatCompletionsTransportV2",
    "RecoveryLiveTransportAttemptCustodyV2",
    "URLOPEN_TIMEOUT_SECONDS",
]
