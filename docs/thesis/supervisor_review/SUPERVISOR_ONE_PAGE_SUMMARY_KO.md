# 지도교수 검토용 핵심 요약

## A. 연구 주제와 현재 framing

**권장 제목**

> Evidence-Bound and Verifiable Rule Construction for Explainable
> Multivariate CPS Anomaly Detection

**한 문장 연구 입장**

> 확인된 다변량 CPS 관계와 정상 데이터 기반 수치 참조를 사용하여,
> 제안 생성과 결정론적 검증을 분리한 근거 결속형 규칙 구성 파이프라인을
> 제시하고 구성 유효성, 확률적 강건성, 호출 비용 및 fail-closed 입장을
> 비교한 연구입니다.

여기서 **verifiable**은 검증기 적격성에 대한 결정론적 구성 검증을
뜻합니다. 이상탐지 성능, 운영 runtime 또는 배포 안전성이 검증되었다는
의미는 아닙니다.

## B. 연구 흐름

```text
Candidate Discovery: META / STAT / GDN
        ↓
47 unique pairs
        ↓
Normal Relation Profiling
        ↓
25 supported pairs / 45 directions
        ↓
One-way Confirmation
        ↓
42 confirmed directions
        ↓
Deterministic Numeric Calibration
        ↓
Rule Construction: T0 | T1 | T1-B | T2
        ↓
Deterministic Verifier
        ↓
Accepted / no_rule

Completed empirical boundary
----------------------------
Downstream labeled utility: NOT_EXECUTED
```

## C. 핵심 결과

| 항목 | 결과 | 논문에서의 해석 |
|---|---:|---|
| Candidate union | 47 pairs | 서로 다른 후보 근거의 무점수 합집합 |
| Normal relation fit | 25 pairs / 45 directions | 정상 데이터 관계 적합 근거 |
| One-way confirmation | 42 directions | 구성 입력으로 확인된 방향 관계 |
| T0 | 42/42 accepted, 0 calls | 결정론적 기준선; 유용성 승자 아님 |
| T1 | 42/42 accepted, 42 calls | 본 코호트·단일 실행에서 one-shot 가능성 |
| T1-B | 42/42 accepted, 126 calls | 첫 draw 실패 1건 복구, T1 대비 3배 호출 |
| T2 | 39/42 accepted, 3 `no_rule`, 42 calls | 증분 유효성 이득 미관찰 |
| Direct-number | 42/42 structured output | 구조 적합과 수치 정확성은 다름 |
| Utility | `NOT_EXECUTED` | Utility는 평가되지 않음 |

T1-B는 call 1/2/3 이후 누적 산출률이 41/41/42였고, 선택된 call은
41/0/1이었습니다. T2는 bounded verifier-feedback construction으로
설계되었으나, 세 거절이 모두 non-repairable이어서 feedback eligible,
revise, retrieve, follow-up 및 recovery가 모두 0이었습니다. 따라서
feedback recovery는 실증적으로 작동하지 않았습니다.

T0, T1, T1-B가 모두 42/42에 도달한 것은 **construction-validity
ceiling**을 뜻합니다. 구성 유효성만으로는 downstream 우월성을 구별할
수 없습니다. 이 때문에 utility가 과학적으로 중요했지만, 별도로 동결한
post-result/pre-label 프로토콜의 최종 집중 감사에서 두 평가 권한 문제가
남아 실제 라벨·테스트 특징값 접근 전에 중단했습니다.

## D. 현재 contribution

- **C1 — Evidence-bound construction pipeline:** 후보 탐색부터 확인된 관계,
  수치 참조, 제안 및 검증까지 연결한 근거 결속형 파이프라인
- **C2 — Deterministic numeric authority:** 정상 데이터 보정과 참조 결속에
  기반한 결정론적 수치 권한
