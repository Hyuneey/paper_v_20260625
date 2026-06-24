# Revision Notes — Codex Work-Order Pack v2

This revision incorporates the reviewed ARGOS and GDN repositories and SWaT data constraints.

## Global changes

1. Added local-only SWaT governance and dataset-manifest requirements.
2. Added canonical high-resolution rule view and optional GDN view.
3. Added raw-timeline split-before-windowing and purge-gap requirements.
4. Added upstream pinning, license, and third-party notice requirements.
5. Replaced direct legacy GDN dependency with a preferred modern port strategy.
6. Required CandidateUniverse masking before GDN Top-K.
7. Required candidate self-edge exclusion and self-loop separation.
8. Prohibited reuse of upstream GDN test-tuned scoring.
9. Limited ARGOS reuse to architectural concepts.
10. Prohibited `exec`, `eval`, dynamic imports, and generated Python execution.
11. Added provider-neutral LLM interfaces, mock-only CI, prompt redaction, and provenance.
12. Sealed final test until TASK-014 and disabled point adjustment by default.

## Ticket-specific changes

- TASK-000 now audits upstream revisions, licenses, environments, and local SWaT provenance.
- TASK-001 now implements dataset manifests, separate views, split-before-windowing, and purge gaps.
- TASK-002 now records metadata source and human-review status.
- TASK-003 now exports an explicit candidate mask and empty-target policy.
- TASK-004 now requires a modern masked GDN port and self-edge safeguards.
- TASK-005 uses a pre-registered relation reference, not final attack outcomes.
- TASK-006 profiles on the canonical high-resolution view and records units/provenance.
- TASK-007 defines a safe JSON/AST DSL and bans arbitrary code execution.
- TASK-008 remains the deterministic baseline.
- TASK-009 uses only the deterministic DSL evaluator.
- TASK-010 guarantees runtime LLM-free execution.
- TASK-011 is validation-only; the final test stays sealed.
- TASK-012 adds provider abstraction, mock tests, redaction, and structured JSON output.
- TASK-013 adds bounded, privacy-safe refinement with immutable variables/numbers.
- TASK-014 defines a frozen, sealed final evaluation with PA-free metrics by default.
