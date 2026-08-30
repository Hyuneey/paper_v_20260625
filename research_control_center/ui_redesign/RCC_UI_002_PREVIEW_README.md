# RCC Dashboard V2 Preview

## 여는 방법

압축을 푼 뒤 `dashboard/index.html`을 브라우저로 연다. Dashboard는 정적 HTML, CSS, JavaScript만 사용하며 외부 CDN이나 네트워크 연결이 필요하지 않다.

## 포함 범위

- Dashboard V2 정적 화면과 로컬 assets
- 표시 순서·한글 label·아키텍처 layout을 정의하는 view-only config
- Overview, Architecture, Experiment, Readiness, Mobile 대표 screenshot

## 포함하지 않는 것

- HAI 원시 데이터나 test2
- private numeric authority payload
- credential 또는 사용자 로컬 경로
- scientific production source와 재실행 도구
- 제한된 provider response 및 private artifact

## 해석 경계

표시된 D0/D1/D2 결과는 **PILOT V1**의 고정된 예비 결과다. test1의 14개 연속 공격 구간 단위를 사용했으며 통계적 독립성과 held-out 일반화는 확인되지 않았다. 결과 무결성 확인은 과학적 검증 또는 독립 재현과 같지 않다.

Dashboard config는 표시 계층일 뿐 scientific Registry state를 변경하거나 대체하지 않는다.
