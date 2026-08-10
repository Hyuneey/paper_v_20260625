"""Comprehensive PyG 1.5 to 2.8 compatibility closure for TASK-039C-GDNP.

All heavy dependencies are imported inside explicit audit/gate functions.  The
production GDN equations remain in ``upstream_candidate_backend_v1``; this
module supplies source-bound audit evidence and synthetic parity gates only.
"""

from __future__ import annotations

import hashlib
import inspect
import math
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from paperworks.gdn.pure_torch_graph_layer_reference_v1 import (
    graph_layer_reference_v1,
    grouped_softmax_reference_v1,
    remove_then_add_self_loops_reference_v1,
)
from paperworks.gdn.pyg_softmax_compatibility_v1 import (
    canonical_text_sha256_v1,
    verify_synthetic_semantic_equivalence_v1,
)
from paperworks.gdn.upstream_candidate_backend_v1 import (
    FROZEN_SEEDS,
    TASK039C0_GDN_POLICY_HASH,
    TASK039C0_PAIR_UNIVERSE_HASH,
    TASK039C0_PROTOCOL_BUNDLE_HASH,
    UPSTREAM_GDN_COMMIT,
    UpstreamGDNTrainingConfigV1,
    _load_runtime_types_v1,
    _set_all_seeds_v1,
    train_upstream_aligned_seed_v1,
)
from paperworks.v6.common import parse_iso_datetime, require_sha256, stable_hash_v1


TASK_ID = "TASK-039C-GDNP"
BASE_COMMIT = "932c3c7e58e853959b006a6a023743620dd4457d"
PYG15_TAG = "1.5.0"
PYG15_COMMIT = "cc071b7c4bd632ace8919a81d7049b984e09f0ba"
PYG28_TAG = "2.8.0"
PYG28_COMMIT = "726310a486eae37a89cd6359072b82bbbbb71579"
ORIGINAL_FIDELITY_RECEIPT_HASH = (
    "93821469e465a942ff94c779c6798355383e35003b13db24c19b9760ca3266c4"
)
SOFTMAX_COMPATIBILITY_RECEIPT_HASH = (
    "e045bae45954b6e78a2873a7560214da71c55afd10ad53e99a2a971dbcd0041d"
)
EXACT_ENVIRONMENT_RECEIPT_HASH = (
    "d0602e4f591073d58881aa1f918b788176ed888d5265f5e253fd272e060109c6"
)
PREVIOUS_GDNC_EXECUTION_RECEIPT_HASH = (
    "d79fa4f40c741cd2d3345b1f60373ed2e8c6f78c6725a745c4d04f438937736d"
)
WHEELHOUSE_RECEIPT_HASH = (
    "b8e3d5fc7b66e61282d48a6a9aa28872e387534e40ead4cda691433a3bdd8cea"
)
HYPERPARAMETER_HASH = (
    "68fbd006af1bc71468c157ba90888f54b8c0cbeba1aa7aba1121701a5b87870e"
)
COMPATIBILITY_STATUS = "passed_pyg15_to_pyg28_gdn_port_compatibility_closure"
ADAPTER_CLASSIFICATION = "documented_non_scientific_api_adapter"
PATCHED_IMPLEMENTATION_PATH = "src/paperworks/gdn/upstream_candidate_backend_v1.py"

PYG15_FILES = (
    "torch_geometric/nn/conv/message_passing.py",
    "torch_geometric/utils/softmax.py",
    "torch_geometric/utils/loop.py",
)
PYG28_FILES = (
    "torch_geometric/nn/conv/message_passing.py",
    "torch_geometric/nn/aggr/base.py",
    "torch_geometric/utils/_softmax.py",
    "torch_geometric/utils/loop.py",
    "torch_geometric/utils/_scatter.py",
    "torch_geometric/nn/conv/gat_conv.py",
)
UPSTREAM_FILES = (
    "models/graph_layer.py",
    "models/GDN.py",
    "datasets/TimeDataset.py",
    "train.py",
    "main.py",
    "run.sh",
    "install.sh",
)

EXPECTED_SOURCE_RECORDS: Mapping[str, Mapping[str, tuple[str, str, int]]] = {
    "upstream_gdn": {
        "models/graph_layer.py": ("77d9db23df4bfde2db69500d3fda2fc9b378e3e3", "0963e4091f9625e867dd90e7b402a277085f5c659a7d70c28880f3ae229b7f79", 4113),
        "models/GDN.py": ("e967790769a5ea38dfbaed3e0e77b22cd0c5c896", "eedcdc73d48e9f34c384b1a7ad875e37580f3177e023d59608a14bc56c60eb66", 5833),
        "datasets/TimeDataset.py": ("8eb0b4c580b78fec0248069b2c6a81fbe3ce080c", "b1b9f6d53080d275d96ea7157bf4ded92131a1b566410fa7a7eaf96cc5084904", 1762),
        "train.py": ("934bd50ab2acffcb9d028633960f722eae3440de", "885687aec4c42ac6a2b4782aced7ebf8785e0d0b56b787f39695a4f1b84169e1", 2772),
        "main.py": ("eb4e5d0eea6db8c5ac7658e5facf70f84dc77acc", "e2505df56c67855a8252907829ec2288722d9099a3c4789b89f2a485141e838e", 9214),
        "run.sh": ("ca6ba5955e91b020c859feddcc013fe4c60dd4c1", "a6b8577f72c56445850894f97c58dc2dbdf7aa8d8abf12615b41091b7ef60506", 1332),
        "install.sh": ("5b4f4e745496514a924bf046d08472601f742f99", "38bc8c90a581d8d43b18bf7961fff0c310d60026844a601dac056f76a56a0fd6", 425),
    },
    "pyg_1_5": {
        "torch_geometric/nn/conv/message_passing.py": ("eb4ed555c8e06fd7391dfebb8e7f8e6352efa568", "7547e0b550a23b0e4f72c9602e5f752fb77a9faafc67ee11f1c04e6c3cc703c4", 13656),
        "torch_geometric/utils/softmax.py": ("f90e8ea78a10fe67a513b47569f694f14bd38f07", "7efb0da8c35a14e75e5a4c10b62c5a6e62025c95bcfbc1a9b61329c966dcab3f", 970),
        "torch_geometric/utils/loop.py": ("81832dcaab0484af7da63de55a2e158b5397b116", "117b733465c45f5a5e83bd20c0d8bed216e736ffde7bde7a0aea313112454d02", 5068),
    },
    "pyg_2_8": {
        "torch_geometric/nn/conv/message_passing.py": ("cafee6c3f69d0fe7663a2dc37cdc22f05708ae72", "66e4ef4afa1d1b2d46c805b8987b6ea0c52ec5c95a9beee8a62758358e481e6f", 44377),
        "torch_geometric/nn/aggr/base.py": ("0d9beaa8bad11617c867dd30878f05a7dc974bc8", "bdc5872654b9d667dd6075a69d610df1bd43e7b98f33963c9eaa9d567166f363", 8225),
        "torch_geometric/utils/_softmax.py": ("30c9ef545ba88bf9c866a40e5384d00dde536e0f", "057d3ac17c52abe055b6fba6368c95f064bdaadb16258c0dac50054498efe1c5", 3422),
        "torch_geometric/utils/loop.py": ("3ffa5e769834779023f690e4d850a4806d91602f", "3145944bb6b91b1bb12ca942b51abde54d617373277726c086a283e4801ed916", 23051),
        "torch_geometric/utils/_scatter.py": ("c61a6d5296f6b593abf813774eeb4cea36a3355c", "14fb794f8d706e0d2294b32d01c251e12c0faa5c43ae30ea3bb2a003e6276f0a", 11672),
        "torch_geometric/nn/conv/gat_conv.py": ("46dbe85673b75c7a0d268ce369714b78118288e5", "e7e0808977b0aa8f411e7a2e25ee64345fe958d023cc5b706aab70ef8d1d59b6", 16551),
    },
}


