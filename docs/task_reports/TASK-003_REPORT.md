# TASK-003 Completion Report

## Summary

Implemented a deterministic, provenance-aware candidate-universe builder with explicit target-major masks for downstream GDN Top-K filtering. The module supports domain, normal-only statistical, and explicit fallback origins while preserving per-pair provenance and empty-target reporting.

## Changed files

- `src/paperworks/__init__.py`
- `src/paperworks/candidates/__init__.py`
- `src/paperworks/candidates/universe.py`
- `configs/candidates/swat_candidate_policy.json`
- `tests/test_candidate_universe.py`
- `docs/CANDIDATE_UNIVERSE.md`
- `docs/DECISIONS_REQUIRED.md`
- `TASKS/TASK-003_CANDIDATE_UNIVERSE_BUILDER.md`
- `docs/task_reports/TASK-003_REPORT.md`

## Interfaces added or changed

Added:

- `CandidatePolicy`
  - `CandidatePolicy.from_dict()`
- `CandidatePair`
- `CandidateTargetStatus`
- `CandidateUniverseArtifact`
- `CandidateUniverseError`
- `build_candidate_universe()`
- `candidate_mask()`
- `indexed_candidates_by_target()`

Changed:

- Root package export now includes `candidates`.

## Design decisions and rationale

- Used a target-major mask contract: `mask[target_index][source_index]`.
- Excluded candidate self-edges at the schema and builder level.
- Kept source-target direction explicit in every `CandidatePair`.
- Required every allowed pair to include at least one origin.
- Merged origins when multiple mechanisms select the same pair.
- Enforced `train_candidate_learner` split permission before building candidates.
- Required explicit normal data for statistical candidates.
- Left statistical and fallback origins disabled in the default SWaT policy to avoid unapproved research choices.
- Added DEC-008 and DEC-009 for candidate feasibility criteria and real-data policy activation.

## Commands run

```powershell
$env:PYTHONPATH="C:\Users\hyun\Desktop\paperworks\260625\src"
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_candidate_universe -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m compileall -q src tests
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m json.tool configs\candidates\swat_candidate_policy.json
git ls-files dataset external
```

## Test, lint, and type-check results

Unit tests:

```text
Ran 31 tests
OK
```

Candidate-specific tests:

```text
Ran 12 tests
OK
```

`compileall` passed. JSON validation passed for the candidate policy config. Dedicated lint/type-check commands are not configured yet.

## Artifacts produced

- `configs/candidates/swat_candidate_policy.json`
- `docs/CANDIDATE_UNIVERSE.md`
- `docs/task_reports/TASK-003_REPORT.md`

No raw SWaT rows, derived windows, GDN outputs, or candidate result artifacts from real data were produced.

## Research-invariant checks

- No test split is accepted by candidate-universe construction.
- Statistical origin tests use synthetic normal data only.
- No attack labels or held-out intervals are used.
- Candidate relations are not described as causal.
- No SWaT relation pairs are hard-coded in library logic.
- Runtime LLM behavior is unaffected.
- GDN self-loops remain separate from persisted candidate edges.

## Known limitations

- The default SWaT policy enables only metadata same-stage candidates.
- Statistical Top-M is implemented as absolute lagged Pearson over caller-supplied normal data; it has not been approved for real SWaT smoke runs yet.
- Fallback expansion is explicit and tested, but disabled in the default SWaT policy.
- No persisted real-data candidate artifact was generated in TASK-003.

## Unresolved decisions / recommended next task

Open decisions:

- DEC-008: Candidate feasibility gate criteria before TASK-005.
- DEC-009: Whether to enable statistical and fallback origins on real SWaT smoke runs.
- DEC-007 remains open for final evaluation provenance.

Recommended next task:

- TASK-004: Modern GDN candidate extraction with CandidateUniverse mask enforcement.
