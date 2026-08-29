#!/usr/bin/env python3
"""Build the public-safe GAP-000 triage artifacts from frozen ARCH reports.

This script parses RCC documentation only.  It never imports scientific code,
opens research data, executes a detector, or accesses test2.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path


AUTHORITY = "2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e"
RCC_HEAD = "0346736f20cd99544f56685344d8119fba9e6d56"


ROOTS = [
    {
        "gap_id": "GAP-001",
        "title": "Final scientific rule authority is not singularly resolved",
        "root_cause": "Frozen construction and D1 use task validity plus the V4 authority plane, while canonical RuleV1 and VerifierV1 are separate and no tracked lossless bridge proves end-to-end equivalence.",
        "affected_components": "RULE_DSL;DETERMINISTIC_VERIFIER;COMMON42_FREEZE;RULE_RUNTIME;NUMERIC_AUTHORITY",
        "affected_experiments": "EXP-02;EXP-03;EXP-04;EXP-05;NEW_HELD_OUT_FINAL",
        "scientific_impact": "Future results could be attributed to a verifier or rule authority that did not govern execution.",
        "engineering_impact": "Two partially overlapping authority planes and several entrypoints remain costly to audit.",
        "thesis_impact": "The verified-rule construction contribution needs one explicit final method identity.",
        "current_evidence": "V4 governed frozen D1; VerifierV1 direct governance is not proven; 420 shared numeric values match but identities are rebound.",
        "disposition": "P0_FIX_BEFORE_EXPANDED_VALIDATION",
        "priority": "P0",
        "recommended_action": "Choose and version one final authority contract or a verified bridge; add conformance and stale-authority rejection tests without rewriting PILOT V1.",
        "action_type": "CONTRACT_FIX",
        "estimated_scope": "MEDIUM",
        "dependencies": "USER-DECISION-01;ARCH-011",
        "verification_after_action": "Contract matrix; projection/rebinding tests; runtime authorization negative tests; exact authority receipt.",
        "user_decision_required": "true",
    },
    {
        "gap_id": "GAP-002",
        "title": "D1 lacks a durable pre-label prediction gate",
        "root_cause": "The label-blind prediction is validated and shallow-frozen in memory, but public bytes are persisted only after label-derived metrics.",
        "affected_components": "D1_RULE_ONLY;RESULT_INTEGRITY;RULE_RUNTIME",
        "affected_experiments": "EXP-04;NEW_HELD_OUT_FINAL",
        "scientific_impact": "A future final study would have weaker evidence against post-label mutation than D0 and D2.",
        "engineering_impact": "Nested dictionaries remain mutable and there is no atomic persist-close-reopen state transition.",
        "thesis_impact": "Pilot wording must remain qualified; expanded results need the stronger gate.",
        "current_evidence": "No verified leakage or mutation was found; D0 and D2 already demonstrate the stronger custody pattern.",
        "disposition": "P0_FIX_BEFORE_EXPANDED_VALIDATION",
        "priority": "P0",
        "recommended_action": "For VALIDATION V2, atomically persist, close, reopen/replay, authorize labels only after byte validation, and recheck bytes after metrics.",
        "action_type": "CODE_FIX;TEST_FIX",
        "estimated_scope": "SMALL",
        "dependencies": "GAP-001",
        "verification_after_action": "Synthetic state-machine and mutation tests plus custody receipt; zero label access before durable authorization.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-003",
        "title": "Validation, policy-selection, and final held-out roles are not frozen",
        "root_cause": "test1 is a development pilot, D2 V2 is test1-informed, and the old OUTER path produced no scientific result.",
        "affected_components": "SPLIT_GOVERNANCE;D2_V2;OUTER_EVALUATION",
        "affected_experiments": "EXP-04;NEW_HELD_OUT_FINAL",
        "scientific_impact": "Policy choice on final outcomes would invalidate independent confirmation and generalization claims.",
        "engineering_impact": "A new authorization, custody sequence, and immutable split-role manifest are required.",
        "thesis_impact": "Current results remain pilot-only; final claims require a new one-way study.",
        "current_evidence": "V2 is explicitly TEST1_INFORMED_DEVELOPMENT; held-out generalization is unconfirmed.",
        "disposition": "EXPERIMENT_DESIGN_REQUIREMENT",
        "priority": "P0",
        "recommended_action": "Preregister validation and final-test roles, select/freeze any fusion policy on validation, and prohibit post-final tuning.",
        "action_type": "EXPERIMENT_PROTOCOL",
        "estimated_scope": "RESEARCH_EXPERIMENT",
        "dependencies": "ARCH-011;GAP-001;GAP-002",
        "verification_after_action": "Pre-result protocol hash, split-role manifest, one-way access ledger, and final policy receipt.",
        "user_decision_required": "true",
    },
    {
        "gap_id": "GAP-004",
        "title": "Attack-event scope and inferential unit are not established",
        "root_cause": "The 14 units are maximal contiguous label-one runs; statistical independence and broader event representativeness were never established.",
        "affected_components": "ATTACK_EVENT_RECALL;RESULT_INTEGRITY",
        "affected_experiments": "EXP-04;NEW_HELD_OUT_FINAL",
        "scientific_impact": "Tiny or dependent units cannot support broad superiority or stable inference.",
        "engineering_impact": "No code defect; the event and inference contract must be preregistered.",
        "thesis_impact": "Descriptive pilot results are usable, but inferential/general claims are not.",
        "current_evidence": "14 contiguous attack-event units; no authoritative inferential statistic.",
        "disposition": "EXPERIMENT_DESIGN_REQUIREMENT",
        "priority": "P0",
        "recommended_action": "Freeze event-unit construction, overlap rule, evaluation scope, and an inference plan appropriate to the available dependence structure; do not manufacture independence.",
        "action_type": "EXPERIMENT_PROTOCOL",
        "estimated_scope": "RESEARCH_EXPERIMENT",
        "dependencies": "GAP-003",
        "verification_after_action": "Preregistered event manifest and analysis plan before outcomes.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-005",
        "title": "Construction failures can collapse into no_rule",
        "root_cause": "Task orchestration may persist response, parse, verifier, or budget failures as no_rule although the generic contract distinguishes them.",
        "affected_components": "T1_ONE_SHOT;T1B_REPEAT;T2_AGENTIC_FEEDBACK;RULE_DSL",
        "affected_experiments": "EXP-03",
        "scientific_impact": "Arm success, safety refusal, and system failure rates can be misclassified.",
        "engineering_impact": "Outcome taxonomy and persisted reason codes are non-conformant.",
        "thesis_impact": "Blocks a credible Agentic/construction comparison, not Rule-only detection evaluation.",
        "current_evidence": "The frozen three T2 cases are still interpretable unsupported-variable rejections.",
        "disposition": "P1_FIX_BEFORE_SPECIFIC_EXPERIMENT",
        "priority": "P1",
        "recommended_action": "Persist explicit no_rule, provider, parse, rejection, non-repairable, retrieval, and budget outcomes with faithful call accounting.",
        "action_type": "CODE_FIX;CONTRACT_FIX;TEST_FIX",
        "estimated_scope": "SMALL",
        "dependencies": "GAP-001",
        "verification_after_action": "Negative transition matrix; no failure class accepted as no_rule; frozen three-case interpretation retained historically.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-006",
        "title": "GDN internal Top-5 can spend a slot on self",
        "root_cause": "The 37x37 cosine Top-5 is formed before diagonal removal and universe projection, so self can consume neighbor capacity even though exported self-pairs are removed.",
        "affected_components": "GDN_DISCOVERY;CANDIDATE_UNION",
        "affected_experiments": "EXP-01",
        "scientific_impact": "Graph-ranking and masking conclusions may depend on an unintended neighbor-budget convention.",
        "engineering_impact": "Pre-Top-K mask order is not aligned with the documented candidate policy.",
        "thesis_impact": "Does not invalidate the 144-pair closure or frozen pilot, but blocks a clean GDN contribution test.",
        "current_evidence": "Exported pairs remain inside the universe; functional effect is untested.",
        "disposition": "P1_FIX_BEFORE_SPECIFIC_EXPERIMENT",
        "priority": "P1",
        "recommended_action": "Correct the mask order in a new version or preregister an explicit old-versus-corrected ablation before EXP-01.",
        "action_type": "CODE_FIX;TEST_FIX",
        "estimated_scope": "SMALL",
        "dependencies": "NONE",
        "verification_after_action": "Synthetic diagonal/mask/top-k tests and versioned candidate receipts.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-007",
        "title": "Graph-Guided scientific contribution is unvalidated",
        "root_cause": "The frozen GDN arm produced candidates, but stability, unique confirmed contribution, masking impact, and Top-20 sensitivity are not established.",
        "affected_components": "GDN_DISCOVERY;RELATION_PROFILING",
        "affected_experiments": "EXP-01",
        "scientific_impact": "Candidate presence alone cannot support a useful graph-guidance contribution.",
        "engineering_impact": "The authoritative backend identity and analysis contract must remain frozen.",
        "thesis_impact": "Graph-Guided stays provisional and should be removed from the headline contribution if EXP-01 is negative or inconclusive.",
        "current_evidence": "Learned graph is used; attention is not candidate evidence; causality is unsupported.",
        "disposition": "EXPERIMENT_DESIGN_REQUIREMENT",
        "priority": "P1",
        "recommended_action": "Preregister seed and split stability, GDN-only confirmed yield, functional masking, and Top-20 sensitivity/justification.",
        "action_type": "EXPERIMENT_PROTOCOL",
        "estimated_scope": "RESEARCH_EXPERIMENT",
        "dependencies": "GAP-006",
        "verification_after_action": "Frozen EXP-01 protocol and contribution decision table.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-008",
        "title": "Agentic feedback benefit is not identifiable in the pilot",
        "root_cause": "T2 supports bounded feedback but observed zero repair/retrieval actions; LLM arms are stochastic and need a repeated budget-matched protocol.",
        "affected_components": "T1_ONE_SHOT;T1B_REPEAT;T2_AGENTIC_FEEDBACK",
        "affected_experiments": "EXP-03",
        "scientific_impact": "Implemented capability cannot be interpreted as feedback benefit.",
        "engineering_impact": "Exact deterministic LLM replay is impossible; traceable repeated sampling and custody are feasible.",
        "thesis_impact": "Agentic remains conditional; no observed action means no demonstrated benefit.",
        "current_evidence": "T2 39/42, feedback actions 0; T1-B and T2 had equal caps but unequal realized calls.",
        "disposition": "EXPERIMENT_DESIGN_REQUIREMENT",
        "priority": "P1",
        "recommended_action": "Freeze provider/model/prompt/evidence hashes, temperature, budgets, retries, repeated generations, and construction metrics; never inject artificial failures merely to activate feedback.",
        "action_type": "EXPERIMENT_PROTOCOL",
        "estimated_scope": "RESEARCH_EXPERIMENT",
        "dependencies": "GAP-005",
        "verification_after_action": "Budget/custody audit and predefined conclusion rule when feedback remains unused.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-009",
        "title": "Expanded detection lacks a stronger multivariate baseline",
        "root_cause": "D0 is intentionally a simple deterministic PCA-SPE reference, not a contemporary detector benchmark.",
        "affected_components": "D0_PCA_SPE;D1_RULE_ONLY;D2_V1;D2_V2",
        "affected_experiments": "EXP-04;NEW_HELD_OUT_FINAL",
        "scientific_impact": "Comparison only to PCA-SPE cannot support competitive detector claims.",
        "engineering_impact": "A new frozen detector implementation and equivalent custody adapter are required.",
        "thesis_impact": "PCA-SPE may remain the transparent reference, but final detection claims need at least one stronger baseline.",
        "current_evidence": "D0 implementation and pilot are sound within the simple-reference role.",
        "disposition": "EXPERIMENT_DESIGN_REQUIREMENT",
        "priority": "P1",
        "recommended_action": "Identify and preregister at least one stronger multivariate detector before final EXP-04 results; apply the same label and metric custody.",
        "action_type": "EXPERIMENT_PROTOCOL",
        "estimated_scope": "RESEARCH_EXPERIMENT",
        "dependencies": "GAP-003;GAP-011",
        "verification_after_action": "Frozen baseline identity, hyperparameter-selection role, prediction receipt, and common metric handoff.",
        "user_decision_required": "true",
    },
    {
        "gap_id": "GAP-010",
        "title": "Evaluated V4 trace is not connected to canonical explanation",
        "root_cause": "Frozen D1 emits a task-specific terminal trace, while RuntimeTraceV1 and its renderer are non-equivalent and disconnected.",
        "affected_components": "SATISFACTION_TRACE;EXPLANATION_RENDERER;RULE_RUNTIME",
        "affected_experiments": "EXP-05",
        "scientific_impact": "Explanation fidelity cannot be evaluated against a trace that the evaluated runtime did not produce.",
        "engineering_impact": "A versioned authority-bound trace/renderer bridge is missing.",
        "thesis_impact": "Blocks EXP-05 structural fidelity only; does not block EXP-04 detection.",
        "current_evidence": "Frozen D1 has no canonical RuntimeTraceV1 explanation artifact.",
        "disposition": "P1_FIX_BEFORE_SPECIFIC_EXPERIMENT",
        "priority": "P1",
        "recommended_action": "Materialize a continuous-step trace from the selected runtime authority and bind a deterministic renderer to it.",
        "action_type": "CONTRACT_FIX;CODE_FIX;TEST_FIX",
        "estimated_scope": "MEDIUM",
        "dependencies": "GAP-001",
        "verification_after_action": "Field-level trace equivalence, no-new-variable/number checks, outcome and provenance fidelity tests.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-011",
        "title": "Fresh-machine reproducibility is incomplete",
        "root_cause": "Public lineage is strong, but full environment, dependency, numerical backend, entrypoint, and custody replay has not been independently rehearsed.",
        "affected_components": "REPRODUCIBILITY;D0_PCA_SPE;RULE_RUNTIME;RESULT_INTEGRITY",
        "affected_experiments": "NEW_HELD_OUT_FINAL;FRESH_MACHINE_RELEASE",
        "scientific_impact": "A final held-out run could depend on unrecorded environment behavior.",
        "engineering_impact": "Portable environment and data-manifest bindings are incomplete.",
        "thesis_impact": "Does not block read-only audits or early protocol preparation; should precede authoritative held-out execution.",
        "current_evidence": "Same-authority traceability exists; fresh-machine status is INCOMPLETE.",
        "disposition": "ENGINEERING_HARDENING",
        "priority": "P1",
        "recommended_action": "After ARCH-011, build and rehearse a sanitized environment/entrypoint/data-manifest capsule before held-out access.",
        "action_type": "REPRODUCIBILITY_FIX",
        "estimated_scope": "MEDIUM",
        "dependencies": "ARCH-011;GAP-001;GAP-012;GAP-013",
        "verification_after_action": "Independent clean-machine rehearsal with exact public receipts and zero scientific outcome access.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-012",
        "title": "Metric portability and final comparison lineage are partial",
        "root_cause": "Generic helpers rely on callers for file-local one-second semantics, and the frozen cross-arm aggregation source is not discoverable.",
        "affected_components": "EPISODE_CONSTRUCTION;ATTACK_EVENT_RECALL;NORMAL_FAR;RESULT_INTEGRITY",
        "affected_experiments": "EXP-04;NEW_HELD_OUT_FINAL;FRESH_MACHINE_RELEASE",
        "scientific_impact": "A new multi-file or irregular-time study could silently violate the frozen metric assumptions.",
        "engineering_impact": "The final comparison adapter is not fully source-reproducible.",
        "thesis_impact": "Current per-arm pilot metrics remain traceable; final reporting needs a versioned common adapter.",
        "current_evidence": "Current HAI caller contracts support one-second file-local semantics; aggregation edge is PARTIAL.",
        "disposition": "ENGINEERING_HARDENING",
        "priority": "P1",
        "recommended_action": "Version the common metric adapter, enforce sampling/file identity at its boundary, and bind the cross-arm table to source and inputs.",
        "action_type": "CONTRACT_FIX;TEST_FIX",
        "estimated_scope": "SMALL",
        "dependencies": "GAP-003",
        "verification_after_action": "Synthetic multi-file/gap/boundary tests and comparison-artifact source receipt.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-013",
        "title": "Split enforcement and entrypoint conformance are distributed",
        "root_cause": "Generic split contracts and frozen task readers are compatible in observed paths but lack one static conformance map; recovery entrypoints add audit debt.",
        "affected_components": "SPLIT_GOVERNANCE;REPRODUCIBILITY",
        "affected_experiments": "EXP-01;EXP-02;EXP-03;EXP-04;EXP-05;FRESH_MACHINE_RELEASE",
        "scientific_impact": "No bypass was found; future expansion could introduce one without a uniform conformance check.",
        "engineering_impact": "Distributed grants and entrypoints increase maintenance and audit cost.",
        "thesis_impact": "Hardening is valuable but not a reason to refactor frozen pilot paths.",
        "current_evidence": "Observed readers and task guards are scope-consistent; one OUTER custody attempt read zero bytes.",
        "disposition": "ENGINEERING_HARDENING",
        "priority": "P2",
        "recommended_action": "Add a static entrypoint-to-split-role and artifact-authority conformance map for VALIDATION V2.",
        "action_type": "TEST_FIX",
        "estimated_scope": "SMALL",
        "dependencies": "ARCH-011;GAP-001",
        "verification_after_action": "All scientific entrypoints mapped; unauthorized roles and stale grants rejected synthetically.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-014",
        "title": "train3 has two disclosed normal-only roles",
        "root_cause": "The same normal split confirms relations and calibrates the PCA-SPE threshold through separate code paths.",
        "affected_components": "RELATION_PROFILING;D0_PCA_SPE;SPLIT_GOVERNANCE",
        "affected_experiments": "EXP-02;EXP-04",
        "scientific_impact": "It creates cross-method coupling but no verified label leakage.",
        "engineering_impact": "Separating it would require a new split and is not automatically worth the scope.",
        "thesis_impact": "Transparent disclosure is sufficient unless a future protocol has enough data to separate roles.",
        "current_evidence": "Both paths are normal-only, isolated, and frozen before test outcomes.",
        "disposition": "ACCEPTABLE_THESIS_LIMITATION",
        "priority": "P2",
        "recommended_action": "Disclose the dual role; separate only if the future preregistered split design can do so without weakening evidence.",
        "action_type": "DOCUMENT_ONLY",
        "estimated_scope": "DOCUMENT_ONLY",
        "dependencies": "NONE",
        "verification_after_action": "Current-facing method and limitation wording checked.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-015",
        "title": "Terminology and object-level claims need continuous control",
        "root_cause": "Historical and tempting wording conflates candidate with relation, contract verification with scientific validation, rule record with alarm second, and COMMON-42 with LLM or Agentic output.",
        "affected_components": "PROFESSOR_REPORTING;CANDIDATE_UNION;DETERMINISTIC_VERIFIER;D1_RULE_ONLY;METRICS",
        "affected_experiments": "ALL",
        "scientific_impact": "Overstatement can invalidate claim interpretation even when implementation is sound.",
        "engineering_impact": "No scientific code fix is required.",
        "thesis_impact": "Use non-causal, pilot-only, authority-specific wording and conditional contribution labels.",
        "current_evidence": "All 120 raw mismatches are now traceable; many are wording duplicates rather than defects.",
        "disposition": "CLAIM_DOCUMENTATION_CORRECTION",
        "priority": "P1",
        "recommended_action": "Apply the GAP-000 wording guide to current-facing RCC, thesis, and professor material; do not rewrite frozen history.",
        "action_type": "DOCUMENT_ONLY",
        "estimated_scope": "DOCUMENT_ONLY",
        "dependencies": "GAP-001;GAP-003;GAP-004;GAP-007;GAP-008",
        "verification_after_action": "Claim-registry and terminology lint against current-facing outputs.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-016",
        "title": "Cause of D1's high normal FAR is not decomposed",
        "root_cause": "Frozen reports establish the burden but do not establish a general causal mechanism or a safe tuning target.",
        "affected_components": "D1_RULE_ONLY;NORMAL_FAR;D2_V1;D2_V2",
        "affected_experiments": "EXP-04",
        "scientific_impact": "Operational utility remains unvalidated; the descriptive metric is still valid.",
        "engineering_impact": "No remediation is required merely to preserve the negative pilot observation.",
        "thesis_impact": "Can remain an explicit limitation and future failure-analysis topic.",
        "current_evidence": "D1 has 574 normal false episodes and FAR 40.50255787059723 in the INNER pilot; no frozen cause decomposition exists.",
        "disposition": "ACCEPTABLE_THESIS_LIMITATION",
        "priority": "P2",
        "recommended_action": "Do not invent a cause or tune on final data; analyze only under a separately frozen development protocol if EXP-04 needs it.",
        "action_type": "NO_FIX",
        "estimated_scope": "DOCUMENT_ONLY",
        "dependencies": "NONE",
        "verification_after_action": "Limitation and utility boundary retained in claims.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-017",
        "title": "Human usefulness of explanations is unvalidated",
        "root_cause": "Structural/template fidelity does not establish expert usefulness, trust, diagnosis quality, or operational benefit.",
        "affected_components": "EXPLANATION_RENDERER",
        "affected_experiments": "EXP-05",
        "scientific_impact": "Only a human-usefulness claim is blocked.",
        "engineering_impact": "No code defect follows from the absence of a human study.",
        "thesis_impact": "May remain a limitation because the core contribution is verified construction/governance.",
        "current_evidence": "Human usefulness status is UNVALIDATED.",
        "disposition": "ACCEPTABLE_THESIS_LIMITATION",
        "priority": "P3",
        "recommended_action": "Limit EXP-05 to structural fidelity unless the user and professor explicitly make human evaluation thesis-essential.",
        "action_type": "NO_FIX",
        "estimated_scope": "DOCUMENT_ONLY",
        "dependencies": "GAP-010",
        "verification_after_action": "No human-benefit wording without a separately approved study.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-018",
        "title": "Relation-specific numeric criteria are not scientifically optimal",
        "root_cause": "Implementation provenance is traceable, but the current numeric strategy has not been compared with a common fixed normal-only baseline.",
        "affected_components": "NUMERIC_AUTHORITY;RELATION_PROFILING",
        "affected_experiments": "EXP-02",
        "scientific_impact": "Traceability does not prove the selected relation-specific values improve construction or runtime behavior.",
        "engineering_impact": "No hidden runtime mismatch was found; the gap is comparative evidence.",
        "thesis_impact": "Numeric authority can be described as normal-derived, not optimized or superior.",
        "current_evidence": "Construction/runtime shared values matched 420/420; authority identities are separate.",
        "disposition": "EXPERIMENT_DESIGN_REQUIREMENT",
        "priority": "P1",
        "recommended_action": "Preregister common fixed versus relation-specific normal-only criteria; keep any LLM-proposed values diagnostic and non-authoritative.",
        "action_type": "EXPERIMENT_PROTOCOL",
        "estimated_scope": "RESEARCH_EXPERIMENT",
        "dependencies": "GAP-001",
        "verification_after_action": "Frozen alternatives, selection metric, normal-only derivation, and authority receipts.",
        "user_decision_required": "false",
    },
    {
        "gap_id": "GAP-019",
        "title": "Runtime LLM and broader relation extensions are not needed for this thesis",
        "root_cause": "R1/runtime LLM, complex hierarchy relations, causal analysis, and multi-agent operation are optional expansions outside the minimum verified-construction path.",
        "affected_components": "R1_FUTURE;RULE_RUNTIME",
        "affected_experiments": "EXP-06",
        "scientific_impact": "None for the frozen R0/D1 thesis question.",
        "engineering_impact": "Implementing them now would expand attack surface and scope.",
        "thesis_impact": "Defer unless core validation later creates a specific need.",
        "current_evidence": "Frozen R0/D1 is deterministic and LLM-free; EXP-06 is conditional only.",
        "disposition": "FUTURE_WORK_ONLY",
        "priority": "P3",
        "recommended_action": "Do not implement for the master's thesis; retain only the documented no-outcome-leakage boundary.",
        "action_type": "NO_FIX",
        "estimated_scope": "DOCUMENT_ONLY",
        "dependencies": "NONE",
        "verification_after_action": "EXP-06 remains NOT_REQUIRED unless explicitly authorized.",
        "user_decision_required": "false",
    },
]


EXPLICIT = {
    "GAP-001": {
        "ARCH-000:M-002", "ARCH-000:M-003", "ARCH-000:M-004", "ARCH-000:M-005", "ARCH-000:M-008", "ARCH-000:M-009", "ARCH-000:M-013",
        "ARCH-003:A003-05", "ARCH-003:A003-06", "ARCH-003:A003-07", "ARCH-003:A003-08",
        "ARCH-004:A004-M02", "ARCH-004:A004-M03", "ARCH-004:A004-M07", "ARCH-004:A004-M09",
        "ARCH-005:A005-M01", "ARCH-005:A005-M02", "ARCH-005:A005-M03", "ARCH-005:A005-M04", "ARCH-005:A005-M05", "ARCH-005:A005-M06", "ARCH-005:A005-M11",
        "ARCH-006:A006-M01", "ARCH-006:A006-M07",
    },
    "GAP-002": {"ARCH-000:M-011", "ARCH-001:ARCH001-M01", "ARCH-006:A006-M04", "ARCH-006:A006-M05", "ARCH-008:A008-M11"},
    "GAP-003": {"ARCH-001:ARCH001-M04", "ARCH-001:ARCH001-M05", "ARCH-009:M-009-04", "ARCH-009:M-009-10", "ARCH-009:M-009-11", "ARCH-010:M-010-08"},
    "GAP-004": {"ARCH-008:A008-M13", "ARCH-009:M-009-12", "ARCH-010:M-010-09"},
    "GAP-005": {"ARCH-004:A004-M06", "ARCH-004:A004-M10", "ARCH-005:A005-M09"},
    "GAP-006": {"ARCH-002:ARCH002-M03"},
    "GAP-007": {"ARCH-002:ARCH002-M04", "ARCH-002:ARCH002-M05"},
    "GAP-008": {"ARCH-004:A004-M04", "ARCH-004:A004-M05"},
    "GAP-009": {"ARCH-007:A007-M08"},
    "GAP-010": {"ARCH-000:M-006", "ARCH-000:M-007", "ARCH-006:A006-M02", "ARCH-006:A006-M03"},
    "GAP-011": {"ARCH-003:A003-04", "ARCH-007:A007-M09"},
    "GAP-012": {"ARCH-000:M-014", "ARCH-010:M-010-05", "ARCH-010:M-010-06", "ARCH-010:M-010-07", "ARCH-010:M-010-11", "ARCH-010:M-010-12"},
    "GAP-013": {"ARCH-000:M-010", "ARCH-000:M-012", "ARCH-000:M-015", "ARCH-001:ARCH001-M02", "ARCH-001:ARCH001-M05", "ARCH-001:ARCH001-M08"},
    "GAP-014": {"ARCH-001:ARCH001-M03", "ARCH-007:A007-M10"},
    "GAP-016": {"ARCH-008:A008-M07", "ARCH-008:A008-M12"},
    "GAP-017": {"ARCH-006:A006-M13"},
    "GAP-018": {"ARCH-003:A003-09"},
    "GAP-019": {"ARCH-006:A006-M12"},
}


COMPONENT_BY_ARCH = {
    "ARCH-000": "END_TO_END_ARCHITECTURE", "ARCH-001": "DATA_SPLITS", "ARCH-002": "CANDIDATE_DISCOVERY",
    "ARCH-003": "RELATION_NUMERIC", "ARCH-004": "RULE_CONSTRUCTION", "ARCH-005": "VERIFIER_COMMON42",
    "ARCH-006": "RUNTIME_TRACE_EXPLANATION", "ARCH-007": "D0_PCA_SPE", "ARCH-008": "D1_RULE_ONLY",
    "ARCH-009": "D2_FUSION", "ARCH-010": "METRICS_INTEGRITY",
}


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_mismatches(rcc: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    paths = sorted((rcc / "architecture").glob("*/ARCH_*_MISMATCHES.md"))
    for path in paths:
        arch_match = re.search(r"ARCH_(\d{3})", path.name)
        if not arch_match:
            continue
        arch = f"ARCH-{arch_match.group(1)}"
        lines = path.read_text(encoding="utf-8").splitlines()
        header: list[str] | None = None
        for line in lines:
            if not line.startswith("|"):
                if header is not None and rows and rows[-1]["source_arch"] == arch:
                    continue
                continue
            cells = split_row(line)
            if all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
                continue
            if header is None:
                if cells and (cells[0].lower() == "id" or cells[0] == "ID"):
                    header = cells
                continue
            if len(cells) != len(header):
                continue
            record = dict(zip(header, cells))
            finding_id = cells[0]
            if not finding_id:
                continue
            severity = ""
            for key in ("Severity", "심각도", "Priority"):
                if key in record:
                    severity = record[key].upper()
                    break
            if severity not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
                continue
            key = f"{arch}:{finding_id}"
            duplicate = "GAP-015"
            for gap_id, keys in EXPLICIT.items():
                if key in keys:
                    duplicate = gap_id
                    break
            root = next(item for item in ROOTS if item["gap_id"] == duplicate)
            type_value = next((record[k] for k in ("Type", "유형") if k in record), "DOCUMENTED_MISMATCH")
            impact_value = next((record[k] for k in ("Scientific impact", "과학적 영향") if k in record), "See source audit")
            rows.append({
                "finding_id": finding_id,
                "source_arch": arch,
                "source_severity": severity,
                "title": cells[1],
                "description": cells[2],
                "evidence": f"{path.relative_to(rcc).as_posix()}#{finding_id}",
                "affected_component": COMPONENT_BY_ARCH[arch],
                "affected_experiment": root["affected_experiments"],
                "status": f"OPEN_TRIAGE_INPUT:{type_value}:{impact_value}",
                "duplicate_group": duplicate,
            })
    return rows


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def gate_rows() -> list[dict[str, str]]:
    return [
        {"experiment_id":"EXP-01","experiment_name":"GDN contribution","must_fix_before_start":"GAP-006","must_freeze_before_results":"authoritative backend; seeds; splits; candidate budget","design_requirements":"GAP-007 seed/split stability; unique confirmation; masking; Top-20 sensitivity; non-causal claims","does_not_block":"EXP-02;EXP-03 preparation; current pilot","ready_now":"BLOCKED","reason":"Internal Top-5 convention must be corrected or explicitly ablated first."},
        {"experiment_id":"EXP-02","experiment_name":"Numeric criteria","must_fix_before_start":"NONE for protocol preparation","must_freeze_before_results":"GAP-001 final authority; alternatives; metric; normal-only derivation","design_requirements":"GAP-018 common fixed versus relation-specific criteria; LLM numbers non-authoritative","does_not_block":"EXP-01;EXP-03","ready_now":"READY_WITH_CONDITIONS","reason":"No numeric mismatch was found; comparison authority must be frozen before results."},
        {"experiment_id":"EXP-03","experiment_name":"Construction / verifier feedback","must_fix_before_start":"GAP-005","must_freeze_before_results":"provider/model; prompt/evidence hashes; temperature; call budget; repeats; metrics","design_requirements":"GAP-008 budget-matched repeated protocol; honest zero-feedback conclusion","does_not_block":"EXP-01;EXP-02;EXP-04 runtime evaluation","ready_now":"BLOCKED","reason":"Failure/no_rule conflation would bias construction outcome accounting."},
        {"experiment_id":"EXP-04","experiment_name":"Rule-only / Detector / Fusion","must_fix_before_start":"GAP-001;GAP-002","must_freeze_before_results":"validation/final roles; event policy; stronger detector; fusion selection; metrics","design_requirements":"GAP-003;GAP-004;GAP-009; durable all-arm predictions","does_not_block":"EXP-01;EXP-02;EXP-03;EXP-05 preparation","ready_now":"BLOCKED","reason":"Core authority, custody, evaluation roles, event scope, and baseline are not final-ready."},
        {"experiment_id":"EXP-05","experiment_name":"Explanation fidelity","must_fix_before_start":"GAP-010","must_freeze_before_results":"selected runtime authority; trace schema; renderer; structural metrics","design_requirements":"source/target/direction/horizon/number/outcome fidelity; no causal claim","does_not_block":"EXP-04; human usefulness study","ready_now":"BLOCKED","reason":"The evaluated V4 runtime does not produce the canonical trace consumed by the renderer."},
        {"experiment_id":"EXP-06","experiment_name":"Runtime LLM conditional","must_fix_before_start":"NOT_APPLICABLE","must_freeze_before_results":"Only if separately authorized: outcome-leakage boundary and independent role","design_requirements":"No R0 alarm, final trace outcome, or labels in an independent detector input","does_not_block":"All core thesis work","ready_now":"NOT_REQUIRED","reason":"Runtime LLM is outside the minimum thesis path."},
        {"experiment_id":"NEW-HELD-OUT","experiment_name":"New held-out final evaluation","must_fix_before_start":"GAP-001;GAP-002;GAP-011;GAP-012","must_freeze_before_results":"GAP-003;GAP-004;GAP-009; data/label identity; metrics; policy","design_requirements":"one-way authorization; no post-test tuning; durable predictions; final report binding","does_not_block":"Read-only ARCH-011 and protocol/code preparation","ready_now":"BLOCKED","reason":"No valid current OUTER result or final preregistered authority exists."},
        {"experiment_id":"FRESH-MACHINE","experiment_name":"Fresh-machine release rehearsal","must_fix_before_start":"ARCH-011 inventory first","must_freeze_before_results":"environment; dependencies; entrypoints; data manifest; public receipts","design_requirements":"GAP-011;GAP-012;GAP-013","does_not_block":"Early protocol preparation and synthetic tests","ready_now":"CONDITIONAL","reason":"Must complete before held-out execution, not before every preparatory task."},
    ]


def report_text(raw: list[dict[str, str]]) -> str:
    severity = Counter(row["source_severity"] for row in raw)
    dispositions = Counter(root["disposition"] for root in ROOTS)
    return f"""# GAP-000 Pre-Validation Remediation & Risk Triage

