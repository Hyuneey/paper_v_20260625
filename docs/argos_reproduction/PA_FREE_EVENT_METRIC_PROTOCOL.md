# PA-Free Event Metric Protocol

Point metrics use direct binary outputs with no smoothing, point adjustment, or label-optimized threshold. Undefined precision, recall, and F1 values are reported as zero.

Ground-truth and predicted events are maximal contiguous runs of one. Event matching uses deterministic maximum-cardinality one-to-one interval overlap: each predicted event and each ground-truth event can participate in at most one match. The resulting event precision, recall, and F1 are PA-free event-overlap diagnostics and are not Event-F1-PA.
