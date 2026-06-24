# Environment Strategy

## Current state

No root Python package or project environment exists yet. The root has no `pyproject.toml`, `requirements.txt`, `pytest.ini`, `tox.ini`, or CI workflow.

The only environment files found are inside read-only upstream references:

- `external/argos/pyproject.toml`
- `external/argos/requirements.txt`
- `external/argos/config/agent.yaml`
- `external/gdn/install.sh`

These upstream environments must not be adopted wholesale.

## ARGOS reference environment

ARGOS declares Python `>=3.7` in `pyproject.toml` and pins many packages in `requirements.txt`, including OpenAI client dependencies. ARGOS is not an environment baseline for this project because:

- this project requires provider-neutral LLM interfaces,
- CI must use mock providers,
- runtime must not import planning/LLM modules,
- generated Python execution is prohibited.

Use ARGOS only as an architectural reference.

## GDN reference environment

GDN README and `install.sh` target:

- Python `>=3.6`
- CUDA 10.2
- PyTorch 1.5.1
- PyG / torch-geometric 1.5.0

This is a legacy stack. Do not make it the main project dependency.

## Recommended project environment

For TASK-001 through TASK-003, start with a small modern Python environment:

- Python 3.11 or 3.12, depending on target repository policy.
- `pandas` or `polars` for metadata validation and CSV schema inspection.
- `pydantic` or dataclasses for schemas.
- `pytest` for tests.
- `ruff` for linting.
- `mypy` or `pyright` for type checks if already standard in the target repo.

For TASK-004, choose a modern supported PyTorch/PyG matrix after target hardware is known. GDN parity tests must use synthetic fixtures and must not depend on final test labels.

## Git ownership note

The upstream repos were cloned through an escalated command and are owned by the desktop user. Git queries from the Codex sandbox require command-local safe-directory flags, for example:

```powershell
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external/argos rev-parse HEAD
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/gdn -C external/gdn rev-parse HEAD
```

Avoid changing global Git config unless the user explicitly approves it.

## Root repository note

The root repository was initialized during TASK-000 after `.gitignore` was created. Raw SWaT files under `dataset/` and read-only upstream clones under `external/` are ignored by the root repository.
