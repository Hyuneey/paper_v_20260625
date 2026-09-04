"""Future custodian schema/release validation only; no eligibility classification."""
from __future__ import annotations
from paperworks.validation_v2.exp03b_custody_v1 import replay

STATUSES = frozenset({'P1_ELIGIBLE','CROSS_PROCESS_P1_RELEVANT','OUT_OF_SCOPE','UNRESOLVED'})
FIELDS = frozenset({'scenario_id','official_target_id','mapping_hash','status','official_source_hash'})


def _hash(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def validate_future_eligibility_record_v1(record: dict) -> None:
    """Reject outcome/prediction fields; actual records require a future custodian."""
    if set(record) != FIELDS or record['status'] not in STATUSES:
        raise ValueError('ELIGIBILITY_SCHEMA_OR_OUTCOME_TAINT')
    if not all(isinstance(record[k],str) and record[k] for k in ('scenario_id','official_target_id')):
        raise ValueError('OFFICIAL_SCENARIO_IDENTITY_REQUIRED')
    if not all(_hash(record[k]) for k in ('mapping_hash','official_source_hash')):
        raise ValueError('OFFICIAL_MAPPING_AUTHORITY_REQUIRED')


def validate_future_release_gate_v1(receipt: dict, expected_methods: dict[str,str], *, panel_id: str) -> None:
    """A hash receipt is necessary, not sufficient: outer DG05 is separately required."""
    replay(receipt)
    if (receipt.get('panel_id') != panel_id or not expected_methods or
        receipt.get('method_prediction_hashes') != expected_methods or
        any(not _hash(v) for v in expected_methods.values()) or
        receipt.get('all_predictions_durably_frozen') is not True or
        receipt.get('prediction_generators_revoked') is not True or
        receipt.get('label_access_started') is not False or
        not _hash(receipt.get('dg05_authorization_hash'))):
        raise ValueError('ELIGIBILITY_RELEASE_NOT_AUTHORIZED')
