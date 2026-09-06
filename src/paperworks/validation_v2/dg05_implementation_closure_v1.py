"""Deterministic repository-owned Python import closure for DG05 releases."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Iterable

from .dg05_execution_closure_v1 import (
    file_sha256,
    self_hashed,
    validate_self_hashed,
)


class DG05ImplementationClosureV1Error(ValueError):
    pass


def _module_candidates(repository_root: Path, module: str) -> tuple[Path, ...]:
    relative = Path(*module.split("."))
    return (
        repository_root / "src" / relative.with_suffix(".py"),
        repository_root / "src" / relative / "__init__.py",
        repository_root / relative.with_suffix(".py"),
        repository_root / relative / "__init__.py",
    )


def _module_name(repository_root: Path, path: Path) -> tuple[str, bool]:
    relative = path.relative_to(repository_root)
    under_src = relative.parts[0] == "src"
    module_path = Path(*relative.parts[1:]) if under_src else relative
    if module_path.name == "__init__.py":
        module_path = module_path.parent
        is_package = True
    else:
        module_path = module_path.with_suffix("")
        is_package = False
    return ".".join(module_path.parts), is_package


def _resolve_import(
    repository_root: Path,
    current: Path,
    module: str | None,
    level: int,
) -> Path | None:
    current_module, is_package = _module_name(repository_root, current)
    if level:
        package = current_module if is_package else current_module.rpartition(".")[0]
        parts = package.split(".") if package else []
        climb = level - 1
        if climb > len(parts):
            return None
        prefix = parts[: len(parts) - climb]
        if module:
            prefix.extend(module.split("."))
        module = ".".join(prefix)
    if not module or not (module.startswith("paperworks.") or module.startswith("scripts.")):
        return None
    for candidate in _module_candidates(repository_root, module):
        if candidate.is_file():
            return candidate.resolve()
    return None


def repository_python_import_closure_v1(
    *, repository_root: Path, root_paths: Iterable[Path]
) -> tuple[Path, ...]:
    root = repository_root.resolve()
    pending = [path.resolve() for path in root_paths]
    seen: set[Path] = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        if root not in path.parents or not path.is_file() or path.suffix != ".py" or path.is_symlink():
            raise DG05ImplementationClosureV1Error("INVALID_IMPLEMENTATION_ROOT")
        seen.add(path)
        relative = path.relative_to(root)
        if relative.parts[0] == "src":
            parent = path.parent
            source_root = root / "src"
            while parent != source_root and source_root in parent.parents:
                initializer = parent / "__init__.py"
                if initializer.is_file() and initializer.resolve() not in seen:
                    pending.append(initializer.resolve())
                parent = parent.parent
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise DG05ImplementationClosureV1Error("IMPLEMENTATION_AST_REPLAY_FAILED") from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports = ((alias.name, 0) for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports = [(node.module, node.level)]
                imports.extend(
                    (
                        f"{node.module}.{alias.name}" if node.module else alias.name,
                        node.level,
                    )
                    for alias in node.names
                    if alias.name != "*"
                )
            else:
                continue
            for module, level in imports:
                resolved = _resolve_import(root, path, module, level)
                if resolved is not None and resolved not in seen:
                    pending.append(resolved)
    return tuple(sorted(seen, key=lambda item: item.relative_to(root).as_posix()))


def build_transitive_implementation_authority_v1(
    *, repository_root: Path, root_paths: Iterable[Path], source_commit: str
) -> dict[str, Any]:
    root = repository_root.resolve()
    roots = tuple(sorted({path.resolve() for path in root_paths}, key=lambda item: item.relative_to(root).as_posix()))
    closure = repository_python_import_closure_v1(repository_root=root, root_paths=roots)
    return self_hashed({
        "schema": "dg05_transitive_implementation_authority_v1",
        "resolution_policy": "REPOSITORY_OWNED_STATIC_PYTHON_IMPORT_FIXED_POINT_V1",
        "root_relative_paths": [path.relative_to(root).as_posix() for path in roots],
        "root_count": len(roots),
        "closure_count": len(closure),
        "implementations": [
            {
                "relative_path": path.relative_to(root).as_posix(),
                "byte_hash": file_sha256(path),
            }
            for path in closure
        ],
        "source_commit": source_commit,
    })


def replay_transitive_implementation_authority_v1(
    *, repository_root: Path, authority: dict[str, Any], expected_root_paths: Iterable[Path]
) -> None:
    validate_self_hashed(authority)
    if authority.get("schema") != "dg05_transitive_implementation_authority_v1":
        raise DG05ImplementationClosureV1Error("TRANSITIVE_IMPLEMENTATION_SCHEMA_REQUIRED")
    root = repository_root.resolve()
    expected = build_transitive_implementation_authority_v1(
        repository_root=root,
        root_paths=expected_root_paths,
        source_commit=authority.get("source_commit"),
    )
    if authority != expected:
        raise DG05ImplementationClosureV1Error("TRANSITIVE_IMPLEMENTATION_CLOSURE_REPLAY_FAILED")


__all__ = [
    "DG05ImplementationClosureV1Error",
    "build_transitive_implementation_authority_v1",
    "replay_transitive_implementation_authority_v1",
    "repository_python_import_closure_v1",
]
