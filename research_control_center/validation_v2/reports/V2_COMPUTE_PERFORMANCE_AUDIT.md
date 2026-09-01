# VALIDATION V2 계산 자원·장기 병목 감사

상태: `AUDITED_WITH_EXP01_SAFE_REMEDIATION`

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

## 병목 우선순위

| 우선 | 영역 | 분류 | 확인된 비효율 | 안전한 대응 |
|---|---|---|---|---|
| P0 | EXP-01 관계 확인 | CPU algorithmic | event index마다 전체 시퀀스 재검증, source-event 중첩 scan | 감사된 선형 extractor와 indexed isolation을 사용함 |
| P0 | Formal V4 대량 runtime | CPU/IO | opportunity마다 동일 authority/portfolio 전체 hash·replay 가능성 | 향후 immutable pre-authorized session으로 1회 preflight 후 순수 window 평가; 결과 의미는 유지 |
| P0 | EXP-02 | CPU algorithmic | relation×row 반복 scan 가능성, producer semantics 미동결 | 의미 contract를 먼저 동결한 뒤 1회 open·공유 sufficient-stat cache·batch 평가 |
| P1 | EXP-05 trace custody | IO-bound 가능 | trace마다 fsync/close/reopen이면 작은 파일 IOPS 증가 | contract가 허용할 때 append-only batch와 최종 index/hash; 현재 의미를 먼저 동결 |
| P1 | 미래 GDN training | CPU input overhead | sample별 NumPy→Tensor 변환과 반복 edge transfer | 새 실행 버전에서만 tensor cache/DataLoader 및 device preallocation 검토 |
| 낮음 | Isolation Forest/PCA | CPU appropriate | 표 형태·중간 규모 normal-only 계산 | GPU 강제 사용 불필요, 병렬 CPU thread 수만 환경 receipt에 고정 |
| 낮음 | metric adapter | CPU appropriate | Boolean timeline/episode grouping | 현재 공통 metric 의미 유지, 불필요한 재읽기만 제거 |

## 구현하지 않은 항목

이번 변경은 EXP-01의 증명된 병목만 고쳤다. Formal V4, EXP-02, EXP-05, future GPU
GDN의 개선은 각각 contract와 QA를 동반해야 하므로 이 감사에서 코드를 변경하지
않았다. 특히 EXP-02의 미동결 scientific producer semantics를 속도 목적만으로
추정하지 않는다.

## 과학적 안전

- architecture 변경: 0
- hyperparameter 변경: 0
- seed 변경: 0
- data/split 변경: 0
- protocol/preregistration 변경: 0
- PILOT V1 변경: 0
- test1/test2/held-out/label 접근: 0
