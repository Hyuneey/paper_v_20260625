# RCC Dashboard V2 정보구조

## 사용자 질문

- 지금 연구는 어느 단계인가?
- 전체 시스템은 어떻게 연결되는가?
- 각 구조는 어디까지 구현·실행·점검·재현·검증됐는가?
- 가장 먼저 결정하거나 수정할 것은 무엇인가?

## 5개 1차 메뉴

`개요 / 아키텍처 / 실험·결과 / 준비도·위험 / 이력·근거`

V1의 23개 anchor는 제거했다. 데이터·후보·관계·규칙·Verifier·Runtime·D0·D1·D2·Metrics는 아키텍처 node나 drawer로 이동했다. 32개 component는 검색 가능한 catalog에 남긴다.

## 개요 정보량

1440×900에서 현재 단계, 다음 작업, 연구 rail, 14-node 축약 map, 상위 3개 action, Pilot 비교, EXP-01~05 Gate를 우선 노출한다. 장문 Registry 설명, full SHA, 전체 risk/claim은 상세 화면으로 이동한다.

## 점진적 공개

1. top-level node
2. 쉬운 보기: 필요성, Input, 처리, Output, 상태, 결과, 미검증, 다음 작업
3. 기술 상세: component ID, path, symbol, artifact, test, ref/hash

후보 탐색은 META/STAT/GDN, Rule Construction은 Evidence Pack/T0/T1/T1-B/T2 subnode를 제공한다.