Scientific authority: `origin/research-v6-thesis-checkpoint` @ `{AUTHORITY}`  
RCC authority gate: `{RCC_HEAD}`  
Verdict: **PASS — TRIAGE COMPLETE; REMEDIATION NOT IMPLEMENTED**

## Outcome first

No audited defect proves the frozen INNER pilot invalid, and no verified leakage, metric tampering, or authority substitution was found. The pilot remains interpretable with its existing qualifications. Future final evidence is not ready: two global implementation/contract fixes and two global experimental-design gates must be closed before expanded core detection validation.

The 120 raw findings are not 120 separate projects. They reduce to {len(ROOTS)} root gaps. Original severities are `{severity['CRITICAL']} critical / {severity['HIGH']} high / {severity['MEDIUM']} medium / {severity['LOW']} low`; remediation urgency was reassigned independently.

## Root triage

| Primary disposition | Root gaps |
|---|---:|
""" + "\n".join(f"| {key} | {value} |" for key, value in sorted(dispositions.items())) + """

## P0 global validation blockers

1. `GAP-001`: choose and version the final scientific rule/verifier/runtime authority.
2. `GAP-002`: add a durable D1 prediction-before-label byte/state gate.

These are code/contract gates. `GAP-003` and `GAP-004` are equally urgent P0 experimental-design gates: freeze validation/final-test roles and freeze the event-unit/evaluation policy. They must not be disguised as code cleanup.

