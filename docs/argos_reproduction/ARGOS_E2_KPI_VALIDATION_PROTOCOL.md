# ARGOS E2 KPI Validation Protocol

TASK-034 executes the frozen TASK-033 rule on only the chronological validation
partition of the selected KPI training series. This is validation feasibility,
not a benchmark or thesis-performance result.

## Frozen inputs

- ARGOS commit: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- Rule SHA-256: `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659`
- KPI ID: `05f10d3a-239c-3bef-9bdc-a2feeb0037aa`
- Converted CSV SHA-256: `f6a6d834e23417da5cd0e87af227ae62f0c12a73f080afa08b08a2d332aa5d55`

## Split and seal

The implementation reproduces `datasets/dataset.py`: first compute
`int(N * 0.7)`, then compute `int(train_pool_length * 0.8)`. The guarded reader
retains only validation rows and stops at the validation end, which is the test
start. It does not parse the final 30% or the separate competition ground-truth
package.

## Execution

The dedicated image contains Python, NumPy, and a metric-free entrypoint only.
Two fresh rootless Podman containers receive three mounts: the frozen rule,
validation values, and one private output directory. Labels, repository root,
credentials, test rows, and container sockets are absent. The full validation
array is passed as one `N x 1` inference input without chunking.

Execution must use a clean committed Commit A. Reports and the E3 operating
point are added in Commit B after the two prediction hashes match.
