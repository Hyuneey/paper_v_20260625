# Upstream Sources

## microsoft/ARGOS

- Repository: https://github.com/microsoft/ARGOS
- Local reference path: `external/argos`
- Pinned commit: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- Commit summary: `6b24161 Add rule mutation implementation, parallel training, and OpenEvolve baseline (#13)`
- License: MIT
- Code copied or adapted: none in TASK-000

### Files inspected

- `pyproject.toml`
- `requirements.txt`
- `LICENSE`
- `README.md`
- `datasets/dataset.py`
- `runtime/engine.py`
- `runtime/server.py`
- `agent/detection_agent.py`
- `agent/repair_agent.py`
- `agent/review_agent.py`
- `agent/mutate_agent.py`
- `agent/prompts/detection.py`
- `agent/prompts/repair.py`
- `agent/prompts/review.py`
- `selector/train_perf_selector.py`
- `eval_metrics/point_f1.py`
- `eval_metrics/point_f1pa.py`
- `eval_metrics/event_f1pa.py`
- `driver.py`

### Concepts to reuse

- Training-time planner/repair/review loop.
- Verifier feedback as a structured refinement signal.
- Rule ranking/selection as a separate stage.
- Distinction between generated candidate rules and runtime rule execution.

### Code or behavior not to reuse

- Univariate `value,label,index` dataset contract.
- LLM-generated Python as the rule artifact.
- `exec`-based or dynamically loaded rule execution.
- Test-set evaluation during rule construction or repair.
- Point-adjusted F1 as the default evaluation metric.
- Azure/OpenAI-specific coupling in core logic.

### Findings

ARGOS is useful as an architectural reference, but it directly conflicts with this project's safety and split policies. This project must parse LLM output as JSON DSL, then evaluate only through deterministic DSL/runtime code.

### TASK-022 reproduction-audit notes

- Code copied: none.
- Code adapted: none.
- Additional files inspected:
  - `common/common.py`
  - `datasets/dataset.py`
  - `runtime/engine.py`
  - `agent/agent.py`
  - `agent/prompts/detection.py`
  - `agent/prompts/review.py`
- Paper reference inspected: `https://arxiv.org/abs/2501.14170`
- Current README documents `train-LLM-only`, `train-LLM-only-parallel`, and `train-evolution`.
- Current code still exposes `train-combined-fn`, `train-combined-fp`, and `eval-combined`.
- Detector-plus-rule Aggregator reproduction remains an alignment issue because combined code paths are present but underdocumented in the pinned README.
- Historical README inspection is unresolved because the local ARGOS clone is partial and older blobs require remote fetch.
- No real provider was called, no generated Python was executed, and no full ARGOS experiment was run in TASK-022.

### TASK-023 historical-alignment notes

- Code copied: none.
- Code adapted: none.
- Current upstream HEAD inspected: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`.
- Local pinned commit retained: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`.
- Git tags found: none.
- Historical README commits inspected:
  - `1cfa6d3` initial template README,
  - `5209273` core README with `Argos w/o Aggregator` and `Argos w/ Aggregator`,
  - `c3c28af` RAI README update retaining Aggregator docs,
  - `c03427f` release-name README update retaining Aggregator docs,
  - `6b24161` current README documenting `train-LLM-only`, `train-LLM-only-parallel`, and `train-evolution`.
