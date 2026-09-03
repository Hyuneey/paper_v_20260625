# EXP-05 실제 trace 일치성

상태: 실제 실행 및 artifact 보존 완료, 독립 전체-census QA PASS.

실제 Formal V4 runtime opportunity 6,418개 전부에 대해 trace → deterministic renderer → fidelity artifact를 생성했다. PASS 4,561 / FAIL 681 / ABSTAIN 1,176이다. FAIL rule record 681개는 unique alarm seconds 568개와 구분한다. 전체 alarm episode 565개 중 정상 false episode는 533개다.

원래 full-unit schema를 유지한 26개 batch가 close/reopen/hash replay됐다. Runtime 시작/종료 authority가 일치해야 accepted full-census receipt가 만들어진다. sample-only 평가나 digest-only trace 대체가 아니다.

GDN optional clause는 130개 설명에만 존재한다. 나머지에도 기본 설명은 존재한다. sidecar는 같은 pair/horizon의 predictive functional supporting evidence이며 원래 outcome을 바꾸지 않는다. 모든 split에서의 안정성이나 인과성을 주장하지 않는다.

자동 structural fidelity는 source/target/direction/horizon/numeric provenance/outcome/no-new-variable/no-new-number/noncausal 및 deterministic replay 범위이다. human usefulness는 UNVALIDATED이며 자동 일치성 통과를 인간 유용성이나 물리적 진실로 설명하지 않는다.

독립 reviewer가 원본 26개 full-unit batch를 모두 replay하여 6,418/6,418개에서 11개 검사 전부 PASS를 확인했다. 샘플 대체가 아니며 80개 관련 파일의 before/after hash가 동일하다.
