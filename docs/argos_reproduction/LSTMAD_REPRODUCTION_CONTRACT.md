# LSTMAD Reproduction Contract

## Frozen arms

`LSTMADalpha` and `LSTMADbeta` are co-primary detector provenance arms. Both
must use identical ten-KPI membership, split boundaries, seeds, threshold
protocol, and reporting. No winner is selected.

## Split and label policy

| Split | Allowed use |
|---|---|
| Generation | Detector fit and normalization fit |
| Inner | PA-free threshold selection and diagnostics only |
| Outer | One-way validation after freeze |
| Test | Sealed; parsing prohibited |

The official EasyTSAD LSTMAD methods do not filter training values using
labels. Therefore DEC-063 freezes `contaminated_training`; labels are not used
to remove generation points or windows. This must not be switched after seeing
results.

## Configuration boundary

Official defaults are recorded but ARGOS-specific winning hyperparameters are
unresolved. TASK-037B must pre-register the exact configuration and seeds for
both arms. Hyperparameter and variant selection are prohibited. Weak detector
results cannot trigger curve replacement.

## Operating point

DEC-064 selects a threshold on unique finite inner scores by direct PA-free
point F1, with ties resolved by higher threshold then stable original order.
Outer and test labels cannot select thresholds. EasyTSAD `PointF1PA` and
`EventF1PA` are supplementary source-faithful outputs only because both search
label-aware point-adjusted thresholds.

Primary future reporting includes direct point/event precision, recall and F1,
FP points per 10,000 normal points, false-alarm events per 10,000 points,
AUROC, and AUPRC.

## Synthetic smoke deviation

The container smoke uses reduced synthetic-only fit settings to bound runtime,
and stubs EasyTSAD's unused Controller import to avoid loading plotting code.
It does not alter detector source. It verifies import, fit, checkpoint, score
alignment, finite output, fixed synthetic thresholding, and deterministic
replay only.

## Runtime selection

WSL-native rootless Podman `4.9.3` from Ubuntu package
`4.9.3+ds1-1ubuntu0.2` is selected. It supports the required Linux image,
network disablement, read-only root, capability drop, privilege, CPU, memory,
PID, and digest controls. A WSL-native Docker Engine is not installed in the
selected distribution; the visible Windows Docker Desktop bridge is not a
candidate and is not retried.
