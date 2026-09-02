# EXP-01B 독립 QA

## 판정

`PASS_WITH_NONBLOCKING_INTEGRATION_NOTES`

독립 검토자는 공개 lineage artifact만으로 동결 결과를 다시 계산했고, 기존
`GDN_ABLATION_ONLY` 판정이 변하지 않음을 확인했다. 결과 무결성 PASS는 정상 데이터
범위의 artifact 정합성을 뜻하며, 탐지 성능 검증이나 인과성 증명을 뜻하지 않는다.

## 독립 재생 결과

- public receipt와 freeze의 self-hash 및 cross-file hash: PASS
- 원래 동결 결과 파일 6종의 byte SHA-256 보존: PASS
- pair ranking 2,736행과 metric 76행 재계산: mismatch 0
- seed ranking 6,480행과 seed/split Jaccard 20행 재계산: mismatch 0
- matched-random EdgeMask count 16/10/21과 seed 판정 2/3: PASS
- normal-confirmed pair 37개, directional relation 65개: PASS
- Formal V4 executable pair 21개: PASS
- GDN 고유 confirmed pair 3개, 고유 executable pair 0개: PASS
- 안정적인 양의 unique/baseline functional pair: 각각 0개
- primary Top-K EdgeMask median: 양수가 아님
- 최종 disposition: `GDN_ABLATION_ONLY`, 변경 없음

## 최적화 정합성

장시간 scalar CUDA-to-host 동기화를 tensor 단위 집계로 바꾼 구현은 실제 float32
fixture에서 기존 명시적 매핑과 Python-float exact equality를 만족했다. checkpoint별
private cache는 atomic write, self-hash, checkpoint/state/graph, split receipt,
preregistration, environment, config, feature/pair, source implementation identity를 모두
묶으며 Git 추적 대상에서 제외된다.

최적화 전 장시간 replay는 안전하게 중단되었다. 학습은 다시 실행하지 않았고, 최종
lineage publisher는 원래 scientific result hash와 disposition을 그대로 보존했다.

## 안전 경계

- test1 access: 0
- label access: 0
- test2 access: 0
- held-out access: 0
- provider call: 0
- public private-path 또는 credential 노출: 0
- PILOT V1 변경: 0
- post-result tuning: 0

QA 과정에서 진단 명령이 private derived lineage cache JSON 9개를 한 번 읽어 hash와
replay 상태를 확인했다. Raw HAI, checkpoint, `.env`, test1, label, test2, held-out은
열지 않았고 private 값이나 경로를 출력하지 않았으며 파일 변경도 없었다.

## 비차단 통합 주의사항

공개 reference receipt의 65개 directional ID는 publisher 전용 결정론적 namespace에서
재생된다. 기존 typed `directional_relation_id_v1` authority와 동일하다고 해석해서는
안 되며, 이 receipt는 EXP-01B 결과를 검증하기 위한 mirror이다. downstream scientific
runtime authority는 V2A의 별도 self-hashed Formal V4 authority를 사용한다.
