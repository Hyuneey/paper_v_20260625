# LSTM Score Alignment Protocol

The official LSTMAD score contains `N - window_size - prediction_horizon`
values. TASK-037A froze full-length right alignment by prepending exactly
`window_size + prediction_horizon` zero scores. TASK-037B applies that policy
unchanged: defaults `100 + 3` yield a 103-point missing prefix.

Every score must be one-dimensional, finite, higher-is-more-anomalous, and have
the exact split input length after alignment. Reports retain only counts,
summary statistics, and SHA-256 hashes. Raw and aligned arrays remain private.

The zero prefix is a frozen compatibility policy, not a claim that those points
were evaluated by the model. Any length or nonfinite mismatch fails the unit.