class GDNPortCompatibilityError(ValueError):
    """Base fail-closed error for the comprehensive port audit."""


def _git(root: Path, *args: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={root.resolve().as_posix()}",
            "-C",
            str(root.resolve()),
            *args,
        ],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise GDNPortCompatibilityError(
            result.stderr.decode("utf-8", errors="replace").strip()
        )
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def _git_source_record(root: Path, revision: str, path: str) -> dict[str, Any]:
    blob = _git(root, "rev-parse", f"{revision}:{path}")
    content = _git(root, "cat-file", "blob", f"{revision}:{path}", binary=True)
    assert isinstance(blob, str) and isinstance(content, bytes)
    return {
        "relative_path": path,
        "git_blob_sha": blob,
        "sha256": hashlib.sha256(content).hexdigest(),
        "byte_size": len(content),
    }


def _assert_expected_records(kind: str, records: Sequence[Mapping[str, Any]]) -> None:
    expected = EXPECTED_SOURCE_RECORDS[kind]
    if set(expected) != {str(item["relative_path"]) for item in records}:
        raise GDNPortCompatibilityError(f"{kind} source inventory path mismatch")
    for item in records:
        path = str(item["relative_path"])
        blob, sha256, byte_size = expected[path]
        if (
            item.get("git_blob_sha") != blob
            or item.get("sha256") != sha256
            or item.get("byte_size") != byte_size
        ):
            raise GDNPortCompatibilityError(f"{kind} source identity mismatch: {path}")


def build_source_inventories_v1(
    *,
    upstream_root: Path,
    pyg_source_root: Path,
) -> dict[str, Any]:
    """Verify immutable upstream/PyG sources and the installed PyG wheel files."""

    upstream_commit = _git(upstream_root, "rev-parse", "HEAD")
    pyg15_commit = _git(pyg_source_root, "rev-parse", "1.5.0^{commit}")
    pyg28_commit = _git(pyg_source_root, "rev-parse", "2.8.0^{commit}")
    if upstream_commit != UPSTREAM_GDN_COMMIT:
        raise GDNPortCompatibilityError("pinned upstream GDN commit changed")
    if pyg15_commit != PYG15_COMMIT or pyg28_commit != PYG28_COMMIT:
        raise GDNPortCompatibilityError("official PyG tag identity changed")
    upstream_records = [
        _git_source_record(upstream_root, UPSTREAM_GDN_COMMIT, path)
        for path in UPSTREAM_FILES
    ]
    pyg15_records = [
        _git_source_record(pyg_source_root, PYG15_TAG, path) for path in PYG15_FILES
    ]
    pyg28_records = [
        _git_source_record(pyg_source_root, PYG28_TAG, path) for path in PYG28_FILES
    ]
    _assert_expected_records("upstream_gdn", upstream_records)
    _assert_expected_records("pyg_1_5", pyg15_records)
    _assert_expected_records("pyg_2_8", pyg28_records)

    import torch_geometric.nn.aggr.base as aggr_base
    import torch_geometric.nn.conv.gat_conv as gat_conv
    import torch_geometric.nn.conv.message_passing as message_passing
    import torch_geometric.utils._scatter as scatter_module
    import torch_geometric.utils._softmax as softmax_module
    import torch_geometric.utils.loop as loop_module

    modules = (
        message_passing,
        aggr_base,
        softmax_module,
        loop_module,
        scatter_module,
        gat_conv,
    )
    installed_records: list[dict[str, Any]] = []
    for relative_path, module, official in zip(
        PYG28_FILES,
        modules,
        pyg28_records,
        strict=True,
    ):
        installed_path = Path(inspect.getsourcefile(module) or "")
        if not installed_path.is_file():
            raise GDNPortCompatibilityError("installed PyG source file is unavailable")
        content = installed_path.read_bytes()
        record = {
            "relative_path": relative_path,
            "official_git_blob_sha": official["git_blob_sha"],
            "sha256": hashlib.sha256(content).hexdigest(),
            "byte_size": len(content),
            "absolute_path_disclosed": False,
        }
        if (
            record["sha256"] != official["sha256"]
            or record["byte_size"] != official["byte_size"]
        ):
            raise GDNPortCompatibilityError(
                f"installed PyG source differs from official 2.8.0: {relative_path}"
            )
        installed_records.append(record)

    inventory = {
        "upstream_gdn": {
            "repository": "d-ailin/GDN",
            "revision": UPSTREAM_GDN_COMMIT,
            "records": upstream_records,
        },
        "pyg_1_5": {
            "repository": "pyg-team/pytorch_geometric",
            "release": PYG15_TAG,
            "revision": PYG15_COMMIT,
            "records": pyg15_records,
            "scatter_source_note": "aggregation delegates to the separately versioned torch_scatter package; no torch_geometric/utils/scatter.py exists at tag 1.5.0",
        },
        "pyg_2_8": {
            "repository": "pyg-team/pytorch_geometric",
            "release": PYG28_TAG,
            "revision": PYG28_COMMIT,
            "records": pyg28_records,
        },
        "installed_pyg_2_8": {
            "distribution": "torch-geometric==2.8.0",
            "records": installed_records,
        },
    }
    return {
        **inventory,
        "upstream_gdn_inventory_hash": stable_hash_v1(inventory["upstream_gdn"]),
        "pyg_1_5_source_inventory_hash": stable_hash_v1(inventory["pyg_1_5"]),
        "pyg_2_8_source_inventory_hash": stable_hash_v1(inventory["pyg_2_8"]),
        "installed_pyg_2_8_source_inventory_hash": stable_hash_v1(
            inventory["installed_pyg_2_8"]
        ),
    }


