# TASK-039E3-R2R D0 Model/Threshold Integrity Audit V1

## Boundary

This task independently audits the exact frozen `D0_PCA_SPE_V1` private
preprocessing, model, and threshold plus their sanitized Commit-C receipts. It
does not retrain or recalibrate an authoritative artifact, open any test or
label payload, execute D0 INNER or D2, or read D1 performance.

## Frozen lineage and custody

- Base/continuity: `7ca7c035f1ec5b1fa6950fcfbdb9167d7d958517`
- Training Commit A: `34edab1dc148fdd82a050c3446e87d6eda4f95fe`
- Independent Commit B: `1041b6ed1efc335b8f5c5fe50dbfc22a87ec6d44`
- Freeze Commit C: `44ce989d7f50e2722eed70963e030ba1ba44fadf`
- Design: `357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174`
- Preprocessing: `baae5495094b211731e4fcdf7bab2870e3c81e7c973bfe052fc87b457ccb6270`
- Model: `f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b`
- Threshold: `7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695`

## Audit method

Public lanes verify exact Git ancestry, commit boundaries, implementation and
Commit-C bytes, self/cross-hashes, accounting, and leakage. The coordinator
alone loads the ignored local bindings, exact four normal files, and private
numeric artifacts. A separate audit implementation performs one independent
float64 preprocessing/PCA reconstruction, one train3 threshold reconstruction,
and one train4 sanity reconstruction. It never calls the authoritative training
entry point and never writes a replacement private artifact.

The oracle must reproduce `k=10`, 27 residual dimensions, no tied cutoff,
q-index 125873, 15401 train4 point alarms, 479 episodes, and FAR
8.709090909090909, while matching all three frozen private content hashes.

## Completion

Audit Commit A contains only this task, the audit script, and two new test
suites. Report Commit B contains only sanitized audit reports. Continuity
Commit C contains only project-state updates. D0 remains unauthorized; the
exact next task after PASS is
`TASK-039E3-R2R-UTILITY-INNER-D0-EXECUTION-AUTHORIZATION-V1`.
