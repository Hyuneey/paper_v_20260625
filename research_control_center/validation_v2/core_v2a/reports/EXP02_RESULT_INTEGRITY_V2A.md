# EXP-02 V2A 독립 결과 무결성 점검

상태: **PASS**

- 후보: 37개(고유), frozen guard 통과 28개
- 선택 정책: `RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05`
- 선택 결과 hash: `effb335cecdda1780977658bb6a965a8b8bf52351650822f1b5cd60000062536`
- 선택 정책의 train4 정상 false alarm: 1,470초 / 1,461 episode
- 선택 정책의 ABSTAIN: 3,764
- 모든 후보의 `UNSUPPORTED_RELATION`: 0
- 모든 후보의 `SYSTEM_ERROR`: 0
- 데이터 open: train1, train2, train4 각 1회
- test1 / label / test2 / held-out 접근: 0 / 0 / 0 / 0
- private selected authority hash: `c39d6a05f580765d806fe352a5fadd1cb659ac7c6e342f9273d7857f6f95ae97`
- private Formal V4 numeric authority hash: `c64cb6717681a7128cf21a9cfecd9f2ad86b6a3844ef4a0e080e3e050092dc59`
- Formal V4 closure: 39 relation × 10 numeric roles = 390 binding
- portfolio: 39 relation / 39 rule
- portfolio authority hash: `ec0b3e2a32d457287cb8b101bec39059e99335be3fd85a3d1fb98668224c52aa`
- runtime authorization hash: `b0aefc9dab7655aaaf18774d4c90c047db8ed976ba2b67443f1c5343228a49b8`
- focused tests: 77 PASS
- QA의 raw HAI 및 `.env` open: 0

private 실행 결과에 남은 `COMPLETE_QA_PENDING`은 결과 생성 직후의 역사적 단계 token이며, 이 독립 무결성 보고서가 해당 실행을 `PASS`로 종결한다.

이 PASS는 정상 전용 정책 선택과 artifact 무결성을 뜻한다. test1 탐지 성능 검증이나 held-out 일반화를 뜻하지 않는다.
