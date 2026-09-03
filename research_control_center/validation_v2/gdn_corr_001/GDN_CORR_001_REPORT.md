# GDN-CORR-001 최종 보고서

## 결론

`EXP-01B-R1`은 기존 `EXP-01B-V1`을 수정하지 않고 네 평가 결함을 바로잡아 재분석했다. 정정 후에도 disposition은 `GDN_ABLATION_ONLY`였다. 이어서 하나의 사전등록된 HAI 적응 실험인 `EXP-01C-GDN-HAI-V1`을 수행했으며, 결과는 `LEARNED_GRAPH_SUPPORTING`이다.

따라서 학습 그래프를 VALIDATION V2의 주 후보 탐색 권한으로 승격하지 않는다. 최종 방법 표현은 현재 근거 범위에서 **Process-Graph-Guided with Learned-Graph Evidence**가 적절하다.

## 코어 구현 감사

- GDN edge는 `source → target` 방향으로 일관되게 구성·내보내진다.
- 후보 graph의 self relation은 Top-K 전에 제외된다. 내부 message-passing self-loop와 후보 self relation은 구분된다.
- Attention은 post-normalization shared encoder evidence이며 target graph identity에 맞게 매핑된다.
- EdgeMask는 checkpoint를 고정한 채 해당 edge만 제거하며 재학습하거나 graph를 채우지 않는다.
- 방향 역전, self-exclusion 실패와 같은 치명적 architecture bug는 발견되지 않았다.

## 확인·수정한 네 결함

1. **Rule conversion**: V2A 실행 가능 pair와의 교집합이 아니라, GDN 고유 정상-confirmed directional relation을 동일 EXP-02 numeric policy와 Formal V4 validity/runtime 경로로 직접 검사하도록 수정했다.
2. **Percentile zero collision**: 최하위 관측 항목이 absent evidence `0`과 충돌하지 않도록 `(count - rank_index) / count`를 사용하고, 같은 raw score에는 같은 evidence를 부여했다.
3. **Signed EdgeMask**: 양수만 primary functional rank evidence로 사용하고, 0은 neutral, 음수는 counterevidence로 보존했다.
4. **Random controls**: 전체 focal set을 control 후보에서 제외하고 target·seed·view·graph eligibility·mask cardinality를 맞추며 가능한 경우 중복 없이 선택했다.

## EXP-01B-R1 정정 재분석

- 재학습: 없음
- META+STAT yield@29: `21`
- META+STAT NDCG@29: `0.7768925687839584`
- corrected augmented yield@29: `21`
- corrected augmented NDCG@29: `0.7768925687839584`
- corrected GDN-unique confirmed pair: `0`
- signed EdgeMask: positive `86`, neutral `6`, counterevidence `105`
- disposition: `GDN_ABLATION_ONLY`

참고로 frozen V1에서 GDN-unique였던 3개 pair, 5개 directional relation은 정정된 Formal V4 경로에서 모두 runtime-admissible이었다. 이는 기존 conversion 평가가 잘못되었음을 확인하지만, R1의 전체 disposition 기준을 충족시키지는 않는다.

## HAI 적응 감사

- raw feature range ratio: `3714.4092351486283`
- raw feature standard-deviation ratio: `37288.91547137139`
- first-difference scale ratio: `5493.155844156314`
- near-zero variance feature: `11`
- raw top-5 feature MSE share: `0.996108473849488`
- raw global MSE는 feature scale에 materially dominated된 것으로 판정했다.
- 동결된 선택 규칙에 따라 `TRAIN_ONLY_ROBUST_MEDIAN_IQR`을 EXP-01C preprocessing으로 사용했다.

기존 EXP-01B validation은 모든 9개 run에서 raw timestamp 10개가 train/validation 양쪽에 포함됐다. EXP-01C는 file-local contiguous validation, purge `66`, raw overlap `0`을 적용했다. 원본 overlap 감사의 `TRAIN2_ONLY` 위치 표기 세 행은 R2에서 보고 문구만 정정했으며 과학 값은 재계산하지 않았다.

## EXP-01C-GDN-HAI-V1

- 모델: corrected self-excluded shared learned graph + multi-horizon prediction heads
- horizons: `1/5/10/30/60`초
- scaling: train-only robust median/IQR
- validation: file-local purged block, purge `66`, overlap `0`
- backend: 하나의 동결된 CUDA 환경
- views × seeds: `3 × 3 = 9` run
- META+STAT / augmented yield@29: `21 / 20`
- META+STAT / augmented NDCG@29: `0.7768925687839584 / 0.7391701246781675`
- combined seed Jaccard@29: `0.7284178187403993`
- stable positive event-conditioned EdgeMask pair: `2`
- matched-random 통과 seed: `2/3`
- GDN-unique confirmed pair: `0`
- GDN-unique Formal V4 Rule pair: `0`
- disposition: `LEARNED_GRAPH_SUPPORTING`

Attention은 shared encoder에서 한 번 생성되는 공용 evidence다. 5개 horizon에 명시적으로 결속해 보고하지만 head-specific evidence로 해석하지 않는다. EdgeMask는 graph member에서 target·horizon별로, SourceOcclusion은 모든 144개 eligible pair에서 5개 horizon별로 평가했다.

## 주장 경계

말할 수 있는 것:

- HAI process graph를 이용하는 `PROCESS_GRAPH_GUIDED` 경로는 별도로 유지된다.
- EXP-01C에서 일부 정상-confirmed 관계에 재현 가능한 learned-graph functional supporting evidence가 관측됐다.
- 이 증거는 정상 데이터 기반 predictive/functional evidence다.

말할 수 없는 것:

- learned graph가 primary candidate discovery 성능을 개선했다.
- GDN이 causal/physical relation을 증명했다.
- test1/held-out 탐지 성능이 개선됐다.
- 학습 그래프가 최종적으로 독립 검증됐다.

## 안전 및 다음 단계

- test1 / label / test2 / held-out / provider 접근: 모두 `0`
- PILOT V1 변경: 없음, `3021/3021` blob 보존
- EXP-01B-V1 변경: 없음
- post-result tuning: 없음
- private exposure: `0`
- 다음 단계: `V2-SCI-EXP04-001`
