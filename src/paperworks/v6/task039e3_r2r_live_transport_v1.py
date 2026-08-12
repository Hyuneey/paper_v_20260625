"""R2R live transport with bounded private HTTP-error custody.

This additive transport preserves the frozen Recovery V3 request, response,
retry, and terminal-classification semantics.  Its only behavioral extension
is forensic custody for non-200 HTTP responses: at most 64 KiB of body bytes
are retained privately, with a one-byte truncation probe, while a separate
sanitized projection contains no raw provider error text.

The module performs no I/O at import time.  Tests and offline audits inject an
opener; future network authority remains external to this module.
"""

from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from hashlib import sha256
import json
import time
from typing import Any, BinaryIO, Callable, Mapping
from urllib.error import HTTPError
from urllib.request import urlopen

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import FrozenProviderRequestV1
from paperworks.v6.task039e3_recovery_live_transport_v3 import (
    MAXIMUM_TRANSPORT_RETRIES,
    RESPONSE_ORIGIN,
    RETRY_DELAYS_SECONDS,
    URLOPEN_TIMEOUT_SECONDS,
    RecoveryLiveOpenAIChatCompletionsTransportV3,
    RecoveryProviderResponseV3,
    terminal_classification_v3,
)


MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES = 64 * 1024
HTTP_ERROR_BODY_READ_LIMIT_BYTES = MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES + 1

_RETRYABLE_OUTCOMES = frozenset(
    {
        "connection_failure",
        "connection_reset",
        "timeout_before_response",
        "http_429",
        "http_5xx",
    }
)


def _header(headers: Any, name: str) -> str | None:
    if headers is None:
        return None
    getter = getattr(headers, "get", None)
    if not callable(getter):
        return None
    value = getter(name)
    if value is None and isinstance(headers, Mapping):
        expected = name.casefold()
        value = next(
            (
                candidate
                for key, candidate in headers.items()
                if str(key).casefold() == expected
            ),
            None,
        )
    if value is None:
        return None
    # Response headers are metadata, but still keep their retained form bounded.
    return str(value)[:1024]


