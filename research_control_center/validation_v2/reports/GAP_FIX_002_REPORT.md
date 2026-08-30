# GAP-FIX-002 — Durable D1 Prediction-before-label Gate

## 판정

`PASS` — VALIDATION V2 전용 durable prediction custody contract가 구현됐다. PILOT V1의
in-memory ordering이나 frozen artifact는 변경하지 않았다.

## 고정된 순서

1. immutable `D1PredictionArtifactV2`를 canonical JSON bytes로 만든다.
2. 명시적인 private custody root 내부 sibling temporary file에 exclusive write한다.
3. file flush와 `fsync` 후 close하고 temporary bytes를 다시 읽어 확인한다.
4. `os.link`를 이용해 destination을 no-overwrite 방식으로 원자적으로 생성한다.
5. destination을 새 handle로 다시 열고 schema, self-hash, authority, record ordering/count를 replay한다.
6. 별도 freeze receipt를 같은 방식으로 publish하고 replay한다.
7. freeze receipt와 prediction이 정확히 일치할 때만 durable label-access lease를 publish한다.
8. factory-issued capability를 한 번만 소비해 label reader를 호출한다.
9. label access 뒤 prediction, receipt, lease byte identity를 다시 확인한다.

## 결속되는 authority

- Formal V4 portfolio authority hash
- runtime authorization hash
- execution-context hash
- source commit
- portfolio hash
- file contract hash
- split role `DEVELOPMENT_TEST1`
- ordered file-local prediction coordinates
- contributing rule IDs와 선택적 trace hashes

`alarm=True` record는 적어도 하나의 contributing rule ID를 요구한다. Trace hash의 완전한
materialization/fidelity contract는 EXP-05 gate 소관이며, GAP-FIX-002가 이를 이미 완성했다고
주장하지 않는다.

## Fail-closed 경계

- stale destination 또는 partial temporary file을 덮어쓰지 않는다.
- hard-link no-overwrite primitive가 지원되지 않으면 fallback 없이 실패한다.
- Git 내부 custody root, symlink/path escape, path-shaped `file_id`를 거절한다.
- wrong/stale authority, context, source, portfolio, file contract를 거절한다.
- prediction/receipt/lease mutation을 label access 전·후 모두 거절한다.
- durable lease 때문에 동일 artifact의 두 번째 또는 동시 authorization을 거절한다.
- capability는 process 안에서도 one-shot이며 concurrent consumption은 하나만 성공한다.

Windows에서는 parent-directory `fsync`를 지원한다고 과장하지 않고
`UNSUPPORTED_WINDOWS`로 기록한다. File `fsync`, close, hard-link publication, reopen/replay는
별도 사실로 유지된다.

## 과학적 경계

이 task는 synthetic contract test만 실행했다. 실제 D1, label, metric, test1, test2, held-out을
열거나 실행하지 않았다. 따라서 가능한 주장은 “VALIDATION V2가 durable
prediction-before-label custody contract를 갖는다”뿐이다. PILOT V1의 governance 등급은
소급 변경되지 않는다.
