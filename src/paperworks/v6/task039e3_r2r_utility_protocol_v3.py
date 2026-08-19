"""Final additive closure for the TASK-039E3 R2R utility protocol.

This module is metadata-only and synthetic/offline.  It closes two authority
gaps in Protocol V2: opportunity-count custody and fail-closed input/state
ordering.  It does not load HAI files, read labels, execute real utility,
grant runtime authority, or contact a provider.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
import statistics
from typing import Any, Mapping, Sequence

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_protocol_v2 import (
    CROSS_SOURCE_ISOLATION_RADIUS_SECONDS,
    DATASET_MANIFEST_ID,
    EXECUTABLE_EQUIVALENCE_HASH,
    INNER_SPLIT_ID,
    MINIMUM_STABILITY_FRACTION,
    OUTER_SPLIT_ID,
    SOURCE_POST_WINDOW,
    SOURCE_PRE_WINDOW,
    SOURCE_REFRACTORY_SECONDS,
    SUPPORTED_HORIZONS,
    TARGET_BASELINE_WINDOW,
    TARGET_RESPONSE_WINDOW,
    UTILITY_SOURCE_UNIVERSE_V2,
)


TASK_ID = "TASK-039E3-R2R-UTILITY-PROTOCOL-V3-REOPEN-AND-FINAL-REMEDIATION"
PROTOCOL_ID = "BASE_V1_PLUS_REMEDIATION_V2_PLUS_FINAL_CLOSURE_V3"
SCHEMA_VERSION = "3.0.0"
BASE_COMMIT = "5d6a7b74bf3f43efc0edff44c3ed32fb130cffe9"
REOPEN_AUTHORIZATION_HASH = "dffef0fcc2bdd5d6c0473cac027c81b050c2f9f0bbe74c6b577875de827c2f5a"

V1_COMMIT_A = "0eec09c662ecc1c78daa5f661c2471aba69cf905"
V1_COMMIT_B = "c021768fc29a4560bd1bc52f5ed61462731be1c7"
V1_BUNDLE = "189c662b83e82ed47137d7e67f52ff97580662ef65e696a5d5715d2dddaae86d"
V1_RECEIPT = "f6db67c4ec4c3f64f0acc8031e27f583fc3192029170184e42dd721dbaf15949"
V2_COMMIT_A = "6c63a9a8410d083c8b0e71c344d799284f02941b"
V2_COMMIT_B = "4f9393fd59f23b8093c8fc2b7c95bf3f57ec5c22"
V2_CANONICAL_AUTHORITY = "9e23c16e7c85f825e19dd30da96a17b88e3daf06763eb98c3bdba86bea189d44"
V2_SOURCE_FREEZE = "6ed4f60018993c378e2388565d00a33f189f74d86fc5017468f9a30e6b4a1726"
V2_BUNDLE = "5880ebff1fbda2004dfa3d955376b88d21972721b5287bc5fd62b9e71a6df2cb"
V2_RECEIPT = "46ef239e01697bd54eec3eea5fb9725fe07396ceaf24c82dbb0da1606223f00d"
BLOCKED_REAUDIT_A = "008a34d6ddce536c65ab36322389a34580710f18"
BLOCKED_REAUDIT_B = "4213963e5c3abc9f97b45bb183accb0fc43297be"
BLOCKED_REAUDIT_BUNDLE = "883e32ef7c035707257f0b3596aa5ab1a5df8364f8dab70ffda32c818b1dacac"
BLOCKED_REAUDIT_RECEIPT = "dc0199685029ba5d8e65761ef7b8bddb21e2563b0c65d5927366ab001b106ba5"

OPEN_BLOCKERS = (
    "BLOCKER_UTILITY_PROTOCOL_ABSTENTION_OPPORTUNITY_ENUMERATION_UNDERDEFINED",
    "BLOCKER_SYNTHETIC_INPUT_AND_STATE_FAIL_CLOSED_GAPS",
)
UTILITY_OPPORTUNITY_SAMPLING_POLICY = "FULL_CENSUS_NO_FIXED_SAMPLE_SIZE"
UTILITY_SOURCE_UNIVERSE_V3 = tuple(UTILITY_SOURCE_UNIVERSE_V2)
TARGET_EVALUATION_STATES = frozenset(
    {"evaluated_expected_response", "evaluated_anomaly", "abstain"}
)
SOURCE_DIRECTIONS = frozenset({"step_up", "step_down"})
TARGET_DIRECTIONS = frozenset({"increase", "decrease"})
NUMERIC_PARAMETER_ROLES = frozenset(
    {"source_step_threshold", "source_stability_tolerance", "target_noise_scale"}
)
SOURCE_UNAVAILABLE_REASONS = frozenset(
    {"insufficient_source_pre_window", "incomplete_source_post_window"}
)
TARGET_UNAVAILABLE_REASONS = frozenset(
    {"file_boundary", "split_boundary", "incomplete_target_response_window"}
)
FILE_ROW_COUNTS = {"hai-test1.csv": 54_000, "hai-test2.csv": 230_400}
FILE_SPLITS = {"hai-test1.csv": INNER_SPLIT_ID, "hai-test2.csv": OUTER_SPLIT_ID}

HAI_DATASET_MANIFEST_HASH = DATASET_MANIFEST_ID
HAI_CSV_STRUCTURE_REPORT_HASH = "d4f43034e9402806a4f34da943a1e39191503f8f54465d6d1f98b9cdc31bb7c9"
C0_CONFIG_HASH = "d703d7ec0b87694b53cd4d2b3768ca32efca00cd3bdc3ce12933fc6c8c36d34f"
BR2_CONFIG_HASH = "c101a4cd988b926d160b527d20afe9cdd2590093f9aeb820897dea77dd15783b"
UTILITY_VIEW_ID = "4445c98c0a22e4f53a5679b39b52a984adf342eb02fe893d5d53256ea2133e24"
FEATURE_ORDER_HASH = "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"
SOURCE_IDENTITY_HASH = "0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234"

SOURCE_METADATA_HASHES: Mapping[str, str] = {
    "P1_FCV01D": "9392ea74f3cc9a1896f063369bb33b4ba19c061019d4ba59ed8f92d45dd25047",
    "P1_FCV01Z": "50e198ece814e7e60d92dd610b1b732e19505adcab8502f0de82bb859d08a188",
    "P1_FCV02D": "ad1b49e576376ffb662194ba1ad10cee037540dcf31fe765b1ddd24233b83176",
    "P1_FCV02Z": "1d78be71282f3335e47229086643fe0a0fc54e52e0162ca94cc629847608cf6e",
    "P1_FCV03D": "4025ceb0763f253ad259b5129723831c948beba17ef28ce77f73f3a842eee7d5",
    "P1_FCV03Z": "de4de681de5de8d0eaf2032799d27d8d05e23e3bd7975e45aa856c07fe064b9b",
    "P1_LCV01D": "ddb7a3c679c13bb4f017ccf54ee0fa01b6d71c897e2aabb5be7373f60e5b6e80",
    "P1_LCV01Z": "c8cbc2781b175b27748d9f20cc7b8621a82fe47ff635ab55725a5bec4bcc2838",
    "P1_PCV01D": "12e05bb6ad57d0ec866f1e483f1a00aeea938204f7337c8554f56ae592de5d34",
    "P1_PCV01Z": "7c115fe1e3f4fd6a0eb248e33c3ac6a72853e317e81b798c55416e4907f22a58",
    "P1_PCV02Z": "0f7b89d6260c5dba88c44df760a0a187fbfa07d3d9048c6358fa5c6276324303",
    "P1_PP04": "7c3123c79d06fb4bcfec9ac5e765e5066b211efe202cfade84d37583f8714be7",
}
SOURCE_ROLES: Mapping[str, str] = {
    "P1_FCV01D": "control_command", "P1_FCV01Z": "actuator_feedback",
    "P1_FCV02D": "control_command", "P1_FCV02Z": "actuator_feedback",
    "P1_FCV03D": "control_command", "P1_FCV03Z": "actuator_feedback",
    "P1_LCV01D": "control_command", "P1_LCV01Z": "actuator_feedback",
    "P1_PCV01D": "control_command", "P1_PCV01Z": "actuator_feedback",
    "P1_PCV02Z": "actuator_feedback", "P1_PP04": "actuator_state",
}
TARGET_METADATA_HASHES: Mapping[str, str] = {
    "P1_FT01": "baa8d7036a5bbec1998ca3ff3e2d15c0ef5653d94f526bfd181dc26820ca27de",
    "P1_FT01Z": "4332d406b38eff043621414acc036b945c401c476ae52ee35c292be7eaeb7430",
    "P1_FT02": "e129c2581d1b0fe18c72b1286a373f827aa614eb888c542a8f311767b77797a2",
    "P1_FT02Z": "6e308775e16f2fa38e983d3e2000dbd6a5975f393c35e98b559f2d5412ce6c5e",
    "P1_FT03": "bccb58331d54e5d40d22383f8656880ab623f10bc4060121549e115a1eca9bac",
    "P1_FT03Z": "68e8a4864eed627952c81befcb1dd0e526c6f201a03576d48da639ba48fc3ced",
    "P1_LIT01": "df48559c7d96ddaacb3ec033bee427a37c7024da05c620ab7de3a231cd7f21e2",
    "P1_PIT01": "9a45b46b48c52145d118e05c94a9d6f2f4d77509c41a0fd169e85c3b43884c62",
    "P1_PIT02": "3fd677b9e1a68a623918488c89d4b8ef7e8c07dd98c15601bd03bd4f4f886f91",
    "P1_TIT01": "cea102e2c1e20bb37e183099963024d23b573f589ebe316007cd34c67b7f21b0",
    "P1_TIT02": "59aa8a380be85bb29fbe28fcd4afe8ce7fd61e9ba242526ad5d52cebccf6e7d8",
    "P1_TIT03": "cee7b367fd1d3210fbe2686fc780a15496aa70a65850552873a8e34849dec333",
}


class UtilityProtocolV3Error(ValueError):
    """A fail-closed Protocol V3 authority or input violation."""


@dataclass(frozen=True)
class NumericParameterV3:
    role: str
    value: float

    def __post_init__(self) -> None:
        if self.role not in NUMERIC_PARAMETER_ROLES:
            raise UtilityProtocolV3Error("numeric parameter role is unknown")
        observed = _strict_finite(
            self.value,
            self.role,
            positive=self.role in {"source_step_threshold", "target_noise_scale"},
        )
        if self.role == "source_stability_tolerance" and observed < 0:
            raise UtilityProtocolV3Error("source stability tolerance must be nonnegative")


def _strict_int(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise UtilityProtocolV3Error(f"{name} must be an integer object at least {minimum}")
    return value


def _strict_finite(value: object, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or type(value) not in {int, float}:
        raise UtilityProtocolV3Error(f"{name} must be a real numeric object")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise UtilityProtocolV3Error(f"{name} is outside its finite numeric domain")
    return result


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise UtilityProtocolV3Error(f"{name} must be a SHA-256 identity")
    try:
        int(value, 16)
    except ValueError as exc:
        raise UtilityProtocolV3Error(f"{name} must be hexadecimal") from exc
    return value


def _verify_self_hash(document: Mapping[str, Any], key: str = "artifact_hash", expected: str | None = None) -> str:
    observed = document.get(key)
    if not isinstance(observed, str):
        raise UtilityProtocolV3Error(f"{key} is required")
    payload = {name: value for name, value in document.items() if name != key}
    if stable_hash_v1(payload) != observed or (expected is not None and observed != expected):
        raise UtilityProtocolV3Error("artifact self-hash or authority differs")
    return observed


def validate_reopen_authority_v3(document: Mapping[str, Any]) -> str:
    """Validate the user-approved, scope-limited V3 reopen authority."""

    observed = _verify_self_hash(document, expected=REOPEN_AUTHORIZATION_HASH)
    if (
        document.get("base_commit") != BASE_COMMIT
        or document.get("status") != "authorized_task039e3_r2r_utility_protocol_v3_final_remediation"
        or tuple(document.get("exact_open_blockers", ())) != OPEN_BLOCKERS
        or document.get("authorization_decision_date") != "2026-08-19"
    ):
        raise UtilityProtocolV3Error("V3 reopen decision differs")
    historical = document.get("historical_stop")
    prohibited = document.get("prohibited_authorities")
    if not isinstance(historical, Mapping) or historical.get("prior_status") != "NONE_AUTHORIZED_STOP":
        raise UtilityProtocolV3Error("historical stop custody is missing")
    if not isinstance(prohibited, Mapping) or not prohibited or any(value is not False for value in prohibited.values()):
        raise UtilityProtocolV3Error("a prohibited V3 authority was granted")
    blocked = document.get("blocked_focused_reaudit")
    v2 = document.get("canonical_v2")
    v1 = document.get("original_v1")
    if not isinstance(blocked, Mapping) or not isinstance(v2, Mapping) or not isinstance(v1, Mapping):
        raise UtilityProtocolV3Error("prior lineage bindings are missing")
    expected = (
        (blocked, "audit_commit_a", BLOCKED_REAUDIT_A),
        (blocked, "audit_commit_b", BLOCKED_REAUDIT_B),
        (blocked, "bundle_hash", BLOCKED_REAUDIT_BUNDLE),
        (blocked, "receipt_hash", BLOCKED_REAUDIT_RECEIPT),
        (v2, "authority_hash", V2_CANONICAL_AUTHORITY),
        (v2, "source_freeze_hash", V2_SOURCE_FREEZE),
        (v2, "bundle_hash", V2_BUNDLE),
        (v2, "receipt_hash", V2_RECEIPT),
        (v1, "bundle_hash", V1_BUNDLE),
        (v1, "receipt_hash", V1_RECEIPT),
    )
    if any(mapping.get(field) != value for mapping, field, value in expected):
        raise UtilityProtocolV3Error("prior utility authority binding differs")
    return observed


@dataclass(frozen=True)
class FeatureSchemaEntryV3:
    feature_name: str
    role: str
    expected_raw_representation: str
    expected_logical_type: str
    unit_identity: str | None
    missing_value_policy: str
    finite_value_policy: str
    metadata_authority_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.feature_name, str) or not self.feature_name:
            raise UtilityProtocolV3Error("feature name is required")
        if self.role not in {"source", "target", "source_and_target"}:
            raise UtilityProtocolV3Error("feature role is unknown")
        if self.expected_raw_representation != "strict_decimal_numeric_token":
            raise UtilityProtocolV3Error("raw feature representation differs")
        if self.expected_logical_type != "finite_real_scalar":
            raise UtilityProtocolV3Error("logical feature type differs")
        if self.unit_identity is not None:
            raise UtilityProtocolV3Error("unit identity is unbound and must remain null")
        if self.missing_value_policy != "PROHIBITED_NO_AUTHORIZED_MISSING_TOKEN":
            raise UtilityProtocolV3Error("feature missing-value policy differs")
        if self.finite_value_policy != "FINITE_REQUIRED_FAIL_CLOSED":
            raise UtilityProtocolV3Error("feature finite-value policy differs")
        _sha(self.metadata_authority_hash, "metadata_authority_hash")

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_logical_type": self.expected_logical_type,
            "expected_raw_representation": self.expected_raw_representation,
            "feature_name": self.feature_name,
            "finite_value_policy": self.finite_value_policy,
            "metadata_authority_hash": self.metadata_authority_hash,
            "missing_value_policy": self.missing_value_policy,
            "role": self.role,
            "unit_identity": self.unit_identity,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "FeatureSchemaEntryV3":
        expected = {
            "expected_logical_type", "expected_raw_representation", "feature_name",
            "finite_value_policy", "metadata_authority_hash", "missing_value_policy",
            "role", "unit_identity",
        }
        if set(value) != expected:
            raise UtilityProtocolV3Error("feature schema entry fields differ")
        return cls(**value)


@dataclass(frozen=True)
class P1UtilityFeatureSchemaV3:
    feature_entries: tuple[FeatureSchemaEntryV3, ...]
    required_source_count: int
    required_target_count: int
    timestamp_field: Mapping[str, Any]
    label_field: Mapping[str, Any]
    metadata_authorities: Mapping[str, str]

    def __post_init__(self) -> None:
        names = tuple(entry.feature_name for entry in self.feature_entries)
        if len(names) != len(set(names)) or names != tuple(sorted(names)):
            raise UtilityProtocolV3Error("feature entries must be unique and canonical")
        sources = {entry.feature_name for entry in self.feature_entries if entry.role in {"source", "source_and_target"}}
        targets = {entry.feature_name for entry in self.feature_entries if entry.role in {"target", "source_and_target"}}
        if sources != set(UTILITY_SOURCE_UNIVERSE_V3) or len(sources) != self.required_source_count != 12:
            raise UtilityProtocolV3Error("feature schema does not bind all 12 sources")
        if len(targets) != self.required_target_count or self.required_target_count != 10:
            raise UtilityProtocolV3Error("feature schema target scope differs")
        if self.timestamp_field != {
            "feature_name": "timestamp",
            "expected_raw_representation": "ISO-8601-compatible source timestamp",
            "expected_logical_type": "timestamp",
            "timezone": "source_unspecified",
            "metadata_authority_hash": HAI_DATASET_MANIFEST_HASH,
        }:
            raise UtilityProtocolV3Error("timestamp contract differs")
        if self.label_field != {
            "feature_name": "label",
            "expected_raw_representation": "exact token 0 or 1",
            "expected_logical_type": "strict_binary_integer",
            "encoding": {"normal": 0, "attack": 1},
            "metadata_authority_hash": HAI_DATASET_MANIFEST_HASH,
            "separate_from_feature_parser": True,
        }:
            raise UtilityProtocolV3Error("label contract differs")
        required_authorities = {
            "dataset_manifest": HAI_DATASET_MANIFEST_HASH,
            "csv_structure_report": HAI_CSV_STRUCTURE_REPORT_HASH,
            "candidate_universe_config": C0_CONFIG_HASH,
            "br2_continuous_step_config": BR2_CONFIG_HASH,
            "executable_equivalence": EXECUTABLE_EQUIVALENCE_HASH,
            "utility_view": UTILITY_VIEW_ID,
            "feature_order": FEATURE_ORDER_HASH,
            "source_identity": SOURCE_IDENTITY_HASH,
        }
        if dict(self.metadata_authorities) != required_authorities:
            raise UtilityProtocolV3Error("feature schema authority closure differs")

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "p1_utility_feature_schema_v3",
            "feature_entries": [entry.to_dict() for entry in self.feature_entries],
            "label_field": dict(self.label_field),
            "metadata_authorities": dict(self.metadata_authorities),
            "missing_or_ambiguous_feature_type_count": 0,
            "required_source_count": self.required_source_count,
            "required_target_count": self.required_target_count,
            "schema_version": SCHEMA_VERSION,
            "timestamp_field": dict(self.timestamp_field),
            "type_authority_basis": "COMMITTED_CONTINUOUS_STEP_NUMERIC_SEMANTICS_AND_VARIABLE_METADATA_BINDINGS",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "P1UtilityFeatureSchemaV3":
        observed = _verify_self_hash(value)
        entries = value.get("feature_entries")
        if not isinstance(entries, list):
            raise UtilityProtocolV3Error("feature entries must be a list")
        result = cls(
            tuple(FeatureSchemaEntryV3.from_mapping(item) for item in entries),
            value.get("required_source_count"),
            value.get("required_target_count"),
            value.get("timestamp_field"),
            value.get("label_field"),
            value.get("metadata_authorities"),
        )
        if observed != result.artifact_hash or value != result.to_dict():
            raise UtilityProtocolV3Error("feature schema document differs")
        return result


def build_p1_utility_feature_schema_v3(
    *,
    dataset_manifest: Mapping[str, Any],
    csv_structure_report: Mapping[str, Any],
    c0_config: Mapping[str, Any],
    br2_config: Mapping[str, Any],
    executable_equivalence: Mapping[str, Any],
) -> P1UtilityFeatureSchemaV3:
    """Derive the exact metadata-only 22-feature evaluator schema."""

    _verify_self_hash(dataset_manifest, expected=HAI_DATASET_MANIFEST_HASH)
    _verify_self_hash(csv_structure_report, key="report_hash", expected=HAI_CSV_STRUCTURE_REPORT_HASH)
    _verify_self_hash(c0_config, key="config_hash", expected=C0_CONFIG_HASH)
    _verify_self_hash(br2_config, key="config_hash", expected=BR2_CONFIG_HASH)
    _verify_self_hash(executable_equivalence, expected=EXECUTABLE_EQUIVALENCE_HASH)
    if (
        dataset_manifest.get("dataset_name") != "HAI"
        or dataset_manifest.get("dataset_version_or_edition") != "23.05"
        or dataset_manifest.get("nominal_sampling_interval_seconds") != 1.0
        or csv_structure_report.get("all_headers_aligned") is not True
        or csv_structure_report.get("feature_names_hash") != dataset_manifest.get("feature_names_hash")
    ):
        raise UtilityProtocolV3Error("HAI dataset/header authority differs")
    universe = c0_config.get("common_universe")
    eligibility = br2_config.get("frozen_eligibility", {}).get("P1")
    if not isinstance(universe, Mapping) or not isinstance(eligibility, Mapping):
        raise UtilityProtocolV3Error("P1 variable authority is missing")
    source_records = universe.get("source_identities")
    target_records = universe.get("target_identities")
    if not isinstance(source_records, list) or not isinstance(target_records, list):
        raise UtilityProtocolV3Error("variable metadata records are missing")
    observed_sources = {item.get("variable_name"): item for item in source_records}
    observed_targets = {item.get("variable_name"): item for item in target_records}
    if set(observed_sources) != set(SOURCE_METADATA_HASHES):
        raise UtilityProtocolV3Error("12-source metadata authority differs")
    for name, authority_hash in SOURCE_METADATA_HASHES.items():
        item = observed_sources[name]
        if item.get("metadata_record_hash") != authority_hash or item.get("semantic_role") != SOURCE_ROLES[name]:
            raise UtilityProtocolV3Error("source metadata binding differs")
    relation_records = executable_equivalence.get("relation_records")
    if not isinstance(relation_records, list) or len(relation_records) != 42:
        raise UtilityProtocolV3Error("COMMON executable authority must contain 42 relations")
    required_targets = {
        item.get("executable_signature", {}).get("target") for item in relation_records
    }
    if None in required_targets or len(required_targets) != 10:
        raise UtilityProtocolV3Error("COMMON target scope is missing or ambiguous")
    if not required_targets <= set(observed_targets) or not required_targets <= set(TARGET_METADATA_HASHES):
        raise UtilityProtocolV3Error("required target metadata is absent")
    for name in required_targets:
        item = observed_targets[name]
        if item.get("metadata_record_hash") != TARGET_METADATA_HASHES[name] or item.get("semantic_role") != "process_sensor":
            raise UtilityProtocolV3Error("target metadata binding differs")
    br2_sources = {item.get("variable_name") for item in eligibility.get("sources", [])}
    br2_targets = {item.get("variable_name") for item in eligibility.get("targets", [])}
    if br2_sources != set(UTILITY_SOURCE_UNIVERSE_V3) or not required_targets <= br2_targets:
        raise UtilityProtocolV3Error("BR2 continuous numeric eligibility differs")
    entries = []
    for name in sorted(set(UTILITY_SOURCE_UNIVERSE_V3) | required_targets):
        is_source = name in UTILITY_SOURCE_UNIVERSE_V3
        is_target = name in required_targets
        role = "source_and_target" if is_source and is_target else "source" if is_source else "target"
        entries.append(
            FeatureSchemaEntryV3(
                name,
                role,
                "strict_decimal_numeric_token",
                "finite_real_scalar",
                None,
                "PROHIBITED_NO_AUTHORIZED_MISSING_TOKEN",
                "FINITE_REQUIRED_FAIL_CLOSED",
                SOURCE_METADATA_HASHES[name] if is_source else TARGET_METADATA_HASHES[name],
            )
        )
    return P1UtilityFeatureSchemaV3(
        tuple(entries),
        12,
        10,
        {
            "feature_name": "timestamp",
            "expected_raw_representation": "ISO-8601-compatible source timestamp",
            "expected_logical_type": "timestamp",
            "timezone": "source_unspecified",
            "metadata_authority_hash": HAI_DATASET_MANIFEST_HASH,
        },
        {
            "feature_name": "label",
            "expected_raw_representation": "exact token 0 or 1",
            "expected_logical_type": "strict_binary_integer",
            "encoding": {"normal": 0, "attack": 1},
            "metadata_authority_hash": HAI_DATASET_MANIFEST_HASH,
            "separate_from_feature_parser": True,
        },
        {
            "dataset_manifest": HAI_DATASET_MANIFEST_HASH,
            "csv_structure_report": HAI_CSV_STRUCTURE_REPORT_HASH,
            "candidate_universe_config": C0_CONFIG_HASH,
            "br2_continuous_step_config": BR2_CONFIG_HASH,
            "executable_equivalence": EXECUTABLE_EQUIVALENCE_HASH,
            "utility_view": UTILITY_VIEW_ID,
            "feature_order": FEATURE_ORDER_HASH,
            "source_identity": SOURCE_IDENTITY_HASH,
        },
    )


_DECIMAL_TOKEN = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")


def parse_raw_feature_tokens_v3(
    feature_name: str,
    tokens: Sequence[object],
    schema: P1UtilityFeatureSchemaV3,
) -> tuple[float, ...]:
    """Strict raw-boundary parser; never called inside scientific transitions."""

    if not isinstance(schema, P1UtilityFeatureSchemaV3):
        raise UtilityProtocolV3Error("feature schema is required")
    allowed = {entry.feature_name for entry in schema.feature_entries}
    if feature_name not in allowed:
        raise UtilityProtocolV3Error("feature is unknown")
    if isinstance(tokens, (str, bytes)) or not isinstance(tokens, Sequence):
        raise UtilityProtocolV3Error("raw feature tokens must be a sequence")
    result = []
    for token in tokens:
        if type(token) is not str or not _DECIMAL_TOKEN.fullmatch(token):
            raise UtilityProtocolV3Error("raw feature token is malformed")
        value = float(token)
        if not math.isfinite(value):
            raise UtilityProtocolV3Error("raw feature token is nonfinite")
        result.append(value)
    return tuple(result)


def validate_selected_feature_header_v3(
    header: Sequence[object], schema: P1UtilityFeatureSchemaV3
) -> tuple[str, ...]:
    if isinstance(header, (str, bytes)) or not isinstance(header, Sequence):
        raise UtilityProtocolV3Error("selected header must be a sequence")
    values = tuple(header)
    if any(type(item) is not str for item in values) or len(values) != len(set(values)):
        raise UtilityProtocolV3Error("selected header is malformed or duplicated")
    expected = ("timestamp", *(entry.feature_name for entry in schema.feature_entries))
    if values != expected:
        raise UtilityProtocolV3Error("selected header is missing, unknown, or reordered")
    return values


def parse_raw_label_tokens_v3(tokens: Sequence[object]) -> tuple[int, ...]:
    if isinstance(tokens, (str, bytes)) or not isinstance(tokens, Sequence):
        raise UtilityProtocolV3Error("label tokens must be a sequence")
    result = []
    for token in tokens:
        if type(token) is not str or token not in {"0", "1"}:
            raise UtilityProtocolV3Error("label token is not exact authorized binary encoding")
        result.append(0 if token == "0" else 1)
    return tuple(result)


def _canonical_window(values: object, length: int, name: str) -> tuple[float, ...]:
    if type(values) is not tuple or len(values) != length:
        raise UtilityProtocolV3Error(f"{name} must be a canonical tuple of length {length}")
    if any(type(value) is not float or not math.isfinite(value) for value in values):
        raise UtilityProtocolV3Error(f"{name} must contain only finite canonical floats")
    return values


@dataclass(frozen=True)
class AvailableSourceWindowV3:
    feature_identity: str
    pre_values: tuple[float, ...]
    post_values: tuple[float, ...]
    state: str = "available_source_window"

    def __post_init__(self) -> None:
        if self.feature_identity not in UTILITY_SOURCE_UNIVERSE_V3:
            raise UtilityProtocolV3Error("source feature is unknown")
        _canonical_window(self.pre_values, SOURCE_PRE_WINDOW, "source_pre")
        _canonical_window(self.post_values, SOURCE_POST_WINDOW, "source_post")
        if self.state != "available_source_window":
            raise UtilityProtocolV3Error("source window tag is unknown")


@dataclass(frozen=True)
class UnavailableSourceContextV3:
    feature_identity: str
    reason: str
    state: str = "unavailable_source_context"

    def __post_init__(self) -> None:
        if self.feature_identity not in UTILITY_SOURCE_UNIVERSE_V3:
            raise UtilityProtocolV3Error("source feature is unknown")
        if self.reason not in SOURCE_UNAVAILABLE_REASONS or self.state != "unavailable_source_context":
            raise UtilityProtocolV3Error("source unavailable state is unknown")


@dataclass(frozen=True)
class AvailableTargetWindowV3:
    feature_identity: str
    baseline_values: tuple[float, ...]
    response_values: tuple[float, ...]
    state: str = "available_target_window"

    def __post_init__(self) -> None:
        if self.feature_identity not in TARGET_METADATA_HASHES:
            raise UtilityProtocolV3Error("target feature is unknown")
        _canonical_window(self.baseline_values, TARGET_BASELINE_WINDOW, "target_baseline")
        _canonical_window(self.response_values, TARGET_RESPONSE_WINDOW, "target_response")
        if self.state != "available_target_window":
            raise UtilityProtocolV3Error("target window tag is unknown")


@dataclass(frozen=True)
class UnavailableTargetContextV3:
    feature_identity: str
    reason: str
    state: str = "unavailable_target_context"

    def __post_init__(self) -> None:
        if self.feature_identity not in TARGET_METADATA_HASHES:
            raise UtilityProtocolV3Error("target feature is unknown")
        if self.reason not in TARGET_UNAVAILABLE_REASONS or self.state != "unavailable_target_context":
            raise UtilityProtocolV3Error("target unavailable state is unknown")


@dataclass(frozen=True)
class SourceFormationOutcomeV3:
    state: str
    reason: str | None

    def __post_init__(self) -> None:
        if self.state == "source_opportunity_not_formed":
            valid = self.reason in SOURCE_UNAVAILABLE_REASONS
        elif self.state == "no_trigger":
            valid = self.reason in {
                "below_threshold_or_stability_failure", "clustered_or_nonisolated", "wrong_source_direction"
            }
        else:
            valid = False
        if not valid:
            raise UtilityProtocolV3Error("source outcome state is inconsistent")


@dataclass(frozen=True)
class ExecutableAuthorityV3:
    signatures_by_relation: Mapping[str, Mapping[str, Any]]

    def __post_init__(self) -> None:
        if len(self.signatures_by_relation) != 42:
            raise UtilityProtocolV3Error("executable authority must contain 42 relations")
        for relation, item in self.signatures_by_relation.items():
            _sha(relation, "relation_binding_hash")
            if not isinstance(item, Mapping):
                raise UtilityProtocolV3Error("executable authority record is malformed")
            _sha(item.get("executable_signature_hash"), "executable_signature_hash")
            if item.get("source") not in UTILITY_SOURCE_UNIVERSE_V3:
                raise UtilityProtocolV3Error("executable source is unknown")
            if item.get("target") not in TARGET_METADATA_HASHES:
                raise UtilityProtocolV3Error("executable target is unknown")
            if item.get("source_direction") not in SOURCE_DIRECTIONS:
                raise UtilityProtocolV3Error("executable source direction is unknown")
            if item.get("target_direction") not in TARGET_DIRECTIONS:
                raise UtilityProtocolV3Error("executable target direction is unknown")
            if type(item.get("horizon_seconds")) is not int or item.get("horizon_seconds") not in SUPPORTED_HORIZONS:
                raise UtilityProtocolV3Error("executable horizon is unknown")

    @property
    def authority_hash(self) -> str:
        return EXECUTABLE_EQUIVALENCE_HASH


def executable_authority_v3(document: Mapping[str, Any]) -> ExecutableAuthorityV3:
    _verify_self_hash(document, expected=EXECUTABLE_EQUIVALENCE_HASH)
    records = document.get("relation_records")
    if not isinstance(records, list) or len(records) != 42:
        raise UtilityProtocolV3Error("executable-equivalence records differ")
    result = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise UtilityProtocolV3Error("executable-equivalence record is malformed")
        relation = record.get("relation_binding_hash")
        signature_hash = record.get("semantic_execution_hash")
        signature = record.get("executable_signature")
        if not isinstance(signature, Mapping):
            raise UtilityProtocolV3Error("executable signature is missing")
        _sha(relation, "relation_binding_hash")
        _sha(signature_hash, "semantic_execution_hash")
        if stable_hash_v1(signature) != signature_hash:
            raise UtilityProtocolV3Error("semantic execution hash differs")
        result[relation] = {
            "executable_signature_hash": signature_hash,
            "source": signature.get("source"),
            "target": signature.get("target"),
            "source_direction": signature.get("source_step_direction"),
            "target_direction": signature.get("target_response_direction"),
            "horizon_seconds": signature.get("selected_delay_horizon_seconds"),
        }
    return ExecutableAuthorityV3(result)


@dataclass(frozen=True)
class AcceptedRelationBindingV3:
    relation_binding_hash: str
    executable_signature_hash: str
    portfolio_identity: str
    source: str
    target: str
    expected_source_direction: str
    expected_target_direction: str
    selected_horizon_seconds: int

    def __post_init__(self) -> None:
        _sha(self.relation_binding_hash, "relation_binding_hash")
        _sha(self.executable_signature_hash, "executable_signature_hash")
        if self.portfolio_identity not in {"COMMON-42", "T0", "T1", "T1-B", "T2"}:
            raise UtilityProtocolV3Error("portfolio identity is unknown")
        if self.source not in UTILITY_SOURCE_UNIVERSE_V3 or self.target not in TARGET_METADATA_HASHES:
            raise UtilityProtocolV3Error("relation feature identity is unknown")
        if self.expected_source_direction not in SOURCE_DIRECTIONS or self.expected_target_direction not in TARGET_DIRECTIONS:
            raise UtilityProtocolV3Error("relation direction is unknown")
        if type(self.selected_horizon_seconds) is not int or self.selected_horizon_seconds not in SUPPORTED_HORIZONS:
            raise UtilityProtocolV3Error("relation horizon is unknown")


def accepted_relation_binding_v3(
    authority: ExecutableAuthorityV3,
    relation_binding_hash: str,
    portfolio_identity: str,
) -> AcceptedRelationBindingV3:
    if not isinstance(authority, ExecutableAuthorityV3):
        raise UtilityProtocolV3Error("executable authority is required")
    item = authority.signatures_by_relation.get(relation_binding_hash)
    if item is None:
        raise UtilityProtocolV3Error("relation is unknown")
    return AcceptedRelationBindingV3(
        relation_binding_hash,
        item["executable_signature_hash"],
        portfolio_identity,
        item["source"],
        item["target"],
        item["source_direction"],
        item["target_direction"],
        item["horizon_seconds"],
    )


@dataclass(frozen=True)
class ApplicableRuleEvaluationOpportunityV3:
    relation_binding_hash: str
    executable_signature_hash: str
    portfolio_identity: str
    file_identity: str
    source: str
    target: str
    source_event_physical_index: int
    selected_horizon_seconds: int

    def __post_init__(self) -> None:
        _sha(self.relation_binding_hash, "relation_binding_hash")
        _sha(self.executable_signature_hash, "executable_signature_hash")
        if self.portfolio_identity not in {"COMMON-42", "T0", "T1", "T1-B", "T2"}:
            raise UtilityProtocolV3Error("opportunity portfolio is unknown")
        if self.file_identity not in FILE_ROW_COUNTS:
            raise UtilityProtocolV3Error("opportunity file is unknown")
        if self.source not in UTILITY_SOURCE_UNIVERSE_V3 or self.target not in TARGET_METADATA_HASHES:
            raise UtilityProtocolV3Error("opportunity feature is unknown")
        index = _strict_int(self.source_event_physical_index, "source_event_physical_index")
        if index >= FILE_ROW_COUNTS[self.file_identity]:
            raise UtilityProtocolV3Error("opportunity coordinate is outside the physical file")
        if type(self.selected_horizon_seconds) is not int or self.selected_horizon_seconds not in SUPPORTED_HORIZONS:
            raise UtilityProtocolV3Error("opportunity horizon is unknown")

    @property
    def logical_key(self) -> tuple[Any, ...]:
        return (
            self.relation_binding_hash, self.executable_signature_hash, self.portfolio_identity,
            self.file_identity, self.source, self.target, self.source_event_physical_index,
            self.selected_horizon_seconds,
        )

    @property
    def opportunity_id(self) -> str:
        return stable_hash_v1(
            {
                "executable_signature_hash": self.executable_signature_hash,
                "file_identity": self.file_identity,
                "portfolio_identity": self.portfolio_identity,
                "relation_binding_hash": self.relation_binding_hash,
                "selected_horizon_seconds": self.selected_horizon_seconds,
                "source_event_physical_index": self.source_event_physical_index,
            }
        )


def _validate_relation_binding(
    relation: AcceptedRelationBindingV3,
    authority: ExecutableAuthorityV3,
) -> None:
    item = authority.signatures_by_relation.get(relation.relation_binding_hash)
    if item is None or any(
        (
            relation.executable_signature_hash != item["executable_signature_hash"],
            relation.source != item["source"],
            relation.target != item["target"],
            relation.expected_source_direction != item["source_direction"],
            relation.expected_target_direction != item["target_direction"],
            relation.selected_horizon_seconds != item["horizon_seconds"],
        )
    ):
        raise UtilityProtocolV3Error("accepted relation does not match executable authority")


def _validate_retained_index_map(values: Mapping[str, Sequence[int]], row_count: int) -> dict[str, tuple[int, ...]]:
    if not isinstance(values, Mapping) or set(values) != set(UTILITY_SOURCE_UNIVERSE_V3):
        raise UtilityProtocolV3Error("retained events must bind the exact 12-source universe")
    result = {}
    for source in UTILITY_SOURCE_UNIVERSE_V3:
        indices = values[source]
        if isinstance(indices, (str, bytes)) or not isinstance(indices, Sequence):
            raise UtilityProtocolV3Error("retained event indices must be a sequence")
        normalized = tuple(_strict_int(value, "retained event index") for value in indices)
        if len(normalized) != len(set(normalized)) or normalized != tuple(sorted(normalized)):
            raise UtilityProtocolV3Error("retained event indices must be unique and ordered")
        if any(index >= row_count for index in normalized):
            raise UtilityProtocolV3Error("retained event coordinate is outside the file")
        result[source] = normalized
    return result


def _is_isolated(source: str, index: int, retained: Mapping[str, Sequence[int]]) -> bool:
    return not any(
        abs(index - other) <= CROSS_SOURCE_ISOLATION_RADIUS_SECONDS
        for other_source, indices in retained.items()
        if other_source != source
        for other in indices
    )


def form_source_opportunity_v3(
    *,
    relation: AcceptedRelationBindingV3,
    authority: ExecutableAuthorityV3,
    file_identity: str,
    physical_row_count: int,
    event_index: int,
    source_context: AvailableSourceWindowV3 | UnavailableSourceContextV3,
    source_step_threshold: NumericParameterV3,
    source_stability_tolerance: NumericParameterV3,
    retained_events_by_source: Mapping[str, Sequence[int]],
) -> ApplicableRuleEvaluationOpportunityV3 | SourceFormationOutcomeV3:
    """Validate all structure before any boundary or scientific state."""

    if not isinstance(relation, AcceptedRelationBindingV3) or not isinstance(authority, ExecutableAuthorityV3):
        raise UtilityProtocolV3Error("relation and executable authority are required")
    AcceptedRelationBindingV3(
        relation.relation_binding_hash,
        relation.executable_signature_hash,
        relation.portfolio_identity,
        relation.source,
        relation.target,
        relation.expected_source_direction,
        relation.expected_target_direction,
        relation.selected_horizon_seconds,
    )
    _validate_relation_binding(relation, authority)
    if file_identity not in FILE_ROW_COUNTS:
        raise UtilityProtocolV3Error("file identity is unknown")
    count = _strict_int(physical_row_count, "physical_row_count")
    if count != FILE_ROW_COUNTS[file_identity]:
        raise UtilityProtocolV3Error("physical row count differs from file authority")
    index = _strict_int(event_index, "event_index")
    if index >= count:
        raise UtilityProtocolV3Error("event coordinate is outside the physical file")
    if not isinstance(source_context, (AvailableSourceWindowV3, UnavailableSourceContextV3)):
        raise UtilityProtocolV3Error("source context tag is unknown")
    if isinstance(source_context, AvailableSourceWindowV3):
        AvailableSourceWindowV3(
            source_context.feature_identity,
            source_context.pre_values,
            source_context.post_values,
            source_context.state,
        )
    else:
        UnavailableSourceContextV3(
            source_context.feature_identity, source_context.reason, source_context.state
        )
    if source_context.feature_identity != relation.source:
        raise UtilityProtocolV3Error("source context feature does not match relation")
    if not isinstance(source_step_threshold, NumericParameterV3) or source_step_threshold.role != "source_step_threshold":
        raise UtilityProtocolV3Error("source threshold role differs")
    if not isinstance(source_stability_tolerance, NumericParameterV3) or source_stability_tolerance.role != "source_stability_tolerance":
        raise UtilityProtocolV3Error("source stability role differs")
    NumericParameterV3(source_step_threshold.role, source_step_threshold.value)
    NumericParameterV3(source_stability_tolerance.role, source_stability_tolerance.value)
    threshold = source_step_threshold.value
    tolerance = source_stability_tolerance.value
    retained = _validate_retained_index_map(retained_events_by_source, count)

    boundary_reason = (
        "insufficient_source_pre_window" if index < SOURCE_PRE_WINDOW
        else "incomplete_source_post_window" if index + SOURCE_POST_WINDOW > count
        else None
    )
    if boundary_reason is not None:
        if isinstance(source_context, UnavailableSourceContextV3) and source_context.reason != boundary_reason:
            raise UtilityProtocolV3Error("source boundary reason differs from coordinate authority")
        return SourceFormationOutcomeV3("source_opportunity_not_formed", boundary_reason)
    if isinstance(source_context, UnavailableSourceContextV3):
        raise UtilityProtocolV3Error("unavailable source context lacks an authoritative boundary")

    values = (*source_context.pre_values, *source_context.post_values)
    pre_level = float(statistics.median(values[:SOURCE_PRE_WINDOW]))
    post_level = float(statistics.median(values[SOURCE_PRE_WINDOW:]))
    amplitude = post_level - pre_level
    pre_fraction = sum(abs(value - pre_level) <= tolerance for value in values[:SOURCE_PRE_WINDOW]) / SOURCE_PRE_WINDOW
    post_fraction = sum(abs(value - post_level) <= tolerance for value in values[SOURCE_PRE_WINDOW:]) / SOURCE_POST_WINDOW
    if (
        amplitude == 0
        or abs(amplitude) < threshold
        or pre_fraction < MINIMUM_STABILITY_FRACTION
        or post_fraction < MINIMUM_STABILITY_FRACTION
    ):
        return SourceFormationOutcomeV3("no_trigger", "below_threshold_or_stability_failure")
    if index not in retained[relation.source] or not _is_isolated(relation.source, index, retained):
        return SourceFormationOutcomeV3("no_trigger", "clustered_or_nonisolated")
    observed_direction = "step_up" if amplitude > 0 else "step_down"
    if observed_direction != relation.expected_source_direction:
        return SourceFormationOutcomeV3("no_trigger", "wrong_source_direction")
    return ApplicableRuleEvaluationOpportunityV3(
        relation.relation_binding_hash,
        relation.executable_signature_hash,
        relation.portfolio_identity,
        file_identity,
        relation.source,
        relation.target,
        index,
        relation.selected_horizon_seconds,
    )


@dataclass(frozen=True)
class TargetEvaluationOutcomeV3:
    target_evaluation_state: str
    decision_index: int | None
    alarm_emitted: bool
    abstention_reason: str | None

    def __post_init__(self) -> None:
        if self.target_evaluation_state == "evaluated_expected_response":
            valid = type(self.decision_index) is int and self.decision_index >= 0 and self.alarm_emitted is False and self.abstention_reason is None
        elif self.target_evaluation_state == "evaluated_anomaly":
            valid = type(self.decision_index) is int and self.decision_index >= 0 and self.alarm_emitted is True and self.abstention_reason is None
        elif self.target_evaluation_state == "abstain":
            valid = self.decision_index is None and self.alarm_emitted is False and self.abstention_reason in TARGET_UNAVAILABLE_REASONS
        else:
            valid = False
        if not valid:
            raise UtilityProtocolV3Error("target outcome state is inconsistent")


def evaluate_target_response_v3(
    opportunity: ApplicableRuleEvaluationOpportunityV3,
    *,
    relation: AcceptedRelationBindingV3,
    authority: ExecutableAuthorityV3,
    target_context: AvailableTargetWindowV3 | UnavailableTargetContextV3,
    physical_row_count: int,
    within_split: bool,
    target_noise_scale: NumericParameterV3,
) -> TargetEvaluationOutcomeV3:
    """Validate structure and values before applying boundary precedence."""

    if not isinstance(opportunity, ApplicableRuleEvaluationOpportunityV3):
        raise UtilityProtocolV3Error("applicable opportunity is required")
    ApplicableRuleEvaluationOpportunityV3(
        opportunity.relation_binding_hash,
        opportunity.executable_signature_hash,
        opportunity.portfolio_identity,
        opportunity.file_identity,
        opportunity.source,
        opportunity.target,
        opportunity.source_event_physical_index,
        opportunity.selected_horizon_seconds,
    )
    if not isinstance(relation, AcceptedRelationBindingV3) or not isinstance(authority, ExecutableAuthorityV3):
        raise UtilityProtocolV3Error("relation and executable authority are required")
    AcceptedRelationBindingV3(
        relation.relation_binding_hash,
        relation.executable_signature_hash,
        relation.portfolio_identity,
        relation.source,
        relation.target,
        relation.expected_source_direction,
        relation.expected_target_direction,
        relation.selected_horizon_seconds,
    )
    _validate_relation_binding(relation, authority)
    if opportunity.logical_key != (
        relation.relation_binding_hash,
        relation.executable_signature_hash,
        relation.portfolio_identity,
        opportunity.file_identity,
        relation.source,
        relation.target,
        opportunity.source_event_physical_index,
        relation.selected_horizon_seconds,
    ):
        raise UtilityProtocolV3Error("target opportunity does not match its accepted relation")
    if not isinstance(target_context, (AvailableTargetWindowV3, UnavailableTargetContextV3)):
        raise UtilityProtocolV3Error("target context tag is unknown")
    if isinstance(target_context, AvailableTargetWindowV3):
        AvailableTargetWindowV3(
            target_context.feature_identity,
            target_context.baseline_values,
            target_context.response_values,
            target_context.state,
        )
    else:
        UnavailableTargetContextV3(
            target_context.feature_identity, target_context.reason, target_context.state
        )
    if target_context.feature_identity != opportunity.target:
        raise UtilityProtocolV3Error("target context feature does not match opportunity")
    count = _strict_int(physical_row_count, "physical_row_count")
    if count != FILE_ROW_COUNTS[opportunity.file_identity]:
        raise UtilityProtocolV3Error("physical row count differs from file authority")
    if type(within_split) is not bool:
        raise UtilityProtocolV3Error("within_split must be an actual boolean")
    if not isinstance(target_noise_scale, NumericParameterV3) or target_noise_scale.role != "target_noise_scale":
        raise UtilityProtocolV3Error("target noise role differs")
    NumericParameterV3(target_noise_scale.role, target_noise_scale.value)
    noise = target_noise_scale.value
    decision = opportunity.source_event_physical_index + opportunity.selected_horizon_seconds + TARGET_RESPONSE_WINDOW - 1

    boundary_reason = "file_boundary" if decision >= count else "split_boundary" if not within_split else None
    if boundary_reason is not None:
        if isinstance(target_context, UnavailableTargetContextV3) and target_context.reason != boundary_reason:
            raise UtilityProtocolV3Error("target boundary reason differs from authority precedence")
        return TargetEvaluationOutcomeV3("abstain", None, False, boundary_reason)
    if isinstance(target_context, UnavailableTargetContextV3):
        if target_context.reason in {"file_boundary", "split_boundary"}:
            raise UtilityProtocolV3Error("target boundary reason lacks coordinate support")
        return TargetEvaluationOutcomeV3("abstain", None, False, target_context.reason)

    baseline = float(statistics.median(target_context.baseline_values))
    response = float(statistics.median(target_context.response_values)) - baseline
    matched = response > noise if relation.expected_target_direction == "increase" else response < -noise
    return TargetEvaluationOutcomeV3(
        "evaluated_expected_response" if matched else "evaluated_anomaly",
        decision,
        not matched,
        None,
    )


@dataclass(frozen=True)
class RetainedSourceEventV3:
    source: str
    physical_index: int
    direction: str
    amplitude: float

    def __post_init__(self) -> None:
        if self.source not in UTILITY_SOURCE_UNIVERSE_V3:
            raise UtilityProtocolV3Error("retained source is unknown")
        _strict_int(self.physical_index, "retained physical index")
        if self.direction not in SOURCE_DIRECTIONS:
            raise UtilityProtocolV3Error("retained source direction is unknown")
        _strict_finite(self.amplitude, "retained source amplitude")


def derive_retained_source_events_v3(
    source_series_by_source: Mapping[str, tuple[float, ...]],
    source_step_thresholds: Mapping[str, object],
    source_stability_tolerances: Mapping[str, object],
) -> Mapping[str, tuple[RetainedSourceEventV3, ...]]:
    """Pure synthetic full scan through threshold/stability and clustering."""

    expected = set(UTILITY_SOURCE_UNIVERSE_V3)
    if set(source_series_by_source) != expected or set(source_step_thresholds) != expected or set(source_stability_tolerances) != expected:
        raise UtilityProtocolV3Error("full source census requires the exact 12-source universe")
    if any(type(values) is not tuple for values in source_series_by_source.values()):
        raise UtilityProtocolV3Error("source series must be canonical tuples")
    lengths = {len(values) for values in source_series_by_source.values()}
    if len(lengths) != 1:
        raise UtilityProtocolV3Error("source series must be equal-length canonical tuples")
    row_count = next(iter(lengths))
    if row_count < SOURCE_PRE_WINDOW + SOURCE_POST_WINDOW:
        raise UtilityProtocolV3Error("synthetic census timeline is too short")
    result = {}
    for source in UTILITY_SOURCE_UNIVERSE_V3:
        series = source_series_by_source[source]
        if type(series) is not tuple or any(type(value) is not float or not math.isfinite(value) for value in series):
            raise UtilityProtocolV3Error("source census values must be canonical finite floats")
        threshold = _strict_finite(source_step_thresholds[source], "source step threshold", positive=True)
        tolerance = _strict_finite(source_stability_tolerances[source], "source stability tolerance")
        if tolerance < 0:
            raise UtilityProtocolV3Error("source stability tolerance must be nonnegative")
        candidates = []
        for index in range(SOURCE_PRE_WINDOW, row_count - SOURCE_POST_WINDOW + 1):
            pre = series[index - SOURCE_PRE_WINDOW:index]
            post = series[index:index + SOURCE_POST_WINDOW]
            pre_level = float(statistics.median(pre))
            post_level = float(statistics.median(post))
            amplitude = post_level - pre_level
            pre_fraction = sum(abs(value - pre_level) <= tolerance for value in pre) / SOURCE_PRE_WINDOW
            post_fraction = sum(abs(value - post_level) <= tolerance for value in post) / SOURCE_POST_WINDOW
            if amplitude != 0 and abs(amplitude) >= threshold and pre_fraction >= MINIMUM_STABILITY_FRACTION and post_fraction >= MINIMUM_STABILITY_FRACTION:
                candidates.append(RetainedSourceEventV3(source, index, "step_up" if amplitude > 0 else "step_down", amplitude))
        clusters: list[list[RetainedSourceEventV3]] = []
        for candidate in candidates:
            if not clusters or candidate.physical_index - clusters[-1][-1].physical_index > SOURCE_REFRACTORY_SECONDS:
                clusters.append([candidate])
            else:
                clusters[-1].append(candidate)
        result[source] = tuple(
            min(cluster, key=lambda item: (-abs(item.amplitude), item.physical_index))
            for cluster in clusters
        )
    return result


@dataclass(frozen=True)
class FullCensusEnumerationV3:
    opportunities: tuple[ApplicableRuleEvaluationOpportunityV3, ...]
    accepted_relation_binding_hashes: tuple[str, ...]
    no_rule_relation_binding_hashes: tuple[str, ...]
    portfolio_identity: str
    file_identity: str
    physical_row_count: int
    retained_source_event_census_hash: str

    def __post_init__(self) -> None:
        if self.portfolio_identity not in {"COMMON-42", "T0", "T1", "T1-B", "T2"}:
            raise UtilityProtocolV3Error("enumeration portfolio is unknown")
        if self.file_identity not in FILE_ROW_COUNTS or self.physical_row_count != FILE_ROW_COUNTS[self.file_identity]:
            raise UtilityProtocolV3Error("enumeration file authority differs")
        accepted = self.accepted_relation_binding_hashes
        no_rule = self.no_rule_relation_binding_hashes
        if accepted != tuple(sorted(set(accepted))) or no_rule != tuple(sorted(set(no_rule))) or set(accepted) & set(no_rule):
            raise UtilityProtocolV3Error("accepted/no_rule relation sets are malformed")
        if len(accepted) + len(no_rule) != 42:
            raise UtilityProtocolV3Error("portfolio construction denominator must remain 42")
        ids = tuple(item.opportunity_id for item in self.opportunities)
        keys = tuple(item.logical_key for item in self.opportunities)
        if len(ids) != len(set(ids)) or len(keys) != len(set(keys)):
            raise UtilityProtocolV3Error("opportunity enumeration contains duplicates")
        if tuple(sorted(self.opportunities, key=lambda item: item.logical_key)) != self.opportunities:
            raise UtilityProtocolV3Error("opportunity enumeration order differs")
        if any(
            item.portfolio_identity != self.portfolio_identity
            or item.file_identity != self.file_identity
            or item.relation_binding_hash not in accepted
            for item in self.opportunities
        ):
            raise UtilityProtocolV3Error("opportunity enumeration contains a foreign or no_rule record")
        _sha(self.retained_source_event_census_hash, "retained_source_event_census_hash")


def enumerate_full_census_opportunities_v3(
    *,
    accepted_relations: Sequence[AcceptedRelationBindingV3],
    no_rule_relation_binding_hashes: Sequence[str],
    retained_events_by_source: Mapping[str, Sequence[RetainedSourceEventV3]],
    authority: ExecutableAuthorityV3,
    file_identity: str,
    physical_row_count: int,
) -> FullCensusEnumerationV3:
    """Enumerate every retained, isolated, matching-direction source event."""

    if isinstance(accepted_relations, (str, bytes)) or not isinstance(accepted_relations, Sequence):
        raise UtilityProtocolV3Error("accepted relations must be a sequence")
    if file_identity not in FILE_ROW_COUNTS or physical_row_count != FILE_ROW_COUNTS[file_identity]:
        raise UtilityProtocolV3Error("full-census file authority differs")
    relations = tuple(accepted_relations)
    if not relations:
        raise UtilityProtocolV3Error("accepted portfolio cannot be empty")
    portfolio = relations[0].portfolio_identity
    if any(item.portfolio_identity != portfolio for item in relations):
        raise UtilityProtocolV3Error("full census cannot mix portfolios")
    for relation in relations:
        _validate_relation_binding(relation, authority)
    accepted_hashes = tuple(sorted(item.relation_binding_hash for item in relations))
    if len(accepted_hashes) != len(set(accepted_hashes)):
        raise UtilityProtocolV3Error("accepted relation is duplicated")
    no_rule = tuple(sorted(_sha(value, "no_rule relation binding") for value in no_rule_relation_binding_hashes))
    if len(no_rule) != len(set(no_rule)) or set(no_rule) & set(accepted_hashes):
        raise UtilityProtocolV3Error("no_rule relation set is duplicated or overlaps accepted")
    expected_counts = (42, 0) if portfolio in {"COMMON-42", "T0", "T1", "T1-B"} else (39, 3)
    if (len(accepted_hashes), len(no_rule)) != expected_counts:
        raise UtilityProtocolV3Error("portfolio accepted/no_rule counts differ from construction")
    if set(retained_events_by_source) != set(UTILITY_SOURCE_UNIVERSE_V3):
        raise UtilityProtocolV3Error("retained event census must use exact 12-source universe")
    retained = {}
    for source in UTILITY_SOURCE_UNIVERSE_V3:
        events = tuple(retained_events_by_source[source])
        if any(not isinstance(item, RetainedSourceEventV3) or item.source != source for item in events):
            raise UtilityProtocolV3Error("retained source event is malformed")
        if tuple(sorted(events, key=lambda item: item.physical_index)) != events:
            raise UtilityProtocolV3Error("retained source events must be ordered")
        if any(item.physical_index >= physical_row_count for item in events):
            raise UtilityProtocolV3Error("retained source event is outside the file")
        retained[source] = events
    index_map = {source: tuple(item.physical_index for item in events) for source, events in retained.items()}
    opportunities = []
    for relation in relations:
        for event in retained[relation.source]:
            if event.direction != relation.expected_source_direction or not _is_isolated(relation.source, event.physical_index, index_map):
                continue
            opportunities.append(
                ApplicableRuleEvaluationOpportunityV3(
                    relation.relation_binding_hash,
                    relation.executable_signature_hash,
                    relation.portfolio_identity,
                    file_identity,
                    relation.source,
                    relation.target,
                    event.physical_index,
                    relation.selected_horizon_seconds,
                )
            )
    census_payload = {
        source: [
            {"direction": item.direction, "index": item.physical_index, "amplitude": item.amplitude}
            for item in retained[source]
        ]
        for source in UTILITY_SOURCE_UNIVERSE_V3
    }
    return FullCensusEnumerationV3(
        tuple(sorted(opportunities, key=lambda item: item.logical_key)),
        accepted_hashes,
        no_rule,
        portfolio,
        file_identity,
        physical_row_count,
        stable_hash_v1(census_payload),
    )


def enumerate_full_census_from_timeline_v3(
    *,
    accepted_relations: Sequence[AcceptedRelationBindingV3],
    no_rule_relation_binding_hashes: Sequence[str],
    source_series_by_source: Mapping[str, tuple[float, ...]],
    source_step_thresholds: Mapping[str, object],
    source_stability_tolerances: Mapping[str, object],
    authority: ExecutableAuthorityV3,
    file_identity: str,
    physical_row_count: int,
) -> FullCensusEnumerationV3:
    """Canonical V3 enumeration: own the complete source scan and opportunity census."""

    if file_identity not in FILE_ROW_COUNTS or physical_row_count != FILE_ROW_COUNTS[file_identity]:
        raise UtilityProtocolV3Error("full-census timeline file authority differs")
    if set(source_series_by_source) != set(UTILITY_SOURCE_UNIVERSE_V3):
        raise UtilityProtocolV3Error("full-census timeline must contain exactly 12 sources")
    if any(type(values) is not tuple or len(values) != physical_row_count for values in source_series_by_source.values()):
        raise UtilityProtocolV3Error("full-census timeline must cover every physical row")
    retained = derive_retained_source_events_v3(
        source_series_by_source,
        source_step_thresholds,
        source_stability_tolerances,
    )
    return enumerate_full_census_opportunities_v3(
        accepted_relations=accepted_relations,
        no_rule_relation_binding_hashes=no_rule_relation_binding_hashes,
        retained_events_by_source=retained,
        authority=authority,
        file_identity=file_identity,
        physical_row_count=physical_row_count,
    )


@dataclass(frozen=True)
class ApplicableRuleEvaluationOpportunityRecordV3:
    opportunity_id: str
    relation_binding_hash: str
    executable_signature_hash: str
    portfolio_identity: str
    file_identity: str
    source: str
    target: str
    source_event_physical_index: int
    selected_horizon_seconds: int
    target_evaluation_state: str
    decision_index: int | None
    alarm_emitted: bool
    abstention_reason: str | None

    def __post_init__(self) -> None:
        opportunity = ApplicableRuleEvaluationOpportunityV3(
            self.relation_binding_hash,
            self.executable_signature_hash,
            self.portfolio_identity,
            self.file_identity,
            self.source,
            self.target,
            self.source_event_physical_index,
            self.selected_horizon_seconds,
        )
        if self.opportunity_id != opportunity.opportunity_id:
            raise UtilityProtocolV3Error("opportunity ID differs from its deterministic preimage")
        TargetEvaluationOutcomeV3(
            self.target_evaluation_state,
            self.decision_index,
            self.alarm_emitted,
            self.abstention_reason,
        )
        if self.target_evaluation_state != "abstain":
            expected = self.source_event_physical_index + self.selected_horizon_seconds + TARGET_RESPONSE_WINDOW - 1
            if self.decision_index != expected:
                raise UtilityProtocolV3Error("evaluated record decision index differs")

    @property
    def record_hash(self) -> str:
        return stable_hash_v1(self._payload())

    @property
    def logical_key(self) -> tuple[Any, ...]:
        return (
            self.relation_binding_hash, self.executable_signature_hash, self.portfolio_identity,
            self.file_identity, self.source, self.target, self.source_event_physical_index,
            self.selected_horizon_seconds,
        )

    def _payload(self) -> dict[str, Any]:
        return {
            "abstention_reason": self.abstention_reason,
            "alarm_emitted": self.alarm_emitted,
            "decision_index": self.decision_index,
            "executable_signature_hash": self.executable_signature_hash,
            "file_identity": self.file_identity,
            "opportunity_id": self.opportunity_id,
            "portfolio_identity": self.portfolio_identity,
            "relation_binding_hash": self.relation_binding_hash,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "source": self.source,
            "source_event_physical_index": self.source_event_physical_index,
            "target": self.target,
            "target_evaluation_state": self.target_evaluation_state,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "record_hash": self.record_hash}

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ApplicableRuleEvaluationOpportunityRecordV3":
        observed = value.get("record_hash")
        payload = {key: item for key, item in value.items() if key != "record_hash"}
        result = cls(**payload)
        if observed != result.record_hash or value != result.to_dict():
            raise UtilityProtocolV3Error("opportunity record self-hash differs")
        return result


def opportunity_record_v3(
    opportunity: ApplicableRuleEvaluationOpportunityV3,
    outcome: TargetEvaluationOutcomeV3,
) -> ApplicableRuleEvaluationOpportunityRecordV3:
    if not isinstance(opportunity, ApplicableRuleEvaluationOpportunityV3) or not isinstance(outcome, TargetEvaluationOutcomeV3):
        raise UtilityProtocolV3Error("typed opportunity and target outcome are required")
    return ApplicableRuleEvaluationOpportunityRecordV3(
        opportunity.opportunity_id,
        opportunity.relation_binding_hash,
        opportunity.executable_signature_hash,
        opportunity.portfolio_identity,
        opportunity.file_identity,
        opportunity.source,
        opportunity.target,
        opportunity.source_event_physical_index,
        opportunity.selected_horizon_seconds,
        outcome.target_evaluation_state,
        outcome.decision_index,
        outcome.alarm_emitted,
        outcome.abstention_reason,
    )


@dataclass(frozen=True)
class OpportunityCustodyV3:
    records: tuple[ApplicableRuleEvaluationOpportunityRecordV3, ...]
    accepted_relation_binding_hashes: tuple[str, ...]
    no_rule_relation_binding_hashes: tuple[str, ...]
    portfolio_identity: str
    split_identity: str
    file_identity: str
    source_event_policy_hash: str
    target_evaluation_policy_hash: str
    retained_source_event_census_hash: str

    def __post_init__(self) -> None:
        if self.file_identity not in FILE_ROW_COUNTS or self.split_identity != FILE_SPLITS[self.file_identity]:
            raise UtilityProtocolV3Error("opportunity custody split/file authority differs")
        if self.portfolio_identity not in {"COMMON-42", "T0", "T1", "T1-B", "T2"}:
            raise UtilityProtocolV3Error("opportunity custody portfolio is unknown")
        for value, name in (
            (self.source_event_policy_hash, "source_event_policy_hash"),
            (self.target_evaluation_policy_hash, "target_evaluation_policy_hash"),
            (self.retained_source_event_census_hash, "retained_source_event_census_hash"),
        ):
            _sha(value, name)
        accepted = self.accepted_relation_binding_hashes
        no_rule = self.no_rule_relation_binding_hashes
        if accepted != tuple(sorted(set(accepted))) or no_rule != tuple(sorted(set(no_rule))) or set(accepted) & set(no_rule):
            raise UtilityProtocolV3Error("custody accepted/no_rule sets are malformed")
        expected_counts = (42, 0) if self.portfolio_identity in {"COMMON-42", "T0", "T1", "T1-B"} else (39, 3)
        if (len(accepted), len(no_rule)) != expected_counts:
            raise UtilityProtocolV3Error("custody portfolio counts differ from construction")
        ids = tuple(item.opportunity_id for item in self.records)
        keys = tuple(item.logical_key for item in self.records)
        if len(ids) != len(set(ids)) or len(keys) != len(set(keys)):
            raise UtilityProtocolV3Error("custody contains duplicate opportunities")
        if tuple(sorted(self.records, key=lambda item: item.logical_key)) != self.records:
            raise UtilityProtocolV3Error("custody records are not canonical")
        if any(
            item.portfolio_identity != self.portfolio_identity
            or item.file_identity != self.file_identity
            or item.relation_binding_hash not in accepted
            or item.relation_binding_hash in no_rule
            for item in self.records
        ):
            raise UtilityProtocolV3Error("custody contains foreign or no_rule opportunity")

    @property
    def record_count(self) -> int:
        return len(self.records)

    @property
    def abstained_count(self) -> int:
        return sum(item.target_evaluation_state == "abstain" for item in self.records)

    @property
    def evaluated_count(self) -> int:
        return self.record_count - self.abstained_count

    @property
    def anomaly_count(self) -> int:
        return sum(item.target_evaluation_state == "evaluated_anomaly" for item in self.records)

    @property
    def expected_response_count(self) -> int:
        return sum(item.target_evaluation_state == "evaluated_expected_response" for item in self.records)

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def _payload(self) -> dict[str, Any]:
        return {
            "abstained_count": self.abstained_count,
            "accepted_relation_binding_hashes": list(self.accepted_relation_binding_hashes),
            "anomaly_count": self.anomaly_count,
            "artifact_type": "opportunity_custody_v3",
            "evaluated_count": self.evaluated_count,
            "expected_response_count": self.expected_response_count,
            "file_identity": self.file_identity,
            "full_census_policy": UTILITY_OPPORTUNITY_SAMPLING_POLICY,
            "no_rule_relation_binding_hashes": list(self.no_rule_relation_binding_hashes),
            "portfolio_identity": self.portfolio_identity,
            "record_count": self.record_count,
            "records": [item.to_dict() for item in self.records],
            "retained_source_event_census_hash": self.retained_source_event_census_hash,
            "schema_version": SCHEMA_VERSION,
            "source_event_policy_hash": self.source_event_policy_hash,
            "split_identity": self.split_identity,
            "target_evaluation_policy_hash": self.target_evaluation_policy_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "OpportunityCustodyV3":
        observed = value.get("artifact_hash")
        records = value.get("records")
        if not isinstance(records, list):
            raise UtilityProtocolV3Error("custody records must be a list")
        result = cls(
            tuple(ApplicableRuleEvaluationOpportunityRecordV3.from_mapping(item) for item in records),
            tuple(value.get("accepted_relation_binding_hashes", ())),
            tuple(value.get("no_rule_relation_binding_hashes", ())),
            value.get("portfolio_identity"),
            value.get("split_identity"),
            value.get("file_identity"),
            value.get("source_event_policy_hash"),
            value.get("target_evaluation_policy_hash"),
            value.get("retained_source_event_census_hash"),
        )
        if observed != result.artifact_hash or value != result.to_dict():
            raise UtilityProtocolV3Error("custody summaries, records, or self-hash differ")
        return result


def build_opportunity_custody_v3(
    *,
    enumeration: FullCensusEnumerationV3,
    records: Sequence[ApplicableRuleEvaluationOpportunityRecordV3],
    split_identity: str,
    source_event_policy_hash: str,
    target_evaluation_policy_hash: str,
) -> OpportunityCustodyV3:
    if not isinstance(enumeration, FullCensusEnumerationV3):
        raise UtilityProtocolV3Error("full-census enumeration is required")
    normalized = tuple(sorted(records, key=lambda item: item.logical_key))
    if any(not isinstance(item, ApplicableRuleEvaluationOpportunityRecordV3) for item in normalized):
        raise UtilityProtocolV3Error("typed opportunity records are required")
    if {item.opportunity_id for item in normalized} != {item.opportunity_id for item in enumeration.opportunities}:
        raise UtilityProtocolV3Error("terminal records do not exactly cover the full opportunity census")
    return OpportunityCustodyV3(
        normalized,
        enumeration.accepted_relation_binding_hashes,
        enumeration.no_rule_relation_binding_hashes,
        enumeration.portfolio_identity,
        split_identity,
        enumeration.file_identity,
        source_event_policy_hash,
        target_evaluation_policy_hash,
        enumeration.retained_source_event_census_hash,
    )


def abstention_rate_from_custody_v3(custody: OpportunityCustodyV3) -> dict[str, Any]:
    """Compute the diagnostic only from verified durable opportunity records."""

    if not isinstance(custody, OpportunityCustodyV3):
        raise UtilityProtocolV3Error("OpportunityCustodyV3 is required")
    # Round-trip verification rejects mutated summaries and record hashes.
    verified = OpportunityCustodyV3.from_mapping(custody.to_dict())
    numerator = sum(item.target_evaluation_state == "abstain" for item in verified.records)
    denominator = len(verified.records)
    return {
        "defined": denominator != 0,
        "denominator": denominator,
        "formula_identity": "abstained_opportunity_records_over_all_opportunity_records_v3",
        "no_rule_cells_included": False,
        "numerator": numerator,
        "opportunity_custody_hash": verified.artifact_hash,
        "source_not_formed_included": False,
        "undefined_reason": None if denominator else "no_applicable_opportunities",
        "value": numerator / denominator if denominator else None,
    }


def no_rule_diagnostic_v3() -> dict[str, Any]:
    return {
        "abstentions": 0,
        "alarms": 0,
        "construction_coverage_denominator_membership": True,
        "interpreter_instances": 0,
        "no_rule_relation_diagnostic_only": True,
        "opportunity_records": 0,
        "substitution_allowed": False,
    }


def authority_snapshot_v3() -> dict[str, Any]:
    return {
        "canonical_protocol": PROTOCOL_ID,
        "opportunity_sampling_policy": UTILITY_OPPORTUNITY_SAMPLING_POLICY,
        "utility_protocol_v3_frozen": True,
        "utility_protocol_audited": False,
        "utility_evaluator_implementation_ready": False,
        "utility_execution_authorization_ready": False,
        "real_hai_test_access": False,
        "real_label_access": False,
        "inner_execution": False,
        "outer_execution": False,
        "detector_integration": False,
        "rule_v2": False,
        "production_runtime": False,
        "winner": False,
    }


__all__ = [
    "AcceptedRelationBindingV3",
    "ApplicableRuleEvaluationOpportunityRecordV3",
    "ApplicableRuleEvaluationOpportunityV3",
    "AvailableSourceWindowV3",
    "AvailableTargetWindowV3",
    "ExecutableAuthorityV3",
    "FeatureSchemaEntryV3",
    "FullCensusEnumerationV3",
    "OpportunityCustodyV3",
    "NumericParameterV3",
    "P1UtilityFeatureSchemaV3",
    "RetainedSourceEventV3",
    "SourceFormationOutcomeV3",
    "TargetEvaluationOutcomeV3",
    "UnavailableSourceContextV3",
    "UnavailableTargetContextV3",
    "UTILITY_OPPORTUNITY_SAMPLING_POLICY",
    "UTILITY_SOURCE_UNIVERSE_V3",
    "UtilityProtocolV3Error",
    "abstention_rate_from_custody_v3",
    "accepted_relation_binding_v3",
    "authority_snapshot_v3",
    "build_opportunity_custody_v3",
    "build_p1_utility_feature_schema_v3",
    "derive_retained_source_events_v3",
    "enumerate_full_census_from_timeline_v3",
    "evaluate_target_response_v3",
    "executable_authority_v3",
    "form_source_opportunity_v3",
    "no_rule_diagnostic_v3",
    "opportunity_record_v3",
    "parse_raw_feature_tokens_v3",
    "parse_raw_label_tokens_v3",
    "validate_reopen_authority_v3",
    "validate_selected_feature_header_v3",
]
