<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=c8c7f24b5c73df275f163236e9927800a85e9977c5e794f5ddbb39a40d47622a authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# Rule은 실제 시계열에서 어떻게 판단하는가

## 1. Rule은 언제 발동하는가?

Frozen D1은 매 초 모든 Rule을 판정하는 방식이 아니다. 5개 행의 source 전·후 median이
수치 권한의 magnitude·stability 조건과 방향을 만족하면 하나의 **opportunity**가 생긴다.
같은 source의 10초 single-link cluster에서는 절대 step amplitude가 가장 큰 후보를 남기며,
정확히 동률이면 가장 이른 index를 남긴다. 다른 source event와 ±2초로 겹치는 후보도 제외한다.

## 2. 발동하지 않으면 정상인가, abstain인가?

둘 다 아니다. source event가 없으면 opportunity 자체가 없고 terminal outcome도 없다.
`abstain`은 이미 형성된 opportunity를 미래 window 부족 등으로 평가할 수 없을 때만 나온다.

## 3. Rule이 깨졌다는 것은 무엇인가?

고정 horizon 뒤 target의 3개 행 median이 정상 데이터에서 결속된 expected direction과
noise 조건을 만족하지 못했다는 실행 계약상의 뜻이다. 물리적 원인이나 causal root cause를
증명하는 뜻이 아니다.

## 4. PASS와 FAIL은 무엇인가?

- PASS shorthand는 실제 코드의 `evaluated_expected_response`이며 alarm이 아니다.
- FAIL shorthand는 `evaluated_anomaly`이며 그 decision index에 alarm을 만든다.
- ABSTAIN은 평가 불가능 상태이고 alarm이 아니다.
- 권한·custody·replay 오류는 hard system error이며 abstain이 아니다.

## 5. 42개 결과를 어떻게 D1 alarm으로 만드는가?

어느 Rule이든 `evaluated_anomaly`이면 해당 decision second가 D1 alarm이 된다. Frozen artifact는
6,031 opportunity record와 788 anomalous rule record를 담지만, 같은 시점 중복을 제거하면
630 unique alarm seconds다. 이어진 seconds를 묶은 626 episodes는 metric 단계의 별도 산출물이다.

## 6. Trace에는 무엇이 들어가는가?

Frozen D1 trace는 opportunity, source-event hash, relation hash, terminal state, alarm,
decision index, numeric reference IDs, computation identity를 묶은 task-specific terminal hash다.
단계별 `RuntimeTraceV1` 객체는 저장하지 않았다.

## 7. D1 prediction은 label보다 먼저 정해지는가?

그렇다. 전체 label-blind prediction object를 만든 뒤 검증하고 shallow-frozen 상태로 custody를
확인한 후에 label-test1을 연다. 그래서 현재 분류는 **SAFE_BUT_WEAKER_THAN_D0_D2**이다.

## 8. 왜 durable file freeze가 더 강한가?

현재 object는 top-level frozen dataclass이지만 내부 record dict는 mutable이고, public prediction
file은 metric 계산 뒤에 저장된다. Label 전에 bytes를 atomic하게 저장·재개방하고 label 뒤 동일
bytes를 다시 확인하면 process boundary가 생겨 더 강한 증거가 된다. Frozen pilot은 수정하지 않는다.

## 9. Runtime은 정말 LLM-free인가?

Frozen fixed-rule R0/D1 runtime에서는 LLM, provider, network call이 0이다. 이 문장을 미래 R1이나
전체 가능한 runtime 설계까지 일반화하면 안 된다.

## 10. 설명은 trace를 얼마나 그대로 반영하는가?

Canonical `RuntimeTraceV1`용 deterministic template renderer는 variable·lag·provenance binding을
재검증한다. 그러나 frozen V4 D1은 `RuntimeTraceV1`을 만들지도 renderer를 호출하지도 않았으며,
frozen D1 explanation artifact도 없다.

## 11. 설명이 root cause를 말할 수 있는가?

아니다. Canonical renderer는 causal/root-cause flag를 금지한다. 현재 보장 가능한 것은 canonical
synthetic path의 구조적 binding뿐이며 사람에게 유용한지는 **UNVALIDATED**다.

## 12. 현재 가장 중요한 runtime 위험은 무엇인가?

V4 frozen path와 canonical Rule/Trace 설명을 혼동하는 것, label 전 durable persistence가 없는 것,
그리고 설명 구현이 frozen D1에 실제 연결된 것처럼 표현하는 것이 가장 중요한 위험이다.

다음 task는 **ARCH-007 — D0 PCA-SPE Detector Deep Audit**이다.