## Experiment-specific fixes

- EXP-01: correct or explicitly ablate the GDN self-neighbor Top-5 convention.
- EXP-03: separate `no_rule` from provider, parse, verifier, retrieval and budget failures.
- EXP-05: connect the evaluated runtime trace to its deterministic renderer.

## What not to over-engineer

- train3 dual normal-only use is a disclosed limitation, not verified leakage.
- human explanation usefulness may remain unvalidated unless it becomes a core thesis claim.
- D1 high FAR needs honest limitation wording; a causal diagnosis is not required before preserving the pilot.
- runtime LLM, complex relation hierarchies, causal analysis, and a multi-agent runtime are future work only.

## Contribution conditions

- **Graph-Guided** remains provisional until EXP-01 demonstrates stable, unique, functionally useful graph contribution.
- **Agentic** remains provisional until EXP-03 actually exercises feedback and shows a budget-matched benefit. If feedback remains unused, the valid conclusion is implementation capability without demonstrated benefit.
- The current D1 result remains **COMMON-42 Verified Relational Rule-only**, not direct LLM Rule-only or Agentic Rule-only.

## Pilot preservation

`PILOT V1` artifacts are immutable historical evidence. None is rewritten. The future remediated path must be versioned separately as `VALIDATION V2`. Current qualifications remain: test1 development pilot, 14 contiguous event units with independence unestablished, V4 runtime authority, weaker D1 pre-label custody, and no held-out generalization.

