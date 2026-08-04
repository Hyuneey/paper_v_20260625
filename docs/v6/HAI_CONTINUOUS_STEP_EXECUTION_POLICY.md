# HAI Continuous-Step Execution Policy

TASK-039BR2 binds the reviewed BR0 eligibility records to the BR1 protocol.
Train1 and train2 contribute only within-file differences and windows to source
and target scales. Train3 receives the frozen fit threshold, tolerance,
direction, horizon, and target scale without retuning.

Direction agreement requires the selected direction's consistency to be
strictly greater than the opposite direction in both fit files. Equality in
either file rejects agreement. Only agreeing candidates enter the frozen
consistency, effect, shortest-horizon, and exact-tie ranking. A failed selected
candidate cannot fall back to a lower-ranked candidate.

Full source-parameter, event, isolation, relation, and confirmation ledgers are
private. Public artifacts contain process aggregates, status counts, and
private-ledger hashes only. Feasibility parameters have no final calibration,
Agent, verifier, rule, or runtime authority.
