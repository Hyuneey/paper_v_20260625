"""Authority-field-free rule hashing and accepted-rule materialization."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

from paperworks.contracts.rule_v1 import (
    DelayedResponseRuleV1,
    delayed_response_rule_to_dict,
    parse_delayed_response_rule,
)


class AcceptedRuleError(ValueError):
    """Raised when untrusted authority fields enter materialization."""

    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code
        self.message = message


def canonical_rule_verification_subject_bytes(
    rule: DelayedResponseRuleV1 | Mapping[str, Any],
) -> bytes:
    """Canonical rule bytes excluding only status and verified_rule_hash."""

    if isinstance(rule, DelayedResponseRuleV1):
        document = delayed_response_rule_to_dict(rule)
    else:
        document = copy.deepcopy(dict(rule))
    document.pop("status", None)
    document.pop("verified_rule_hash", None)
    text = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return text.encode("utf-8")


def canonical_rule_verification_subject_sha256(
    rule: DelayedResponseRuleV1 | Mapping[str, Any],
) -> str:
    """Hash all non-authority rule fields for deterministic verifier binding."""

    return hashlib.sha256(canonical_rule_verification_subject_bytes(rule)).hexdigest()


def materialize_accepted_rule(rule: DelayedResponseRuleV1) -> DelayedResponseRuleV1:
    """Create and reparse a new accepted document without authorizing runtime."""

    if rule.status not in {"candidate", "needs_repair"} or rule.verified_rule_hash is not None:
        raise AcceptedRuleError(
            "RULE_AUTHORITY_PRECLAIMED",
            "candidate status and null verified_rule_hash are required",
        )
    subject_hash = canonical_rule_verification_subject_sha256(rule)
    document = copy.deepcopy(delayed_response_rule_to_dict(rule))
    document["status"] = "accepted"
    document["verified_rule_hash"] = subject_hash
    accepted = parse_delayed_response_rule(document)
    if accepted.runtime_authorized:
        raise AcceptedRuleError("RULE_RUNTIME_AUTHORITY", "accepted rule must remain runtime unauthorized")
    return accepted