def _content_length(headers: Any) -> int | None:
    value = _header(headers, "Content-Length")
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _provider_error_fields(
    retained: bytes, *, truncated: bool
) -> tuple[bool, str | None, str | None, str | None, str | None]:
    """Parse only a complete bounded error object; never parse a truncated prefix."""

    if not retained or truncated:
        return False, None, None, None, None
    try:
        document = json.loads(retained.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False, None, None, None, None
    if not isinstance(document, Mapping) or not isinstance(
        document.get("error"), Mapping
    ):
        return False, None, None, None, None
    error = document["error"]

    def text(field: str) -> str | None:
        value = error.get(field)
        return value if isinstance(value, str) else None

    message = text("message")
    return (
        True,
        text("type"),
        text("code"),
        text("param"),
        sha256(message.encode("utf-8")).hexdigest() if message is not None else None,
    )


@dataclass(frozen=True)
class PrivateHTTPErrorCustodyV1:
    """Bounded private custody for one observed non-200 HTTP response."""

    status_code: int
    transport_outcome: str
    body_read_status: str
    retained_error_body: bytes
    retained_body_sha256: str
    full_body_sha256: str | None
    retained_body_byte_length: int
    observed_body_byte_length: int
    original_body_byte_length_if_known: int | None
    body_truncated: bool
    content_type: str | None
    provider_error_payload_received: bool
    provider_error_object_parseable: bool
    provider_error_type: str | None
    provider_error_code: str | None
    provider_error_param: str | None
    provider_error_message_hash: str | None
    x_request_id: str | None
    x_client_request_id: str | None
    body_read_error_class: str | None = None

    def __post_init__(self) -> None:
        if self.body_read_status not in {"complete", "truncated", "read_failed"}:
            raise ValueError("HTTP error body read status differs")
        if len(self.retained_error_body) > MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES:
            raise ValueError("retained HTTP error body exceeds 64 KiB")
        if self.retained_body_byte_length != len(self.retained_error_body):
            raise ValueError("retained HTTP error body length differs")
        if self.retained_body_sha256 != sha256(self.retained_error_body).hexdigest():
            raise ValueError("retained HTTP error body hash differs")
        if self.body_truncated != (self.body_read_status == "truncated"):
            raise ValueError("HTTP error truncation status differs")
        if self.full_body_sha256 is not None and self.body_truncated:
            raise ValueError("truncated HTTP error cannot claim a full-body hash")
        if self.full_body_sha256 is not None and (
            self.full_body_sha256 != self.retained_body_sha256
        ):
            raise ValueError("complete HTTP error body hash differs")
        if self.provider_error_object_parseable and not (
            self.provider_error_payload_received and not self.body_truncated
        ):
            raise ValueError("parsed provider error requires a complete payload")

    def _common_content(self) -> dict[str, Any]:
        return {
            "status_code": self.status_code,
            "transport_outcome": self.transport_outcome,
            "body_read_status": self.body_read_status,
            "retained_body_sha256": self.retained_body_sha256,
            "full_body_sha256": self.full_body_sha256,
            "retained_body_byte_length": self.retained_body_byte_length,
            "observed_body_byte_length": self.observed_body_byte_length,
            "original_body_byte_length_if_known": (
                self.original_body_byte_length_if_known
            ),
            "body_truncated": self.body_truncated,
            "content_type": self.content_type,
            "provider_error_payload_received": self.provider_error_payload_received,
            "provider_error_object_parseable": self.provider_error_object_parseable,
            "provider_error_message_hash": self.provider_error_message_hash,
            "x_request_id": self.x_request_id,
            "x_client_request_id": self.x_client_request_id,
            "body_read_error_class": self.body_read_error_class,
            "model_completion_response_present": False,
            "scientific_response_present": False,
        }

    def to_public_dict(self) -> dict[str, Any]:
        """Return metadata and hashes only; raw body bytes never cross this seam."""

        document = self._common_content()
        # Provider request identifiers remain private and correlatable.  The
        # public projection binds them without publishing their raw values.
        for name in ("x_request_id", "x_client_request_id"):
            value = document.pop(name)
            document[f"{name}_hash"] = (
                sha256(value.encode("utf-8")).hexdigest()
                if value is not None
                else None
            )
        for name, value in (
            ("provider_error_type", self.provider_error_type),
            ("provider_error_code", self.provider_error_code),
            ("provider_error_param", self.provider_error_param),
        ):
            document[f"{name}_hash"] = (
                sha256(value.encode("utf-8")).hexdigest()
                if value is not None
                else None
            )
        document["record_hash"] = stable_hash_v1(document)
        return document

    def to_private_dict(self) -> dict[str, Any]:
        document = self._common_content()
        document.update(
            {
                "provider_error_type": self.provider_error_type,
                "provider_error_code": self.provider_error_code,
                "provider_error_param": self.provider_error_param,
            }
        )
        document["retained_error_body_base64"] = b64encode(
            self.retained_error_body
        ).decode("ascii")
        document["record_hash"] = stable_hash_v1(document)
        return document


def _capture_http_error(
    *, stream: BinaryIO, headers: Any, status_code: int, outcome: str
) -> PrivateHTTPErrorCustodyV1:
    read_error_class: str | None = None
    try:
        observed = stream.read(HTTP_ERROR_BODY_READ_LIMIT_BYTES)
        if not isinstance(observed, (bytes, bytearray)):
            raise TypeError("HTTP error body reader did not return bytes")
        probe = bytes(observed[:HTTP_ERROR_BODY_READ_LIMIT_BYTES])
        truncated = len(probe) > MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES
        retained = probe[:MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES]
        read_status = "truncated" if truncated else "complete"
    except Exception as exc:  # Preserve original HTTP outcome if body custody fails.
        probe = b""
        retained = b""
        truncated = False
        read_status = "read_failed"
        read_error_class = type(exc).__name__
    declared_length = _content_length(headers)
    original_length = (
        declared_length
        if declared_length is not None
        else len(probe)
        if not truncated and read_status == "complete"
        else None
    )
    parseable, error_type, error_code, error_param, message_hash = (
        _provider_error_fields(retained, truncated=truncated)
    )
    retained_hash = sha256(retained).hexdigest()
    full_body_observed = (
        read_status == "complete"
        and not truncated
        and (declared_length is None or declared_length == len(probe))
    )
    return PrivateHTTPErrorCustodyV1(
        status_code=status_code,
        transport_outcome=outcome,
        body_read_status=read_status,
        retained_error_body=retained,
        retained_body_sha256=retained_hash,
        full_body_sha256=retained_hash if full_body_observed else None,
        retained_body_byte_length=len(retained),
        observed_body_byte_length=len(probe),
        original_body_byte_length_if_known=original_length,
        body_truncated=truncated,
        content_type=_header(headers, "Content-Type"),
        provider_error_payload_received=bool(probe),
        provider_error_object_parseable=parseable,
        provider_error_type=error_type,
        provider_error_code=error_code,
        provider_error_param=error_param,
        provider_error_message_hash=message_hash,
        x_request_id=_header(headers, "X-Request-Id"),
        x_client_request_id=_header(headers, "X-Client-Request-Id"),
        body_read_error_class=read_error_class,
    )


class _BoundedNon200Handle:
    def __init__(
        self,
        handle: Any,
        capture: Callable[[PrivateHTTPErrorCustodyV1], None],
    ) -> None:
        self._handle = handle
        self._capture = capture
        self.status = int(handle.status)
        self.headers = getattr(handle, "headers", None)
        self._body: bytes | None = None

    def __enter__(self) -> "_BoundedNon200Handle":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        close = getattr(self._handle, "close", None)
        if callable(close):
            close()

    def read(self) -> bytes:
        if self._body is None:
            outcome = "http_5xx" if self.status >= 500 else f"http_{self.status}"
            custody = _capture_http_error(
                stream=self._handle,
                headers=self.headers,
                status_code=self.status,
                outcome=outcome,
            )
            self._capture(custody)
            self._body = custody.retained_error_body
        return self._body


@dataclass(frozen=True)
class R2RLiveTransportAttemptCustodyV1:
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
    private_http_error: PrivateHTTPErrorCustodyV1 | None

    def _content(self, *, private: bool) -> dict[str, Any]:
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
            "http_error_custody": (
                self.private_http_error.to_private_dict()
                if private and self.private_http_error is not None
                else self.private_http_error.to_public_dict()
                if self.private_http_error is not None
                else None
            ),
        }
        return document

    def to_dict(self) -> dict[str, Any]:
        """Private provider-ledger representation."""

        document = self._content(private=True)
        document["record_hash"] = stable_hash_v1(document)
        return document

    def to_public_dict(self) -> dict[str, Any]:
        document = self._content(private=False)
        document["record_hash"] = stable_hash_v1(document)
        return document


