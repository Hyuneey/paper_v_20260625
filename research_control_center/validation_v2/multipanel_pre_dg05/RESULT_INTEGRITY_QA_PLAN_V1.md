# Independent post-label result-integrity QA

A read-only QA runner will independently recompute the P1 denominator, scenario hits/misses, Wilson 95% intervals, file-local false burden, namespaced-union eTaPR, paired tables, exact McNemar, detection delays, overlap, incremental Recall, and incremental FAR from the frozen prediction/label authorities. It cannot call a provider, mutate predictions, refit detectors, revise Rules, retrain GDN, or change eligibility. Any corrupt post-freeze prediction is an integrity blocker, not a rerun authorization.
