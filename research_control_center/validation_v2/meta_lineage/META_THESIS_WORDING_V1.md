# META thesis wording V1

## A. Short

META는 공식 HAI 공정 그래프와 AI-assisted reviewed semantic metadata를 결합한 결정론적 후보-prior ranking이다.

## B. Methods

META 후보 탐색은 공식 HAI 기술 매뉴얼과 고정된 P1 directed physical graph를 근거 출처로 사용했다. Codex/AI가 이 공식 자료를 검토해 만든 private structured declaration은 variable-to-graph-node mapping, subsystem mapping, 명시적 source→target control-chain declaration과 공식 reference binding을 제공했다. 이후 deterministic code가 frozen 12×12 directed pair universe의 144개 pair를 `M1_EXPLICIT`, `M2_GRAPH_ADJACENT`, `M3_SUBSYSTEM_SUPPORTED`, `UNSUPPORTED`로 분류하고, tier·독립 공식 source category 수·lexical identity의 고정 순서로 ranking하여 Top-20을 선택했다. 이 단계는 실제 HAI 시계열 값, attack label, downstream relation outcome 또는 다른 candidate arm score를 사용하지 않았으며, 결과는 relation의 인과성이나 탐지 성능이 아니라 후속 normal-only profiling에 투입할 candidate prior만 제공한다.

## C. Limitation

Exact META ranking은 공식 reference bytes와 graph만으로 완전히 재생되지 않으며, self-hash가 고정된 private reviewed semantic declaration이 추가로 필요하다. 보존된 실행 기록은 이 declaration을 Codex/AI가 공식 자료를 바탕으로 작성했음을 지지하지만, 연구자가 각 semantic mapping과 explicit pair를 개별적으로 검토·승인했는지, 각 pair가 공식 문장에서 직접 옮겨졌는지 또는 semantic inference를 포함했는지는 확인되지 않는다. 따라서 META를 “fully automatic”, “researcher-selected”, “expert-defined” 또는 순수한 process-graph derivation으로 표현하지 않는다.

## 권장 graph-guided 표현

1차 표현은 **Process-Graph-Guided with AI-assisted Reviewed Semantic Metadata**이다. 한국어로는 **공정 그래프와 검토된 의미 메타데이터 기반 후보 탐색**을 권장한다.

- Process Graph evidence: 공식 P1 graph의 directed adjacency
- Reviewed Semantic Metadata: explicit pair, variable-node, subsystem declaration
- Learned Graph evidence: GDN이 생성하는 별도 정상 prediction relation evidence

세 근거를 하나의 “graph”로 합치거나 인과 graph로 부르지 않는다.
