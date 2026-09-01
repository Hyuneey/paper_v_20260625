# VALIDATION V2 계산 자원·장기 병목 감사

상태: `AUDITED_EXP01_EXP02_FORMAL_V4_EXP05_PERFORMANCE_FOUNDATIONS_QA_PASS`

## 현재 계산 환경

| 항목 | 확인값 |
|---|---|
| GPU | NVIDIA GeForce RTX 5060 Laptop GPU |
| driver | 610.47 |
| VRAM | 8,151 MiB |
| 감사 시 GPU utilization | 0% |
| VALIDATION V2 Python | 3.12.13 |
| PyTorch | 2.12.1+cpu |
| `torch.version.cuda` | `None` |
| `torch.cuda.is_available()` | `False` |
| PyG | 2.8.0 |
| frozen GDN device | `cpu` |
| dtype | `float32` |
| seeds | 11, 23, 37 |

## GPU 판단

이번 EXP-01 checkpoint 복구와 후처리는 `CPU_APPROPRIATE`다.

1. 이미 완료된 12개 checkpoint는 CPU training config hash에 묶여 있다.
2. 현재 전용 환경의 PyTorch는 CPU build라 CUDA를 사용할 수 없다.
3. 이번 병목은 tensor 연산이 아니라 Python 관계 추출의 제곱시간 반복이었다.
4. model은 작고 데이터 window 생성이 Python/CPU 중심이어서, 단순 CUDA 이동만으로
   큰 개선이 보장되지 않는다.
5. CPU checkpoint를 GPU에서 다시 학습하면 완료 결과 재실행이 되고, backend 및
   numerical determinism identity도 새로 동결해야 한다.

따라서 현재 checkpoint salvage에는 GPU를 사용하지 않는다. 향후 새로운 V2 GDN
실행에서 GPU를 선택하려면 별도 backend/config/environment receipt와 CPU/GPU
수치 비결정성 경계를 결과 관찰 전에 동결해야 한다.

실제 재개 실행 중 GPU utilization은 0%, Python working set은 약 630MB였고,
CPU가 주 계산 자원이었다. 최적화된 경로는 이전 학습을 반복하지 않고 완료됐다.

## 병목 우선순위

| 우선 | 영역 | 분류 | 확인된 비효율 | 안전한 대응 |
|---|---|---|---|---|
| P0 | EXP-01 관계 확인 | CPU algorithmic | event index마다 전체 시퀀스 재검증, source-event 중첩 scan | 감사된 선형 extractor와 indexed isolation을 사용함 |
| P0 | Formal V4 대량 runtime | CPU/IO | opportunity마다 동일 authority/portfolio 전체 hash·replay 가능성 | 향후 immutable pre-authorized session으로 1회 preflight 후 순수 window 평가; 결과 의미는 유지 |
| P0 | EXP-02 | CPU algorithmic | relation×row 반복 scan 가능성, producer semantics 미동결 | 의미 contract를 먼저 동결한 뒤 1회 open·공유 sufficient-stat cache·batch 평가 |
| P1 | EXP-05 runtime-to-trace | CPU/IO | unit마다 동일 Formal V4 authority/numeric replay | prepared batch start/end replay와 ordered batch binding을 구현함 |
| P1 | EXP-05 durable custody | IO-bound 가능 | trace마다 fsync/close/reopen이면 작은 파일 IOPS 증가 | 현재 durability 의미를 유지하며 실제 cohort 규모가 확인된 뒤 별도 contract로 판단 |
| P1 | 미래 GDN training | CPU input overhead | sample별 NumPy→Tensor 변환과 반복 edge transfer | 새 실행 버전에서만 tensor cache/DataLoader 및 device preallocation 검토 |
| 낮음 | Isolation Forest/PCA model | CPU appropriate | 표 형태·중간 규모 normal-only 계산 | GPU 강제 사용 불필요, 병렬 CPU thread 수는 환경 receipt에 고정 |
| 완료 | Detector authority hash | CPU memory copy | 대형 matrix/score의 전체 `tobytes()` 복사 | 기존 SHA-256과 byte-identical한 contiguous-buffer hash 적용 |
| 낮음 | metric adapter | CPU appropriate | Boolean timeline/episode grouping | 현재 공통 metric 의미 유지, 불필요한 재읽기만 제거 |

## 구현하지 않은 항목

EXP-01의 증명된 병목은 checkpoint resume와 선형/indexed adapter로 해결했다.
후속 EXP-02 효율화에서는 미동결 scientific producer semantics를 추정하지 않고,
single-parse·summary precompute·37-candidate batch evaluation 경계만 합성 테스트로
구현했다. Formal V4와 EXP-05 runtime-to-trace 경로는 각각 start/end authority
replay를 가진 prepared batch로 구현했다. EXP-05 durable small-file custody와 future
GPU GDN 개선은 별도 contract와 QA가 필요하므로 아직 변경하지 않았다.