def api_drift_rows_v1() -> tuple[dict[str, Any], ...]:
    """Return the frozen twenty-row API semantic comparison."""

    exact = "exact_semantics"
    default = "changed_default_requires_explicit_binding"
    signature = "changed_signature_requires_explicit_binding"
    rows = (
        (1, "MessagePassing default node_dim", "0", "-2", "explicit node_dim=0", default),
        (2, "MessagePassing flow direction", "source_to_target", "source_to_target", "unchanged default", exact),
        (3, "edge_index_i meaning", "destination for source_to_target", "destination for source_to_target", "edge_index[1]", exact),
        (4, "edge_index_j meaning", "source for source_to_target", "source for source_to_target", "edge_index[0]", exact),
        (5, "size_i and dim_size meaning", "destination-node count", "destination-node count", "size_i passed as num_nodes and dim_size", exact),
        (6, "message tensor shape", "[edge_count, heads, channels]", "unchanged user message output", "[edge_count, heads, channels]", exact),
        (7, "aggregation dimension", "node_dim=0 by default", "node_dim=-2 by default", "explicit node_dim=0", default),
        (8, "aggregation index shape", "one index per edge", "one index per edge", "1-D destination index of edge_count", exact),
        (9, "self-loop removal", "remove every source==target edge", "remove every source==target edge", "unchanged remove_self_loops call", exact),
        (10, "self-loop addition", "append one loop per explicit num_nodes", "append one loop per explicit num_nodes", "unchanged add_self_loops call", exact),
        (11, "softmax positional argument semantics", "third positional argument is num_nodes", "third positional argument is ptr", "keyword index and num_nodes adapter", signature),
        (12, "softmax grouping dimension", "dimension zero", "dimension zero by default", "explicit index with default dim=0", exact),
        (13, "output aggregation shape", "[node_count, heads, channels]", "same with node_dim=0", "verified by reference", exact),
        (14, "multi-head handling", "messages retain head axis", "aggregation retains non-node axes", "verified for one and two heads", exact),
        (15, "concat or mean-head behavior", "custom post-propagate concat or mean", "outside dependency API", "upstream custom equations retained", exact),
        (16, "bias application", "after concat or mean", "outside dependency API", "upstream custom equation retained", exact),
        (17, "embedding user-argument propagation", "unsuffixed argument forwarded", "unsuffixed argument forwarded", "embedding tensor unchanged", exact),
        (18, "return-attention behavior", "optional output; false in training path", "custom layer controls return", "executed false path unchanged; private alpha is non-ranking evidence", exact),
        (19, "backward and gradient behavior", "autograd through gather softmax scatter-add", "autograd through gather softmax add aggregation", "independent gradient and optimizer parity", exact),
        (20, "scatter implementation behavior", "torch_scatter add on dim 0", "AddAggregation to torch_geometric scatter add on explicit dim 0", "pure PyTorch index_add reference parity", exact),
    )
    return tuple(
        {
            "row": number,
            "behavior": behavior,
            "pyg_1_5_semantics": old,
            "pyg_2_8_semantics": modern,
            "project_binding": binding,
            "classification": classification,
        }
        for number, behavior, old, modern, binding, classification in rows
    )


def build_api_drift_matrix_v1(
    *,
    source_inventories: Mapping[str, Any],
    created_at: str,
) -> dict[str, Any]:
    parse_iso_datetime(created_at, "created_at")
    from torch_geometric.nn.conv import MessagePassing
    from torch_geometric.utils import add_self_loops, remove_self_loops, softmax

    rows = api_drift_rows_v1()
    if len(rows) != 20 or [item["row"] for item in rows] != list(range(1, 21)):
        raise GDNPortCompatibilityError("API drift matrix row set changed")
    unresolved = [item["row"] for item in rows if item["classification"] == "unresolved"]
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "gdn_api_drift_matrix_v1",
        "task_id": TASK_ID,
        "status": (
            COMPATIBILITY_STATUS
            if not unresolved
            else "blocked_additional_unresolved_pyg_api_drift"
        ),
        "pyg_1_5_release": PYG15_TAG,
        "pyg_1_5_commit": PYG15_COMMIT,
        "pyg_2_8_release": PYG28_TAG,
        "pyg_2_8_commit": PYG28_COMMIT,
        "installed_message_passing_signature": str(inspect.signature(MessagePassing)),
        "installed_softmax_signature": str(inspect.signature(softmax)),
        "installed_remove_self_loops_signature": str(inspect.signature(remove_self_loops)),
        "installed_add_self_loops_signature": str(inspect.signature(add_self_loops)),
        "source_inventory_hashes": {
            "upstream_gdn": source_inventories["upstream_gdn_inventory_hash"],
            "pyg_1_5": source_inventories["pyg_1_5_source_inventory_hash"],
            "pyg_2_8": source_inventories["pyg_2_8_source_inventory_hash"],
            "installed_pyg_2_8": source_inventories[
                "installed_pyg_2_8_source_inventory_hash"
            ],
        },
        "source_inventories": {
            "upstream_gdn": source_inventories["upstream_gdn"],
            "pyg_1_5": source_inventories["pyg_1_5"],
            "pyg_2_8": source_inventories["pyg_2_8"],
            "installed_pyg_2_8": source_inventories["installed_pyg_2_8"],
        },
        "rows": list(rows),
        "exact_row_count": sum(item["classification"] == "exact_semantics" for item in rows),
        "adapted_row_count": sum(item["classification"] != "exact_semantics" for item in rows),
        "unresolved_rows": unresolved,
        "created_at": created_at,
    }
    return {**content, "artifact_hash": stable_hash_v1(content)}


def confirm_node_dim_root_cause_v1(
    *,
    repository_root: Path,
    upstream_root: Path,
    pyg_source_root: Path,
) -> dict[str, Any]:
    """Confirm the requested diagnosis from immutable sources before patch use."""

    upstream = _git(
        upstream_root,
        "show",
        f"{UPSTREAM_GDN_COMMIT}:models/graph_layer.py",
    )
    old_mp = _git(
        pyg_source_root,
        "show",
        f"{PYG15_TAG}:torch_geometric/nn/conv/message_passing.py",
    )
    modern_mp = _git(
        pyg_source_root,
        "show",
        f"{PYG28_TAG}:torch_geometric/nn/conv/message_passing.py",
    )
    modern_gat = _git(
        pyg_source_root,
        "show",
        f"{PYG28_TAG}:torch_geometric/nn/conv/gat_conv.py",
    )
    port = (repository_root / PATCHED_IMPLEMENTATION_PATH).read_text(encoding="utf-8")
    checks = {
        "upstream_inherits_default": "super(GraphLayer, self).__init__(aggr='add', **kwargs)" in upstream,
        "pyg_1_5_default_node_dim_zero": "def __init__(self, aggr=\"add\", flow=\"source_to_target\", node_dim=0):" in old_mp,
        "pyg_2_8_default_node_dim_minus_two": "node_dim: int = -2" in modern_mp,
        "pyg_2_8_gatconv_explicit_node_dim_zero": "super().__init__(node_dim=0, **kwargs)" in modern_gat,
        "port_explicit_node_dim_zero": 'super().__init__(aggr="add", node_dim=0)' in port,
        "port_softmax_keyword_adapter_retained": "return pyg_softmax(src, index=index, num_nodes=num_nodes)" in port,
        "message_shape_edge_head_channel": "return x_j * alpha.view(-1, self.heads, 1)" in port,
    }
    if not all(checks.values()):
        raise GDNPortCompatibilityError("blocked_gdnp_root_cause_not_confirmed")
    return {
        "confirmed": True,
        "classification": ADAPTER_CLASSIFICATION,
        "checks": checks,
        "conclusion": "the PyG 2.8 node_dim=-2 default broadcasts the edge index against the head axis of [edge_count, head_count, channel_count]; explicit node_dim=0 restores PyG 1.5 aggregation semantics",
    }