- Initial rule-only reproduction target selected:
  - mode: `train-LLM-only`,
  - commit: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`.
- Combined detector-plus-rule reproduction remains deferred.
- Historical detector-plus-rule documentation candidate: `c03427f`.
- TASK-023 added an offline mock-only harness under `experiments/argos_reproduction/`; it does not import upstream ARGOS into production runtime and does not execute actual LLM-generated Python.

### TASK-024 KPI preparation and sandbox-smoke notes

- Code copied from ARGOS: none.
- Code adapted from ARGOS: none.
- Pinned ARGOS README references `utility/generate_csv.py`, but TASK-024 did
  not find a compatible `generate_csv.py` preprocessing script in the inspected
  ARGOS history.
- TASK-024 therefore added a minimal KPI-to-ARGOS adapter under
  `experiments/argos_reproduction/`, not under `src/paperworks`.
- External KPI dataset source:
  - repository: `https://github.com/NetManAIOps/KPI-Anomaly-Detection`,
  - source commit: `d06bda15d511d930cbf4e6a6de14bd94d790f0f2`,
  - train package: `Finals_dataset/phase2_train.csv.zip`,
  - ground-truth package: `Finals_dataset/phase2_ground_truth.hdf.zip`.
- Selected KPI ID for fixed-rule smoke:
  `05f10d3a-239c-3bef-9bdc-a2feeb0037aa`.
- Downloaded packages, extracted files, and converted ARGOS CSVs are local
  ignored artifacts only and are not tracked.
- TASK-024 executed only the repository-owned fixed mock rule from TASK-023.
  No real provider was called and no actual LLM-generated Python was executed.

### TASK-025 prompt-fidelity notes

- Code copied from ARGOS: none.
- Code adapted from ARGOS: none.
- Prompt template referenced:
  `external/argos/agent/prompts/detection.py::DETECTION_AGENT_V3_DEFAULT_PROMPT_TEMPLATE`.
- Mode-selection files inspected:
  - `external/argos/driver.py`,
  - `external/argos/runtime/engine.py`.
- Runtime prompt assembly file inspected:
  `external/argos/agent/detection_agent.py`.
- Code-fence extraction reference inspected:
  `external/argos/agent/agent.py::Agent.extract_code`.
- Dataset chunking reference inspected:
  `external/argos/datasets/dataset.py`.
- TASK-025 reconstructs the first DetectionAgentV3 prompt request by reading
  ARGOS prompt source as text/AST, not by importing upstream ARGOS.
- TASK-025 does not run RepairAgent, ReviewAgent, full ARGOS training,
  detector-plus-rule combined mode, real provider calls, or generated Python.

### TASK-026 one-shot capture notes

- Code copied from ARGOS: none.
- Code adapted from ARGOS: none.
- Frozen prompt request source: TASK-025 private request hash
  `14af5d91248f3ca579a445527768264f148497d58d85b49b96b39b8873918aca`.
- TASK-026 adds a provider-gated capture harness under
  `experiments/argos_reproduction/`.
- The harness may inspect one captured provider response or one manual response,
  extract a Python code fence, and run static AST diagnostics.
- TASK-026 does not execute generated Python, run RepairAgent or ReviewAgent,
  run ARGOS training, run detector-plus-rule combined mode, evaluate KPI
  performance, or access SWaT.
- TASK-026 made two approved provider requests, both rejected during provider
  validation before a rule response was produced.
- DEC-029 separately approves one TASK-026R compatibility-remediation request
  with the frozen request hash and `temperature` omitted.
- TASK-026R uses a private one-shot call receipt and does not execute captured
  Python or modify upstream ARGOS.
- TASK-026Q made one post-quota-remediation request with the same frozen ARGOS
  prompt request and captured one response from `gpt-5.6-luna`.
- The captured code was statically analyzed and quarantined only. It was not
  executed, and no ARGOS benchmark or KPI performance evaluation was run.

### TASK-027 semantic-audit notes

- Upstream snapshot remains pinned at
  `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`; no upstream file was modified.
- TASK-027 audits only the fixed TASK-026Q rule hash
  `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659`.
- The audit uses Python AST parsing and redacted expressions. It does not import
  or execute the captured rule.
- No ARGOS module was copied or adapted into `src/paperworks`.
- The future execution boundary is container-only, remains unapproved, and has
  no restricted-subprocess fallback.

### TASK-029 Review, Repair, selection, and fusion audit notes

