"""Record the completed independent read-only QA, bound to exact result bytes."""
from pathlib import Path
import json
from paperworks.validation_v2.exp03b_contract_v1 import require
from paperworks.validation_v2.exp03b_custody_v1 import replay, seal, publish

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / 'research_control_center/validation_v2/exp03b/execution_v2'


def main():
    result = json.loads((PUB / 'EXP03B_REVISED_RESULTS_V1.json').read_text()); replay(result)
    require(result['self_hash'] == 'a187e89e345e9f1eb42ca993c3d53c6f317a8ff5f33ee9fa7c7e8955baa962c8', 'QA_REVIEWED_RESULT_CHANGED')
    qa = seal({
        'schema': 'exp03b_execution_independent_qa_v1', 'status': 'PASS',
        'result_hash': result['self_hash'], 'reviewer_role': 'INDEPENDENT_READ_ONLY_AGENT',
        'provider_calls_by_reviewer': 0, 'scientific_reruns_by_reviewer': 0,
        'ledger_triplets_replayed': 518, 'output_records_replayed': 261,
        'independent_semantic_oracle': 'PASS_NOT_USING_FROZEN_METRIC_FUNCTIONS',
        'strict_semantic_majority': 'PASS', 'failure_no_decision_penalty': 'PASS',
        'pair_F1': {'T0': '10/13', 'T1': '9/17', 'T1-B': '4/7', 'T2': '13/18'},
        'directional_F1': {'T0': '56/69', 'T1': '34/57', 'T1-B': '32/59', 'T2': '48/65'},
        'exact_set_counts': {'T0': 18, 'T1': 12, 'T1-B': 10, 'T2': 17},
        'horizon_hits_of_39': {'T0': 28, 'T1': 17, 'T1-B': 16, 'T2': 24},
        'feedback_distinct_pairs': 22, 'verifier_repaired_distinct_pairs': 13,
        'train3_exact_repair_observations': 20, 'train3_exact_repair_distinct_pairs': 10,
        'all_seven_disposition_criteria': 'PASS',
        'descriptor_lineage_replayed': 204, 'numeric_reference_hashes_replayed': 2040,
        'fixed_numeric_policy_and_max_pooling': 'PASS',
        'train4_qa_boundary': 'FROZEN_AGGREGATE_ARITHMETIC_AND_AUTHORITY_LINEAGE_ONLY_NO_RAW_RUNTIME_RERUN',
        'public_projection': 'PASS', 'source_prompt_configuration_unchanged': True,
        'coordinator_preservation_audit': {'PILOT_blobs': 3021, 'protected_V2_blobs': 149, 'prior_EXP03B_public_files': 63, 'private_input_hash_bindings': 364, 'execution_files': 1853, 'execution_file_hash_bundle': '52ab268b424cc3ad58e235e0de50e32644d0513ef22914e690c9b804ca03e276'},
        'limitations': ['T2_ADVANTAGE_IS_VERSUS_T1B_NOT_T0', 'T0_SEMANTIC_METRICS_HIGHER', 'T2_ABSTAIN_HIGHER_THAN_T1B', 'BURDEN_IS_LEXICOGRAPHIC_NOT_COMPONENTWISE_DOMINANCE', 'NORMAL_REFERENCE_NOT_CAUSAL_OR_HELDOUT_TRUTH', 'OPPORTUNITY_RELATION_COVERAGE_NOT_RETAINED'],
        'test1': 0, 'test2': 0, 'heldout': 0, 'external_attack': 0,
        'attack_labels': 0, 'private_exposures': 0, 'next_gate': 'DG-04',
    })
    publish(PUB / 'EXP03B_EXECUTION_INDEPENDENT_QA_V1.json', qa)
    print(json.dumps({'status': 'PASS', 'qa_hash': qa['self_hash'], 'next_gate': 'DG-04'}))


if __name__ == '__main__': main()
