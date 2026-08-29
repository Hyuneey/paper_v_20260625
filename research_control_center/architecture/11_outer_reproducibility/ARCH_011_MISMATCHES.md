# ARCH-011 Mismatches

| ID | Incorrect or risky wording/state | Audited boundary | Severity |
|---|---|---|---|
| M-011-01 | old OUTER can simply retry | one authorized attempt consumed; zero retries | HIGH |
| M-011-02 | full scientific environment is dependency-locked | NumPy/test tooling/root lock incomplete | HIGH |
| M-011-03 | installed wheel is equivalent to source checkout | schema loaders and Git gates assume repository layout | HIGH |
| M-011-04 | fresh-machine scientific replay is available | private assets and environment capsule are missing | HIGH |
| M-011-05 | generic GDN optional install reproduces frozen GDN | exact Windows/wheel/root contract differs | HIGH |
| M-011-06 | test2 was untouched or scientifically read | one custody check, zero content reads | MEDIUM |
| M-011-07 | same physical test2 is automatically reusable | new-study design/authorization decision required | MEDIUM |
| M-011-08 | same-machine integrity replay equals scientific recomputation | scope and authorization differ | MEDIUM |
| M-011-09 | historical preservation bundle is current restore capsule | it predates current RCC/scientific state | MEDIUM |
| M-011-10 | private scientific assets are public-regenerable | payloads remain external/restricted | MEDIUM |
| M-011-11 | PILOT V1 and VALIDATION V2 may share unversioned identity | prospective method/version separation required | MEDIUM |
| M-011-12 | bridge is already the locked authority | it is preferred but DEC-020 remains open | MEDIUM |
| M-011-13 | Windows dashboard launcher blocks science | underlying RCC scripts are portable stdlib | LOW |
| M-011-14 | a one-command CLI is mandatory | useful hardening, not thesis-critical | LOW |

Totals: 14 — CRITICAL 0, HIGH 5, MEDIUM 7, LOW 2.
