# Continuous-Step Relation Semantics

`continuous_step_delayed_response_v1` is a preregistered experimental
delayed-response family separate from Rule v1. It binds exactly one documented
continuous control/actuator source to one distinct continuous sensor target.

Each candidate has one explicit directional identity:

- `step_up -> target_increase`
- `step_up -> target_decrease`
- `step_down -> target_increase`
- `step_down -> target_decrease`

The only violation is `missing_expected_response`; runtime output is binary
anomaly or abstain. Supported claims are normal-data step-conditioned
association, typical lag, direction, support, and transfer. Causality, root
cause, universal invariance, complete process models, and attack mechanisms
are prohibited.

Setpoints and discrete Rule v1 sources do not enter this family. Data behavior
or official graph membership alone cannot establish control semantics.
