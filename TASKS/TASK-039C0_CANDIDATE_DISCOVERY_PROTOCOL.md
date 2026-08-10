# TASK-039C0: P1 Candidate-Discovery Protocol Freeze

Status: `passed_task039c0_candidate_discovery_protocol_freeze`

TASK-039C0 integrates the independently audited TASK-039BR2 result, freezes P1
Boiler as the selected process, and preregisters three non-overlapping
candidate-discovery arms over one identity-only directed universe.

## Frozen Scope

- Relation family: `continuous_step_delayed_response_v1`
- Sources: 12 reviewed P1 continuous control or actuator variables with valid
  BR2 fit-only source support
- Targets: 12 reviewed P1 continuous process sensors
- Eligible directed pairs: 144
- Primary budget: top 20
- Sensitivity views: top 10 and top 40 from the same ranking

## Arms

- `TASK-039C-META`: official documentation, graph, roles, and subsystem
  evidence only; no feature values.
- `TASK-039C-STAT`: deterministic within-file lagged change correlation using
  P1 train1 and train2 only.
- `TASK-039C-GDN`: pinned upstream-aligned GDN learned graph, subject to a
  mandatory fidelity receipt, using P1 train1 and train2 only.

The arms cannot use BR2 pair-level outcomes. Integration is an unscored set
union with method provenance. TASK-039D remains unauthorized.

## Execution Boundary

This task accessed no HAI feature values, executed no candidate ranking,
trained no model, and created no final CandidateUniverse.

## Parallel Bootstrap

After the verified C0 commit, the META, STAT, GDN, review, and integration
branches are created from that exact commit without empty commits.
