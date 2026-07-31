from __future__ import annotations

from paperworks.gdn.fidelity_v1 import (
    GDNBackendFidelityRecordV1,
    GDNFidelityClassV1,
    GDNFidelityFreezeV1,
    UpstreamFileRecordV1,
)


CREATED_AT = "2026-07-31T00:00:00+09:00"
MASKED_SOURCE_SHA256 = (
    "84847639853996f7c9dfd3804a83fab58f12efea73641c4caca564c69caf0a68"
)
TORCH_BEHAVIOR_AST_SHA256 = (
    "21989ea5de8459259514ef35784a55123082c9a6bf078e8ec878655e3f29723c"
)
UPSTREAM_FILES = (
    UpstreamFileRecordV1(
        path="models/GDN.py",
        git_blob_sha="e967790769a5ea38dfbaed3e0e77b22cd0c5c896",
        sha256="eedcdc73d48e9f34c384b1a7ad875e37580f3177e023d59608a14bc56c60eb66",
    ),
    UpstreamFileRecordV1(
        path="models/graph_layer.py",
        git_blob_sha="77d9db23df4bfde2db69500d3fda2fc9b378e3e3",
        sha256="0963e4091f9625e867dd90e7b402a277085f5c659a7d70c28880f3ae229b7f79",
    ),
    UpstreamFileRecordV1(
        path="datasets/TimeDataset.py",
        git_blob_sha="8eb0b4c580b78fec0248069b2c6a81fbe3ce080c",
        sha256="b1b9f6d53080d275d96ea7157bf4ded92131a1b566410fa7a7eaf96cc5084904",
    ),
    UpstreamFileRecordV1(
        path="train.py",
        git_blob_sha="934bd50ab2acffcb9d028633960f722eae3440de",
        sha256="885687aec4c42ac6a2b4782aced7ebf8785e0d0b56b787f39695a4f1b84169e1",
    ),
    UpstreamFileRecordV1(
        path="test.py",
        git_blob_sha="58ae62520552cd0548318ed14d4a5fc07965a4f8",
        sha256="156de035bdb1b2d4931787cd863090064e2f4c6b05ae92e3f2103cba305eddeb",
    ),
    UpstreamFileRecordV1(
        path="evaluate.py",
        git_blob_sha="ae4110dc37d3665a93c1a88de35d313da6b4dd73",
        sha256="daa647f55b26e1dd627257a25b9084c60fc36488f58c45faf9d7455491231e83",
    ),
    UpstreamFileRecordV1(
        path="util/net_struct.py",
        git_blob_sha="ccc6256180aeb40395004a695446721fe073c754",
        sha256="e0079cc401b2b9cf6e03634146382581accf267918d91c1ebffe628c82a6bac4",
    ),
)


