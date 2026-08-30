# Dashboard V2 View Model

## 파이프라인

Registry + GAP-000 tables + display config → `build_dashboard_view_model()` → 정적 HTML·embedded JSON.

## 핵심 collection

- `nodes`: 14개 top-level node, component binding, Input/Process/Output, six-axis status.
- `edges`: source/target, evidence class, artifact, audit report.
- `catalog`: Registry 32개 component의 검색용 projection.
- `pilot_results`: Registry에서 읽고 exact frozen assertion을 통과한 D0/D1/D2 값.
- `overlap`: Registry overlap 10/1/3/0 assertion.
- `experiments`: experiments.csv와 GAP gate의 결합 view.
- `root_issues`: GAP root issue와 remediation primary disposition/urgency의 결합 view.

## 검증 규칙

- 모든 component ID는 Registry에 존재해야 한다.
- 14 node ID와 edge ID는 중복될 수 없다.
- 모든 edge endpoint는 유효 node여야 한다.
- 32 component는 node/detail/catalog-only 중 정확한 접근 경로가 있어야 한다.
- Pilot, overlap, candidate, construction 수치는 한 곳에서 assertion한다.

Display config는 scientific status를 override할 수 없다.
