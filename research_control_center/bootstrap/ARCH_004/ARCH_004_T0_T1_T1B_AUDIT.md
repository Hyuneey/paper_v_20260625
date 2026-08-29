# T0 / T1 / T1-B Audit

Verdict: PASS.

- T0: `run_real_t0_v1`, deterministic local template, 0 LLM calls, 42 parsed/admissible relation outcomes.
- T1: 42 one-shot calls, 42 parsed/admissible relation outcomes.
- T1-B: 126 stateless feedback-free calls; 125 parsed, 122 admissible proposals, 3 rejected, 1 parse failure; earliest admissible selection yielded 42 accepted relations.
- T1-B and T2 are fair by maximum opportunity contract and initial input/model configuration, but realized calls differ and feedback effect is not evaluable in this cohort.