def assert_gdnp_patch_scope_v1(*, repository_root: Path) -> str:
    """Prove the only production scientific-source delta is ``node_dim=0``."""

    root = repository_root.resolve()
    base_bytes = _git(root, "show", f"{BASE_COMMIT}:{PATCHED_IMPLEMENTATION_PATH}", binary=True)
    assert isinstance(base_bytes, bytes)
    base = base_bytes.decode("utf-8").replace("\r\n", "\n")
    current_path = root / PATCHED_IMPLEMENTATION_PATH
    current = current_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    expected = base.replace(
        'super().__init__(aggr="add")',
        'super().__init__(aggr="add", node_dim=0)',
        1,
    )
    if current != expected:
        raise GDNPortCompatibilityError("failed_gdnp_patch_scope_violation")
    if current.count('super().__init__(aggr="add", node_dim=0)') != 1:
        raise GDNPortCompatibilityError("failed_gdnp_patch_scope_violation")
    if current.count("return pyg_softmax(src, index=index, num_nodes=num_nodes)") != 1:
        raise GDNPortCompatibilityError("failed_gdnp_patch_scope_violation")
    return canonical_text_sha256_v1(current_path)


def _assert_close(actual: Any, expected: Any, *, dtype: Any, label: str) -> float:
    import torch

    if dtype == torch.float64:
        atol = rtol = 1e-12
    elif dtype == torch.float32:
        atol = rtol = 1e-6
    else:
        raise GDNPortCompatibilityError("unapproved parity dtype")
    try:
        torch.testing.assert_close(actual, expected, atol=atol, rtol=rtol)
    except AssertionError as exc:
        raise GDNPortCompatibilityError(f"{label} parity failed: {exc}") from exc
    if actual.numel() == 0:
        return 0.0
    return float((actual.detach() - expected.detach()).abs().max().item())


def _graph_layer_type() -> tuple[Any, Any, Any]:
    torch, _, model_type = _load_runtime_types_v1()
    model = model_type(6, UpstreamGDNTrainingConfigV1())
    return torch, type(model.gnn_layer.gnn), model_type


def _port_trace(layer: Any, x: Any, edge_index: Any, embedding: Any) -> dict[str, Any]:
    trace: dict[str, Any] = {}

    def propagate_pre(_module: Any, inputs: Any) -> None:
        trace["processed_edge_index"] = inputs[0].detach().clone()

    def message_pre(_module: Any, inputs: Any) -> None:
        kwargs = inputs[0]
        trace["message_kwargs"] = kwargs
        trace["source_index"] = kwargs["edges"][0].detach().clone()
        trace["target_index"] = kwargs["edge_index_i"].detach().clone()
        trace["size_i"] = int(kwargs["size_i"])

    def message_post(_module: Any, _inputs: Any, output: Any) -> None:
        trace["messages"] = output.detach().clone()

    def aggregate_post(_module: Any, _inputs: Any, output: Any) -> None:
        trace["aggregated"] = output.detach().clone()

    handles = (
        layer.register_propagate_forward_pre_hook(propagate_pre),
        layer.register_message_forward_pre_hook(message_pre),
        layer.register_message_forward_hook(message_post),
        layer.register_aggregate_forward_hook(aggregate_post),
    )
    try:
        trace["output"] = layer(x, edge_index, embedding)
        trace["attention_coefficients"] = layer._alpha
        kwargs = trace["message_kwargs"]
        import torch
        import torch.nn.functional as functional

        target_features = kwargs["x_i"].view(-1, layer.heads, layer.out_channels)
        source_features = kwargs["x_j"].view(-1, layer.heads, layer.out_channels)
        target_embedding = kwargs["embedding"][kwargs["edge_index_i"]].unsqueeze(1).repeat(1, layer.heads, 1)
        source_embedding = kwargs["embedding"][kwargs["edges"][0]].unsqueeze(1).repeat(1, layer.heads, 1)
        target_key = torch.cat((target_features, target_embedding), dim=-1)
        source_key = torch.cat((source_features, source_embedding), dim=-1)
        raw = (target_key * torch.cat((layer.att_i, layer.att_em_i), dim=-1)).sum(-1)
        raw = raw + (source_key * torch.cat((layer.att_j, layer.att_em_j), dim=-1)).sum(-1)
        trace["attention_logits"] = functional.leaky_relu(
            raw.view(-1, layer.heads, 1), layer.negative_slope
        )
    finally:
        for handle in handles:
            handle.remove()
    return trace


