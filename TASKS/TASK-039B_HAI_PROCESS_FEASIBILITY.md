# TASK-039B: HAI P1/P3 Normal-Only Delayed-Response Feasibility

## Objective

Compare P1 Boiler and P3 Water Treatment using only the four verified HAI
23.05 normal training files. Freeze one process only if the fixed minimum gate
and unweighted Pareto policy make the choice defensible.

## Frozen Data Roles

- `normal_candidate_fit`: `hai-train1.csv`, `hai-train2.csv`
- `normal_relation_calibration`: `hai-train3.csv`
- `normal_guard`: `hai-train4.csv`, hash/header/row-count access only

No test, label, summary-label, custody, attack, outer, or sealed artifact is an
input. Splits are file-level and precede windowing. The purge gap is 120
samples for a 60-second context and 60-second maximum lag.

## Screening

Eligible reviewed discrete control/actuator transitions are screened against
eligible reviewed continuous sensors at 1, 5, 10, 30, and 60 seconds. The
baseline is the target at `t-1`; the noise scale is normal-fit one-step MAD.
Primary support uses transitions isolated from changes in other eligible
sources by two seconds on either side.

Fit and calibration thresholds, the increase-only Rule v1 bridge, process
minimum gate, and Pareto metrics are frozen in
`configs/v6/task039b_hai_p1_p3_feasibility.json`.

## Execution Boundary

Commit A contains implementation, schemas, synthetic tests, config, and this
protocol. Real normal-data execution starts only from a clean Commit A.
Detailed pair identities and aggregate statistics remain in a private ledger
outside the repository. Public reports contain process aggregates and ledger
hashes only.

TASK-039B does not construct a CandidateUniverse, train a graph ranker,
calibrate rule parameters, generate or execute a rule, run a detector, or
calculate anomaly-detection performance.

## Outcome

Status: `blocked_no_feasible_delayed_response_process`.

P1 and P3 both produced zero eligible reviewed, nonconstant binary/discrete
source variables. No process, selected view, or authoritative split was
frozen. The implementation and sanitized blocked result are preserved on the
task branch; main is not advanced by this blocked task.
