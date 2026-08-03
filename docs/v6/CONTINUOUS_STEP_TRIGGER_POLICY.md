# Continuous-Step Trigger Policy

At one-second sampling, an event candidate at `t` uses the median of the five
preceding values and the median of the five values beginning at `t`. Their
difference must exceed the fit-derived source threshold and define exactly one
of `step_up` or `step_down`. Each window must have at least 0.80 of its values
within the fit-derived stability tolerance.

Only `NORMAL_CANDIDATE_FIT` may derive:

- `source_noise_scale = max(1.4826 * MAD(dx), 1e-12)`
- `source_step_threshold = max(5 * source_noise_scale, Q75(A_positive))`
- `source_stability_tolerance = max(3 * source_noise_scale, 0.10 * threshold)`

`Q75` uses linear interpolation at `0.75 * (n - 1)`. Fewer than 20
nontrivial amplitudes is unsupported. Same-source candidates within ten
seconds form one cluster; largest absolute amplitude wins and an exact tie
uses the earliest time. Primary evidence requires no other eligible source
event within two seconds. Isolation is not a runtime abstention rule.

These values screen feasibility only and have no final parameter authority.