- **C3 — Deterministic verification + fail-closed `no_rule`:** 유효하지 않은
  제안을 승인 집합에 포함시키지 않는 구성 입장 정책
- **C4 — Controlled T0/T1/T1-B/T2 comparison:** 부정적 결과와 호출 비용을
  포함한 구성 전략 비교

Direct-number 실험에서는 모든 출력이 구조적으로 완전했지만 정규화 수치
오차가 컸습니다. 이는 본 계약에서 LLM이 권위 있는 수치를 직접 생성하게
하기보다 정상 데이터 기반 보정값을 참조하게 하는 설계를 지지합니다.

## E. 가장 중요한 한계와 논문 가능성

가장 중요한 한계는 **라벨 기반 downstream anomaly utility가 없다는
점**입니다. 따라서 이상탐지 성능 향상, detector 개선 또는 useful-rule
winner는 주장할 수 없습니다.

그럼에도 본 연구에는 완결된 후보-관계 파이프라인, 결정론적 수치 권한,
통제된 4개 구성 전략 비교, 의미 있는 T2 부정적 결과, Direct-number 보정
ablation, 결정론적 verifier/`no_rule` 결과 및 엄격한 주장 경계가 있습니다.
따라서 논문을 construction, calibration, verification 및 governance에
한정하면 일관된 석사논문 기여가 가능합니다.

## F. 제목 선택지

1. **Option A — 권장 / 균형형**

   *Evidence-Bound and Verifiable Rule Construction for Explainable
   Multivariate CPS Anomaly Detection*

   응용 맥락을 유지하면서 구성·검증 기여를 균형 있게 표현하지만,
   utility 미평가 경계를 본문에서 명확히 해야 합니다.

2. **Option B — 보수형**

   *Governed Construction of Verifier-Admissible Rules from Normal-Data CPS
   Relations*

   현재 실증 범위와 가장 정확히 일치하며 anomaly-performance를 암시할
   위험이 가장 낮습니다.

3. **Option C — 비교 실험형**

   *Comparing Deterministic and Bounded LLM-Assisted Rule Construction for
   Multivariate CPS Anomaly Detection*

   T0/T1/T1-B/T2 비교를 선명하게 보여주지만 LLM 비교를 연구 전체보다
   과도하게 중심화할 위험이 있습니다.

## G. 범위 선택지

- **PATH A — 권장: NARROWED CONSTRUCTION-GOVERNANCE THESIS**
  새 실험 없이 writing으로 진행하며, 주장을 construction validity,
  calibration, verification 및 governance에 한정합니다.
- **PATH B — 교수님이 학위 요건상 명시적으로 요구하는 경우에만:
  ANOMALY-EFFECTIVENESS THESIS**
  추가 label-aware utility evidence가 필요하며, 이는 별도 설계·승인이
  필요한 새로운 과학 작업입니다. 중단된 utility 경로를 자동 재개하지
  않습니다.

T2가 긍정적으로 보이도록 provider를 재실행하거나, cohort·verifier
threshold·metric을 사후 변경하거나, repairable 사례만 선택하는 세 번째
경로는 제안하지 않습니다.

## 교수님께 확인드리고 싶은 사항

1. **Decision 1 — 논문 framing:** anomaly-detection 성능 향상 주장을
   제외하고 construction, calibration, verification 및 governance를 핵심
   contribution으로 석사논문을 마무리하는 방향이 적절한지요?
2. **Decision 2 — 제목/범위:** 위 세 제목 중 어느 수준까지 application-
   oriented한 표현을 유지하는 것이 적절한지요?
3. **Decision 3 — empirical scope:** 현재 RQ/contribution과 실증 범위로
   충분한지요? 부족하다고 판단하실 경우, 학위논문 요건 충족을 위해
   반드시 추가되어야 하는 **구체적인 한 가지 empirical evidence**가
   무엇인지 확인 부탁드립니다. 이 질문은 utility가 필수라고 전제하지
   않습니다.
