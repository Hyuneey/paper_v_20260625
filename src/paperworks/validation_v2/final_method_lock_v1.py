"""Prospective DG-04 method lock; no data loading or scientific computation."""
from __future__ import annotations

from .exp03b_contract_v1 import require
from .exp03b_custody_v1 import seal, replay

BASELINE = 'f7a9296f79aed963daee8ee12afd20cbc093ff91'
RESULT_HASH = 'a187e89e345e9f1eb42ca993c3d53c6f317a8ff5f33ee9fa7c7e8955baa962c8'
QA_HASH = 'f6bf6d42a0dc9cd240d4c3e1a3afec811461f92f2ac3c2bda8b8090c6aded447'
TITLE = ('Verifier-Guided Agentic Relational Rule Induction '
         'with GDN-Based Learned-Graph Evidence '
         'for Explainable Multivariate Time-Series Anomaly Detection')
NUMERIC_POLICY = 'RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05'


def method_lock(result: dict, qa: dict) -> dict:
    """Bind the explicit user decision to immutable independently audited results."""
    replay(result); replay(qa)
    require(result['self_hash'] == RESULT_HASH and qa['self_hash'] == QA_HASH,
            'BLOCKED_CURRENT_AUTHORITY_MISMATCH')
    require(qa['status'] == 'PASS' and qa['result_hash'] == RESULT_HASH,
            'BLOCKED_CURRENT_AUTHORITY_MISMATCH')
    return seal({
        'schema': 'final_method_and_scoped_agentic_lock_v1',
        'decision_id': 'DEC-025', 'status': 'APPROVED_WITH_SCOPED_AGENTIC_CLAIM',
        'decision_source': 'EXPLICIT_USER_DG04_XVER_PREP_001',
        'integration_baseline': BASELINE, 'title': TITLE,
        'result_hash': RESULT_HASH, 'independent_qa_hash': QA_HASH,
        'supported_claim': 'Verifier-guided feedback improved LLM-based semantic Rule induction relative to matched-maximum-budget independent generation T1-B under the frozen normal-only EXP-03B protocol.',
        'required_limitation': 'T2 did not outperform deterministic T0 on the principal semantic induction metrics.',
        'roles': {'META+STAT': 'PRIMARY_CANDIDATE_PAIR_AUTHORITY',
                  'GDN': 'CORE_LEARNED_GRAPH_EVIDENCE_MODULE_NOT_CANDIDATE_DETECTOR_CAUSAL_OR_NUMERIC_AUTHORITY',
                  'T0': 'STRONG_SAME_INFORMATION_DETERMINISTIC_BASELINE',
                  'T2': 'VERIFIER_GUIDED_AGENTIC_SEMANTIC_RULE_INDUCTION',
                  'SCI02B': 'DETERMINISTIC_POST_INDUCTION_NUMERIC_BINDING',
                  'FormalV4': 'EXECUTABLE_RULE_AUTHORITY',
                  'train4': 'ONE_WAY_NORMAL_GUARD',
                  'fusion': 'PREREGISTERED_COMPARISON_NOT_CONTRIBUTION_NO_REDESIGN',
                  'explanation': 'STRUCTURAL_FIDELITY_SUPPORTED_HUMAN_USEFULNESS_UNVALIDATED'},
        'contributions': [
            'Multi-source relational evidence combining domain/statistical candidate evidence with GDN-based learned-graph evidence.',
            'Verifier-guided Agentic semantic Rule induction with bounded feedback and hidden normal-data verification.',
            'Deterministic post-induction numeric binding, Formal V4 conversion, and normal-operation guard.',
            'Executable relational anomaly analysis and trace-grounded structural explanation.'],
        'research_questions': [
            'Can domain, statistical, and GDN-based learned-graph evidence be converted into empirically confirmed relational Rule candidates?',
            'Can bounded verifier feedback improve LLM-based semantic Rule induction over one-shot and matched-budget independent generation?',
            'How do deterministic Rule-only, Agentic Rule-only, Detector-only, and Detector+Rule methods differ in attack response and false burden?',
            'Are generated explanations structurally faithful to actual Formal V4 runtime traces?'],
        'claim_status': {'rule_induction': 'SUPPORTED_DEVELOPMENT_NORMAL_ONLY',
                         'agentic_feedback': 'SUPPORTED_VS_T1B', 'agentic_vs_T0': 'NOT_SUPPORTED',
                         'agentic_attack_detection_utility': 'UNVALIDATED',
                         'cross_version_generalization': 'UNVALIDATED'},
        'numeric_policy': NUMERIC_POLICY, 'numeric_reselection_allowed': False,
        'T0_repeat': 'DETERMINISTIC_SINGLE_RUN_REFERENCE', 'T2_portfolio_repeat': 1,
        'V2A_role': 'EVIDENCE_RICH_DETERMINISTIC_REFERENCE_PORTFOLIO',
        'primary_methods': {'H0': 'PCA-SPE', 'H1': 'T0_RULE_ONLY', 'H2': 'T2_RULE_ONLY',
                            'H3': 'PCA_SPE_PLUS_T0', 'H4': 'PCA_SPE_PLUS_T2'},
        'secondary_methods': {'S0': 'ISOLATION_FOREST', 'S1': 'IF_PLUS_T2',
                              'S2': 'V2A_RULE_ONLY', 'S3': 'V2A_FUSION_CONTINUITY_WHERE_NEEDED'},
        'fusion': {'same_file': True, 'same_physical_second': True,
                   'outcomes': ['FAIL'], 'minimum_distinct_physical_sources': 2,
                   'preserve_base_detector_alarm_pointwise': True},
        'additional_agentic_rescue_allowed': False, 'provider_calls_allowed': False,
        'attack_access_allowed': False, 'production_authorized': False,
        'next_provider_gate': 'DG-03C', 'attack_gate': 'DG-05', 'submission_gate': 'DG-06',
    })
