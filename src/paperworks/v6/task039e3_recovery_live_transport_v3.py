"""Recovery transport V3 with lossless provider-response semantics.

This additive TASK-039E3-R1D2 transport separates an observed HTTP response
from successful structured decoding.  In particular, every provider-authored
HTTP-200 response is a present response even when its bytes, JSON envelope, or
strict structured content are malformed.  Such a response is terminal and is
never mislabeled as a transport failure or transport exhaustion.

The transport performs one attempt per :meth:`send` call.  The frozen caller
owns logical-request retry scheduling.  All tests use injected openers; this
module performs no work merely by being imported.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import socket
import time
from types import MappingProxyType
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from paperworks.v6.common import freeze_json, stable_hash_v1, thaw_json
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
class RecoveryProviderResponseV3(MockProviderResponseV1):
    """Mapped provider result that distinguishes response from parse success.

    ``MockProviderResponseV1`` historically required a present response to
    have parseable model and response-id metadata.  V3 deliberately relaxes
    only that constraint for ``schema_invalid_response`` because invalid UTF-8
    or invalid JSON can genuinely make those fields unknowable.  It remains a
    subclass so unchanged frozen parsers safely turn malformed responses into
    deterministic invalid-response outcomes rather than transport failures.
    """

    transport_response_received: bool = False
    provider_payload_received: bool = False
    provider_contacted: bool = True
    provider_authored_response: bool = False
    structured_payload_valid: bool = False
    system_fingerprint: str | None = None
    provider_payload_hash: str | None = None

    def __post_init__(self) -> None:
        malformed_http_200 = (
            self.response_present
            and self.status_code == 200
            and self.outcome == "schema_invalid_response"
        )
        if malformed_http_200:
            if self.content is not None or self.refusal:
                raise TASK039E3PreparationError(
                    "malformed provider response cannot carry accepted content"
                )
            if not (
                self.transport_response_received
                and self.provider_payload_received
                and self.provider_contacted
                and self.provider_authored_response
            ):
                raise TASK039E3PreparationError(
                    "malformed HTTP-200 provider observation flags differ"
                )
            if self.structured_payload_valid:
                raise TASK039E3PreparationError(
                    "schema-invalid provider response cannot be structured-valid"
                )
            if self.token_usage is not None:
                object.__setattr__(self, "token_usage", freeze_json(self.token_usage))
        else:
            MockProviderResponseV1.__post_init__(self)

        if self.provider_authored_response and not self.transport_response_received:
            raise TASK039E3PreparationError(
                "provider-authored response requires an observed transport response"
            )
        if self.structured_payload_valid and (
            not self.response_present or not self.provider_authored_response
        ):
            raise TASK039E3PreparationError(
                "structured-valid response requires a present provider response"
            )

    @property
    def response_hash(self) -> str | None:
        if not self.response_present:
            return None
        return stable_hash_v1(
            {
                "outcome": self.outcome,
                "status_code": self.status_code,
                "model": self.model,
                "content": self.content,
                "refusal": self.refusal,
                "finish_reason": self.finish_reason,
                "response_id": self.response_id,
                "token_usage": thaw_json(self.token_usage),
                "transport_response_received": self.transport_response_received,
                "provider_payload_received": self.provider_payload_received,
                "provider_contacted": self.provider_contacted,
                "provider_authored_response": self.provider_authored_response,
                "structured_payload_valid": self.structured_payload_valid,
                "system_fingerprint": self.system_fingerprint,
                "provider_payload_hash": self.provider_payload_hash,
            }
        )


@dataclass(frozen=True)
class RecoveryLiveTransportAttemptCustodyV3:
    """One real transport attempt with explicit response provenance."""

    sequence_index: int
    attempt_number: int
    request_hash: str
    response_origin: str
    transport_response_received: bool
    provider_payload_received: bool
    provider_contacted: bool
    provider_authored_response: bool
    response_present: bool
    structured_payload_valid: bool
    outcome: str
    terminal_classification: str
    status_code: int | None
    returned_model: str | None
    response_id: str | None
    finish_reason: str | None
    token_usage: Mapping[str, int] | None
    system_fingerprint: str | None
    provider_payload_hash: str | None
    retry_eligible: bool
    actual_retry_delay_before_attempt_seconds: float | None
    retry_after_seconds_observed: float | None

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "sequence_index": self.sequence_index,
            "attempt_number": self.attempt_number,
            "request_hash": self.request_hash,
            "response_origin": self.response_origin,
            "transport_response_received": self.transport_response_received,
            "provider_payload_received": self.provider_payload_received,
            "provider_contacted": self.provider_contacted,
            "provider_authored_response": self.provider_authored_response,
            "response_present": self.response_present,
            "structured_payload_valid": self.structured_payload_valid,
            "outcome": self.outcome,
            "terminal_classification": self.terminal_classification,
            "status_code": self.status_code,
            "returned_model": self.returned_model,
            "response_id": self.response_id,
            "finish_reason": self.finish_reason,
            "token_usage": (
                dict(self.token_usage) if self.token_usage is not None else None
            ),
            "system_fingerprint": self.system_fingerprint,
            "provider_payload_hash": self.provider_payload_hash,
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


def terminal_classification_v3(response: RecoveryProviderResponseV3) -> str:
    """Return the attempt/logical terminal class without transport conflation."""

    if response.outcome == "model_identity_integrity":
        return "completed_model_identity_mismatch"
    if response.outcome == "schema_invalid_response" and response.response_present:
        return "completed_schema_invalid_response"
    if not response.response_present and response.outcome in _RETRYABLE_OUTCOMES:
        return "retryable_transport_failure"
    if response.outcome == "provider_refusal":
        return "completed_provider_refusal"
    if response.response_present:
        return "completed_provider_response"
    return "completed_nonretryable_transport_failure"


def logical_parse_status_v3(response: RecoveryProviderResponseV3) -> str:
    """Map a terminal V3 response to non-conflating logical custody status."""

    if response.outcome == "schema_invalid_response" and response.response_present:
        return "schema_invalid_response"
    if response.response_present:
        return "provider_response_received"
    return "transport_failure"


class RecoveryLiveOpenAIChatCompletionsTransportV3(MockProviderTransportV1):
    """One-attempt Chat Completions transport for future authorized execution."""

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
        self._attempt_custody: list[RecoveryLiveTransportAttemptCustodyV3] = []
        self._retry_pending = False
        self._retry_ordinal = 0
        self._next_delay_seconds: float | None = None

    @property
    def calls(self) -> int:
        return self._calls

    @property
    def request_hashes(self) -> tuple[str, ...]:
        return tuple(self._request_hashes)

    @property
    def attempt_custody(self) -> tuple[RecoveryLiveTransportAttemptCustodyV3, ...]:
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
        response: RecoveryProviderResponseV3,
        actual_delay: float | None,
        retry_after: float | None,
    ) -> RecoveryProviderResponseV3:
        retryable = (
            not response.response_present and response.outcome in _RETRYABLE_OUTCOMES
        )
        self._attempt_custody.append(
            RecoveryLiveTransportAttemptCustodyV3(
                sequence_index=len(self._attempt_custody),
                attempt_number=attempt_number,
                request_hash=request_hash,
                response_origin=RESPONSE_ORIGIN,
                transport_response_received=response.transport_response_received,
                provider_payload_received=response.provider_payload_received,
                provider_contacted=response.provider_contacted,
                provider_authored_response=response.provider_authored_response,
                response_present=response.response_present,
                structured_payload_valid=response.structured_payload_valid,
                outcome=response.outcome,
                terminal_classification=terminal_classification_v3(response),
                status_code=response.status_code,
                returned_model=response.model,
                response_id=response.response_id,
                finish_reason=response.finish_reason,
                token_usage=response.token_usage,
                system_fingerprint=response.system_fingerprint,
                provider_payload_hash=response.provider_payload_hash,
                retry_eligible=retryable,
                actual_retry_delay_before_attempt_seconds=actual_delay,
                retry_after_seconds_observed=retry_after,
            )
        )
        self._retry_pending = retryable
        self._next_delay_seconds = (
            retry_after if response.outcome == "http_429" else None
        )
        if not retryable:
            self._retry_ordinal = 0
            self._next_delay_seconds = None
        return response

    @staticmethod
    def _transport_failure(
        outcome: str,
        status_code: int | None,
        *,
        transport_response_received: bool,
    ) -> RecoveryProviderResponseV3:
        return RecoveryProviderResponseV3(
            False,
            outcome,
            status_code,
            None,
            None,
            transport_response_received=transport_response_received,
            provider_payload_received=False,
            provider_contacted=True,
            provider_authored_response=False,
            structured_payload_valid=False,
        )

    @staticmethod
    def _schema_invalid_http_200(
        raw: bytes,
        *,
        returned_model: str | None = None,
        response_id: str | None = None,
        finish_reason: str | None = None,
        token_usage: Mapping[str, int] | None = None,
        system_fingerprint: str | None = None,
    ) -> RecoveryProviderResponseV3:
        return RecoveryProviderResponseV3(
            True,
            "schema_invalid_response",
            200,
            returned_model,
            None,
            finish_reason=finish_reason,
            response_id=response_id,
            token_usage=token_usage,
            transport_response_received=True,
            provider_payload_received=True,
            provider_contacted=True,
            provider_authored_response=True,
            structured_payload_valid=False,
            system_fingerprint=system_fingerprint,
            provider_payload_hash=sha256(raw).hexdigest(),
        )

    def send(self, request: FrozenProviderRequestV1) -> RecoveryProviderResponseV3:
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
                response = self._transport_failure(
                    outcome, status, transport_response_received=True
                )
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                )

            try:
                decoded = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                response = self._schema_invalid_http_200(raw)
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                )

            if not isinstance(decoded, Mapping):
                response = self._schema_invalid_http_200(raw)
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
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
            payload_hash = sha256(raw).hexdigest()

            if returned_model is not None and returned_model != EXACT_MODEL:
                if response_id is None:
                    response = self._schema_invalid_http_200(
                        raw,
                        returned_model=returned_model,
                        finish_reason=finish_reason,
                        token_usage=usage,
                        system_fingerprint=system_fingerprint,
                    )
                else:
                    response = RecoveryProviderResponseV3(
                        True,
                        "model_identity_integrity",
                        200,
                        returned_model,
                        None,
                        finish_reason=finish_reason,
                        response_id=response_id,
                        token_usage=usage,
                        transport_response_received=True,
                        provider_payload_received=True,
                        provider_contacted=True,
                        provider_authored_response=True,
                        # Model identity is terminal before structured content
                        # can be accepted under the required snapshot.
                        structured_payload_valid=False,
                        system_fingerprint=system_fingerprint,
                        provider_payload_hash=payload_hash,
                    )
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                )

            if (
                returned_model != EXACT_MODEL
                or response_id is None
                or not isinstance(raw_message, Mapping)
            ):
                response = self._schema_invalid_http_200(
                    raw,
                    returned_model=returned_model,
                    response_id=response_id,
                    finish_reason=finish_reason,
                    token_usage=usage,
                    system_fingerprint=system_fingerprint,
                )
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                )

            refusal_value = raw_message.get("refusal")
            if refusal_value is not None and not isinstance(refusal_value, str):
                response = self._schema_invalid_http_200(
                    raw,
                    returned_model=returned_model,
                    response_id=response_id,
                    finish_reason=finish_reason,
                    token_usage=usage,
                    system_fingerprint=system_fingerprint,
                )
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                )

            refusal = isinstance(refusal_value, str) and bool(refusal_value.strip())
            content_value = raw_message.get("content")
            if refusal:
                content: str | None = None
            elif not isinstance(content_value, str):
                response = self._schema_invalid_http_200(
                    raw,
                    returned_model=returned_model,
                    response_id=response_id,
                    finish_reason=finish_reason,
                    token_usage=usage,
                    system_fingerprint=system_fingerprint,
                )
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    attempt_number=attempt_number,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                )
            else:
                content = content_value
                try:
                    structured = json.loads(content)
                except (TypeError, ValueError, json.JSONDecodeError):
                    structured = None
                if not isinstance(structured, Mapping):
                    response = self._schema_invalid_http_200(
                        raw,
                        returned_model=returned_model,
                        response_id=response_id,
                        finish_reason=finish_reason,
                        token_usage=usage,
                        system_fingerprint=system_fingerprint,
                    )
                    return self._finish_attempt(
                        request_hash=request.request_hash,
                        attempt_number=attempt_number,
                        response=response,
                        actual_delay=actual_delay,
                        retry_after=None,
                    )

            response = RecoveryProviderResponseV3(
                True,
                "provider_refusal" if refusal else "successful_response",
                200,
                returned_model,
                content,
                refusal=refusal,
                finish_reason=finish_reason,
                response_id=response_id,
                token_usage=usage,
                transport_response_received=True,
                provider_payload_received=True,
                provider_contacted=True,
                provider_authored_response=True,
                structured_payload_valid=not refusal,
                system_fingerprint=system_fingerprint,
                provider_payload_hash=payload_hash,
            )
            return self._finish_attempt(
                request_hash=request.request_hash,
                attempt_number=attempt_number,
                response=response,
                actual_delay=actual_delay,
                retry_after=None,
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
            response = self._transport_failure(
                outcome, status, transport_response_received=True
            )
        except (TimeoutError, socket.timeout):
            response = self._transport_failure(
                "timeout_before_response", None, transport_response_received=False
            )
        except (ConnectionResetError, BrokenPipeError):
            response = self._transport_failure(
                "connection_reset", None, transport_response_received=False
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
            response = self._transport_failure(
                outcome, None, transport_response_received=False
            )
        return self._finish_attempt(
            request_hash=request.request_hash,
            attempt_number=attempt_number,
            response=response,
            actual_delay=actual_delay,
            retry_after=retry_after,
        )


__all__ = [
    "MAXIMUM_TRANSPORT_ATTEMPTS",
    "MAXIMUM_TRANSPORT_RETRIES",
    "RESPONSE_ORIGIN",
    "RETRY_DELAYS_SECONDS",
    "RecoveryLiveOpenAIChatCompletionsTransportV3",
    "RecoveryLiveTransportAttemptCustodyV3",
    "RecoveryProviderResponseV3",
    "URLOPEN_TIMEOUT_SECONDS",
    "logical_parse_status_v3",
    "terminal_classification_v3",
]
