# Detector Error-Segment Contract

Generation labels and frozen detector predictions define point categories:

- TP: label 1, prediction 1
- FN: label 1, prediction 0
- FP: label 0, prediction 1
- TN: label 0, prediction 0

Each category is represented by sorted maximal contiguous runs. Project-owned
intervals are half-open `[start, end)`. The ARGOS compatibility serializer
converts them explicitly to inclusive `[start, end - 1]` endpoints. Runs cannot
overlap within a category.

Every private segment manifest binds the detector prediction hash and threshold
record hash. Tracked reports may expose only counts and hashes. TASK-037A tests
this contract with synthetic binary arrays and constructs no real KPI segment.
