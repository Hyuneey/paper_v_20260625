# 실행 전 독립 점검

## 검증 결과

- V2 tests: 464개 실행, 실패 0, optional/platform skip 5. 이후 추가 freeze/path 부정 테스트 2개 PASS.
- RCC/UI tests: 180개 PASS. Registry+generated validation 및 privacy PASS.
- PILOT V1: 3,021/3,021 authority blobs 보존. V2A / GDN frozen result 경로 diff 없음.
- 신규 focused suite: 57개 실행, 실패 0, inherited platform skip 2.
- 정확한 detector 환경에서 five-method fit/predict/durable freeze/one-shot labels/common metrics/full EXP05+GDN annotation synthetic end-to-end PASS.
- 실제 protocol source, V2A authority source, 새 execution commit이 서로 다른 경우와 잘못된 policy/metric/commit 거부를 검사했다.
- in-memory alarm 또는 native census 변조는 frozen bytes/census replay에서 거부한다.
- 원래 full-unit materializer와 최적화 경로의 unit documents가 일치한다. authority mutation은 final accepted census와 bundle 생성 전에 실패한다.

기존 GDN attention fixture는 Python float64 literal을 float32 tensor 결과와 exact 비교해 실패했다. oracle 입력을 동일 float32 값으로 맞췄으며 exact assertion과 GDN 과학 구현은 그대로 유지했다. 동결 실험 결과는 재실행하지 않았다.

## 독립 역할

front_custody: split/authority/공식 transport/label gate 정합성. front_gdn_mapping: exact sidecar와 설명 결속/공개 안전성. front_performance: source event/runtime equivalence/full trace 보존. Coordinator만 구현 및 artifact를 작성했다. 동시 쓰기 충돌 없음.

세 검토의 지적은 pre-feature 단계에서 수정했다. 본 PASS는 과학 결과의 무결성 승인이 아니라 Commit A/B 준비 상태이다. 사후 결과 QA는 실제 모든 예측/label receipt와 metric/report를 별도로 검사해야 한다.

## 성능

최종 V2 cProfile은 39개 합성 규칙, 390/1,560 full traces를 각각 2회 검사했다. 약11.2/11.3초,42.4/44.6초이며 GDN 주석과 강한 replay를 포함한다. loaded source hashes 시작/종료 동일. GPU 강제 사용 없음. 이전 V1 tracemalloc profile과 계측 방식이 달라 speedup 배수를 주장하지 않는다. 실제 scientific wall time 예측이 아니다.

## 보존 범위와 제한

기준 Git tracked records 3,875개, 등록 worktree metadata 152개를 기준으로 exact artifact locator만 확인했다. 필수 numeric/evidence 10개 복원 PASS. 현재 데이터 bytes는 실행 adapter gate에서만 연다. 과거 checkpoint/META reviewed input 및 Codex transcript contents는 현재 실행에 필요하지 않으며 추가 수집·공개하지 않는다. transcript 보존 및 독립 저장장치 백업은 NOT_VERIFIED, NONBLOCKING_REPRODUCIBILITY_DEBT다.

test1 feature/label, test2/heldout/provider/GDN 학습 접근은 이 prefeature 점검에서 0이다. Source A / exact freeze B 이후에만 승인된 개발 실행을 시작한다.
