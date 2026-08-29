# ARCH-001 Split and Leakage Audit

Verdict: `NO_VERIFIED_LEAKAGE_FOUND`

The matrix covers 21 stages across train1/train2/train3/train4/test1/test2 feature and label fields. Normal construction uses train1/train2, one-way confirmation uses train3, D0 threshold calibration also uses train3, and D0 normal sanity uses train4. Labels are forbidden until metric stages.

Two high qualifications remain:

1. D1 has an in-memory label-blind prediction before labels, not a durable pre-label public file.
2. D2 V2 was designed with prior INNER outcome information and is not independent confirmation.

train3 dual use is `ACCEPTABLE_WITH_SCOPE_LIMITATION`. No test outcome was found flowing backward into COMMON-42, D0 fit/calibration, or D1 rule selection.
