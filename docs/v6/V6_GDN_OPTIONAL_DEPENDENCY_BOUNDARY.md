# V6 GDN Optional Dependency Boundary

## Lightweight Imports

These imports are dependency-light and must not load Torch or PyG:

```python
import paperworks
import paperworks.gdn
import paperworks.candidates
import paperworks.e2e
```

`paperworks.gdn` eagerly exposes only the project-owned masked extraction,
dependency-status, and fidelity contracts. Historical Torch exports are
resolved through module `__getattr__` only when accessed.

`paperworks.candidates` eagerly exposes the candidate-universe contract. Its
historical TASK-005 smoke exports are lazy because that workflow requires the
optional Torch/PyG backend. `paperworks.e2e` remains importable because its
eager modules use only lightweight candidate and masked-extraction exports.

## Failure Contract

`GDNOptionalDependencyError` is an `ImportError` with stable issue code:

`GDN_OPTIONAL_DEPENDENCY_UNAVAILABLE`

Both package-level optional symbol access and direct
`paperworks.gdn.torch_backend` import fail through this error. An uncontrolled
package-level `ModuleNotFoundError` is not part of the public contract.

Dependency status is inspected with `importlib.util.find_spec` and
`importlib.metadata.version`. Inspection does not import the backend and grants
no fidelity, scientific validity, or execution authority.

## Installation

Core installation retains `jsonschema[format-nongpl]==4.26.0`. The unchanged
GDN pins are optional:

```text
pip install -e ".[gdn]"
```

TASK-039P1D installs or upgrades no dependency.