- Code copied from ARGOS: none.
- Code adapted from ARGOS: none.
- Production imports from ARGOS: none.
- Pinned rule-only commit inspected:
  `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`.
- Historical Aggregator candidate inspected:
  `c03427f2ab16e377946d4c1176585156ddae7254`.
- Pinned files inspected:
  - `runtime/engine.py`,
  - `agent/agent.py`,
  - `agent/detection_agent.py`,
  - `agent/repair_agent.py`,
  - `agent/review_agent.py`,
  - `agent/prompts/detection.py`,
  - `agent/prompts/review.py`,
  - `selector/train_perf_selector.py`,
  - `datasets/dataset.py`,
  - `common/common.py`,
  - `driver.py`,
  - evaluation metric implementations used by `ReviewAgent`.
- Historical artifacts inspected through Git object history:
  - `README.md`,
  - `runtime/engine.py`,
  - `agent/review_agent.py`,
  - `selector/train_perf_selector.py`,
  - `eval_metrics/point_f1.py`.
- Paper inspected: `https://arxiv.org/abs/2501.14170`.
- The pinned selector ranks rule-only candidates on validation Event-F1-PA,
  while the historical candidate ranks on train point F1.
- Combined FN/FP code remains identifiable, but the pinned README no longer
  documents it and detector artifact generation is external and incomplete.
- TASK-029's prediction evaluation harness reimplements only the elementary
  binary `max`/`min` composition semantics outside `src/paperworks`; it never
  imports or executes upstream generated rules.
- No provider, agent, detector, KPI, SWaT, or generated-code execution occurred.

### TASK-030 proposed-method contract notes

- No new ARGOS or GDN source file was inspected or executed.
- Frozen ARGOS audit commits remain:
  - rule-only: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`,
  - historical Aggregator: `c03427f2ab16e377946d4c1176585156ddae7254`.
- ARGOS code copied: none.
- ARGOS code adapted into `src/paperworks`: none.
- ARGOS remains prior work, a reproduction target, and rule/fusion baseline;
  it is not a production dependency.
- The proposed contract replaces unrestricted Python with a project-owned JSON
  DSL, deterministic calibration records, a non-overridable verifier, and an
  LLM-free runtime.
- ARGOS min/max fusion semantics are retained only as predeclared baselines.
- TASK-030 accessed no upstream checkout, captured rule, provider, detector,
  KPI, SWaT, WADI, or Kaggle data.

### TASK-034 ARGOS split and metric fidelity references

- Reference commit: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`.
- Read-only files and Git blob hashes:
  - `datasets/dataset.py`: `6a018dddd0a50d2498706e11fad25febb25ba438`
  - `common/common.py`: `2c1bd7546df4c547770b6055eea49ea169ea64a4`
  - `eval_metrics/point_f1.py`: `a96440baf55a0859a7d08831eeaee6871d170bf1`
  - `eval_metrics/point_f1pa.py`: `ec4b57072086fb907b23b6cce73cb50585c17c42`
  - `eval_metrics/event_f1pa.py`: `ef7c77ab087500b70ada062f81d75d0125258348`
  - `agent/review_agent.py`: `83936fdfc2875d245f79cd556b9ded96c6d1af25`
- Code copied into `src/paperworks`: none.
- Project-owned reproduction code is isolated under
  `experiments/argos_reproduction/` and preserves validation-only split,
  smoothing, metric-search, and tie behavior.
- Upstream ARGOS modules, agents, provider paths, detector paths, and test
  evaluation were not executed. TASK-034 executed only the frozen captured rule
  in the dedicated validation container; host metric code reproduced the pinned
  source behavior from the recorded blobs.

### TASK-032A schema validation dependency

