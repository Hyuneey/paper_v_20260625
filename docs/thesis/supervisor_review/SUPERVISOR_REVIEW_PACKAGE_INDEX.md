# 지도교수 검토 패키지 V1

Status: `passed_thesis_supervisor_review_package_v1`

이 패키지는 commit `dc88c917af7dd030678047631c1fea50b4301a25`의
동결된 thesis framing, RQ, contribution, Method, Results 및 Discussion을
지도교수 의사결정용으로 축약한 문서입니다.

## 권장 읽기 순서

1. [SUPERVISOR_ONE_PAGE_SUMMARY_KO.md](SUPERVISOR_ONE_PAGE_SUMMARY_KO.md)
   **목적:** 연구 전체를 1–2페이지의 과학적 이야기와 세 가지 핵심
   의사결정으로 축약합니다.
2. [SUPERVISOR_DECISION_QUESTIONS_KO.md](SUPERVISOR_DECISION_QUESTIONS_KO.md)
   **목적:** 미팅에서 답변이 필요한 질문을 다섯 개의 구체적 결정으로
   제한합니다.
3. [SUPERVISOR_TECHNICAL_APPENDIX_KO.md](SUPERVISOR_TECHNICAL_APPENDIX_KO.md)
   **목적:** RQ, contribution, exact result table, T2, Direct-number,
   utility 중단 경위 및 limitation의 수치 근거를 제공합니다.
4. [THESIS_MASTER_DRAFT_V1.md](../THESIS_MASTER_DRAFT_V1.md) — reference only
   **목적:** 지도교수가 세부 chapter 구조나 문맥을 확인하려는 경우에만
   참조합니다. 구현 전체 검토를 요청하는 문서가 아닙니다.

별도 전송 초안:
[SUPERVISOR_REVIEW_REQUEST_KO.md](SUPERVISOR_REVIEW_REQUEST_KO.md)

## 패키지 불변 조건

```text
T0 = 42/42
T1 = 42/42
T1-B = 42/42
T2 = 39/42 + 3 no_rule
T2 feedback eligible/revise/retrieve/follow-up/recovery = 0/0/0/0/0
Utility = NOT_EXECUTED
Winner = NONE
```

Claim status는 다음과 같이 고정됩니다.

- A/B/F/G: `SUPPORTED`
- C: `PARTIALLY_SUPPORTED`
- D/E: `NOT_SUPPORTED`
- H: `INCONCLUSIVE`
- Labeled utility: `NOT_EXECUTED`

## 지도교수에게 필요한 결정

- D1: narrowed construction/governance thesis의 학위논문 충분성
- D2: 세 title option 중 application scope의 적절한 경계
- D3: 현재 empirical scope가 부족한 경우 반드시 필요한 구체적인 한
  가지 evidence

D3는 utility가 필수라고 전제하지 않습니다.

## 권한 경계

이 패키지는 새 실험, utility 재개, label/test 접근, provider 호출,
Rule v2/runtime 또는 다른 과학 작업을 승인하지 않습니다. 다음 단계는
**USER / SUPERVISOR REVIEW**입니다. 추가 empirical evidence가 명시적으로
요구되는 경우에만 그 한 가지 요건에 맞춘 최소 과학 작업을 별도로
설계합니다.