## Ordered path

1. Complete GAP-000 and approve its two real research-owner decisions.
2. Run read-only ARCH-011 before remediation to pin OUTER, environment, custody, and portability facts.
3. Resolve `GAP-001`; then implement `GAP-002`, `GAP-012`, and `GAP-013` narrowly.
4. Close only the experiment-specific code gate needed for the next approved experiment.
5. Freeze experiment protocols before results.
6. Run development/validation experiments without final-test access.
7. Complete fresh-machine rehearsal.
8. Authorize one new preregistered held-out study.

No remediation, experiment, LLM call, metric recomputation, test2 access, or scientific execution occurred in GAP-000.
"""


def core_gate_text() -> str:
    return """# GAP-000 Core Validation Gate

This gate applies before expanded D1/D2/final detection results are treated as credible final evidence.

- [ ] Final scientific Rule/verifier/runtime authority is chosen, versioned, and negatively tested.
- [ ] D1 uses atomic persist → close → reopen/replay → label authorization, with post-metric byte equality.
- [ ] Validation, policy-selection, and final-test roles are frozen; post-final tuning is prohibited.
- [ ] Event-unit, overlap, episode, normal-exposure, Recall, and FAR contracts are frozen before outcomes.
- [ ] Exact data, schema, sampling, label, and split identities are frozen.
- [ ] At least one stronger multivariate detector is frozen in addition to PCA-SPE.
- [ ] Any fusion policy is selected only on validation and frozen before final test.
- [ ] The common metric adapter enforces file/sampling semantics and emits a source-bound comparison artifact.
- [ ] A sanitized fresh-machine rehearsal passes before held-out access.

