# META reviewed evidence 계보 감사 V1

## 결론

META 후보 근거의 가장 방어 가능한 1차 분류는 `HYBRID_REVIEWED_METADATA`이다. 공식 HAI 기술 매뉴얼과 P1 물리 그래프가 근거 출처이고, AI/Codex가 그 공식 자료를 검토해 만든 semantic declaration과 물리 그래프의 결정론적 처리가 함께 최종 ranking에 기여했다. 최종 META Top-20 자체를 연구자가 수동으로 고른 증거는 없다.

연구자 개입 수준은 `HUMAN_INTERVENTION_LEVEL_1`로 분류한다. 사용자는 공식 자료와 frozen protocol을 승인했지만, 살아남은 실행 기록상 pair-level declaration은 Codex가 작성했다. 다만 declaration의 **개입 표면**은 12개 source→target pair를 명시한 LEVEL 3 수준이다. 이는 연구자 본인이 그 12개 pair를 선택했다는 뜻이 아니다.

## 감사 범위와 불변성

- 기준 branch/head: `validation-v2` @ `2f5eabdb9fb5c9f01947a17a086a20ecab325d3f`
- META implementation commit: `2b3df4443619b8d0d19434bbcd1ded3b31a1b8ea`
- META public result commit: `b8a744c4b2cc70cd70bfc73ce45408c2ec8b5824`
- META result artifact hash: `0e3b055df911c74bd0e0993b7b3bb122860b265192ad0cf91d54edc1e74635bf`
- reviewed input의 공개 attested hash: `8cdb1e606149a2d7647f4b68955280187ad7219d09fde17660cdfb80f2708e39`
- 이 감사의 과학 실행, HAI feature-value 접근, label 접근, test1/test2/held-out 접근: 모두 0

META Top-20, 144-pair universe, V2A candidate union, 39-rule portfolio, EXP-02 및 GDN artifact는 변경하지 않았다.

## Reviewed evidence 상태

예상 local-only 파일 `artifacts/task039c_meta/TASK-039C_META_REVIEWED_EVIDENCE_INPUT.json`은 감사 시점에 존재하지 않았다. Git에는 추적된 적이 없고 `artifacts/` ignore 규칙의 적용 대상임을 확인했다. 따라서 현재 bytes와 내부 reference catalog 전체를 직접 재검사하거나 bytes unchanged를 증명할 수는 없다. 파일을 재구성하지 않았으며, 아래 구조 평가는 공개 schema·validator·result와 보존된 실행 기록만 사용한다.

## 정확한 계보

| 단계 | 입력 → 출력 | 변환 분류 | 정확한 의미 |
|---|---|---|---|
| 1 | 공식 HAI 기술 매뉴얼 → reference identity | `OFFICIAL_REFERENCE_LOOKUP` | 매뉴얼 bytes의 SHA-256/Git blob을 고정했다. 매뉴얼 의미를 production code가 자동 파싱하지는 않았다. |
| 2 | 공식 P1 물리 그래프 → directed node adjacency | `OFFICIAL_REFERENCE_LOOKUP` + `AUTOMATIC_CODE_TRANSFORMATION` | 고정 JSON graph를 code가 파싱했다. |
| 3 | 공식 자료 → reviewed evidence input | `AI_ASSISTED_EXTRACTION` + `STATIC_DECLARATION` | 보존된 Codex 실행 기록에서 입력 파일을 생성·수정한 patch가 확인된다. 연구자의 pair-level 작성은 확인되지 않았다. |
| 4 | frozen role lists → 144 pairs | `AUTOMATIC_CODE_TRANSFORMATION` | 12 source × 12 target의 결정론적 directed cross product다. |
| 5 | reviewed declaration + graph → M1/M2/M3/UNSUPPORTED | `AUTOMATIC_CODE_TRANSFORMATION` | code가 고정 우선순위로 모든 pair를 분류한다. |
| 6 | supported records → META ranking | `AUTOMATIC_CODE_TRANSFORMATION` | tier, 독립 공식 source category 수, lexical identity 순이다. |
| 7 | ranking → Top-20 | `AUTOMATIC_CODE_TRANSFORMATION` | 정렬된 supported ranking의 앞 20개이며 사람의 최종 선택이 아니다. |

흐름은 다음과 같다.

`공식 HAI 매뉴얼 + 공식 P1 물리 그래프 → AI-assisted reviewed semantic declaration → deterministic 144-pair tiering/ranking → META Top-20`

## Reviewed evidence의 구조적 역할

공개 validator와 결과가 증명하는 최소 구조는 다음과 같다.

- source variable→graph-node binding declaration: 12
- target variable→graph-node binding declaration: 12
- source variable→subsystem binding declaration: 12
- target variable→subsystem binding declaration: 12
- explicit source→target pair declaration: 12
- 공식 근거 category: HAI technical manual, P1 physical graph
- reference ID와 reviewed annotation을 가진 declaration 구조

