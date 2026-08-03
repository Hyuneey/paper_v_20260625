# Continuous-Step Response Policy

For an isolated source event, target baseline is the median of the preceding
five target values. At horizons `1, 5, 10, 30, 60`, response is the median of a
three-second target window minus that baseline. An incomplete response window
is right-censored.

Target noise is fit only:

`max(1.4826 * MAD(one_step_target_changes), 1e-12)`

Increase evidence must exceed the positive noise scale; decrease evidence
must be below its negative. Absolute response without direction is prohibited.
No target response may calibrate the source trigger.