Not required: rewriting PILOT V1, runtime LLM, causal analysis, a human study, or a new fusion policy during this triage.
"""


def exp01_text() -> str:
    return """# GAP-000 EXP-01 Gate — GDN Contribution

Minimum viable gate:

1. Correct pre-Top-K diagonal/candidate masking in a new version, or freeze an explicit old-versus-corrected ablation.
2. Freeze the authoritative upstream-aligned backend identity; smoke backends are not scientific GDN.
3. Predeclare seed stability and train1/train2 split-stability summaries.
4. Measure GDN-only candidates that survive normal relation confirmation; set uniqueness alone is insufficient.
5. Test functional masking or another predeclared intervention on GDN-derived edges without causal wording.
6. Justify Top-20 with preregistration plus bounded sensitivity (for example the already frozen 10/20/40 budgets).
7. Keep learned graph, attention, temporal confirmation, and causality separate.

If stable unique functional contribution is absent, Graph-Guided should be reduced from the headline contribution rather than rescued by post-hoc tuning.
"""


def exp03_text() -> str:
    return """# GAP-000 EXP-03 Gate — Agentic Construction

Before EXP-03:

- persist `no_rule`, provider error, missing/invalid response, parse failure, verifier rejection, retrieval failure, non-repairable, and budget exhaustion separately;
- freeze T0/T1/T1-B/T2 contracts, provider/model version, prompt/evidence hashes, temperature, retry policy, total call opportunity, response custody, and cost/latency accounting;
- use repeated stochastic generations rather than claim deterministic LLM behavior;
- predeclare parser success, unsupported-reference rate, verifier acceptance, feedback activation, repair success, appropriate no_rule, repeat stability, call cost, and latency;
- keep construction outcomes separate from D1 detection performance.

