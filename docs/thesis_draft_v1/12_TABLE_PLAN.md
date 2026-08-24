# 논문 표 계획

## Table 1. Dataset, process, split roles

열: dataset/edition, process, sampling, split role, allowed operation, label
access, leakage prohibition. HAI 23.05 P1과 train1/2/3/4, test1, test2를 포함한다.

## Table 2. Candidate discovery arms

열: arm, input, feature-value access, score/evidence type, primary K, claim
boundary. META/STAT/GDN과 unscored union을 비교한다.

## Table 3. Rule-construction arms

열: arm, provider calls, feedback, shared contract, allowed output, frozen
outcome. T0/T1/T1-B/T2의 fair budget과 no_rule 의미를 포함한다.

## Table 4. Hyperparameter provenance summary

열: parameter, value, role, freeze point, label used, sensitivity, assessment.
main body에는 Top-K, horizons, refractory/isolation, relation gates, PCA 0.95,
q=0.999, D2 source count/time policy만 두고 전체 register는 부록으로 보낸다.

## Table 5. D0/D1/D2 results

| Arm | Recall | Normal FAR/hour | D0 miss recovery |
|---|---:|---:|---:|
| D0 | 0.7857142857142857 | 0.4939336325682589 | baseline |
| D1 | 0.9285714285714286 | 40.50255787059723 | 3/3 |
| D2 V1 | 0.7857142857142857 | 0.7056194750975128 | 0/3 |
| D2 V2 | 0.7857142857142857 | 6.915070855955625 | 0/3 |

## Table 6. Complementarity decomposition

열: D0 alarm event membership, D1 membership, count, interpretation. BOTH 10,
D0_ONLY 1, D1_ONLY 3, NEITHER 0, union 14/14를 사용한다.

## Table 7. Supported and unsupported claims

열: claim, status, exact evidence, scope, prohibited overstatement. graph-guided
construction, verified rules, complementarity, fusion negative result, TSFM,
ARTIST, causal explanation, OUTER를 포함한다.

## Table 8. Limitations

열: limitation, scientific/software class, current impact, mitigation option,
professor dependency. 새 실험을 현재 완료 범위처럼 쓰지 않는다.
