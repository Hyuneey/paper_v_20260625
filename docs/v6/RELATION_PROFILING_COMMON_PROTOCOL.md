# Common Normal Relation-Profiling Protocol

The protocol evaluates each of the 47 unique P1 Boiler pairs once. It uses all
12 frozen sources for simultaneous-event isolation and all 12 reviewed targets
for shared target-scale derivation. The proposing arm never changes a formula,
threshold, gate, or fallback.

For D1, one-step differences are formed separately in train1 and train2 and
pooled only afterward. Source and target noise scales are
`max(1.4826 * MAD(file-local difference), 1e-12)`. Source amplitudes use
five-second median pre/post windows; at least 20 amplitudes strictly exceeding
source noise are required. The threshold is
`max(5 * source_noise_scale, Q75_linear(A_positive))`, and stability tolerance
is `max(3 * source_noise_scale, 0.10 * source_step_threshold)`.

Sustained events require amplitude at least the threshold and at least 0.80
stable samples in each five-second level window. File-local single-link
10-second clustering retains the largest absolute step, then the earliest
index. An event is usable only when no retained event from any other frozen
source occurs within inclusive plus or minus two seconds.

Target responses compare the five-second pre-event median with a three-second
median at horizons 1, 5, 10, 30, and 60 seconds. Incomplete windows are
right-censored and never imputed.
