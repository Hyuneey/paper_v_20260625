# Repair Outer Utility Protocol

TASK-038E evaluates all 13 TASK-038B repaired executable rules against the
matching detector-only outer baseline. The original rules were not executable
and therefore do not provide a valid detection-performance baseline.

Every repaired rule is included regardless of TASK-038D selection. FN rules
use binary maximum and FP rules use binary minimum. Reports retain selection
status, detector-combined PA-free metrics, directional benefit and cost, and
the point-F1 delta against detector-only.

Execution recovery and outer utility are distinct outcomes. A repaired rule
may be operationally recovered yet outer-equal or outer-regressive.