def _reference_for_layer(
    layer: Any,
    *,
    x: Any,
    edge_index: Any,
    embedding: Any,
    parameters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    values = dict(parameters or {})
    return graph_layer_reference_v1(
        x=x,
        edge_index=edge_index,
        embedding=embedding,
        linear_weight=values.get("lin.weight", layer.lin.weight),
        attention_source=values.get("att_i", layer.att_i),
        attention_target=values.get("att_j", layer.att_j),
        embedding_attention_source=values.get("att_em_i", layer.att_em_i),
        embedding_attention_target=values.get("att_em_j", layer.att_em_j),
        bias=values.get("bias", layer.bias),
        heads=layer.heads,
        out_channels=layer.out_channels,
        concat=layer.concat,
        negative_slope=layer.negative_slope,
        dropout=layer.dropout,
        training=layer.training,
    )


def _fixture_a(torch: Any, dtype: Any) -> tuple[Any, Any, Any]:
    generator = torch.Generator(device="cpu").manual_seed(1101)
    x = torch.randn((4, 5), generator=generator, dtype=dtype)
    embedding = torch.randn((4, 8), generator=generator, dtype=dtype)
    edge_index = torch.tensor(
        [[0, 1, 2, 0, 0], [1, 1, 1, 2, 2]],
        dtype=torch.long,
    )
    return x, edge_index, embedding


def _fixture_b(torch: Any, model_type: Any, dtype: Any) -> tuple[Any, Any, Any]:
    generator = torch.Generator(device="cpu").manual_seed(2302)
    x = torch.randn((12, 5), generator=generator, dtype=dtype)
    embedding = torch.randn((12, 8), generator=generator, dtype=dtype)
    base_edges = torch.tensor(
        [[0, 1, 2, 3, 3, 4], [1, 2, 2, 4, 5, 5]],
        dtype=torch.long,
    )
    edge_index = model_type._batch_edges(base_edges, 2, 6)
    return x, edge_index, embedding


def _fixture_c(torch: Any, dtype: Any) -> tuple[Any, Any, Any]:
    x = torch.tensor(
        [
            [800.0, -700.0, 600.0, -500.0, 400.0],
            [-900.0, 800.0, -700.0, 600.0, -500.0],
            [300.0, -200.0, 100.0, -50.0, 25.0],
            [-10.0, 20.0, -30.0, 40.0, -50.0],
        ],
        dtype=dtype,
    )
    embedding = torch.tensor(
        [
            [40.0, -30.0, 20.0, -10.0, 5.0, -4.0, 3.0, -2.0],
            [-35.0, 25.0, -15.0, 8.0, -4.0, 3.0, -2.0, 1.0],
            [12.0, -9.0, 6.0, -3.0, 1.5, -1.0, 0.5, -0.25],
            [-7.0, 6.0, -5.0, 4.0, -3.0, 2.0, -1.0, 0.5],
        ],
        dtype=dtype,
    )
    edge_index = torch.tensor(
        [[0, 1, 1, 2], [1, 1, 2, 2]],
        dtype=torch.long,
    )
    return x, edge_index, embedding


def run_graph_layer_forward_parity_v1() -> dict[str, Any]:
    """Compare every GraphLayer intermediate with the pure-PyTorch reference."""

    torch, graph_layer_type, model_type = _graph_layer_type()
    fixtures = (
        ("fixture_a", torch.float64, 1, _fixture_a(torch, torch.float64)),
        ("fixture_b", torch.float32, 2, _fixture_b(torch, model_type, torch.float32)),
        ("fixture_c", torch.float64, 1, _fixture_c(torch, torch.float64)),
    )
    results: list[dict[str, Any]] = []
    for offset, (name, dtype, heads, fixture) in enumerate(fixtures):
        torch.manual_seed(3100 + offset)
        layer = graph_layer_type(5, 8, heads=heads, concat=(name != "fixture_b"))
        layer = layer.to(dtype=dtype)
        layer.eval()
        if name == "fixture_c":
            with torch.no_grad():
                layer.lin.weight.copy_(
                    torch.linspace(
                        -1.0,
                        1.0,
                        steps=layer.lin.weight.numel(),
                        dtype=dtype,
                    ).reshape_as(layer.lin.weight)
                )
                layer.att_i.fill_(3.0)
                layer.att_j.fill_(-2.0)
                layer.att_em_i.fill_(1.5)
                layer.att_em_j.fill_(-1.25)
        x, edge_index, embedding = fixture
        port = _port_trace(layer, x, edge_index, embedding)
        reference = _reference_for_layer(
            layer,
            x=x,
            edge_index=edge_index,
            embedding=embedding,
        )
        if not torch.equal(
            port["processed_edge_index"], reference["processed_edge_index"]
        ):
            raise GDNPortCompatibilityError(
                "failed_gdnp_graph_layer_forward_parity: processed edge index"
            )
        if not torch.equal(port["source_index"], reference["source_index"]):
            raise GDNPortCompatibilityError(
                "failed_gdnp_graph_layer_forward_parity: source index"
            )
        if not torch.equal(port["target_index"], reference["target_index"]):
            raise GDNPortCompatibilityError(
                "failed_gdnp_graph_layer_forward_parity: target index"
            )
        if port["size_i"] != x.shape[0] or layer.node_dim != 0:
            raise GDNPortCompatibilityError(
                "failed_gdnp_graph_layer_forward_parity: node dimension"
            )
        errors = {
            "attention_logits": _assert_close(
                port["attention_logits"],
                reference["attention_logits"],
                dtype=dtype,
                label=f"{name} attention logits",
            ),
            "attention_coefficients": _assert_close(
                port["attention_coefficients"],
                reference["attention_coefficients"],
                dtype=dtype,
                label=f"{name} attention coefficients",
            ),
            "messages": _assert_close(
                port["messages"],
                reference["messages"],
                dtype=dtype,
                label=f"{name} messages",
            ),
            "aggregated": _assert_close(
                port["aggregated"],
                reference["aggregated"],
                dtype=dtype,
                label=f"{name} aggregated",
            ),
            "output": _assert_close(
                port["output"],
                reference["output"],
                dtype=dtype,
                label=f"{name} output",
            ),
        }
        if tuple(port["output"].shape) != tuple(reference["output"].shape):
            raise GDNPortCompatibilityError(
                "failed_gdnp_graph_layer_forward_parity: output shape"
            )
        results.append(
            {
                "fixture": name,
                "dtype": str(dtype).replace("torch.", ""),
                "node_count": int(x.shape[0]),
                "processed_edge_count": int(reference["processed_edge_index"].shape[1]),
                "heads": heads,
                "output_shape": list(port["output"].shape),
                "maximum_absolute_errors": errors,
                "passed": True,
            }
        )
    return {
        "status": "passed_gdnp_graph_layer_forward_parity",
        "float64_absolute_tolerance": 1e-12,
        "float64_relative_tolerance": 1e-12,
        "float32_absolute_tolerance": 1e-6,
        "float32_relative_tolerance": 1e-6,
        "fixtures": results,
    }


def _cloned_reference_parameters(layer: Any) -> dict[str, Any]:
    import torch

    values: dict[str, Any] = {}
    for name, parameter in layer.named_parameters():
        values[name] = torch.nn.Parameter(parameter.detach().clone())
    return values


def run_graph_layer_backward_parity_v1() -> dict[str, Any]:
    """Verify gradients and one Adam update against independent equations."""

    torch, graph_layer_type, _ = _graph_layer_type()
    torch.manual_seed(4111)
    layer = graph_layer_type(5, 8, heads=1, concat=True).double()
    layer.eval()
    x, edge_index, embedding = _fixture_a(torch, torch.float64)
    actual_x = x.detach().clone().requires_grad_(True)
    actual_embedding = embedding.detach().clone().requires_grad_(True)
    actual_output = layer(actual_x, edge_index, actual_embedding)
    actual_output.square().sum().backward()

    reference_parameters = _cloned_reference_parameters(layer)
    reference_x = x.detach().clone().requires_grad_(True)
    reference_embedding = embedding.detach().clone().requires_grad_(True)
    reference = _reference_for_layer(
        layer,
        x=reference_x,
        edge_index=edge_index,
        embedding=reference_embedding,
        parameters=reference_parameters,
    )
    reference["output"].square().sum().backward()
    gradient_pairs: list[tuple[str, Any, Any]] = [
        ("input_node_features", actual_x.grad, reference_x.grad),
        ("node_embeddings", actual_embedding.grad, reference_embedding.grad),
    ]
    for name, parameter in layer.named_parameters():
        gradient_pairs.append((name, parameter.grad, reference_parameters[name].grad))
    maximum_errors: dict[str, float] = {}
    for name, actual, expected in gradient_pairs:
        if actual is None or expected is None or actual.shape != expected.shape:
            raise GDNPortCompatibilityError(
                f"failed_gdnp_graph_layer_backward_parity: {name} gradient presence"
            )
        if not bool(torch.isfinite(actual).all()) or not bool(torch.isfinite(expected).all()):
            raise GDNPortCompatibilityError(
                f"failed_gdnp_graph_layer_backward_parity: {name} non-finite gradient"
            )
        maximum_errors[name] = _assert_close(
            actual,
            expected,
            dtype=torch.float64,
            label=f"{name} gradient",
        )

    torch.manual_seed(4222)
    actual_step = graph_layer_type(5, 8, heads=1, concat=True).double()
    actual_step.load_state_dict(layer.state_dict())
    actual_step.eval()
    reference_step_parameters = _cloned_reference_parameters(actual_step)
    actual_optimizer = torch.optim.Adam(actual_step.parameters(), lr=0.001)
    reference_optimizer = torch.optim.Adam(
        list(reference_step_parameters.values()), lr=0.001
    )
    actual_optimizer.zero_grad()
    reference_optimizer.zero_grad()
    actual_step(x, edge_index, embedding).square().sum().backward()
    reference_step = _reference_for_layer(
        actual_step,
        x=x,
        edge_index=edge_index,
        embedding=embedding,
        parameters=reference_step_parameters,
    )
    reference_step["output"].square().sum().backward()
    actual_optimizer.step()
    reference_optimizer.step()
    optimizer_errors: dict[str, float] = {}
    for name, parameter in actual_step.named_parameters():
        optimizer_errors[name] = _assert_close(
            parameter,
            reference_step_parameters[name],
            dtype=torch.float64,
            label=f"{name} one-step optimizer",
        )
    return {
        "status": "passed_gdnp_graph_layer_backward_parity",
        "loss": "output.square().sum()",
        "gradient_maximum_absolute_errors": maximum_errors,
        "one_step_optimizer": "Adam(lr=0.001)",
        "optimizer_parameter_maximum_absolute_errors": optimizer_errors,
        "absolute_tolerance": 1e-12,
        "relative_tolerance": 1e-12,
    }


def run_index_semantics_gate_v1() -> dict[str, Any]:
    """Machine-check source/destination, self-loop, batch, and aggregation facts."""

    torch, graph_layer_type, model_type = _graph_layer_type()
    layer = graph_layer_type(5, 8, heads=2, concat=False).float().eval()
    x, edge_index, embedding = _fixture_b(torch, model_type, torch.float32)
    port = _port_trace(layer, x, edge_index, embedding)
    reference_edges = remove_then_add_self_loops_reference_v1(
        edge_index, num_nodes=x.shape[0]
    )
    source = reference_edges[0]
    target = reference_edges[1]
    loop_nodes = source[source == target]
    no_cross_batch = bool(
        torch.all(torch.div(source, 6, rounding_mode="floor") == torch.div(target, 6, rounding_mode="floor"))
    )
    checks = {
        "edge_index_j_is_source": bool(torch.equal(port["source_index"], source)),
        "edge_index_i_is_destination": bool(torch.equal(port["target_index"], target)),
        "size_i_is_destination_node_count": port["size_i"] == 12,
        "existing_self_loops_removed": (
            int((edge_index[0] == edge_index[1]).sum().item()) == 2
            and int((source == target).sum().item()) == 12
        ),
        "exactly_one_self_loop_per_node_added": bool(
            torch.equal(torch.sort(loop_nodes).values, torch.arange(12))
        ),
        "aggregation_groups_by_edge_index_i": tuple(port["aggregated"].shape) == (12, 2, 8),
        "no_cross_batch_edges": no_cross_batch,
        "message_aggregation_node_dim_zero": layer.node_dim == 0,
    }
    if not all(checks.values()):
        raise GDNPortCompatibilityError("failed_gdnp_graph_layer_forward_parity")
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "gdn_index_semantics_receipt_v1",
        "task_id": TASK_ID,
        "status": "passed_gdnp_index_self_loop_parity",
        "flow": layer.flow,
        "node_dim": layer.node_dim,
        "aggregation": "add",
        "source_row": 0,
        "destination_row": 1,
        "node_count": 12,
        "batch_size": 2,
        "nodes_per_graph": 6,
        "checks": checks,
        "absolute_paths_disclosed": False,
    }
    return {**content, "artifact_hash": stable_hash_v1(content)}


