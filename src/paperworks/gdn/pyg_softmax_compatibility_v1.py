"""TASK-039C-GDNC PyG softmax compatibility evidence and scope guards."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from paperworks.v6.common import require_sha256, stable_hash_v1


TASK_ID = "TASK-039C-GDNC"
GDNR_RESULT_COMMIT = "6474816068aae786a490c634c28d665772bc2243"
GDNR_IMPLEMENTATION_COMMIT = "914e5159e719271262c8caa5bf94a2a806efc589"
UPSTREAM_GDN_COMMIT = "9853899da860682669a134e4af315d036aab4eca"
ORIGINAL_FIDELITY_RECEIPT_HASH = (
    "93821469e465a942ff94c779c6798355383e35003b13db24c19b9760ca3266c4"
)
GDNR_EXECUTION_RECEIPT_HASH = (
    "f46eb437aa307be41cad593fca8384d226c632738c1336a62c57554e42cf3a80"
)
EXACT_ENVIRONMENT_RECEIPT_HASH = (
    "d0602e4f591073d58881aa1f918b788176ed888d5265f5e253fd272e060109c6"
)
WHEELHOUSE_RECEIPT_HASH = (
    "b8e3d5fc7b66e61282d48a6a9aa28872e387534e40ead4cda691433a3bdd8cea"
)
GDNR_DATA_ACCESS_AUDIT_HASH = (
    "6c1de4784e7cfc3d8f9daf30a7542326aad5030c2dfed9daa1c74630b01cf2dc"
)
FROZEN_HYPERPARAMETER_HASH = (
    "68fbd006af1bc71468c157ba90888f54b8c0cbeba1aa7aba1121701a5b87870e"
)
COMPATIBILITY_STATUS = "passed_semantics_preserving_pyg_softmax_compatibility"
COMPATIBILITY_CLASSIFICATION = "documented_non_scientific_api_adapter"
PATCHED_IMPLEMENTATION_PATH = (
    "src/paperworks/gdn/upstream_candidate_backend_v1.py"
)
UPSTREAM_CALL = "softmax(alpha, edge_index_i, size_i)"
CORRECTED_CALL = "softmax(src, index=index, num_nodes=num_nodes)"
INSTALLED_PYG_SIGNATURE = (
    "(src: torch.Tensor, index: Optional[torch.Tensor] = None, "
    "ptr: Optional[torch.Tensor] = None, num_nodes: Optional[int] = None, "
    "dim: int = 0) -> torch.Tensor"
)
FLOAT64_ATOL = 1e-12
FLOAT64_RTOL = 1e-12
FLOAT32_ATOL = 1e-6
FLOAT32_RTOL = 1e-6

FROZEN_UNCHANGED_PATHS = (
    "configs/v6/task039c_gdn_backend_v1.json",
    "src/paperworks/candidates/gdn_candidate_discovery_v1.py",
    "src/paperworks/gdn/gdn_remediation_environment_v1.py",
    "src/paperworks/contracts/rule_v1.py",
    "src/paperworks/contracts/verifier_v1.py",
    "src/paperworks/contracts/runtime_v1.py",
    "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json",
)


class PyGSoftmaxCompatibilityError(ValueError):
    """Raised when the one authorized compatibility boundary is violated."""


def canonical_text_sha256_v1(path: Path) -> str:
    """Hash UTF-8 text after canonicalizing checkout-specific line endings."""

    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def independent_grouped_softmax_reference_v1(
    src: Any,
    index: Any,
    num_nodes: int,
) -> Any:
    """Independent stable grouped softmax; it never calls the PyG adapter."""

    import torch

    if not isinstance(num_nodes, int) or num_nodes < 0:
        raise PyGSoftmaxCompatibilityError("num_nodes must be a nonnegative integer")
    if src.ndim < 1 or index.ndim != 1 or src.shape[0] != index.shape[0]:
        raise PyGSoftmaxCompatibilityError("grouped-softmax tensor shapes are invalid")
    if index.dtype != torch.long:
        raise PyGSoftmaxCompatibilityError("group index must use torch.long")
    if index.numel() and (int(index.min()) < 0 or int(index.max()) >= num_nodes):
        raise PyGSoftmaxCompatibilityError("group index is outside num_nodes")
    result = torch.empty_like(src)
    for group_id in range(num_nodes):
        positions = torch.nonzero(index == group_id, as_tuple=False).flatten()
        if positions.numel() == 0:
            continue
        values = src.index_select(0, positions)
        shifted = values - values.amax(dim=0, keepdim=True)
        numerator = shifted.exp()
        normalized = numerator / numerator.sum(dim=0, keepdim=True)
        result.index_copy_(0, positions, normalized)
    return result


def verify_synthetic_semantic_equivalence_v1() -> tuple[dict[str, Any], ...]:
    """Run the frozen pre-HAI float64 semantic-equivalence matrix."""

    import torch

    from paperworks.gdn.upstream_candidate_backend_v1 import (
        upstream_sparse_softmax_compat_v1,
    )

    cases: tuple[tuple[str, Any, Any, int], ...] = (
        (
            "two_groups_positive_negative_repeated",
            [-2.0, 0.5, 3.0, -1.0, 2.5, 0.0],
            [0, 1, 0, 1, 0, 1],
            2,
        ),
        (
            "unused_nodes_and_one_element_group",
            [1.25, -0.75, 2.0, -3.0],
            [0, 3, 3, 5],
            7,
        ),
        (
            "large_magnitude_stability",
            [1000.0, 999.0, -1000.0, -1001.0, 2500.0],
            [2, 2, 4, 4, 6],
            8,
        ),
        (
            "multidimensional_graph_layer_shape",
            [
                [[-3.0], [2.0]],
                [[0.0], [-4.0]],
                [[5.0], [1.0]],
                [[-1.0], [3.0]],
                [[2.0], [-2.0]],
            ],
            [1, 0, 1, 0, 1],
            4,
        ),
    )
    records: list[dict[str, Any]] = []
    for name, values, groups, num_nodes in cases:
        src = torch.tensor(values, dtype=torch.float64)
        index = torch.tensor(groups, dtype=torch.long)
        original_index = index.clone()
        expected = independent_grouped_softmax_reference_v1(src, index, num_nodes)
        observed = upstream_sparse_softmax_compat_v1(src, index, num_nodes)
        torch.testing.assert_close(
            observed,
            expected,
            atol=FLOAT64_ATOL,
            rtol=FLOAT64_RTOL,
        )
        if not torch.equal(index, original_index):
            raise PyGSoftmaxCompatibilityError("compatibility call mutated grouping index")
        absolute = (observed - expected).abs()
        denominator = expected.abs().clamp_min(torch.finfo(expected.dtype).tiny)
        records.append(
            {
                "case_id": name,
                "dtype": "float64",
                "input_shape": list(src.shape),
                "element_count": int(src.shape[0]),
                "num_nodes": num_nodes,
                "max_absolute_error": float(absolute.max().item()),
                "max_relative_error": float((absolute / denominator).max().item()),
                "passed": True,
            }
        )
    return tuple(records)


def _git(repository_root: Path, *arguments: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={repository_root.resolve().as_posix()}",
            "-C",
            str(repository_root),
            *arguments,
        ],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise PyGSoftmaxCompatibilityError("Git compatibility-scope inspection failed")
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


class _ScientificPatchNormalizer(ast.NodeTransformer):
    def visit_Module(self, node: ast.Module) -> ast.Module:  # noqa: N802
        node.body = [
            item
            for item in node.body
            if not (
                isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and item.name == "upstream_sparse_softmax_compat_v1"
            )
        ]
        return self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:  # noqa: N802
        if node.module == "torch_geometric.utils":
            node.names = [item for item in node.names if item.name != "softmax"]
        return node

    def visit_Call(self, node: ast.Call) -> ast.AST:  # noqa: N802
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "upstream_sparse_softmax_compat_v1":
            if len(node.args) != 3 or node.keywords:
                raise PyGSoftmaxCompatibilityError("patched graph-layer call shape changed")
            return ast.copy_location(
                ast.Call(func=ast.Name(id="softmax", ctx=ast.Load()), args=node.args, keywords=[]),
                node,
            )
        return node

    def visit_List(self, node: ast.List) -> ast.AST:  # noqa: N802
        node = self.generic_visit(node)
        node.elts = [
            item
            for item in node.elts
            if not (
                isinstance(item, ast.Constant)
                and item.value == "upstream_sparse_softmax_compat_v1"
            )
        ]
        return node


def _normalized_scientific_ast(source: str) -> str:
    tree = ast.parse(source)
    normalized = _ScientificPatchNormalizer().visit(tree)
    ast.fix_missing_locations(normalized)
    return ast.dump(normalized, include_attributes=False)


def assert_gdnc_scientific_patch_scope_v1(
    *,
    repository_root: Path,
    base_commit: str = GDNR_RESULT_COMMIT,
) -> str:
    """Prove that only the old-to-modern softmax binding changed scientifically."""

    root = repository_root.resolve()
    current_path = root / PATCHED_IMPLEMENTATION_PATH
    base_bytes = _git(
        root,
        "show",
        f"{base_commit}:{PATCHED_IMPLEMENTATION_PATH}",
        binary=True,
    )
    assert isinstance(base_bytes, bytes)
    base_source = base_bytes.decode("utf-8")
    current_source = current_path.read_text(encoding="utf-8")
    if _normalized_scientific_ast(base_source) != _normalized_scientific_ast(current_source):
        raise PyGSoftmaxCompatibilityError("failed_gdnc_patch_scope_violation")
    tree = ast.parse(current_source)
    wrappers = [
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef)
        and item.name == "upstream_sparse_softmax_compat_v1"
    ]
    expected_wrapper = ast.parse(
        """\
