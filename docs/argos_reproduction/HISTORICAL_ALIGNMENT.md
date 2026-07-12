# ARGOS Historical Alignment

TASK-023 resolves the source-alignment portion of DEC-027 only. It does not approve real LLM calls, unrestricted generated-Python execution, full ARGOS training, detector-plus-rule benchmarking, or changes to `src/paperworks`.

## Repository State

| Item | Value |
|---|---|
| Upstream repository | `https://github.com/microsoft/ARGOS` |
| Current upstream HEAD inspected | `6b24161ff08de069840a1fb4fbaecf7bf8e393f1` |
| Local pinned commit | `6b24161ff08de069840a1fb4fbaecf7bf8e393f1` |
| Tags/releases | No git tags found in the fetched ARGOS repository; GitHub release history was not used as a source artifact. |
| Local source policy | `external/argos` remains a read-only reference. The checkout was not moved from the pinned commit. |

The local ARGOS clone is a partial clone with `remote.origin.partialclonefilter`
set to `blob:none`. TASK-023 fetched upstream refs/tags and lazily fetched
historical README blobs for audit only.

## Commit Alignment Table

| Commit | Date | README modes | Rule-only | Combined FN/FP | Aggregator docs | Paper alignment |
|---|---|---|---|---|---|---|
| `1cfa6d3` | 2025-04-02 | Template README only | No documented ARGOS mode | No documented combined mode | No | Not aligned; repository template. |
| `5209273` | 2025-04-06 | `Argos w/o Aggregator`, `Argos w/ Aggregator`; example `train-LLM-only`, example `train-combined-fp` | Yes | Yes, at least FP documented; code history shows FN/FP paths in core commit | Yes, but base-detector artifact steps are TODO | Strongest historical README alignment for paper Aggregator narrative, but incomplete artifact instructions. |
| `c3c28af` | 2025-07-03 | Same Aggregator-oriented modes after RAI README update | Yes | Yes, FP documented | Yes, with TODO for model incorrect examples | Paper-aligned documentation retained. |
| `c03427f` | 2025-07-28 | Same Aggregator-oriented modes after release-name docs update | Yes | Yes, FP documented | Yes, with TODO for model incorrect examples | Best historical documentation candidate for detector-plus-rule alignment before README removal. |
| `6b24161` | 2026-05-13 | `train-LLM-only`, `train-LLM-only-parallel`, `train-evolution` | Yes | Code paths remain for `train-combined-fn`, `train-combined-fp`, `eval-combined`, but README no longer documents them | Removed from current README | Best rule-only target because it is current upstream HEAD and the pinned reviewed commit; combined path is underdocumented and deferred. |

## Code Path Audit

Combined detector-plus-rule code remains present at the pinned commit:

- `driver.py` accepts `train-combined-fn`, `train-combined-fp`, and
  `eval-combined`.
- `common/common.py` implements `combine_labels`:
  - `train-combined-fn`: `np.maximum(model_labels, rule_labels)`;
  - `train-combined-fp`: `np.minimum(model_labels, rule_labels)`.
- `datasets/dataset.py` expects base-detector artifacts under
  `model_res_path`, including `IncorrectIndices/train.json` with `FN` and `FP`
  segments.
- `agent/prompts/detection.py` contains combined FN/FP prompt templates.
- `agent/prompts/review.py` contains `REVIEW_AGENT_COMBINED_PROMPT`.
- `agent/review_agent.py` contains combined evaluation and inference methods.
- `runtime/engine.py` routes combined modes to combined evaluation paths.

Selector and top-k behavior exists in the current pinned commit and was touched
again in `6b24161` together with parallel/evolution changes.

## Alignment Decision

Initial rule-only reproduction is frozen as:

```yaml
initial_reproduction_mode: train-LLM-only
initial_source_commit: 6b24161ff08de069840a1fb4fbaecf7bf8e393f1
combined_mode_status: deferred
```

Rationale:

- The pinned commit is also current upstream HEAD.
- It still supports the rule-only path.
- Historical evidence does not identify a clearly better rule-only commit.
- Detector-plus-rule combined reproduction has better historical README
  alignment at `c03427f`, but its base-detector artifact workflow remains
  incomplete and should wait until rule-only behavior is reproduced.

Best detector-plus-rule candidate:

```yaml
candidate_commit: c03427f
candidate_role: historical README alignment for Aggregator documentation
status: deferred
```

If the pinned combined paths cannot be executed reproducibly with explicit
base-detector artifacts in a future task, build a minimal paper-faithful adapter
around the paper's FN/FP aggregation semantics rather than silently changing the
source pin.