- Package source: https://github.com/python-jsonschema/jsonschema
- Direct package: `jsonschema[format-nongpl]==4.26.0`
- License: MIT
- Validator: `jsonschema.validators.Draft202012Validator`
- Role: structural validation of the seven canonical TASK-030 schemas.
- Format validation: explicitly enabled for `date` and `date-time`.
- Canonical schema source: existing files under `schemas/`; no schema copy was
  created and no TASK-030 schema was modified.
- Code copied or adapted: none; the project uses the public package API.
- Semantic checks remain project-owned and are not implemented by TASK-032A.

## d-ailin/GDN

- Repository: https://github.com/d-ailin/GDN
- Local reference path: `external/gdn`
- Pinned commit: `9853899da860682669a134e4af315d036aab4eca`
- Commit summary: `9853899 add some process scripts and readme`
- License: MIT
- Code copied or adapted: none in TASK-000

### Files inspected

- `README.md`
- `install.sh`
- `LICENSE`
- `main.py`
- `train.py`
- `test.py`
- `evaluate.py`
- `models/GDN.py`
- `models/graph_layer.py`
- `datasets/TimeDataset.py`
- `scripts/process_swat.py`
- `util/preprocess.py`
- `util/net_struct.py`
- `util/data.py`
- `util/iostream.py`

### Concepts to reuse

- Sensor/node ID embeddings.
- Cosine similarity over learned embeddings.
- Top-K learned graph as a relation-candidate source.
- Graph-attention forecasting architecture.

### Required adaptations

- Port to modern supported PyTorch/PyG.
- Apply `CandidateUniverse C_i` mask before Top-K.
- Exclude self-edges from persisted candidate-relation artifacts.
- Keep message-passing self-loops separate from exported candidate relations.
- Export stable candidate-edge artifacts with source, target, rank, score, K, seed, feature order, source view, and provenance.

### Code or behavior not to reuse

- Legacy Python/PyTorch/PyG dependency stack as the main environment.
- `report=best` or any test-label threshold selection.
- Original temporal split/windowing behavior without split-before-windowing review.
- Original SWaT preprocessing/downsampling without explicit approval.

### Findings

GDN's `models/GDN.py` computes cosine similarity over all node embeddings and calls `torch.topk` over the full similarity matrix. It does not apply this project's per-target candidate mask before Top-K. `models/graph_layer.py` removes and then adds self-loops for message passing, so candidate relation export must explicitly distinguish relation artifacts from internal self-loops.

### TASK-004 adaptation notes

- Code copied: none.
- Code adapted: none.
- Conceptually reimplemented:
  - node-embedding cosine similarity,
  - Top-K graph extraction,
  - self-loop separation for message passing.
- Project-specific changes:
  - `CandidateUniverse` mask is applied before Top-K,
  - persisted candidate self-edges are rejected,
  - candidate edges include `candidate_universe_id`, `feature_order_hash`, `checkpoint_id`, source view, sampling period, K, seed, rank, and candidate origins.
- TASK-004 implementation:
  - added a project-owned CPU PyTorch/PyG synthetic trainer in `src/paperworks/gdn/torch_backend.py`,
  - uses PyG `MessagePassing` for mean neighbor aggregation,
  - keeps learned embedding export and masked candidate-edge export under project-owned schemas,
  - does not copy upstream modules.

## TASK-035A upstream alignment

- ARGOS reference commit:
  `6b24161ff08de069840a1fb4fbaecf7bf8e393f1` (MIT, read-only).
- Prompt source: `agent/prompts/detection.py`,
  `DETECTION_AGENT_V3_DEFAULT_PROMPT_TEMPLATE`, and
  `build_detection_agent_v3_prompt` semantics.
- Sample serialization source: `agent/detection_agent.py`,
  `curr_df.to_string(index=False, header=False)`.
- Intentional deviation: deterministic pre-registered anomaly-anchor coverage
  replaces seeded random chunk selection; all requests are independent first
  iterations without prior rule history, RepairAgent, or ReviewAgent.