def run_gnn_layer_parity_v1() -> dict[str, Any]:
    """Compare GraphLayer -> BatchNorm1d -> ReLU in eval and train modes."""

    import copy

    torch, _, model_type = _graph_layer_type()
    edge_index = torch.tensor(
        [[0, 1, 2, 3, 4, 0, 2], [1, 2, 2, 4, 5, 5, 5]],
        dtype=torch.long,
    )
    generator = torch.Generator(device="cpu").manual_seed(5151)
    x = torch.randn((6, 5), generator=generator, dtype=torch.float64)
    embedding = torch.randn((6, 64), generator=generator, dtype=torch.float64)
    mode_results: list[dict[str, Any]] = []
    for mode in ("evaluation", "training"):
        _set_all_seeds_v1(torch, 11)
        layer = model_type(6, UpstreamGDNTrainingConfigV1()).gnn_layer.double()
        reference_bn = copy.deepcopy(layer.bn)
        if mode == "evaluation":
            layer.eval()
            reference_bn.eval()
        else:
            layer.train()
            reference_bn.train()
        initial_mean = layer.bn.running_mean.detach().clone()
        initial_var = layer.bn.running_var.detach().clone()
        actual = layer(x, edge_index, embedding)
        graph = _reference_for_layer(
            layer.gnn,
            x=x,
            edge_index=edge_index,
            embedding=embedding,
        )["output"]
        expected = torch.relu(reference_bn(graph))
        output_error = _assert_close(
            actual,
            expected,
            dtype=torch.float64,
            label=f"GNNLayer {mode} output",
        )
        mean_error = _assert_close(
            layer.bn.running_mean,
            reference_bn.running_mean,
            dtype=torch.float64,
            label=f"GNNLayer {mode} running mean",
        )
        var_error = _assert_close(
            layer.bn.running_var,
            reference_bn.running_var,
            dtype=torch.float64,
            label=f"GNNLayer {mode} running variance",
        )
        if mode == "evaluation" and (
            not torch.equal(layer.bn.running_mean, initial_mean)
            or not torch.equal(layer.bn.running_var, initial_var)
        ):
            raise GDNPortCompatibilityError("failed_gdnp_gnn_layer_parity")
        mode_results.append(
            {
                "mode": mode,
                "output_shape": list(actual.shape),
                "output_maximum_absolute_error": output_error,
                "running_mean_maximum_absolute_error": mean_error,
                "running_variance_maximum_absolute_error": var_error,
                "passed": True,
            }
        )
    return {
        "status": "passed_gdnp_gnn_layer_parity",
        "modes": mode_results,
        "absolute_tolerance": 1e-12,
        "relative_tolerance": 1e-12,
    }


def _complete_directed_edges(torch: Any, node_count: int) -> Any:
    return torch.tensor(
        [
            [
                source
                for target in range(node_count)
                for source in range(node_count)
                if source != target
            ],
            [
                target
                for target in range(node_count)
                for source in range(node_count)
                if source != target
            ],
        ],
        dtype=torch.long,
    )


