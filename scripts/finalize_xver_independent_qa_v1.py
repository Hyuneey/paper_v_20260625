"""Record the independent public-only QA after all external normal authorities exist."""

from xver_execution_common import PUB, document
from paperworks.validation_v2.exp03b_custody_v1 import publish, seal


RESULT_HASH = "1646bc0cbf21a3011566f8a8690e888ba062274ca7893a17e6521df52b708e1e"
PRIVATE_INDEX_HASH = "a0b5b51f12b1b8902f67be8b6956d5d01dbc50a04dc99d227be5ffb150df84be"
RESULT_COMMIT = "449e263ef12010163a4b8718f7182c9d9cd18b8c"


def main() -> None:
    result = document(PUB / "NORMAL_EXECUTION_RESULT_V1.json")
    index = document(PUB / "PUBLIC_PRIVATE_EXECUTION_INDEX_V2.json")
    hai22 = document(PUB / "HAI22_INDEPENDENT_SUBQA_V1.json")
    hai21 = document(PUB / "HAI21_INDEPENDENT_SUBQA_V1.json")
    if result["self_hash"] != RESULT_HASH or index["self_hash"] != PRIVATE_INDEX_HASH:
        raise SystemExit("BLOCKED_INDEPENDENT_QA_AUTHORITY_MISMATCH")
    if any(item["status"] != "PASS" for item in (hai22, hai21)):
        raise SystemExit("BLOCKED_VERSION_SUBQA")
    qa = seal(
        {
            "schema": "xver_independent_execution_qa_v1",
            "status": "PASS",
            "scope": "SCOPED_NORMAL_ONLY_PREPARATION",
            "result_authority_hash": RESULT_HASH,
            "private_index_hash": PRIVATE_INDEX_HASH,
            "result_source_commit": RESULT_COMMIT,
            "version_subQA_hashes": {
                "22.04": hai22["self_hash"],
                "21.03": hai21["self_hash"],
            },
            "public_self_hashes_replayed": 49,
            "scientific_GDN_runs": 12,
            "global_event_roles_separated": True,
            "global_event_fusion": False,
            "best_seed_selection": False,
            "frozen_stage_a_hashes": {
                "V2A": "ec0b3e2a32d457287cb8b101bec39059e99335be3fd85a3d1fb98668224c52aa",
                "T0": "d95c0bb8234304f2b769e088f4399b6c071b2156982c9e1fadd175dbab5dba02",
                "T2": "bc2b5996989228f198dbcbf38cbedaf38516366f55d5011978ecda94ccf699b6",
            },
            "pilot_v1_preservation": {"passed": 3021, "total": 3021},
            "test_results": {
                "focused_reporting": {"passed": 43, "failed": 0},
                "validation_v2": {"passed": 458, "skipped": 14, "failed": 0},
                "exp03b": {"passed": 95, "failed": 0},
                "RCC_UI": {"passed": 218, "failed": 0},
                "eTaPR_conformance_cases": {"passed": 109, "failed": 0},
            },
            "unresolved_pre_DG05_metrics": [
                "MULTI_FILE_AGGREGATION",
                "EMPTY_INPUT_CONVENTION",
                "SECONDARY_P1_INTERPRETATION",
            ],
            "historical_unrelated_failure": "CUDA exact dependency string 2.12.1 versus 2.12.1+cu130",
            "safety": {
                "test1_reopened": 0,
                "test2_accesses": 0,
                "external_attack_accesses": 0,
                "attack_label_accesses": 0,
                "excluded_normal_label_values_parsed": 0,
                "provider_calls": 0,
                "credential_reads": 0,
                "private_exposures": 0,
                "frozen_scientific_path_changes": 0,
            },
            "gates": {
                "DG_XVER_PROVIDER": "USER_DECISION_REQUIRED",
                "DG05": "NOT_APPROVED",
                "professor_package": "NOT_SUBMITTED",
            },
            "limitations": [
                "Independent QA replayed public receipts and hashes; it did not deserialize private numeric evidence or model tensors.",
                "Normal-only preparation is not attack utility, held-out generalization, production readiness, or causal evidence.",
            ],
        }
    )
    publish(PUB / "INDEPENDENT_EXECUTION_QA_V1.json", qa)
    print("XVER_INDEPENDENT_EXECUTION_QA_PASS")


if __name__ == "__main__":
    main()
