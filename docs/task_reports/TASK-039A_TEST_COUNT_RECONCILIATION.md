# TASK-039A Test-Count Reconciliation

The public TASK-039A/TASK-039AR targeted count of 37 is the sum of the five
task modules run for the provenance and byte-equivalence result:

- `test_task039a_custody_references`
- `test_task039a_lfs_csv`
- `test_task039a_manifest_schemas`
- `test_task039a_reports`
- `test_task039ar_distribution_equivalence`

The final user summary count of 40 came from a post-commit rerun that also
included `test_task039p1d_reports`, which contains three historical report
regression tests. The difference is therefore three separately counted rerun
regressions. It is not a historical report omission and does not reveal an
unreported failure. Historical TASK-039A/TASK-039AR counts remain unchanged.
