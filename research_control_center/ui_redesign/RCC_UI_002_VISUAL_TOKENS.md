# Dashboard V2 시각 토큰

## 방향

연구 운영 dashboard에 맞는 밝은 중립 배경, 흰 surface, navy navigation, blue selection을 사용한다. 장식적 gradient와 card wall은 사용하지 않는다.

## 의미 색

- `--accent-primary`: 선택·상호작용
- `--state-implemented`: 구현 상태
- `--state-verified`: 근거·무결성 확인
- `--state-warning`: 조건부·주의
- `--state-blocked`: blocker·authority gap
- `--state-unvalidated`: 미실행·미확인·미검증

## 타이포그래피

본문은 16px 이상, line-height 1.58이다. 시스템 font stack과 `Noto Sans KR` fallback을 사용하고, path·symbol·hash는 monospace로 분리한다.

## 밀도

`--space-1`~`--space-8`, 6/12px radius, 한 단계 shadow를 재사용한다. 상태는 색만 쓰지 않고 label·dot·aria-label을 함께 제공한다.