def make_fidelity_records() -> tuple[GDNBackendFidelityRecordV1, ...]:
    deterministic = GDNBackendFidelityRecordV1(
        backend_id="deterministic_embedding_smoke",
        backend_version="1.0",
        implementation_module="paperworks.gdn.masked",
        implementation_symbols=("fit_deterministic_embedding_checkpoint",),
        implementation_behavior_hash=MASKED_SOURCE_SHA256,
        fidelity_class=GDNFidelityClassV1.SYNTHETIC_SMOKE_ONLY,
        scientific_gdn_claim_allowed=False,
        production_candidate_ranking_allowed=False,
        upstream_repository="https://github.com/d-ailin/GDN",
        upstream_commit="9853899da860682669a134e4af315d036aab4eca",
        upstream_file_records=(UPSTREAM_FILES[0], UPSTREAM_FILES[2], UPSTREAM_FILES[3]),
        mapped_upstream_features=(
            "node-indexed embedding vectors can feed cosine extraction",
            "deterministic checkpoint provenance",
        ),
        missing_upstream_features=(
            "sliding-window per-node input",
            "next-value neural objective",
            "dynamic learned cosine graph",
            "embedding-conditioned attention",
            "output gating",
            "validation checkpoint selection",
        ),
        intentional_project_deviations=(
            "summary statistics replace learned embeddings",
            "no neural model is trained",
        ),
        input_contract="sequence of scalar feature mappings",
        training_objective="none; deterministic summary construction",
        learned_graph_behavior="none in trainer; extraction is a separate component",
        candidate_mask_policy="not applicable during embedding construction",
        self_edge_policy="not applicable during embedding construction",
        split_policy="legacy train_normal guard on caller-provided rows",
        dependency_requirements=("standard_library_only",),
        data_accessed=False,
        model_trained=False,
        created_at=CREATED_AT,
    )
    torch_smoke = GDNBackendFidelityRecordV1(
        backend_id="torch_pyg_cpu_smoke",
        backend_version="1.0",
        implementation_module="paperworks.gdn.torch_backend",
        implementation_symbols=(
            "TorchGDNEmbeddingModel",
            "TorchGDNTrainingConfig",
            "fit_torch_gdn_embedding_checkpoint",
        ),
        implementation_behavior_hash=TORCH_BEHAVIOR_AST_SHA256,
        fidelity_class=GDNFidelityClassV1.SYNTHETIC_SMOKE_ONLY,
        scientific_gdn_claim_allowed=False,
        production_candidate_ranking_allowed=False,
        upstream_repository="https://github.com/d-ailin/GDN",
        upstream_commit="9853899da860682669a134e4af315d036aab4eca",
        upstream_file_records=(
            UPSTREAM_FILES[0],
            UPSTREAM_FILES[1],
            UPSTREAM_FILES[2],
            UPSTREAM_FILES[3],
        ),
        mapped_upstream_features=(
            "node embedding table",
            "next-row per-node MSE objective",
            "graph message passing",
        ),
        missing_upstream_features=(
            "sliding-window per-node input",
            "dynamic embedding-cosine Top-K graph",
            "custom embedding-conditioned attention",
            "embedding output gating",
            "upstream batch normalization and dropout stack",
            "validation-loss checkpoint selection",
        ),
        intentional_project_deviations=(
            "fixed CandidateUniverse graph with mean aggregation",
            "current scalar plus neighbor scalar plus embedding decoder",
            "fixed-epoch final embedding export",
        ),
        input_contract="adjacent scalar rows shaped as time by node",
        training_objective="mean squared error for the next row per node",
        learned_graph_behavior="fixed candidate graph; no dynamic learned graph",
        candidate_mask_policy="CandidateUniverse edges constrain message passing",
        self_edge_policy="explicit message-passing self-loops are appended",
        split_policy="legacy train_normal guard; no backend window construction",
        dependency_requirements=(
            "torch==2.12.1",
            "torch-geometric==2.8.0",
        ),
        data_accessed=False,
        model_trained=False,
        created_at=CREATED_AT,
    )
    masked = GDNBackendFidelityRecordV1(
        backend_id="masked_candidate_extraction",
        backend_version="1.0",
        implementation_module="paperworks.gdn.masked",
        implementation_symbols=(
            "cosine_similarity_matrix",
            "extract_masked_topk_edges",
            "message_passing_self_loops",
        ),
        implementation_behavior_hash=MASKED_SOURCE_SHA256,
        fidelity_class=GDNFidelityClassV1.PROJECT_OWNED_EXTRACTION_COMPONENT,
        scientific_gdn_claim_allowed=False,
        production_candidate_ranking_allowed=False,
        upstream_repository="https://github.com/d-ailin/GDN",
        upstream_commit="9853899da860682669a134e4af315d036aab4eca",
        upstream_file_records=(UPSTREAM_FILES[0], UPSTREAM_FILES[1], UPSTREAM_FILES[6]),
        mapped_upstream_features=(
            "node-embedding cosine similarity",
            "per-target directed Top-K ordering",
        ),
        missing_upstream_features=(
            "GDN forecasting model",
            "embedding training",
            "custom attention graph layer",
            "anomaly scoring and checkpoint selection",
        ),
        intentional_project_deviations=(
            "CandidateUniverse mask is applied before Top-K",
            "persisted self-relations are prohibited",
            "message-passing self-loops are separate from candidate edges",
            "project-owned provenance is attached to every edge",
        ),
        input_contract="frozen embeddings plus exact CandidateUniverse",
        training_objective="none; deterministic masked extraction",
        learned_graph_behavior="masked cosine Top-K is computed from supplied embeddings",
        candidate_mask_policy="required before Top-K",
        self_edge_policy="excluded from candidate output and tracked separately",
        split_policy="legacy train_normal guard for extraction inputs",
        dependency_requirements=("standard_library_only",),
        data_accessed=False,
        model_trained=False,
        created_at=CREATED_AT,
    )
    return deterministic, torch_smoke, masked


def make_fidelity_freeze() -> GDNFidelityFreezeV1:
    return GDNFidelityFreezeV1(
        task_id="TASK-039P1D",
        status="passed_gdn_optional_import_and_fidelity_freeze",
        upstream_repository="https://github.com/d-ailin/GDN",
        upstream_commit="9853899da860682669a134e4af315d036aab4eca",
        upstream_license="MIT",
        upstream_license_blob_sha="956d782cc7291c801373a8d256135b497597e539",
        upstream_license_sha256=(
            "ffdad180c52921c5fb96b388ac08a4b5fa9e8eed6fd531969726219877a70b33"
        ),
        upstream_file_records=UPSTREAM_FILES,
        backend_records=make_fidelity_records(),
        required_rq1_fidelity_class="upstream_aligned_validated",
        production_backend_decision="pending_TASK039A_B_feasibility",
        future_backend_options=(
            "project_owned_source_aligned_minimal_GDN_port",
            "alternative_learned_graph_ranker_explicitly_named",
        ),
        data_accessed=False,
        model_trained=False,
        created_at=CREATED_AT,
    )
