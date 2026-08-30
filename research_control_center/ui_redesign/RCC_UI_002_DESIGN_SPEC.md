# RCC Dashboard V2 설계 명세

## 목표

Dashboard V2는 Registry를 과학 상태의 단일 출처로 유지하면서, 사용자가 `현재 단계 → 전체 구조 → 세부 근거 → 다음 작업` 순서로 이해하도록 구성한다. 한 페이지 장문 보고서였던 V1을 5개 화면을 가진 정적 애플리케이션으로 전환한다.

## 화면

1. 개요: 현재 단계, 다음 작업, 연구 rail, 축약 아키텍처, Pilot 결과, Gate/위험/최근 변경.
2. 아키텍처: 4 lane·14 top-level node SVG, edge 근거 상태, 구성요소 catalog.
3. 실험·결과: Recall, FAR/hour, D0/D1 overlap, EXP roadmap.
4. 준비도·위험: Primary disposition과 Urgency를 분리한 GAP-000 view.
5. 이력·근거: milestone, decision, claim, source authority.

## 불변 조건

- Registry와 ARCH audit가 의미를 제공하고 display config는 순서와 표현만 제공한다.
- 외부 CDN·원격 runtime dependency가 없다.
- 과학 source, result, artifact를 생성하거나 수정하지 않는다.
- UNKNOWN은 추정하지 않는다.

## 구현

`build_dashboard.py`가 `dashboard_v2.py`의 view model과 renderer를 호출한다. 결과는 `dashboard/index.html`, `assets/rcc.css`, `assets/rcc.js`로 구성된다. JavaScript는 화면 전환과 표시 상호작용만 수행하며 Registry를 변경하지 않는다.
