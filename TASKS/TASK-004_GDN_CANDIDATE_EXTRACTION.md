---
id: TASK-004
title: Implement modern masked GDN candidate extraction
status: blocked
depends_on: [TASK-003]
phase_gate: Milestone 2
suggested_branch: task-004-gdn-candidates
---

# TASK-004: Modern Masked GDN Candidate Extraction

## Current progress

- Mask-enforced embedding Top-K extraction core is implemented under `src/paperworks/gdn`.
- Deterministic smoke checkpoint and synthetic tests are implemented.
- Full modern PyTorch/PyG trainer remains blocked by DEC-010 because the current bundled Python environment lacks `torch` and `torch_geometric`.

## 1. Goal

Implement or adapt a modern, reproducible GDN relation learner that trains only on approved normal data and exports Top-K candidate edges strictly inside the CandidateUniverse mask.

## 2. Architecture context

The upstream GDN repository is a model reference, but its main environment is legacy and its current Top-K implementation operates over the full embedding-similarity matrix. This project requires explicit `C_i` masking and candidate self-edge exclusion.

## 3. Upstream reference

- repository: `https://github.com/d-ailin/GDN`
- reviewed snapshot: `9853899da860682669a134e4af315d036aab4eca`
- license: MIT
- required documentation:
  - pinned revision,
  - files adapted/copied,
  - modifications,
  - preserved notices.

## 4. Strategy

Preferred:

- minimal modern PyTorch/PyG port,
- architecture behavior documented,
- synthetic behavioral/parity tests.

Do not install the legacy PyTorch 1.5.1/PyG 1.5.0 stack as the primary project environment unless TASK-000 explicitly approved it.

Use d-ailin/GDN only as a behavioral and architectural reference.

The implementation in this repository must:

- use modern supported PyTorch/PyG,
- enforce CandidateUniverse masks before Top-K,
- exclude candidate self-edges,
- export relation candidates separately from message-passing self-loops,
- avoid upstream test-label threshold selection,
- pass parity tests on a synthetic fixture.

## 5. Inputs

- `train_normal` windows from approved GDN view,
- variable metadata,
- CandidateUniverse mask,
- feature order,
- training config and seeds.

## 6. Required adaptations

For every target `i`:

1. compute embedding similarity,
2. set scores outside `C_i` to `-inf`,
3. exclude `i` itself,
4. select at most K remaining sources,
5. export only masked candidate relations,
6. distinguish candidate edges from self-loops added later for message passing,
7. handle `K > |C_i|` deterministically,
8. fail or emit unsupported status for empty `C_i` according to approved policy.

## 7. Required outputs

- model/checkpoint artifact,
- training config and log,
- node embeddings,
- masked candidate-edge artifact,
- optional attention artifact clearly distinguished from embedding Top-K,
- K/seed run index,
- upstream adaptation report,
- license notice update.

Each edge must include:

```text
source
target
embedding_similarity
rank
K
seed
candidate_origins
candidate_universe_id
feature_order_hash
source_view
sampling_period_seconds
checkpoint_id
```

## 8. Forbidden reuse

- no upstream `report=best`,
- no test-label threshold selection,
- no test-guided checkpoint selection,
- no upstream split-after-window behavior,
- no candidate edge outside `C_i`,
- no persisted candidate self-edge.

## 9. Acceptance criteria

1. Training uses only `train_normal`.
2. Every exported edge is in `C_i`.
3. No exported edge has `source == target`.
4. Message-passing self-loops are not exported as candidate relations.
5. K and seed are configurable and recorded.
6. Repeated same seed/config reproduces candidates within approved tolerance.
7. GDN-view preprocessing is fully traceable.
8. Modern-port differences from upstream are documented.
9. No final test label is loaded.

## 10. Required tests

- candidate-mask enforcement,
- self-candidate exclusion,
- message-passing self-loop separation,
- K larger than candidate count,
- empty candidate set,
- feature-order mismatch rejection,
- deterministic seed behavior,
- synthetic training smoke test,
- no-test-split guard,
- behavioral comparison against a small reference calculation.

## 11. Stop conditions

Stop if:

- modern dependencies cannot reproduce required semantics,
- feature order or candidate mask is ambiguous,
- upstream adaptation would require unapproved architecture changes,
- training requires test labels or raw-data redistribution.