## 비-EXP01 정적 병목 상세

### 1. Formal V4 runtime

현재 정적 호출 경로는 각 rule opportunity마다 runtime authorization과 bound
artifact를 다시 검증한다. 최악의 정적 경로상 opportunity마다 약 18회의
bound-file read/hash pass와 3회의 JSON parse가 반복될 수 있다. 수천 개
opportunity를 처리하는 D1·EXP-05에서는 다음으로 큰 CPU/IO 병목이다.

안전한 개선은 실행 시작 시 authority 전체를 한 번 replay해 immutable prepared
capability와 descriptor/numeric lookup map을 만들고, 각 window는 O(1) lookup으로
평가한 뒤 종료 시 bound bytes를 다시 hash하는 것이다. 이 경계는
`FORMAL_V4_PREPARED_RUNTIME_PERFORMANCE_V2.md`에 따라 구현됐다. 단순 `lru_cache`가
아니며, 시작/종료 full replay와 mutation fail-closed를 유지한다. 기존 single-window
trace와 PASS/FAIL/ABSTAIN bit-identical synthetic conformance도 통과했다. 실제 V2
portfolio scientific runner 연결은 아직 수행하지 않았다.

### 2. EXP-02

scientific runner를 구현하기 전에 다음 성능 계약을 고정해야 한다.

- train1/train2/train4는 각 한 번만 parse한다.
- normal summary는 relation/policy별로 반복 계산하지 않고 승인된 identity별로
  한 번 사전계산한다.
- event extraction과 isolation은 `TASK-039D1R` linear/indexed adapter를 사용한다.
- 모든 frozen candidate를 그대로 평가하고 결과만 deterministic sorted merge한다.
- candidate, relation, row, seed 분모를 줄이지 않는다.

이는 다시 발생할 수 있는 relation×row×full-sequence 반복 scan을 실행 전에
차단하는 조건이다. 이 경계는 `EXP02_PERFORMANCE_FOUNDATION_V2.md`에 따라 구현됐고,
실제 producer 연결은 세 external scientific binding과 별도 V2 cohort가 동결된 뒤에만
허용된다. 이 로직은 branch 중심 CPU 작업이므로 GPU 대상이 아니다.

### 3. HAI parsing 및 detector

HAI adapter는 큰 CSV를 Python row 단위로 timestamp parse와 37개 float 변환을
수행한다. 한 scientific session에서 split을 한 번 열어 immutable frame을
D0, Isolation Forest, D1 consumer에 공유하는 것이 안전한 1차 개선이다. 장기적으로는
raw SHA, parser source hash, feature-order hash, sampling contract, matrix hash에 묶인
private feature cache가 가능하지만 원본과의 value/byte parity receipt가 필요하다.

Isolation Forest는 CPU-only이며 frozen `n_jobs=1`이다. GPU 이동이나 `n_jobs`
변경은 현재 config를 바꾸므로 적용하지 않는다. 대형 matrix/score hash의
`tobytes()` 임시 복사는 동일 digest를 유지하는 contiguous-buffer `memoryview`
hash로 교체했고 synthetic byte-equivalence와 allocation regression을 통과했다.

### 4. EXP-05, EXP-04, Metrics

- EXP-05 runtime-to-trace는 prepared Formal V4 batch에 연결되어 unit 수에 비례한
  authority/numeric file replay를 제거했다. direct unit과 bit-identical이며 종료
  replay 전 trace를 공개하지 않는다.
- EXP-05 trace별 atomic write, fsync, close, reopen은 그대로 유지한다. 실제 cohort
  규모와 IOPS 증거 없이 append-only 형식으로 바꾸면 durable custody 의미가 달라질
  수 있으므로 이번 최적화 범위에서 제외했다.
- EXP-04 fusion은 rule outcomes 중복 순회와 coordinate별 set 정렬을 한 번의
  grouped pass로 합칠 수 있다.
- 현재 14-unit metric의 event×episode 비교는 규모가 작아 최적화 우선순위가
  낮다. 확대 held-out에서만 two-pointer sweep을 검토한다.

## 실행 우선순위

1. EXP-02 runner 전에 single-parse·precompute·linear/indexed contract를 동결한다.
2. V2 portfolio 이후 D1/EXP-05 전에 prepared Formal V4 batch runtime을 별도
   conformance task로 구현한다.
3. EXP-04에서는 test1을 허가된 한 번의 session에서 parse해 모든 method adapter가
   공유하도록 한다.
4. GPU GDN은 향후 새 실행 identity에서만 별도 동결한다.

## 과학적 안전

- architecture 변경: 0
- hyperparameter 변경: 0
- seed 변경: 0
- data/split 변경: 0
- protocol/preregistration 변경: 0
- PILOT V1 변경: 0
- test1/test2/held-out/label 접근: 0
