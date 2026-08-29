# 지금 실제 시스템은 어떻게 돌아가는가

## 전체 구조 한 장

데이터의 출처와 사용 범위를 먼저 고정하고, P1 변수 관계 후보를 세 방법(META, STAT, GDN)으로 찾는다. 후보를 합친 뒤 정상 데이터에서 시간 지연 관계를 확인하고, 제한된 형식의 규칙을 만들고 코드 검증기를 통과시킨다. Frozen 규칙은 LLM 없이 D1으로 실행된다. 별도 PCA-SPE detector가 D0이고, frozen D0/D1 예측을 결합한 것이 D2다.

## 데이터는 어디서 시작하는가

공개 가능한 것은 데이터의 identity와 custody hash뿐이다. 실제 값은 private이다. Split과 접근 권한은 governance 계층에서 제한한다. 이번 감사는 데이터 파일이나 test2를 열지 않았다.

## 관계는 어떻게 만들어지는가

12개 source와 12개 target의 144개 가능성에서 META, STAT, GDN이 각각 후보를 만든다. 이들은 인과관계가 아니라 후보 증거다. Union 뒤에 정상 데이터 기반 profiling이 확인 관계를 만든다.

## 규칙은 어떻게 만들어지고 검증되는가

T0, T1, T1-B, T2 네 construction 경로가 있다. 실제 실행 경로는 canonical verifier 문서만 직접 쓰는 것이 아니라 task-specific deterministic verifier를 사용한다. T2는 실행됐지만 이번 cohort에서 feedback action은 0이었고 COMMON-42 utility에는 선택되지 않았다.

## 규칙은 실제로 어떻게 실행되는가

D1 frozen 결과는 Utility V4 rule descriptor와 private numeric authority를 사용하는 real runtime bridge에서 나왔다. Canonical RuntimeTrace와 설명 renderer는 구현돼 있지만 frozen D1 결과에 직접 사용됐다는 연결은 확인되지 않았다.

## Detector는 어디에 있는가

D0는 별도 PCA-SPE baseline이다. 규칙 생성과 detector 학습은 같은 것이 아니다. D0 prediction은 label을 열기 전에 파일로 고정됐다.

## 둘은 어떻게 비교/결합되는가

D2 V1/V2는 D0나 D1을 다시 실행하지 않고 frozen prediction을 입력으로 사용한다. V1 결과는 첫 infrastructure abort 뒤 authorized recovery entrypoint로 완성됐다. V2의 integrity PASS는 결과 재실행 없이 여러 감사 기록을 결합한 completion이다.

## 실제 결과는 어디서 나오는가

각 D0/D1/D2 prediction에서 alarm episode를 만들고, 그 뒤 허가된 label로 attack-event recall과 normal FAR를 계산한다. 현재 수치는 14개 사건의 pilot 관찰이며 검증된 성능 결론이 아니다.

## 구현만 된 것 vs 실제 실행된 것

후보 탐색부터 D0/D1/D2와 integrity audit까지는 실행 evidence가 있다. Explanation renderer, OUTER scientific result, fresh-machine reproduction은 같은 수준으로 완료됐다고 말할 수 없다.

## 아직 못 믿어도 되는 부분

GDN 고유 기여, Agentic feedback 이점, Rule-only 운영 효용, fusion 개선, held-out 일반화, 사람에게 유용한 설명은 아직 검증되지 않았다.

## 다음에 내가 이해해야 할 것

1. provenance와 split이 실제 실행 entrypoint에서 어떻게 enforce되는가
2. canonical contract와 task-specific bridge가 어떻게 변환되는가
3. D1 trace와 explanation이 frozen 결과에 왜 포함되지 않았는가
4. 어떤 mismatch를 우선 deep review할 것인가
5. ARCH-001 시작 승인 여부