private 파일이 없으므로 전체 reference catalog entry 수와 raw annotation 내용은 `UNRESOLVED`다. 공개 결과에는 30개 supported record가 있고 tier count는 M1 12, M2 11, M3 7이다. M1 12개는 중복 없는 explicit pair declaration 12개와 일대일 대응한다.

## META tier 의미

| Tier | source | 명시 pair 필요 | 자동 graph 처리 | reviewed semantic 판단 | 수치 데이터 |
|---|---|---:|---:|---:|---:|
| `M1_EXPLICIT` | 공식 매뉴얼에 결속된 explicit control-chain declaration | 예 | adjacency는 보조 근거일 수 있음 | 예 | 없음 |
| `M2_GRAPH_ADJACENT` | reviewed variable→node mapping 뒤의 공식 directed graph edge | 아니오 | 예 | mapping에 필요 | 없음 |
| `M3_SUBSYSTEM_SUPPORTED` | reviewed source/target subsystem membership의 교집합 | 아니오 | 아니오 | 예 | 없음 |
| `UNSUPPORTED` | 승인된 세 근거 모두 없음 | 아니오 | 아니오 | 추가 판단 없음 | 없음 |

Top-20은 M1 12개와 M2 상위 8개로 구성된다. 따라서 explicit reviewed declaration과 graph automation이 모두 exact ranking에 실질적으로 기여한다.

## 수동·AI 개입 질문

| 질문 | 답 | 근거 |
|---|---|---|
| Q1. 연구자가 최종 META Top-20을 수동 선택했는가? | `NO` | code가 고정 ranking의 prefix를 선택한다. |
| Q2. 인간 또는 AI가 reviewed input에 source→target pair를 명시했는가? | `YES` | 12개 M1 explicit declaration과 보존된 Codex patch 기록이 있다. |
| Q3. 그 pair는 공식 문장의 직접 복사인가, semantic inference인가? | `UNRESOLVED` | 공식 reference 결속은 확인되지만 pair별 인용·추출 절차는 보존되지 않았다. |
| Q4. 공식 bytes와 graph와 deterministic code만으로 exact Top-20을 재생할 수 있는가? | `NO` | reviewed variable mappings, subsystem mappings, explicit pairs가 추가 authority다. |
| Q5. private reviewed input은 무엇을 더하는가? | `YES` | 위 semantic mappings, explicit pair declarations, official-reference bindings를 추가한다. |
| Q6. 실제 HAI 시계열 값이 사용됐는가? | `NO` | public data-access audit에서 feature-value file access가 0이다. |
| Q7. attack label 또는 downstream relation outcome이 사용됐는가? | `NO` | label/outcome 입력 API가 없고 BR2 pair supervision·cross-arm score가 false다. |

## Authorship 판단

Git commit author는 content author를 증명하지 않는다. 다만 보존된 원 실행 transcript(`019fea51-699a-78a0-a6e6-e717cda13b02`, transcript SHA-256 `96d0ab6eb2a6a33308dcd6c56c4420127bc8882bb1859b0b5e7994592635267c`)에는 Codex가 공식 manual/graph를 점검한 뒤 정확한 expected private input 경로를 add/update한 도구 기록이 있다. 해당 사용자 메시지에는 P1 variable ID나 pair list가 없었다.

따라서 surviving evidence가 지지하는 진술은 **“Codex/AI가 공식 자료를 검토하여 structured semantic declaration을 작성했고, deterministic code가 최종 ranking을 만들었다”**이다. 연구자가 그 declaration을 pair별로 검토·승인했는지는 `UNRESOLVED`다.

기존 public parallel review의 `general_llm_semantic_inference_used=false`는 frozen META execution 중 새로운 LLM inference가 없었다는 뜻으로 해석해야 한다. execution 전에 Codex가 private reviewed declaration을 작성했다는 계보와 모순되지 않는다.

## 재현성

분류는 `PARTIALLY_REPRODUCIBLE_PRIVATE_REVIEWED_INPUT_REQUIRED`다. GitHub clone만으로 code, official reference identity, public result, tier/ranking semantics은 감사할 수 있지만 exact Top-20을 새로 생성하려면 self-hash가 맞는 private reviewed declaration이 필요하다. 현재 그 파일은 없으므로 surviving public artifacts만으로 exact regeneration은 불가능하다.

## Claim 경계

- 권장 primary term: **Process-Graph-Guided with AI-assisted Reviewed Semantic Metadata**
- 짧은 한국어: **공정 그래프와 검토된 의미 메타데이터 기반 후보 탐색**
- Process Graph evidence: M2 adjacency를 결정론적으로 제공한다.
- Reviewed Semantic Metadata: M1 explicit pair, variable→node, subsystem mapping을 제공한다.
- Learned Graph/GDN evidence: 별도 정상 데이터 기반 prediction relation evidence이며 META에 포함되지 않는다.

`fully automatic`, `researcher-selected`, `expert-defined`, `causal graph derived`는 현재 근거보다 강하므로 피한다.

