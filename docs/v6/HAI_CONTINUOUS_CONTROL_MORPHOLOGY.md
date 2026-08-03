# HAI Continuous-Control Morphology

TASK-039BR0 evaluated source morphology only. It did not evaluate target
responses or delayed-response pairs.

| Process | Documented continuous candidates | Nonconstant train1/train2/train3 | Repeated-change candidates in all files | Status |
|---|---:|---:|---:|---|
| P1 | 13 | 13/13/12 | 12 | continuous-step route ready for versioned feasibility |
| P3 | 2 | 2/2/2 | 2 | continuous-step route ready for versioned feasibility |

For diagnosis only, a large-change candidate was a one-step change greater
than five times the robust one-step MAD scale. A candidate had repeated bounded
changes only when it was finite, nonconstant, and had at least two nonzero and
two diagnostic large changes in each of train1, train2, and train3.

This threshold is non-authoritative. It is not a rule parameter, calibration
result, pair score, or process-selection criterion. TASK-039BR1 must define a
versioned continuous-step trigger family before any pair feasibility work.

The private morphology ledger hash is
`3cef789579ca54b4b829a381db7763feb3b1c4ee5b53e6ca61015f5d5aec25a3`.
