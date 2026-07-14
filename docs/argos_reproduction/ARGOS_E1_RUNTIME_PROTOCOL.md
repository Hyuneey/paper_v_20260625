# ARGOS E1 Runtime Protocol

## Scope

E1 executes one frozen TASK-026Q rule in isolated Linux containers against four
repository-owned synthetic, non-KPI arrays. It checks runtime plumbing, output
shape, binary domain, finite values, exception handling, and deterministic
replay. It does not assess whether any label is scientifically correct.

## Frozen input

- ARGOS commit: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- Rule SHA-256:
  `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659`
- Request SHA-256:
  `14af5d91248f3ca579a445527768264f148497d58d85b49b96b39b8873918aca`
- Response SHA-256:
  `f7a1241323c98b716c651dac797cd502c0fd2c7b3c2a7b6142f34e8bbb418810`

The rule remains in ignored private storage. The wrapper verifies its hash and
reruns the frozen static allowlist. The image verifies the hash again before
loading the rule. No source excerpt is persisted.

## Isolation

Every rule container uses `--network none`, a read-only root, dropped
capabilities, `no-new-privileges`, PID/CPU/memory limits, and bounded
`noexec,nosuid` tmpfs mounts. The image user is non-root. Only the exact rule
file and exact fixture file are mounted read-only. The repository root, host
home, credentials, and container socket are not mounted.

The container emits a bounded JSON result and a same-content ephemeral output
file. Tracked reports retain hashes and structural checks only.

## Fixtures and replay

The fixture matrix is constant, monotonic, localized-spike, and empty `N x 1`
numeric series. None derives from KPI, SWaT, WADI, Kaggle, or provider data.

Each fixture is run twice in a fresh container. Successful repetitions must
match on rule hash, fixture hash, image digest, exit status, output count,
binary-domain result, and output hash. The empty series is an edge-case probe;
the three non-empty fixtures define the pass gate.

## Claim boundary

`passed_runtime_smoke` means only that the frozen Python rule loaded and
returned deterministic, finite binary arrays with matching lengths for the
three required non-empty synthetic fixtures. No accuracy, precision, recall,
F1, anomaly-detection effectiveness, or benchmark conclusion follows.
