# EXP-03 독립 결과 QA

판정: **PASS**. coordinator가 모든 과학 호출·출력의 단일 writer이며 세 reviewer는 read-only로 검토했다. 공유 쓰기 충돌은 0이다.

- `front_custody`: 55개 실행 binding, 585개 request/response, 390개 terminal, private/public 결과·ledger replay PASS. 승인 projection 외 numeric/path/label/cross-arm 노출 0.
- `front_performance`: 별도 stdlib arithmetic/state oracle로 토큰·Decimal 비용·모든 reservation prefix·single in-flight·1-call gate·재시도 0을 검증했다.
- `front_gdn_mapping`: 별도 stdlib oracle로 원본 585개 응답의 실제 content를 재분류하고 T1-B earliest accepted·T2 종료·390개 terminal을 확인했다.

## 원본 응답과 실패 분류

| arm | 생성 출력 승인 | INTENTIONAL_NO_RULE | PARSE_FAILURE | VERIFIER_REJECTION |
|---|---:|---:|---:|---:|
| T1 | 104/117 | 2 | 9 | 2 |
| T1-B (선택 전 draw) | 311/351 | 13 | 24 | 3 |
| T2 | 105/117 | 4 | 8 | 0 |

41개 PARSE_FAILURE는 전부 **valid JSON의 NO_RULE envelope consistency 검사 실패**였다. JSON 문법 오류·응답 truncation·API transport/schema failure로 바꾸어 설명하지 않는다. 동결된 분류는 수정하지 않았다. T1-B는 3회 생성 후 115/117개 terminal을 승인했고 2개는 ALL_DRAWS_FAILED였다.

같은 관계의 세 반복에서 terminal class가 일치한 그룹은 T1 30/39, T1-B 37/39, T2 30/39였다. T2 acceptance 여부만 일치한 그룹은 31/39였다. 이 반복은 독립 관계 표본이 아니다.

T2 feedback 발생은 0/117이다. repair denominator가 0이므로 repair rate는 **NOT_OBSERVED**이며 0%로 쓰지 않는다. synthetic stress 390/390은 별도 deterministic 계약 점검이고 자연 feedback 이점의 증거가 아니다.

## 비용·보관

585 generation calls; input 439,845 + output 196,425 = 636,270 tokens. 표준요금 상한 USD 1.21379625 (cache 할인 미반영, 최종 invoice 아님). 별도의 model metadata GET 1회는 generation call이 아니다.

동시 호출 최대 1개, 재시도 0, 각 슬롯 single-use dispatch, 첫 gate 뒤에만 두 번째 호출 허용. 모든 budget prefix가 승인 범위 내에 있었다. 보관 원본 응답과 ledger는 변경하지 않았다. private 자료는 기존 vault 안 별도 namespace에 local-only로 보관되며 새 독립 backup이 있다고 주장하지 않는다.

## 보존·결정

PILOT V1 3,021/3,021 보존 검사 PASS. V2A/EXP-02/EXP-04/05/GDN 결과와 config 변경 0. 이번 task의 test1·test2·held-out·공격 labels 접근 0. 독립 QA는 provider 호출을 하지 않았다.

최종 과학적 기여·제목은 **DG-04 사용자 결정**이다. DG-05와 DG-06은 열지 않았다.