- KPI source repository: `https://github.com/NetManAIOps/KPI-Anomaly-Detection`
  at `d06bda15d511d930cbf4e6a6de14bd94d790f0f2`.
- TASK-035A permits only the previously acquired public
  `Finals_dataset/phase2_train.csv.zip` package. Ground-truth and competition
  test packages are prohibited.
- Code copied: none. Prompt text is reconstructed from the pinned read-only
  source by the existing AST-based fidelity helper.

## TASK-035AR upstream alignment

- ARGOS and KPI upstream revisions remain identical to TASK-035A.
- The same 50 private anchor artifacts and exact TASK-035A prompt bytes are
  hash-verified before use.
- No upstream source or prompt text is changed. The only execution difference
  is the provider maximum output-token budget, increased from 2,000 to 6,000.
- No upstream code is copied or adapted by TASK-035AR.

## TASK-037A EasyTSAD detector audit

- Official repository: https://github.com/dawnvince/EasyTSAD
- Ignored local reference: `external/easytsad`
- Frozen commit: `55eff2c6d62f9c792bf6253c046dcc04636efe5a`
- Commit date: `2024-08-23T11:57:57+08:00`
- Package version at commit: `0.2.0.2`
- License: GPL-3.0
- Selection rationale: last official repository revision before the January
  2025 ARGOS paper release. This is a time-bounded closest source, not proof of
  the exact ARGOS experiment revision.
- Inspected: both LSTMAD method/config/dataset directories, Naive/BaseSchema,
  data loading/normalization, PointF1PA/EventF1PA, package metadata and license.
- Exact file hashes: `TASK-037A_SOURCE_ALIGNMENT_REPORT.json`.
- Code copied into production: none. The source is copied only into an ignored
  ephemeral detector-image build context for synthetic preflight.
- Compatibility deviation: the synthetic wrapper supplies the unused
  `PathManager` import boundary without loading plotting/controller modules and
  explicitly left-pads source scores for full input alignment. Upstream files
  are unchanged.
- Primary paper source: https://arxiv.org/abs/2501.14170
- Official package metadata: https://pypi.org/project/EasyTSAD/

## TASK-037B EasyTSAD execution alignment

- Reuses unchanged EasyTSAD `0.2.0.2` commit
  `55eff2c6d62f9c792bf6253c046dcc04636efe5a` and the source hashes frozen by
  TASK-037A.
- Executes official `LSTMADalpha` and `LSTMADbeta` classes with their official
  default configs in the pinned TASK-037A image.
- Project-owned adapters provide split guarding, deterministic seeding,
  checkpoint loading, full-length score alignment, artifact hashing and
  container orchestration. No upstream source is modified or vendored into
  `src/paperworks`.
- The `naive` schema choice and explicit zero-prefix alignment remain documented
  closest-reproducible compatibility decisions, not recovered ARGOS settings.

## TASK-037D ARGOS combined-prompt alignment

- ARGOS reference commit:
  `6b24161ff08de069840a1fb4fbaecf7bf8e393f1` (MIT, read-only).
- Inspected and hash-pinned:
  `agent/prompts/detection.py`, `agent/detection_agent.py`,
  `datasets/dataset.py`, and `runtime/engine.py`.
- Reconstructed system templates:
  `DETECTION_AGENT_V3_COMBINED_FN_PROMPT_TEMPLATE` and
  `DETECTION_AGENT_V3_COMBINED_FP_PROMPT_TEMPLATE`.
- Reconstructed user sections preserve `##### DATA 0`, FN
  `##### NORMAL DATA 0 `, FP `##### ABNORMAL DATA 0`, and pandas
  `to_string(index=False, header=False)` serialization.
- Upstream code copied or modified: none. Prompt text is extracted from the
  pinned source by the existing AST-based helper.
- Project-owned deviation: deterministic matched contrast replaces random or
  iteration-dependent contrast sampling for reproducibility.