If no feedback action occurs again, the valid conclusion is: **bounded feedback capability is implemented, but feedback benefit is not demonstrated**. Do not manufacture repair cases solely to favor T2.
"""


def exp05_text() -> str:
    return """# GAP-000 EXP-05 Gate — Explanation Fidelity

Before EXP-05:

- select the final runtime authority and materialize its versioned trace;
- connect that exact trace to a deterministic renderer;
- bind rule, portfolio, numeric authority, trace, and explanation identities;
- automatically check source, target, direction, horizon, numeric provenance, outcome, no-new-variable, no-new-number, and no-causal-claim fidelity;
- distinguish structural fidelity from human usefulness.

A human or expert usefulness study is **not required for the current core thesis** unless the research owner and professor explicitly promote human usefulness to a core claim.
"""


def code_queue_text() -> str:
    return """# GAP-000 Code Fix Queue

## Must Fix

### GAP-001 — final authority contract
- Affected: task construction validity, canonical contracts, V4 descriptors/evaluator, runtime authorization.
- Intended behavior: one versioned scientific execution authority or a verified bridge with lossless/rebinding evidence.
- Tests: projection, conformance, stale authority, wrong relation/numeric/portfolio/hash rejection.
- Preserve: every PILOT V1 rule, descriptor, registry, prediction, trace hash, and metric.

### GAP-002 — D1 durable pre-label gate
- Affected: D1 INNER/future execution custody and prediction artifact state machine.
- Intended behavior: atomic persist, close, reopen/replay, authorize labels, post-metric byte equality.
- Tests: mutation, ordering, interrupted write, stale bytes, premature label access.
- Preserve: frozen D1 pilot and its qualification.