class R2RLiveOpenAIChatCompletionsTransportV1(
    RecoveryLiveOpenAIChatCompletionsTransportV3
):
    """Frozen V3 transport plus bounded private non-200 error custody."""

    def __init__(
        self,
        *,
        api_key: str,
        opener: Callable[..., Any] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
        timeout_seconds: float = URLOPEN_TIMEOUT_SECONDS,
    ) -> None:
        self._raw_opener = opener
        self._pending_http_error: PrivateHTTPErrorCustodyV1 | None = None
        super().__init__(
            api_key=api_key,
            opener=self._bounded_opener,
            sleeper=sleeper,
            timeout_seconds=timeout_seconds,
        )

    def _store_http_error(self, custody: PrivateHTTPErrorCustodyV1) -> None:
        if self._pending_http_error is not None:
            raise ValueError("multiple HTTP error observations in one attempt")
        self._pending_http_error = custody

    def _bounded_opener(self, *args: Any, **kwargs: Any) -> Any:
        try:
            handle = self._raw_opener(*args, **kwargs)
        except HTTPError as exc:
            status = int(exc.code)
            outcome = (
                "http_429"
                if status == 429
                else "http_5xx"
                if status >= 500
                else f"http_{status}"
            )
            custody = _capture_http_error(
                stream=exc,
                headers=exc.headers,
                status_code=status,
                outcome=outcome,
            )
            self._store_http_error(custody)
            raise
        status = int(getattr(handle, "status", 200))
        if status != 200:
            return _BoundedNon200Handle(handle, self._store_http_error)
        return handle

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
        http_error = self._pending_http_error
        self._pending_http_error = None
        if response.status_code is not None and response.status_code != 200:
            if http_error is None:
                raise ValueError("non-200 response lacks bounded HTTP-error custody")
            if (
                http_error.status_code != response.status_code
                or http_error.transport_outcome != response.outcome
            ):
                raise ValueError("HTTP-error custody disagrees with transport outcome")
        elif http_error is not None:
            raise ValueError("HTTP-error custody attached to a non-HTTP outcome")
        self._attempt_custody.append(
            R2RLiveTransportAttemptCustodyV1(
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
                private_http_error=http_error,
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

    def send(self, request: FrozenProviderRequestV1) -> RecoveryProviderResponseV3:
        if self._pending_http_error is not None:
            raise ValueError("stale HTTP-error custody before transport attempt")
        return super().send(request)


__all__ = [
    "HTTP_ERROR_BODY_READ_LIMIT_BYTES",
    "MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES",
    "PrivateHTTPErrorCustodyV1",
    "R2RLiveOpenAIChatCompletionsTransportV1",
    "R2RLiveTransportAttemptCustodyV1",
]
