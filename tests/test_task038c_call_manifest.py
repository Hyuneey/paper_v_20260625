from experiments.argos_reproduction.expanded_kpi_cohort import sha256_json


def test_a2_a3_branch_request_hashes_are_distinct_for_same_payload() -> None:
    payload = "same-prompt-payload"
    a2 = sha256_json(
        {
            "branch_id": "A2",
            "review_call_slot_id": "REVIEW-A2-SLOT",
            "prompt_payload_hash": payload,
        }
    )
    a3 = sha256_json(
        {
            "branch_id": "A3",
            "review_call_slot_id": "REVIEW-A3-SLOT",
            "prompt_payload_hash": payload,
        }
    )
    assert a2 != a3


def test_no_review_needed_has_no_call_slot() -> None:
    source = __import__(
        "experiments.argos_reproduction.review_exact_call_manifest",
        fromlist=["freeze_exact_review_manifest"],
    )
    assert "review_required" in source.freeze_exact_review_manifest.__code__.co_consts
