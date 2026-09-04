"""Global-only adapter into the frozen EXP03B provider projector.

No auxiliary input parameter, hidden authority, numeric role or I/O capability.
External execution must separately replay each seed's checkpoint/input custody.
"""
from .exp03b_contract_v1 import require, digest
from .exp03b_semantic_v2 import Train1SemanticEvidenceV2
from .exp03b_firewall_v1 import SplitPurePredictiveEvidenceV1
from .exp03b_firewall_v2 import project, render, assert_clean
from .xver_gdn_roles_v1 import GlobalSeedEvidenceV1, provider_global


def project_global_only(*, version: str, train1: Train1SemanticEvidenceV2,
                        global_seeds: tuple[GlobalSeedEvidenceV1, ...],
                        stat_association: float, checkpoint_receipt_hash: str) -> dict:
    require(type(train1) is Train1SemanticEvidenceV2, 'PROVIDER_TYPE_FIREWALL')
    rows = provider_global(global_seeds, version=version)
    require(all((s.source, s.target) == (train1.source, train1.target) for s in global_seeds), 'GLOBAL_PAIR_BINDING')
    require(type(checkpoint_receipt_hash) is str and len(checkpoint_receipt_hash) == 64
            and all(c in '0123456789abcdef' for c in checkpoint_receipt_hash), 'GLOBAL_CUSTODY_HASH')
    predictive = SplitPurePredictiveEvidenceV1('train1', train1.candidate_id,
        digest({'version': version, 'checkpoint_receipt_hash': checkpoint_receipt_hash,
                'train1_input_hash': train1.input_hash}), stat_association, rows)
    document = render(project(train1, predictive))
    assert_clean(document)
    require(len(document['gdn_rows']) == 5 and set(document) == {
        'candidate_id', 'source', 'target', 'split', 'structural_columns',
        'structural_rows', 'stat_association', 'gdn_columns', 'gdn_rows'}, 'CLOSED_GLOBAL_PROVIDER_SCHEMA')
    return document
