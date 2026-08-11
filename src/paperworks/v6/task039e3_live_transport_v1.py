"""Authorized standard-library OpenAI transport for TASK-039E3.

This module is additive to the frozen TASK-039E3-PREP mock harness.  It maps
one stateless Chat Completions request into the already-frozen provider
transport result without ever serializing credentials or request headers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
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


CALL_TIMEOUT_SECONDS = 30
RETRY_DELAYS_SECONDS = (2, 4)
_RETRYABLE = frozenset(
    {"connection_failure", "connection_reset", "timeout_before_response", "http_429", "http_5xx"}
)


@dataclass(frozen=True)
class LiveTransportAttemptCustodyV1:
    sequence_index: int
    request_hash: str
    outcome: str
    status_code: int | None
    response_present: bool
    actual_retry_delay_before_attempt_seconds: float | None
    retry_after_seconds_observed: float | None
    response_id: str | None
    returned_model: str | None
    finish_reason: str | None
    token_usage: Mapping[str, int] | None
    system_fingerprint: str | None

    def to_dict(self) -> dict[str, Any]:
        document = {
            "sequence_index": self.sequence_index,
            "request_hash": self.request_hash,
            "outcome": self.outcome,
            "status_code": self.status_code,
            "response_present": self.response_present,
            "actual_retry_delay_before_attempt_seconds": self.actual_retry_delay_before_attempt_seconds,
            "retry_after_seconds_observed": self.retry_after_seconds_observed,
            "response_id": self.response_id,
            "returned_model": self.returned_model,
            "finish_reason": self.finish_reason,
            "token_usage": dict(self.token_usage) if self.token_usage is not None else None,
            "system_fingerprint": self.system_fingerprint,
        }
        document["record_hash"] = stable_hash_v1(document)
        return document


def parse_retry_after_seconds_v1(value: str | None, *, now: datetime | None = None) -> float | None:
    """Parse a standard Retry-After delta or HTTP date without guessing."""

    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        seconds = float(stripped)
    except ValueError:
        try:
            when = parsedate_to_datetime(stripped)
        except (TypeError, ValueError, OverflowError):
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        seconds = (when - current).total_seconds()
    if seconds < 0 or seconds != seconds or seconds == float("inf"):
        return None
    return seconds


class LiveOpenAIChatCompletionsTransportV1(MockProviderTransportV1):
    """Live transport accepted by the frozen PREP executor via subclassing."""

    def __init__(
        self,
        *,
        api_key: str,
        opener: Callable[..., Any] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
        timeout_seconds: int = CALL_TIMEOUT_SECONDS,
    ) -> None:
        if not isinstance(api_key, str) or not api_key:
            raise TASK039E3PreparationError("blocked_task039e3_credential_unavailable")
        if timeout_seconds != CALL_TIMEOUT_SECONDS:
            raise TASK039E3PreparationError("live timeout differs from frozen E2 timeout")
        self._api_key = api_key
        self._opener = opener
        self._sleeper = sleeper
        self._timeout_seconds = timeout_seconds
        self._calls = 0
        self._request_hashes: list[str] = []
        self._attempt_custody: list[LiveTransportAttemptCustodyV1] = []
        self._retry_pending = False
        self._retry_ordinal = 0
        self._next_delay_seconds: float | None = None
        self._last_retry_after: float | None = None

    @property
    def calls(self) -> int:
        return self._calls

    @property
    def request_hashes(self) -> tuple[str, ...]:
        return tuple(self._request_hashes)

    @property
    def attempt_custody(self) -> tuple[LiveTransportAttemptCustodyV1, ...]:
        return tuple(self._attempt_custody)

    def _before_attempt(self) -> float | None:
        if not self._retry_pending:
            self._retry_ordinal = 0
            return None
        self._retry_ordinal += 1
        if self._retry_ordinal not in {1, 2}:
            raise TASK039E3PreparationError("transport retry budget exceeded")
        delay = self._next_delay_seconds
        if delay is None:
            delay = float(RETRY_DELAYS_SECONDS[self._retry_ordinal - 1])
        self._sleeper(delay)
        return delay

    def _finish_attempt(
        self,
        *,
        request_hash: str,
        response: MockProviderResponseV1,
        actual_delay: float | None,
        retry_after: float | None,
        response_metadata: Mapping[str, Any] | None = None,
    ) -> MockProviderResponseV1:
        metadata = response_metadata or {}
        self._attempt_custody.append(
            LiveTransportAttemptCustodyV1(
                sequence_index=len(self._attempt_custody),
                request_hash=request_hash,
                outcome=response.outcome,
                status_code=response.status_code,
                response_present=response.response_present,
                actual_retry_delay_before_attempt_seconds=actual_delay,
                retry_after_seconds_observed=retry_after,
                response_id=response.response_id,
                returned_model=response.model,
                finish_reason=response.finish_reason,
                token_usage=response.token_usage,
                system_fingerprint=(
                    str(metadata["system_fingerprint"])
                    if metadata.get("system_fingerprint") is not None
                    else None
                ),
            )
        )
        retryable = not response.response_present and response.outcome in _RETRYABLE
        self._retry_pending = retryable
        self._next_delay_seconds = retry_after if response.outcome == "http_429" else None
        self._last_retry_after = retry_after
        if not retryable:
            self._retry_ordinal = 0
            self._next_delay_seconds = None
        return response

    def send(self, request: FrozenProviderRequestV1) -> MockProviderResponseV1:
        if not isinstance(request, FrozenProviderRequestV1):
            raise TASK039E3PreparationError("live transport requires frozen request")
        actual_delay = self._before_attempt()
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
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                )
            try:
                document = json.loads(raw.decode("utf-8"))
                choices = document["choices"]
                if not isinstance(choices, list) or len(choices) != 1:
                    raise ValueError("expected exactly one choice")
                choice = choices[0]
                message = choice["message"]
                returned_model = document["model"]
                response_id = document["id"]
                if returned_model != EXACT_MODEL:
                    response = MockProviderResponseV1(
                        False, "model_identity_integrity", 200, None, None
                    )
                    return self._finish_attempt(
                        request_hash=request.request_hash,
                        response=response,
                        actual_delay=actual_delay,
                        retry_after=None,
                        response_metadata=document,
                    )
                refusal_value = message.get("refusal")
                refusal = isinstance(refusal_value, str) and bool(refusal_value.strip())
                content = None if refusal else message.get("content")
                if content is not None and not isinstance(content, str):
                    raise ValueError("message content is not text")
                usage_raw = document.get("usage")
                usage = None
                if isinstance(usage_raw, Mapping):
                    usage = MappingProxyType(
                        {
                            str(key): int(value)
                            for key, value in usage_raw.items()
                            if isinstance(value, int) and not isinstance(value, bool)
                        }
                    )
                response = MockProviderResponseV1(
                    True,
                    "provider_refusal" if refusal else "successful_response",
                    200,
                    returned_model,
                    content,
                    refusal=refusal,
                    finish_reason=choice.get("finish_reason"),
                    response_id=response_id,
                    token_usage=usage,
                )
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                    response_metadata=document,
                )
            except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
                response = MockProviderResponseV1(
                    True,
                    "schema_invalid_response",
                    200,
                    EXACT_MODEL,
                    None,
                    finish_reason="invalid_response",
                    response_id=stable_hash_v1({"invalid_response": self._calls}),
                )
                return self._finish_attempt(
                    request_hash=request.request_hash,
                    response=response,
                    actual_delay=actual_delay,
                    retry_after=None,
                )
        except HTTPError as exc:
            status = int(exc.code)
            if status == 429:
                outcome = "http_429"
                retry_after = parse_retry_after_seconds_v1(exc.headers.get("Retry-After"))
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
            response=response,
            actual_delay=actual_delay,
            retry_after=retry_after,
        )


__all__ = [
    "CALL_TIMEOUT_SECONDS",
    "LiveOpenAIChatCompletionsTransportV1",
    "LiveTransportAttemptCustodyV1",
    "parse_retry_after_seconds_v1",
]