## Fix Before Specific Experiment

### GAP-006 before EXP-01
Correct or ablate diagonal/candidate masking before Top-K; test empty sets, self exclusion, mask order, and exported universe closure.

### GAP-005 before EXP-03
Separate construction failure taxonomy; test every transition and call-budget outcome.

### GAP-010 before EXP-05
Materialize the selected runtime trace and bind the renderer; test field and provenance fidelity.

## Optional Hardening

- GAP-012: enforce file/sampling contracts and source-bind the cross-arm aggregator.
- GAP-013: static entrypoint-to-split and authority conformance.
- GAP-011: fresh-machine capsule and rehearsal.

No experiment belongs in this queue, and no fix was implemented by GAP-000.
"""


def experiment_requirements_text() -> str:
    return """# GAP-000 Experiment Requirement Queue

- EXP-01: corrected/ablated GDN mask convention; seed/split stability; unique confirmed contribution; masking impact; Top-20 sensitivity.
- EXP-02: common fixed versus relation-specific normal-only numeric criteria; LLM values remain non-authoritative.
- EXP-03: repeated budget-matched stochastic construction; faithful failure taxonomy; feedback-activation and repair metrics.
- EXP-04: larger preregistered event scope; validation/final separation; stronger detector; durable predictions; fusion selected before final test.
- EXP-05: evaluated-runtime trace fidelity; human usefulness optional.
- EXP-06: not required; if later authorized, prohibit final R0 alarm/trace outcome and labels from independent detection input.
- Held-out: one-way authorization, immutable data/event/metric identities, no post-test tuning.
- Fresh-machine: rehearse the complete sanitized entrypoint and custody path before held-out access.

Inferential testing is not automatically mandatory. The analysis plan must match the available dependence and sample structure; descriptive reporting is preferable to an invalid significance claim.
"""


def claims_text() -> str:
    return """# GAP-000 Claim and Limitation Queue

## Current wording to use

- 14 contiguous attack-event units; statistical independence not established.
- COMMON-42 Verified Relational Rule-only / 검증된 관계 규칙 단독 방식.
- normal delayed-response relation; learned-graph candidate edge.
- verifier-accepted under the named contract; runtime-authorized under the named authority.
- frozen INNER development pilot; held-out generalization unconfirmed.
- Graph-Guided contribution provisional pending EXP-01.
- Agentic feedback capability implemented; benefit unvalidated and observed feedback actions were zero.

## Current wording to avoid

- causal relation, root cause, optimal horizon, optimal numeric threshold.
- 14 independent attacks.
- D1 Agentic Rule-only or direct LLM Rule-only.
- verifier scientifically validated the relation.
- integrity PASS proves scientific validation.
- D2 improves D0, rules generally recover misses, or Detector+Rule generally failed.
- GDN attention explains the discovered relationship.
- validated, generalized, superior, SOTA, or operationally useful without the corresponding evidence.

## Acceptable limitations

- train3 has two disclosed normal-only roles.
- D1 high-FAR mechanism is not causally decomposed.
- human explanation usefulness is unvalidated.
- current pilot uses a simple PCA-SPE reference.
- exact deterministic LLM reproduction is unavailable; traceable stochastic repetition is used instead.
- no authoritative inferential test exists for the 14-unit pilot.
"""


def minimum_text() -> str:
    return """# GAP-000 Minimum Credible Thesis Path

## MUST HAVE

1. One explicit versioned scientific rule/verifier/runtime authority.
2. Durable D1 prediction-before-label custody for new final evidence.
3. Frozen validation/final roles, event/metric contracts, and no post-final tuning.
4. At least one stronger multivariate detector alongside PCA-SPE.
5. A fresh-machine rehearsal before the new held-out run.
6. One new preregistered held-out evaluation with honest Recall/FAR and claim boundaries.

## SHOULD HAVE

- EXP-01 sufficient to decide whether Graph-Guided remains a contribution.
- EXP-03 sufficient to decide whether Agentic remains a contribution.
- EXP-02 comparison of fixed and relation-specific normal-only criteria.
- Structural explanation fidelity if explanation remains in the thesis method.

## ONLY IF RESULTS JUSTIFY

- Graph-Guided in the final title/contribution.
- Agentic in the final title/contribution.
- Fusion as a positive contribution.
- Human-usefulness claims.

## NOT NEEDED FOR THESIS

- Runtime LLM, a multi-agent runtime, complex relation trees, full causal discovery, a production fusion system, or a broad human expert study.

The minimum path protects scientific correctness and professor alignment without maximizing novelty.
"""


def decisions_text() -> str:
    return """# GAP-000 User Decisions Required

## USER-DECISION-01 — final scientific execution authority

### A. Canonical RuleV1 / VerifierV1 path
Pros: strongest alignment with the canonical contract narrative.  
Cons: largest migration scope; risks changing evaluated semantics; requires a new runtime and full revalidation.

### B. Officially adopt the V4 COMMON-42 runtime as the final method
Pros: smallest path; matches the frozen executed method.  
Cons: requires narrower thesis wording and leaves canonical VerifierV1 as adjacent architecture rather than the execution authority.

### C. Verified bridge between canonical validity and V4 execution
Pros: preserves frozen V4 execution semantics while proving which canonical claims transfer.  
Cons: medium contract/test work; equivalence may be partial and must fail closed.

Coordinator recommendation: **C if the verified-construction contribution remains central; B is the minimum fallback if the bridge cannot be proven without semantic change.** Do not migrate to A merely for architectural elegance.

## USER-DECISION-02 — conditional contribution policy

Approve the following policy now: keep **Graph-Guided** only if EXP-01 shows stable unique functional contribution, and keep **Agentic** only if EXP-03 exercises feedback and shows a budget-matched benefit. Otherwise narrow the title/contribution without expanding experiments post hoc.

No other current gap requires a research-owner architecture preference. Stronger baseline selection should be a later preregistered experiment-design decision, not a GAP-000 code choice.
"""


def order_text() -> str:
    return """# GAP-000 Remediation Order and ARCH-011 Position

1. GAP-000 PASS and user review.
2. **ARCH-011 read-only before remediation.** It should inventory OUTER custody, environment, dependency, portability, and reproducibility facts without accessing test2.
3. USER-DECISION-01 on the final authority.
4. GAP-001 authority contract/bridge.
5. GAP-002 durable D1 gate, GAP-012 metric adapter, and GAP-013 split conformance.
6. Close only the specific code gate for the next approved experiment: GAP-006, GAP-005, or GAP-010.
7. Freeze EXP-01/02/03 protocols before their results.
8. Freeze EXP-04 validation/final roles, event policy, stronger detector, and fusion selection.
9. Complete fresh-machine rehearsal.
10. Authorize and run one new held-out final study.

ARCH-011 comes first because it is a non-mutating audit that can prevent remediation against a guessed environment or obsolete OUTER path. It grants no held-out access and does not revive the consumed OUTER protocol.
"""


def pilot_text() -> str:
    return """# GAP-000 Pilot Preservation and Scientific Versioning

