# ARGOS Training Loop Audit

## Scope

- Repository: `https://github.com/microsoft/ARGOS`
- Pinned commit: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- Mode: `train-LLM-only`
- Paper: `https://arxiv.org/abs/2501.14170`
- Audit type: source inspection only; no agent, provider, rule, detector, KPI, or
  SWaT execution

## End-to-end trace

| Stage | Pinned source | Input and output | Random behavior | Split and metric | Generated-code execution | Leakage or discrepancy |
|---|---|---|---|---|---|---|
| CLI construction | `driver.py:30-139` | CLI arguments become an `Engine`; training calls `engine.run()` | `repeat` creates separate output directories | No metric yet | No | `eval-LLM-only` can repair a failing rule using test data; it is not a sealed evaluation path. |
| Dataset loading | `datasets/dataset.py:38-90` | CSV with `value,label,index` becomes data frames and chunk dictionaries | None | First `train_test_split=0.7` is train pool; final 30% is test | No | No split manifest, purge, or boundary protection. |
| Train/validation split | `datasets/dataset.py:49-61` | First 70% is split 80/20 into train and validation | None | Effective default ranges are 56% train, 14% validation, 30% test | No | This validation split was added after the historical Aggregator code. |
| Chunk construction | `datasets/dataset.py:411-422` | Each split is divided into contiguous chunks; final short chunk is retained | None | Default code/CLI chunk size is 1000 | No | Paper reports dataset-specific calibrated sizes; pinned code only consumes a supplied size. |
| Chunk sampling | `runtime/engine.py:67-68,600-606` | `sample_per_prompt` train chunks are selected | NumPy seed is fixed to 8; each index is `randint(0,1000)` and then reduced modulo chunk count | Train only | No | Sampling is reproducible only for NumPy call order. Provider output and Python retry jitter remain unseeded. |
| Detection prompt | `agent/detection_agent.py:476-570`; `agent/prompts/detection.py` | Labeled chunk text plus previous rule becomes a prompt; a fenced `inference` function is requested | LLM temperature 0.75; no provider seed | Train labels are included directly | No | Constraints are natural-language instructions, not an enforceable rule schema. |
| Rule extraction | `agent/agent.py:198-221`; `agent/detection_agent.py:493-570` | Regex extracts a Python fence containing `def inference`; text is written to a `.py` file | Provider dependent | No metric | No | It does not enforce one code fence, an import allowlist, or semantic constraints. |
| Repair | `agent/repair_agent.py:29-91` | Rule plus runtime error is sent to RepairAgent until it runs and returns the expected length | LLM temperature 0.75; repeated calls on failure | Initially the sampled train chunk | Yes: `exec(rule, local_env)` and `inference(curr_df.values)` | `run_with_timeout` currently calls the function directly; the configured inference timeout is not enforced. |
| Review regression check | `agent/review_agent.py:62-247` | Current rule is compared with previous rule; F1 regression triggers a prompt containing code, diff, metrics, and regression samples | LLM temperature 0.75 | Despite variable names such as `curr_validate_res`, rule-only mode uses the full train frame | Yes | Paper says ReviewAgent verifies validation accuracy; pinned `run()` performs this feedback decision on train performance. |
| Review result | `agent/review_agent.py:360-378` | After review converges, `run()` returns `eval_test()` | None | Test labels and a test-optimized threshold are used | Yes | Test evaluation occurs inside every training iteration. It is saved even though the pinned selector separately uses validation. |
| Error feedback loop | `runtime/engine.py:694-715` | Syntax/runtime errors from review are sent back to RepairAgent | Retry order depends on failures | The failing frame can be train or test; a failure during `eval_test()` carries test rows | Yes | Test data can enter repair feedback after a test-time runtime failure. |
| Train evaluation | `runtime/engine.py:724-761` | Full train result is saved | None | Train Point-F1, Point-F1-PA, Event-F1-PA | Yes | Diagnostic only in the pinned selector path. |
| Validation evaluation | `runtime/engine.py:763-779`; `agent/review_agent.py:248-269` | Candidate validation result is saved and passed to selector | None | Validation Event-F1-PA threshold and F1 | Yes | This is the pinned rule-only selection path. Combined `eval_val()` incorrectly routes to train combined evaluation. |
| Candidate selection | `selector/train_perf_selector.py:72-122`; `runtime/engine.py:791-817` | `rule_per_group` highest validation Event-F1-PA rules are retained and copied round-robin into `top_k` histories | Tie behavior is deterministic from list order unless previous-pipeline ranking is supplied | Validation Event-F1-PA F1 | No new execution beyond evaluation | `top_k` is candidate count; `rule_per_group` is retained count. |
| Iteration history | `runtime/engine.py:579,811-817`; `detection_agent.py:505-552` | Selected previous rule text is appended to the next DetectionAgent prompt | LLM is reset after each query | Previous code, not conversational history, carries iteration state | No at prompt assembly | `past_message_num=10` is effectively bypassed because each agent calls `reset()` after a response. |
| Early stop | `review_agent.py:270-289`; `engine.py:799-808` | Stop after three consecutive validation-F1 decreases | None | Validation F1 | Yes during validation | Tracks decreases relative to best F1, not a global post-training rule search. |
| Finalization | `runtime/engine.py:878-895` | Writes stats and last selected rule paths | None | No final metric | No | The pinned normal run has no single final sealed-test gate. Test evaluation has already happened per iteration. |
| Explicit evaluation | `driver.py:112-136`; `engine.py:1212-1233` | A supplied rule is evaluated on test | None | Test metrics | Yes | A failure may invoke RepairAgent on test data in `driver.py`. |

## Rule revision semantics

1. DetectionAgent receives labeled train chunks and the selected previous rule.
2. RepairAgent executes the candidate and changes it only after an exception or
   output-length failure.
3. ReviewAgent compares current and prior train F1. If F1 regresses, it sends
   code, a Unix `diff`, metric deltas, and selected regression samples to the
   LLM, then overwrites the candidate.
4. The engine separately evaluates each candidate on validation and retains the
   highest Event-F1-PA candidates.
5. Selected code is inserted into the next DetectionAgent prompt.

ReviewAgent is not a deterministic verifier. It is another code-generating LLM
agent whose output remains subject to execution and metric evaluation.

## What is and is not reproduced

Confirmed without execution:

- source/history alignment;
- prompt and code-fence path;
- rule capture and static/semantic analysis;
- exact Repair/Review/selection control flow;
- split, metric, threshold, and fusion code paths.

Still unverified:

- captured-rule runtime behavior;
- RepairAgent and ReviewAgent effects on real candidates;
- rule-only KPI validation/test results;
- detector-only and combined KPI results;
- paper performance claims.
