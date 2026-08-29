# ARCH-011 Environment Audit

The public source is inspectable without private data, but a complete fresh scientific environment is not reconstructible from project metadata alone.

Key findings:

1. `pyproject.toml` declares Python >=3.11 and `jsonschema[format-nongpl]==4.26.0`; frozen scientific NumPy 2.3.5 and pytest are not declared, and no root resolved lock exists.
2. Frozen D0 pins CPython 3.12.13 and NumPy 2.3.5 but not the NumPy wheel, BLAS/LAPACK vendor, CPU instruction set, or thread identity.
3. Exact GDN is a narrow CPython 3.12.13/windows-amd64/CPU/exact-wheel/external-root contract; generic `.[gdn]` is not equivalent.
4. Canonical and v6 schema loaders assume a repository source-tree layout; schemas are not evidenced as installed package data.
5. Git checkout/ancestry is part of several governance gates. A wheel or source archive without `.git` cannot replay every historical authorization path.
6. Private HAI, numeric, model, registry, and locator assets are intentionally external. This is a custody boundary, not a reason to publish them.
7. RCC Python is stdlib/path-relative; its Windows batch launcher is convenience debt, not a scientific blocker.

Classification: `PASS_WITH_PORTABILITY_BLOCKERS`. Fresh-machine remains P1 engineering hardening before held-out execution, not a blocker to read-only design work.