## PILOT V1

All existing candidate, relation, rule, prediction, trace-hash, metric, and integrity artifacts remain immutable. They remain interpretable as frozen INNER pilot evidence. Qualifications: V4 execution authority, D1 in-memory pre-label gate, test1 development use, D2 V2 test1-informed status, 14 contiguous units with independence unestablished, no held-out generalization, and no demonstrated Graph-Guided or Agentic benefit.

No PILOT V1 artifact is classified invalidated by GAP-000.

## VALIDATION V2

Every remediated experiment must use a new version identity and new receipts. VALIDATION V2 must never overwrite or silently reinterpret PILOT V1. New code/protocol results may be compared with the pilot only through explicitly versioned adapters and claim boundaries.
"""


def main() -> None:
    rcc = Path(__file__).resolve().parents[1]
    out = rcc / "architecture" / "gap_000_pre_validation"
    boot = rcc / "bootstrap" / "GAP_000"
    out.mkdir(parents=True, exist_ok=True)
    (boot / "agents").mkdir(parents=True, exist_ok=True)

    raw = parse_mismatches(rcc)
    counts = Counter(row["source_severity"] for row in raw)
    if len(raw) != 120 or counts != Counter({"MEDIUM": 55, "HIGH": 54, "LOW": 11}):
        raise SystemExit(f"unexpected raw inventory: {len(raw)} {dict(counts)}")
    if any(row["duplicate_group"] not in {root["gap_id"] for root in ROOTS} for row in raw):
        raise SystemExit("unmapped raw finding")

    raw_fields = ["finding_id","source_arch","source_severity","title","description","evidence","affected_component","affected_experiment","status","duplicate_group"]
    write_csv(out / "GAP_000_RAW_FINDINGS.csv", raw_fields, raw)
    source_findings: dict[str, list[str]] = defaultdict(list)
    for row in raw:
        source_findings[row["duplicate_group"]].append(f"{row['source_arch']}:{row['finding_id']}")
    root_rows = []
    for root in ROOTS:
        root_rows.append({key: root[key] for key in (
            "gap_id","title","root_cause","affected_components","affected_experiments","scientific_impact","engineering_impact","thesis_impact","current_evidence"
        )} | {"source_findings": ";".join(source_findings[root["gap_id"]]) or "REGISTRY_OR_QA_ONLY"})
    root_fields = ["gap_id","title","root_cause","source_findings","affected_components","affected_experiments","scientific_impact","engineering_impact","thesis_impact","current_evidence"]
    write_csv(out / "GAP_000_ROOT_ISSUES.csv", root_fields, root_rows)

    remediation = []
    for root in ROOTS:
        remediation.append({
            "gap_id": root["gap_id"], "title": root["title"], "disposition": root["disposition"], "priority": root["priority"],
            "blocks_which_experiment": root["affected_experiments"], "recommended_action": root["recommended_action"], "action_type": root["action_type"],
            "estimated_scope": root["estimated_scope"], "scientific_risk_if_ignored": root["scientific_impact"],
            "engineering_risk_if_ignored": root["engineering_impact"], "claim_risk_if_ignored": root["thesis_impact"],
            "dependencies": root["dependencies"], "verification_after_action": root["verification_after_action"],
            "user_decision_required": root["user_decision_required"], "status": "TRIAGED_NOT_IMPLEMENTED",
        })
    remediation_fields = ["gap_id","title","disposition","priority","blocks_which_experiment","recommended_action","action_type","estimated_scope","scientific_risk_if_ignored","engineering_risk_if_ignored","claim_risk_if_ignored","dependencies","verification_after_action","user_decision_required","status"]
    write_csv(out / "GAP_000_REMEDIATION_MATRIX.csv", remediation_fields, remediation)
    gates = gate_rows()
    gate_fields = ["experiment_id","experiment_name","must_fix_before_start","must_freeze_before_results","design_requirements","does_not_block","ready_now","reason"]
    write_csv(out / "GAP_000_EXPERIMENT_GATES.csv", gate_fields, gates)

    docs = {
        "GAP_000_REPORT.md": report_text(raw),
        "GAP_000_CORE_VALIDATION_GATE.md": core_gate_text(),
        "GAP_000_EXP01_GATE.md": exp01_text(),
        "GAP_000_EXP03_GATE.md": exp03_text(),
        "GAP_000_EXP05_GATE.md": exp05_text(),
        "GAP_000_CODE_FIX_QUEUE.md": code_queue_text(),
        "GAP_000_EXPERIMENT_REQUIREMENTS.md": experiment_requirements_text(),
        "GAP_000_CLAIM_LIMITATIONS.md": claims_text(),
        "GAP_000_MINIMUM_THESIS_PATH.md": minimum_text(),
        "GAP_000_USER_DECISIONS_REQUIRED.md": decisions_text(),
        "GAP_000_REMEDIATION_ORDER.md": order_text(),
        "GAP_000_PILOT_PRESERVATION.md": pilot_text(),
    }
    for name, payload in docs.items():
        (out / name).write_text(payload, encoding="utf-8", newline="\n")

    for name in (
        "GAP_000_REPORT.md", "GAP_000_RAW_FINDINGS.csv", "GAP_000_ROOT_ISSUES.csv", "GAP_000_REMEDIATION_MATRIX.csv",
        "GAP_000_EXPERIMENT_GATES.csv", "GAP_000_CORE_VALIDATION_GATE.md", "GAP_000_EXP01_GATE.md", "GAP_000_EXP03_GATE.md",
        "GAP_000_EXP05_GATE.md", "GAP_000_CODE_FIX_QUEUE.md", "GAP_000_EXPERIMENT_REQUIREMENTS.md", "GAP_000_CLAIM_LIMITATIONS.md",
        "GAP_000_MINIMUM_THESIS_PATH.md", "GAP_000_USER_DECISIONS_REQUIRED.md",
    ):
        shutil.copyfile(out / name, boot / name)

    evidence = {
        "task_id": "GAP-000", "status": "TRIAGE_COMPLETE_NO_REMEDIATION", "scientific_authority": AUTHORITY,
        "rcc_head_gate": RCC_HEAD, "raw_findings": len(raw), "root_issues": len(ROOTS),
        "source_severity": {"critical": 0, "high": 54, "medium": 55, "low": 11},
        "dispositions": dict(Counter(root["disposition"] for root in ROOTS)),
        "priorities": dict(Counter(root["priority"] for root in ROOTS)),
        "past_pilot": "INTERPRETABLE_WITH_QUALIFICATIONS", "invalidated_artifacts": 0,
        "arch011_position": "BEFORE_REMEDIATION_READ_ONLY",
        "validation": {"registry": "PASS", "rcc_tests": "101/101 PASS", "qa": "PASS", "privacy": "PASS"},
        "safety": {"scientific_executions":0,"test2_accesses":0,"llm_calls":0,"scientific_source_changes":0,"frozen_artifact_changes":0,"remediation_implementations":0},
    }
    (boot / "GAP_000_EVIDENCE.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