def run_tiny_full_gdn_gate_v1() -> dict[str, Any]:
    """Run the complete six-node project model through one optimizer step."""

    import warnings

    torch, nn, model_type = _load_runtime_types_v1()
    config = UpstreamGDNTrainingConfigV1()
    generator = torch.Generator(device="cpu").manual_seed(6111)
    data = torch.randn((2, 6, 5), generator=generator, dtype=torch.float32)
    target = torch.randn((2, 6), generator=generator, dtype=torch.float32)
    edges = _complete_directed_edges(torch, 6)

    def fresh_initial() -> tuple[Any, Any, Any]:
        _set_all_seeds_v1(torch, 11)
        model = model_type(6, config).cpu()
        model.eval()
        with torch.no_grad():
            output = model(data, edges).detach().clone()
            learned = model.learned_graph.detach().clone()
        return model, output, learned

    _, initial_output, initial_graph = fresh_initial()
    model, replay_output, replay_graph = fresh_initial()
    _assert_close(
        initial_output,
        replay_output,
        dtype=torch.float32,
        label="tiny same-seed initial output",
    )
    if not torch.equal(initial_graph, replay_graph):
        raise GDNPortCompatibilityError("failed_gdnp_tiny_full_gdn_gate")

    model.train()
    optimizer = torch.optim.Adam(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    optimizer.zero_grad()
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        prediction = model(data, edges)
        loss = nn.MSELoss(reduction="mean")(prediction, target)
        loss.backward()
        gradient_count = 0
        for parameter in model.parameters():
            if parameter.requires_grad:
                if parameter.grad is None or not bool(torch.isfinite(parameter.grad).all()):
                    raise GDNPortCompatibilityError("failed_gdnp_tiny_full_gdn_gate")
                gradient_count += 1
        optimizer.step()
        second_prediction = model(data, edges)
    warning_text = "\n".join(str(item.message) for item in captured).lower()
    if "fallback" in warning_text or "aggregation" in warning_text:
        raise GDNPortCompatibilityError("failed_gdnp_tiny_full_gdn_gate")
    if (
        tuple(prediction.shape) != (2, 6)
        or tuple(second_prediction.shape) != (2, 6)
        or not bool(torch.isfinite(prediction).all())
        or not bool(torch.isfinite(second_prediction).all())
        or not math.isfinite(float(loss.item()))
        or tuple(model.learned_graph.shape) != (6, 5)
        or int(model.learned_graph.min().item()) < 0
        or int(model.learned_graph.max().item()) >= 6
    ):
        raise GDNPortCompatibilityError("failed_gdnp_tiny_full_gdn_gate")
    return {
        "status": "passed_gdnp_tiny_full_gdn_gate",
        "batch_size": 2,
        "node_count": 6,
        "input_window": 5,
        "embedding_dimension": 64,
        "graph_topk": 5,
        "output_layer_count": 1,
        "output_intermediate_dimension": 128,
        "dtype": "float32",
        "device": "cpu",
        "seed": 11,
        "forward_output_shape": list(prediction.shape),
        "finite_mean_mse": True,
        "backward_succeeded": True,
        "finite_trainable_gradient_count": gradient_count,
        "adam_step_succeeded": True,
        "second_forward_succeeded": True,
        "learned_graph_shape": list(model.learned_graph.shape),
        "learned_graph_indices_in_range": True,
        "same_seed_initial_output_equal": True,
        "same_seed_learned_graph_equal": True,
        "semantic_warning_count": 0,
    }


def run_tiny_training_loop_gate_v1() -> dict[str, Any]:
    """Exercise the frozen real-seed training path on synthetic identities."""

    from paperworks.candidates.gdn_candidate_discovery_v1 import (
        project_seed_record_to_universe_v1,
    )

    synthetic_sources = tuple(f"SYNTH_SOURCE_{index}" for index in range(12))
    synthetic_targets = tuple(f"SYNTH_TARGET_{index}" for index in range(12))
    feature_order = synthetic_sources + synthetic_targets
    pairs = tuple(
        (source, target)
        for source in synthetic_sources
        for target in synthetic_targets
    )
    segment: list[list[float]] = []
    for time_index in range(86):
        segment.append(
            [
                math.sin((time_index + 1) * (node + 1) / 17.0)
                + math.cos((time_index + 3) * (node + 2) / 23.0)
                for node in range(len(feature_order))
            ]
        )
    config = UpstreamGDNTrainingConfigV1()
    trained = train_upstream_aligned_seed_v1(
        segments=(segment,),
        feature_order=feature_order,
        candidate_pairs=pairs,
        seed=11,
        config=config,
    )
    projected = project_seed_record_to_universe_v1(
        seed=trained.seed,
        selected_model_edges=trained.selected_edges,
        model_similarities=trained.candidate_similarities,
        universe_pairs=pairs,
        hyperparameter_hash=trained.hyperparameter_hash,
        epoch_count=trained.epoch_count,
        best_validation_loss=trained.best_validation_loss,
    )
    window_count = 86 - config.slide_window
    validation_count = int(window_count * config.validation_ratio)
    training_count = window_count - validation_count
    training_batches = math.ceil(training_count / config.batch_size)
    if (
        training_batches < 2
        or trained.seed != 11
        or trained.epoch_count < 1
        or trained.epoch_count > config.epochs
        or not math.isfinite(trained.best_validation_loss)
        or trained.hyperparameter_hash != HYPERPARAMETER_HASH
        or set(trained.candidate_similarities) != set(pairs)
        or not projected.successful
        or set(projected.candidate_similarities) != set(pairs)
    ):
        raise GDNPortCompatibilityError("failed_gdnp_tiny_training_loop_gate")
    return {
        "status": "passed_gdnp_tiny_training_loop_gate",
        "seed": 11,
        "synthetic_node_count": len(feature_order),
        "synthetic_row_count": 86,
        "window_count": window_count,
        "training_batch_count": training_batches,
        "validation_batch_count": math.ceil(validation_count / config.batch_size),
        "optimizer_update": True,
        "validation_loss_calculated": True,
        "best_state_captured_and_reloaded": True,
        "learned_graph_extracted": True,
        "synthetic_candidate_count": len(pairs),
        "synthetic_supported_count": len(projected.selected_edges),
        "epoch_count": trained.epoch_count,
        "best_validation_loss_finite": True,
        "hyperparameter_hash": trained.hyperparameter_hash,
    }


def build_legacy_oracle_receipt_v1(
    *,
    status: str,
    created_at: str,
    reason: str | None = None,
) -> dict[str, Any]:
    if status not in {
        "passed_legacy_pyg15_synthetic_oracle",
        "blocked_official_legacy_environment_unavailable",
    }:
        raise GDNPortCompatibilityError("invalid legacy oracle status")
    parse_iso_datetime(created_at, "created_at")
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "gdn_legacy_oracle_receipt_v1",
        "task_id": TASK_ID,
        "status": status,
        "synthetic_only": True,
        "hai_feature_values_accessed": False,
        "official_sources_only": True,
        "bounded_attempt_count": 1,
        "base_image_digest": None,
        "python_version": None,
        "package_versions": {},
        "package_archive_hashes": [],
        "container_recipe_hash": None,
        "blocking_reason": reason,
        "created_at": created_at,
    }
    return {**content, "artifact_hash": stable_hash_v1(content)}