def upstream_sparse_softmax_compat_v1(src: Any, index: Any, num_nodes: int) -> Any:
    \"\"\"Bind upstream PyG-1.5 ``num_nodes`` semantics to the PyG-2.8 API.\"\"\"
    from torch_geometric.utils import softmax as pyg_softmax
    return pyg_softmax(src, index=index, num_nodes=num_nodes)
"""
    ).body[0]
    if len(wrappers) != 1 or ast.dump(wrappers[0], include_attributes=False) != ast.dump(
        expected_wrapper, include_attributes=False
    ):
        raise PyGSoftmaxCompatibilityError("failed_gdnc_patch_scope_violation")
    compat_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "upstream_sparse_softmax_compat_v1"
    ]
    if len(compat_calls) != 1 or len(compat_calls[0].args) != 3 or compat_calls[0].keywords:
        raise PyGSoftmaxCompatibilityError("failed_gdnc_patch_scope_violation")
    for relative in FROZEN_UNCHANGED_PATHS:
        base = _git(root, "show", f"{base_commit}:{relative}", binary=True)
        assert isinstance(base, bytes)
        observed = (root / relative).read_bytes()
        if base.replace(b"\r\n", b"\n") != observed.replace(b"\r\n", b"\n"):
            raise PyGSoftmaxCompatibilityError("failed_gdnc_patch_scope_violation")
    return canonical_text_sha256_v1(current_path)


def assert_allowed_gdnc_paths_v1(
    *,
    repository_root: Path,
    allowed_paths: Sequence[str],
    base_commit: str = GDNR_RESULT_COMMIT,
) -> tuple[str, ...]:
    """Reject any committed or working-tree path outside the bounded GDNC patch."""

    root = repository_root.resolve()
    committed = str(_git(root, "diff", "--name-only", base_commit, "HEAD")).splitlines()
    status = str(_git(root, "status", "--porcelain=v1", "--untracked-files=all"))
    working: list[str] = []
    for line in status.splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) != 2:
            raise PyGSoftmaxCompatibilityError("unparseable Git status record")
        raw = fields[1]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        working.append(raw.replace("\\", "/"))
    changed = tuple(sorted(set(committed).union(working)))
    prohibited = sorted(set(changed).difference(allowed_paths))
    if prohibited:
        raise PyGSoftmaxCompatibilityError(
            "failed_gdnc_patch_scope_violation: " + ", ".join(prohibited)
        )
    return changed


def build_pyg_softmax_compatibility_receipt_v1(
    *,
    patched_implementation_hash: str,
    installed_pyg_signature: str,
    equivalence_cases: Sequence[Mapping[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    """Create the self-hashed public receipt for the one allowed correction."""

    require_sha256(patched_implementation_hash, "patched implementation hash")
    if installed_pyg_signature != INSTALLED_PYG_SIGNATURE:
        raise PyGSoftmaxCompatibilityError("installed PyG signature changed")
    if len(equivalence_cases) != 4 or not all(
        item.get("passed") is True for item in equivalence_cases
    ):
        raise PyGSoftmaxCompatibilityError("synthetic semantic-equivalence gate is incomplete")
    content: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "pyg_softmax_compatibility_receipt_v1",
        "task_id": TASK_ID,
        "status": COMPATIBILITY_STATUS,
        "classification": COMPATIBILITY_CLASSIFICATION,
        "upstream_repository": "https://github.com/d-ailin/GDN",
        "upstream_commit": UPSTREAM_GDN_COMMIT,
        "upstream_dependency_versions": {"torch": "1.5.1", "torch-geometric": "1.5.0"},
        "approved_dependency_versions": {"torch": "2.12.1", "torch-geometric": "2.8.0"},
        "upstream_softmax_call": UPSTREAM_CALL,
        "frozen_port_softmax_call_before_correction": UPSTREAM_CALL,
        "installed_pyg_softmax_signature": installed_pyg_signature,
        "corrected_softmax_binding": CORRECTED_CALL,
        "patched_implementation_path": PATCHED_IMPLEMENTATION_PATH,
        "patched_implementation_hash": patched_implementation_hash,
        "patched_implementation_hash_method": "sha256_utf8_lf_canonical_text",
        "original_fidelity_receipt_hash": ORIGINAL_FIDELITY_RECEIPT_HASH,
        "failed_gdnr_execution_receipt_hash": GDNR_EXECUTION_RECEIPT_HASH,
        "exact_environment_receipt_hash": EXACT_ENVIRONMENT_RECEIPT_HASH,
        "wheelhouse_receipt_hash": WHEELHOUSE_RECEIPT_HASH,
        "frozen_hyperparameter_hash": FROZEN_HYPERPARAMETER_HASH,
        "semantic_equivalence": {
            "reference_method": "independent_numerically_stable_grouped_softmax",
            "float64_absolute_tolerance": FLOAT64_ATOL,
            "float64_relative_tolerance": FLOAT64_RTOL,
            "float32_graph_layer_absolute_tolerance": FLOAT32_ATOL,
            "float32_graph_layer_relative_tolerance": FLOAT32_RTOL,
            "tolerance_basis": "precommitted_dtype_rounding_only",
            "cases": [dict(item) for item in equivalence_cases],
        },
        "upstream_semantics_preserved": True,
        "upstream_source_unchanged": True,
        "model_equations_unchanged": True,
        "tensor_grouping_unchanged": True,
        "node_count_semantics_unchanged": True,
        "only_dependency_api_binding_changed": True,
        "hai_result_information_used_to_design_correction": False,
        "meta_stat_results_consulted": False,
        "br2_pair_results_consulted": False,
        "candidate_ranking_existed_before_correction": False,
        "created_at": created_at,
    }
    return {**content, "artifact_hash": stable_hash_v1(content)}


def verify_pyg_softmax_compatibility_receipt_v1(
    document: Mapping[str, Any],
) -> str:
    """Verify immutable receipt fields and its deterministic self-hash."""

    payload = dict(document)
    observed = str(payload.pop("artifact_hash", ""))
    require_sha256(observed, "compatibility receipt hash")
    if stable_hash_v1(payload) != observed:
        raise PyGSoftmaxCompatibilityError("compatibility receipt self-hash mismatch")
    exact = {
        "status": COMPATIBILITY_STATUS,
        "classification": COMPATIBILITY_CLASSIFICATION,
        "upstream_commit": UPSTREAM_GDN_COMMIT,
        "original_fidelity_receipt_hash": ORIGINAL_FIDELITY_RECEIPT_HASH,
        "failed_gdnr_execution_receipt_hash": GDNR_EXECUTION_RECEIPT_HASH,
        "exact_environment_receipt_hash": EXACT_ENVIRONMENT_RECEIPT_HASH,
        "wheelhouse_receipt_hash": WHEELHOUSE_RECEIPT_HASH,
        "frozen_hyperparameter_hash": FROZEN_HYPERPARAMETER_HASH,
    }
    if any(payload.get(key) != value for key, value in exact.items()):
        raise PyGSoftmaxCompatibilityError("compatibility receipt identity mismatch")
    required_true = (
        "upstream_semantics_preserved",
        "upstream_source_unchanged",
        "model_equations_unchanged",
        "tensor_grouping_unchanged",
        "node_count_semantics_unchanged",
        "only_dependency_api_binding_changed",
    )
    required_false = (
        "hai_result_information_used_to_design_correction",
        "meta_stat_results_consulted",
        "br2_pair_results_consulted",
        "candidate_ranking_existed_before_correction",
    )
    if any(payload.get(field) is not True for field in required_true) or any(
        payload.get(field) is not False for field in required_false
    ):
        raise PyGSoftmaxCompatibilityError("compatibility claim boundary changed")
    return observed


__all__ = [
    "COMPATIBILITY_CLASSIFICATION",
    "COMPATIBILITY_STATUS",
    "EXACT_ENVIRONMENT_RECEIPT_HASH",
    "FLOAT32_ATOL",
    "FLOAT32_RTOL",
    "FLOAT64_ATOL",
    "FLOAT64_RTOL",
    "GDNR_DATA_ACCESS_AUDIT_HASH",
    "GDNR_EXECUTION_RECEIPT_HASH",
    "GDNR_IMPLEMENTATION_COMMIT",
    "GDNR_RESULT_COMMIT",
    "INSTALLED_PYG_SIGNATURE",
    "ORIGINAL_FIDELITY_RECEIPT_HASH",
    "PATCHED_IMPLEMENTATION_PATH",
    "PyGSoftmaxCompatibilityError",
    "WHEELHOUSE_RECEIPT_HASH",
    "assert_allowed_gdnc_paths_v1",
    "assert_gdnc_scientific_patch_scope_v1",
    "build_pyg_softmax_compatibility_receipt_v1",
    "canonical_text_sha256_v1",
    "independent_grouped_softmax_reference_v1",
    "verify_pyg_softmax_compatibility_receipt_v1",
    "verify_synthetic_semantic_equivalence_v1",
]
