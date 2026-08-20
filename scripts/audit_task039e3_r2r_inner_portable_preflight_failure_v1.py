"""Path-silent staged audit of the portable INNER custody preflight.

This is a diagnostic harness, not an authorization or scientific execution
bridge.  It opens only the already-authorized custody inputs, reports fixed
stage identifiers, suppresses every internal output and exception, never
calls the production one-attempt preflight, and never parses CSV rows.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import shlex
import sys
from typing import Any

from paperworks.v6 import (
    task039e3_r2r_utility_inner_execution_authorization_v1 as authorization,
)
from paperworks.v6 import (
    task039e3_r2r_utility_normal_only_authority_v1 as main_authority,
)
from paperworks.v6 import (
    task039e3_r2r_utility_source_census_supplement_v1 as supplement,
)


ENV_FILE_NAME = ".env.custody.local"
APPROVED_BINDING_KEYS = (
    authorization.HAI_DATA_ROOT_ENV,
    authorization.MAIN_REGISTRY_ENV,
    authorization.MAIN_LOCATOR_ENV,
    authorization.SUPPLEMENT_REGISTRY_ENV,
    authorization.SUPPLEMENT_LOCATOR_ENV,
)

STAGE_NAMES = (
    "D01_ENV_BINDINGS",
    "D02_MAIN_REGISTRY_FILE",
    "D03_MAIN_LOCATOR_FILE",
    "D04_MAIN_MATERIALIZATION_AUTHORITY",
    "D05_MAIN_LOCATOR_SCHEMA",
    "D06_MAIN_LOCATOR_REGISTRY_BINDING",
    "D07_MAIN_REGISTRY_DOCUMENT",
    "D08_MAIN_REGISTRY_CANONICAL_HASH",
    "D09_SUPPLEMENT_REGISTRY_FILE",
    "D10_SUPPLEMENT_LOCATOR_FILE",
    "D11_SUPPLEMENT_MATERIALIZATION_AUTHORITY",
    "D12_SUPPLEMENT_LOCATOR_SCHEMA",
    "D13_SUPPLEMENT_LOCATOR_REGISTRY_BINDING",
    "D14_SUPPLEMENT_REGISTRY_DOCUMENT",
    "D15_SUPPLEMENT_REGISTRY_CANONICAL_HASH",
    "D16_HAI_ROOT",
    "D17_TEST1_FEATURE_FILE",
    "D18_TEST1_FEATURE_HASH",
    "D19_TEST1_LABEL_FILE",
    "D20_TEST1_LABEL_HASH",
    "D21_FULL_PREFLIGHT_REPLAY",
)

ROOT_CAUSE_BY_STAGE = {
    "D01_ENV_BINDINGS": "CLASS_A_LOCAL_ASSET_WIRING",
    "D02_MAIN_REGISTRY_FILE": "CLASS_A_LOCAL_ASSET_WIRING",
    "D03_MAIN_LOCATOR_FILE": "CLASS_A_LOCAL_ASSET_WIRING",
    "D04_MAIN_MATERIALIZATION_AUTHORITY": (
        "CLASS_D_MATERIALIZATION_AUTHORIZATION_REPLAY"
    ),
    "D05_MAIN_LOCATOR_SCHEMA": "CLASS_B_MAIN_LOCATOR_SEMANTIC_COMPATIBILITY",
    "D06_MAIN_LOCATOR_REGISTRY_BINDING": "CLASS_A_LOCAL_ASSET_WIRING",
    "D07_MAIN_REGISTRY_DOCUMENT": "CLASS_E_REGISTRY_VALIDATION",
    "D08_MAIN_REGISTRY_CANONICAL_HASH": "CLASS_E_REGISTRY_VALIDATION",
    "D09_SUPPLEMENT_REGISTRY_FILE": "CLASS_A_LOCAL_ASSET_WIRING",
    "D10_SUPPLEMENT_LOCATOR_FILE": "CLASS_A_LOCAL_ASSET_WIRING",
    "D11_SUPPLEMENT_MATERIALIZATION_AUTHORITY": (
        "CLASS_D_MATERIALIZATION_AUTHORIZATION_REPLAY"
    ),
    "D12_SUPPLEMENT_LOCATOR_SCHEMA": (
        "CLASS_C_SUPPLEMENT_LOCATOR_SEMANTIC_COMPATIBILITY"
    ),
    "D13_SUPPLEMENT_LOCATOR_REGISTRY_BINDING": "CLASS_A_LOCAL_ASSET_WIRING",
    "D14_SUPPLEMENT_REGISTRY_DOCUMENT": "CLASS_E_REGISTRY_VALIDATION",
    "D15_SUPPLEMENT_REGISTRY_CANONICAL_HASH": "CLASS_E_REGISTRY_VALIDATION",
    "D16_HAI_ROOT": "CLASS_F_HAI_TEST1_CUSTODY",
    "D17_TEST1_FEATURE_FILE": "CLASS_F_HAI_TEST1_CUSTODY",
    "D18_TEST1_FEATURE_HASH": "CLASS_F_HAI_TEST1_CUSTODY",
    "D19_TEST1_LABEL_FILE": "CLASS_F_HAI_TEST1_CUSTODY",
    "D20_TEST1_LABEL_HASH": "CLASS_F_HAI_TEST1_CUSTODY",
    "D21_FULL_PREFLIGHT_REPLAY": "CLASS_G_AUTHORIZATION_PREFLIGHT_LOGIC",
}


class DiagnosticStageFailure(RuntimeError):
    """Internal path-free sentinel; it is never printed with its exception text."""


@dataclass(frozen=True)
class DiagnosticOutcome:
    completed_stages: tuple[tuple[str, str], ...]
    terminal_stage: str
    root_cause_class: str | None


def _require(condition: bool) -> None:
    if not condition:
        raise DiagnosticStageFailure


def _parse_binding_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        tokens = shlex.split(line, comments=False, posix=True)
        _require(len(tokens) == 1 and "=" in tokens[0])
        key, value = tokens[0].split("=", 1)
        _require(key in APPROVED_BINDING_KEYS and key not in values and bool(value))
        values[key] = value
    return values


def _load_approved_bindings(
    repository_root: Path,
    environ: Mapping[str, str],
) -> dict[str, str]:
    binding_file = repository_root / ENV_FILE_NAME
    _require(not binding_file.is_symlink() and binding_file.is_file())
    values = _parse_binding_text(binding_file.read_text(encoding="utf-8"))
    for key in APPROVED_BINDING_KEYS:
        current = environ.get(key)
        if isinstance(current, str) and current:
            values[key] = current
    _require(set(values) == set(APPROVED_BINDING_KEYS))
    return values


def _json_document(path: Path) -> dict[str, Any]:
    document = authorization._json_from_custody_bytes_v1(  # noqa: SLF001
        authorization._read_bytes_once_v1(path)  # noqa: SLF001
    )
    _require(type(document) is dict)
    return document


def _resolve_private_file(path: Path, repository_root: Path) -> Path:
    return authorization._resolve_regular_file_v1(  # noqa: SLF001
        path,
        repository_root=repository_root,
        outside_git=True,
    )


def _build_real_stage_actions(
    repository_root: Path,
    environ: Mapping[str, str],
) -> tuple[tuple[str, Callable[[], None]], ...]:
    context: dict[str, Any] = {
        "repository_root": repository_root.resolve(strict=True),
        "environ": environ,
    }

    def d01() -> None:
        context["bindings"] = _load_approved_bindings(
            context["repository_root"], context["environ"]
        )

    def binding_path(key: str) -> Path:
        return Path(context["bindings"][key])

    def d02() -> None:
        context["main_registry_path"] = _resolve_private_file(
            binding_path(authorization.MAIN_REGISTRY_ENV),
            context["repository_root"],
        )

    def d03() -> None:
        context["main_locator_path"] = _resolve_private_file(
            binding_path(authorization.MAIN_LOCATOR_ENV),
            context["repository_root"],
        )

    def d04() -> None:
        materialization = (
            main_authority.load_committed_materialization_execution_authorization_r1(
                context["repository_root"]
            )
        )
        _require(
            materialization.authorization_hash
            == authorization.MAIN_MATERIALIZATION_AUTHORIZATION_HASH
        )
        context["main_authorization"] = materialization

    def d05() -> None:
        document = _json_document(context["main_locator_path"])
        main_authority.validate_local_locator_manifest_v1(
            document,
            repository_root=context["repository_root"],
            execution_authorization=context["main_authorization"],
        )
        context["main_locator_document"] = document

    def d06() -> None:
        document = context["main_locator_document"]
        embedded = _resolve_private_file(
            Path(str(document.get("absolute_private_authority_path", ""))),
            context["repository_root"],
        )
        _require(embedded == context["main_registry_path"])
        _require(
            document.get("private_authority_hash")
            == authorization.MAIN_PRIVATE_REGISTRY_HASH
        )
        _require(
            document.get("execution_authorization_hash")
            == authorization.MAIN_MATERIALIZATION_AUTHORIZATION_HASH
        )

    def d07() -> None:
        document = _json_document(context["main_registry_path"])
        observed = main_authority.validate_private_registry_document_v1(
            document,
            authorization._build_main_registry_validation_authority_v1(  # noqa: SLF001
                context["repository_root"]
            ),
        )
        context["main_registry_hash"] = observed

    def d08() -> None:
        _require(
            context["main_registry_hash"]
            == authorization.MAIN_PRIVATE_REGISTRY_HASH
        )

    def d09() -> None:
        context["supplement_registry_path"] = _resolve_private_file(
            binding_path(authorization.SUPPLEMENT_REGISTRY_ENV),
            context["repository_root"],
        )

    def d10() -> None:
        context["supplement_locator_path"] = _resolve_private_file(
            binding_path(authorization.SUPPLEMENT_LOCATOR_ENV),
            context["repository_root"],
        )

    def d11() -> None:
        document = authorization._load_public_self_hashed_v1(  # noqa: SLF001
            context["repository_root"]
            / authorization._SUPPLEMENT_MATERIALIZATION_AUTHORIZATION_RELATIVE_PATH,  # noqa: SLF001
            authorization.SUPPLEMENT_MATERIALIZATION_AUTHORIZATION_HASH,
        )
        observed = supplement.validate_materialization_authorization_document_v1(
            document
        )
        _require(
            observed == authorization.SUPPLEMENT_MATERIALIZATION_AUTHORIZATION_HASH
        )
        context["supplement_authorization"] = document

    def d12() -> None:
        document = _json_document(context["supplement_locator_path"])
        supplement.validate_local_locator_document_v1(
            document,
            repository_root=context["repository_root"],
        )
        context["supplement_locator_document"] = document

    def d13() -> None:
        document = context["supplement_locator_document"]
        embedded = _resolve_private_file(
            Path(str(document.get("absolute_private_authority_path", ""))),
            context["repository_root"],
        )
        _require(embedded == context["supplement_registry_path"])
        _require(
            document.get("private_registry_hash")
            == authorization.SUPPLEMENT_PRIVATE_REGISTRY_HASH
        )
        _require(
            document.get("authorization_hash")
            == authorization.SUPPLEMENT_MATERIALIZATION_AUTHORIZATION_HASH
        )

    def d14() -> None:
        document = _json_document(context["supplement_registry_path"])
        observed = supplement.validate_supplement_private_registry_document_v1(
            document
        )
        context["supplement_registry_hash"] = observed

    def d15() -> None:
        _require(
            context["supplement_registry_hash"]
            == authorization.SUPPLEMENT_PRIVATE_REGISTRY_HASH
        )

    def d16() -> None:
        root = binding_path(authorization.HAI_DATA_ROOT_ENV)
        _require(not root.is_symlink())
        root = root.resolve(strict=True)
        _require(root.is_dir())
        context["hai_root"] = root

    def d17() -> None:
        context["feature_path"] = authorization._resolve_regular_file_v1(  # noqa: SLF001
            context["hai_root"] / "hai-23.05" / authorization.TEST1_FEATURE_FILENAME,
            repository_root=context["repository_root"],
            outside_git=False,
        )

    def d18() -> None:
        observed = sha256(
            authorization._read_bytes_once_v1(context["feature_path"])  # noqa: SLF001
        ).hexdigest()
        _require(observed == authorization.TEST1_FEATURE_SHA256)
        context["feature_hash"] = observed

    def d19() -> None:
        context["label_path"] = authorization._resolve_regular_file_v1(  # noqa: SLF001
            context["hai_root"] / "hai-23.05" / authorization.TEST1_LABEL_FILENAME,
            repository_root=context["repository_root"],
            outside_git=False,
        )

    def d20() -> None:
        observed = sha256(
            authorization._read_bytes_once_v1(context["label_path"])  # noqa: SLF001
        ).hexdigest()
        _require(observed == authorization.TEST1_LABEL_SHA256)
        context["label_hash"] = observed

    def d21() -> None:
        main_custody = authorization.validate_portable_private_locator_custody_v1(
            "MAIN",
            locator_path=context["main_locator_path"],
            registry_path=context["main_registry_path"],
        )
        supplement_custody = (
            authorization.validate_portable_private_locator_custody_v1(
                "SUPPLEMENT",
                locator_path=context["supplement_locator_path"],
                registry_path=context["supplement_registry_path"],
            )
        )
        _require(
            main_custody == authorization._portable_locator_result_v1("MAIN")  # noqa: SLF001
        )
        _require(
            supplement_custody
            == authorization._portable_locator_result_v1("SUPPLEMENT")  # noqa: SLF001
        )
        _require(
            (
                context["main_registry_hash"],
                context["supplement_registry_hash"],
                context["feature_hash"],
                context["label_hash"],
            )
            == (
                authorization.MAIN_PRIVATE_REGISTRY_HASH,
                authorization.SUPPLEMENT_PRIVATE_REGISTRY_HASH,
                authorization.TEST1_FEATURE_SHA256,
                authorization.TEST1_LABEL_SHA256,
            )
        )

    actions = (
        d01,
        d02,
        d03,
        d04,
        d05,
        d06,
        d07,
        d08,
        d09,
        d10,
        d11,
        d12,
        d13,
        d14,
        d15,
        d16,
        d17,
        d18,
        d19,
        d20,
        d21,
    )
    return tuple(zip(STAGE_NAMES, actions, strict=True))


def execute_stage_actions(
    actions: Sequence[tuple[str, Callable[[], None]]],
) -> DiagnosticOutcome:
    """Run stages with complete output and exception suppression."""

    completed: list[tuple[str, str]] = []
    try:
        _require(tuple(name for name, _ in actions) == STAGE_NAMES)
        for name, action in actions:
            try:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    action()
            except BaseException:
                completed.append((name, "BLOCK"))
                return DiagnosticOutcome(
                    completed_stages=tuple(completed),
                    terminal_stage=name,
                    root_cause_class=ROOT_CAUSE_BY_STAGE[name],
                )
            completed.append((name, "PASS"))
    except BaseException:
        return DiagnosticOutcome(
            completed_stages=tuple(completed),
            terminal_stage="UNEXPECTED_FAIL_CLOSED",
            root_cause_class=None,
        )
    return DiagnosticOutcome(
        completed_stages=tuple(completed),
        terminal_stage="ALL_DIAGNOSTIC_STAGES_PASS",
        root_cause_class=None,
    )


def render_fixed_output(outcome: DiagnosticOutcome) -> str:
    lines = [f"{name}={status}" for name, status in outcome.completed_stages]
    lines.append(f"DIAGNOSTIC_TERMINAL_STAGE={outcome.terminal_stage}")
    return "\n".join(lines)


def run_diagnostic(
    repository_root: Path,
    *,
    environ: Mapping[str, str] | None = None,
) -> DiagnosticOutcome:
    actions = _build_real_stage_actions(
        repository_root,
        os.environ if environ is None else environ,
    )
    return execute_stage_actions(actions)


def main() -> int:
    sys.tracebacklimit = 0
    try:
        if len(sys.argv) != 1:
            raise DiagnosticStageFailure
        repository_root = Path(__file__).resolve(strict=True).parents[1]
        outcome = run_diagnostic(repository_root)
        print(render_fixed_output(outcome))
        return 0 if outcome.terminal_stage == "ALL_DIAGNOSTIC_STAGES_PASS" else 2
    except BaseException:
        print("DIAGNOSTIC_TERMINAL_STAGE=UNEXPECTED_FAIL_CLOSED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
