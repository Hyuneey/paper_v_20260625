# 교수 미팅 후 선택지

## 옵션 A — 논문 초안 우선 (권고)

- 기여를 graph-guided verified rule construction으로 고정
- INNER 범위와 negative fusion 결과를 정직하게 서술
- TSFM/ARTIST/causality/generalization은 future work
- 비용: 낮음, 현재 근거를 가장 빨리 논문화

## 옵션 B — 강한 detector baseline 1개 추가

- 교수님이 PCA-SPE 약점을 핵심 위험으로 판단할 때만 진행
- detector, split, calibration, 비교 metric을 새로 preregister
- 현재 D1 규칙은 고정하고 detector error complementarity만 새로 평가
- 비용: 중간, 새 실험과 결과 무결성 작업 필요

## 옵션 C — 독립 OUTER 연구

- 기존 1회 시도 자동 재개가 아니라 새 연구로 분리
- custody를 먼저 독립 검증하고 그 뒤 one-shot preregistration
- generalization을 확인할 수 있으나 실패/공수 위험 큼
- 비용: 중간~높음

## 옵션 D — ARTIST식 segment selection 추가

- 교수님이 설명을 관계 trace만으로 불충분하다고 판단할 때
- segment proposal/selection의 입력·label boundary와 평가를 별도 RQ로 설계
- 현재 규칙 설명을 대체하지 않고 상위 localization layer로 비교
- 비용: 높음, thesis scope 확장

## 옵션 E — TSFM 비교

- 새로운 detector/representation study로 취급
- 현재 검증 규칙 기여와 분리된 protocol 필요
- 비용: 높음, 현재 first-results package의 결론을 보완하지만 필수는 아님

## 옵션 F — D2 V3

현재는 **권고하지 않음**. V1/V2 모두 0/3 회복이고 V2는 FAR 비용을 크게 늘렸다. 새 policy를 만들기 전에 과학적으로 독립된 가설과 교수님 승인이 필요하다.