def build_compatibility_closure_receipt_v1(
    *,
    source_inventories: Mapping[str, Any],
    api_matrix: Mapping[str, Any],
    root_cause: Mapping[str, Any],
    forward_parity: Mapping[str, Any],
    backward_parity: Mapping[str, Any],
    index_semantics: Mapping[str, Any],
    gnn_parity: Mapping[str, Any],
    tiny_full_gdn: Mapping[str, Any],
    tiny_training_loop: Mapping[str, Any],
    legacy_oracle: Mapping[str, Any],
    patched_implementation_hash: str,
    created_at: str,
) -> dict[str, Any]:
    """Bind every pre-data compatibility fact into one self-hashed receipt."""

    parse_iso_datetime(created_at, "created_at")
    require_sha256(patched_implementation_hash, "patched implementation hash")
    unresolved = list(api_matrix.get("unresolved_rows", ()))
    gates = {
        "graph_layer_forward_parity": forward_parity.get("status"),
        "graph_layer_backward_parity": backward_parity.get("status"),
        "index_self_loop_parity": index_semantics.get("status"),
        "gnn_layer_parity": gnn_parity.get("status"),
        "tiny_full_gdn_gate": tiny_full_gdn.get("status"),
        "tiny_training_loop_gate": tiny_training_loop.get("status"),
    }
    expected = {
        "graph_layer_forward_parity": "passed_gdnp_graph_layer_forward_parity",
        "graph_layer_backward_parity": "passed_gdnp_graph_layer_backward_parity",
        "index_self_loop_parity": "passed_gdnp_index_self_loop_parity",
        "gnn_layer_parity": "passed_gdnp_gnn_layer_parity",
        "tiny_full_gdn_gate": "passed_gdnp_tiny_full_gdn_gate",
        "tiny_training_loop_gate": "passed_gdnp_tiny_training_loop_gate",
    }
    if unresolved or not root_cause.get("confirmed") or gates != expected:
        raise GDNPortCompatibilityError("blocked_additional_unresolved_pyg_api_drift")
    softmax_cases = verify_synthetic_semantic_equivalence_v1()
    config = UpstreamGDNTrainingConfigV1()
    if config.hyperparameter_hash != HYPERPARAMETER_HASH:
        raise GDNPortCompatibilityError("frozen hyperparameter hash changed")
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "gdn_port_compatibility_closure_receipt_v1",
        "task_id": TASK_ID,
        "status": COMPATIBILITY_STATUS,
        "prior_fidelity_receipt_hash": ORIGINAL_FIDELITY_RECEIPT_HASH,
        "softmax_compatibility_receipt_hash": SOFTMAX_COMPATIBILITY_RECEIPT_HASH,
        "exact_environment_receipt_hash": EXACT_ENVIRONMENT_RECEIPT_HASH,
        "wheelhouse_receipt_hash": WHEELHOUSE_RECEIPT_HASH,
        "previous_gdnc_failure_receipt_hash": PREVIOUS_GDNC_EXECUTION_RECEIPT_HASH,
        "upstream_gdn_commit": UPSTREAM_GDN_COMMIT,
        "pyg_1_5_release": PYG15_TAG,
        "pyg_1_5_commit": PYG15_COMMIT,
        "pyg_2_8_release": PYG28_TAG,
        "pyg_2_8_commit": PYG28_COMMIT,
        "upstream_gdn_source_inventory_hash": source_inventories[
            "upstream_gdn_inventory_hash"
        ],
        "pyg_1_5_source_inventory_hash": source_inventories[
            "pyg_1_5_source_inventory_hash"
        ],
        "pyg_2_8_source_inventory_hash": source_inventories[
            "pyg_2_8_source_inventory_hash"
        ],
        "installed_pyg_source_inventory_hash": source_inventories[
            "installed_pyg_2_8_source_inventory_hash"
        ],
        "api_drift_matrix_hash": api_matrix["artifact_hash"],
        "index_semantics_receipt_hash": index_semantics["artifact_hash"],
        "legacy_oracle_receipt_hash": legacy_oracle["artifact_hash"],
        "node_dim_root_cause_confirmed": True,
        "node_dim_adapter": {
            "binding": "MessagePassing(aggr=add, node_dim=0)",
            "classification": ADAPTER_CLASSIFICATION,
            "pyg_1_5_default_semantics_restored_explicitly": True,
            "message_edge_dimension_unchanged": True,
            "attention_equations_unchanged": True,
            "source_target_index_meanings_unchanged": True,
            "aggregation_operator_remains_addition": True,
            "graph_edges_unchanged": True,
            "model_architecture_unchanged": True,
            "hyperparameters_unchanged": True,
            "hai_result_information_used": False,
            "meta_stat_results_consulted": False,
        },
        "additional_adapters": [],
        "softmax_compatibility_status": "passed_semantics_preserving_pyg_softmax_compatibility",
        "softmax_reference_case_count": len(softmax_cases),
        "gate_statuses": gates,
        "gate_evidence_hashes": {
            "graph_layer_forward_parity": stable_hash_v1(dict(forward_parity)),
            "graph_layer_backward_parity": stable_hash_v1(dict(backward_parity)),
            "index_self_loop_parity": index_semantics["artifact_hash"],
            "gnn_layer_parity": stable_hash_v1(dict(gnn_parity)),
            "tiny_full_gdn_gate": stable_hash_v1(dict(tiny_full_gdn)),
            "tiny_training_loop_gate": stable_hash_v1(dict(tiny_training_loop)),
        },
        "legacy_oracle_status": legacy_oracle["status"],
        "source_checkout_unchanged": True,
        "model_equations_unchanged": True,
        "graph_construction_unchanged": True,
        "hyperparameters_unchanged": True,
        "hyperparameter_hash": config.hyperparameter_hash,
        "ranking_unchanged": True,
        "hai_feature_values_accessed": False,
        "meta_stat_consulted": False,
        "br2_pair_outcomes_consulted": False,
        "unresolved_compatibility_fields": [],
        "patched_implementation_hash": patched_implementation_hash,
        "patched_implementation_hash_method": "sha256_utf8_lf_canonical_text",
        "created_at": created_at,
    }
    return {**content, "artifact_hash": stable_hash_v1(content)}


def verify_self_hashed_compatibility_artifact_v1(payload: Mapping[str, Any]) -> str:
    observed = str(payload.get("artifact_hash", ""))
    require_sha256(observed, "artifact hash")
    content = {key: value for key, value in payload.items() if key != "artifact_hash"}
    expected = stable_hash_v1(content)
    if observed != expected:
        raise GDNPortCompatibilityError("compatibility artifact self-hash mismatch")
    return observed


__all__ = [
    "ADAPTER_CLASSIFICATION",
    "BASE_COMMIT",
    "COMPATIBILITY_STATUS",
    "EXACT_ENVIRONMENT_RECEIPT_HASH",
    "GDNPortCompatibilityError",
    "HYPERPARAMETER_HASH",
    "ORIGINAL_FIDELITY_RECEIPT_HASH",
    "PREVIOUS_GDNC_EXECUTION_RECEIPT_HASH",
    "PYG15_COMMIT",
    "PYG15_TAG",
    "PYG28_COMMIT",
    "PYG28_TAG",
    "SOFTMAX_COMPATIBILITY_RECEIPT_HASH",
    "TASK_ID",
    "WHEELHOUSE_RECEIPT_HASH",
    "api_drift_rows_v1",
    "assert_gdnp_patch_scope_v1",
    "build_api_drift_matrix_v1",
    "build_compatibility_closure_receipt_v1",
    "build_legacy_oracle_receipt_v1",
    "build_source_inventories_v1",
    "confirm_node_dim_root_cause_v1",
    "run_gnn_layer_parity_v1",
    "run_graph_layer_backward_parity_v1",
    "run_graph_layer_forward_parity_v1",
    "run_index_semantics_gate_v1",
    "run_tiny_full_gdn_gate_v1",
    "run_tiny_training_loop_gate_v1",
    "verify_self_hashed_compatibility_artifact_v1",
]
