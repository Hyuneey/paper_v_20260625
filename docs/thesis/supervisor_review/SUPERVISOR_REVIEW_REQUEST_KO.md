# 지도교수 검토 요청 메시지 초안

> **전송하지 않은 초안입니다.**

교수님 안녕하세요.

지난 피드백 이후 연구 구현과 실험을 진행하면서, 최종 결과에 맞추어
논문의 framing과 contribution 범위를 다시 정리했습니다.

핵심적으로는 **“T2 agentic superiority”보다 “evidence-bound and
verifiable rule construction”을 중심으로 논문 범위를 좁히는 방향**입니다.

- 정상 데이터 기반 파이프라인에서 최종 42개 방향 관계를 확인했습니다.
- 구성 결과는 T0 42/42, T1 42/42, T1-B 42/42, T2 39/42였고,
  T2의 3건은 `no_rule`로 종료되었습니다. T2 feedback action은 모두
  0이어서 feedback recovery는 실증적으로 실행되지 않았습니다.
- Direct-number 실험은 구조적으로는 성공했지만 수치 오차가 커서,
  정상 데이터 기반 결정론적 보정의 필요성을 지지했습니다.
- 라벨 기반 utility는 프로토콜 권한이 최종 완결되지 않아 실제 라벨과
  테스트 특징값에 접근하기 전에 중단했으며, 상태는 `NOT_EXECUTED`입니다.

현재는 anomaly-detection 성능 향상을 주장하지 않고, evidence-bound
construction, deterministic calibration, verification, fail-closed
`no_rule`, 그리고 T0/T1/T1-B/T2 비교를 논문의 중심 기여로 정리했습니다.
이번 요청은 새 실험이나 utility 재개 승인이 아니라, 해당 framing과
학위논문 범위의 적절성 검토를 부탁드리는 것입니다.

첨부한 요약 자료를 보시고 다음 세 가지를 검토 부탁드립니다.

1. 이 범위로 석사논문을 정리해도 괜찮을지
2. 제안한 세 제목 중 어느 범위가 적절할지
3. 현재 실증 범위가 부족하다면 반드시 필요한 구체적인 empirical
   evidence 한 가지가 무엇인지

감사합니다.
