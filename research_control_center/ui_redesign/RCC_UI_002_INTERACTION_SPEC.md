# Dashboard V2 상호작용 명세

## 화면 전환

5개 navigation button과 URL hash가 같은 view state를 제어한다. 동시에 하나의 view만 표시한다.

## Architecture Explorer

- node click/Enter/Space: 선택, upstream/downstream highlight, 나머지 dim, drawer open.
- 검색·lane·risk·frozen-only·unknown edge filter.
- zoom in/out, fit, reset.
- Candidate Discovery와 Rule Construction 선택 시 subnode strip 표시.

Edge 표기: frozen execution 굵은 실선, code/test 확인 얇은 실선, design/conditional 점선, authority gap 빨간 점선, legacy/reference 회색선.

## Drawer

기본은 쉬운 보기이며 기술 상세 tab으로 전환한다. Escape, 닫기 button, backdrop으로 닫고 원래 focus를 복원한다. 모바일에서는 full-screen sheet다.

## 표

Catalog, experiment, GAP row는 keyboard Enter로 상세를 연다. chart에는 exact-value table을 병기한다.
