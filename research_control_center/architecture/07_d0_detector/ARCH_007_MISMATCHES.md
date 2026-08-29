# ARCH-007 Mismatches

| ID | Documented or possible wording | Actual evidence | Severity | Recommended action |
|---|---|---|---|---|
| A007-M01 | D0 uses sklearn StandardScaler/PCA | It uses custom NumPy population standardization, covariance and `np.linalg.eigh`. | MEDIUM | Name the actual backend. |
| A007-M02 | PCA is configured with `k=10` | The policy is the smallest `k` reaching 0.95; 10 is the frozen fitted outcome. | MEDIUM | Separate policy from observed fit. |
| A007-M03 | q=.999 is an interpolated percentile | It is stable sort plus exact `ceil(q*n)-1`, without interpolation. | MEDIUM | Use empirical order-statistic wording. |
| A007-M04 | Alarm uses `score >= threshold` | Exact equality is non-alarm; comparator is strict `>`. | MEDIUM | Preserve boundary semantics. |
| A007-M05 | D0 uses only continuous relation-role variables | It consumes all 37 frozen P1 numeric columns without type-specific transformation. | MEDIUM | Distinguish detector feature scope from relation roles. |
| A007-M06 | FAR/hour is a point false-positive rate | It counts normal false alarm episodes per normal labeled hour. | MEDIUM | Name numerator and denominator. |
| A007-M07 | 876 alarms equals 46 episodes | 876 is point alarms; 46 is consecutive-index alarm episodes. | MEDIUM | Keep output levels separate. |
| A007-M08 | D0 is strong/SOTA or the thesis contribution | It is a simple deterministic reference detector. | HIGH | Add a stronger detector in future expanded validation. |
| A007-M09 | D0 is bitwise deterministic on every machine | Code is deterministic with environment assumptions; BLAS/LAPACK identity and fresh-machine replay remain incomplete. | MEDIUM | Keep reproduction qualification. |
| A007-M10 | train3 is only relation confirmation or only detector calibration | The same normal split has separate confirmation and D0 calibration roles. | LOW | Disclose dual use without labeling it leakage. |

Totals: 10 mismatches; CRITICAL 0, HIGH 1, MEDIUM 8, LOW 1.

