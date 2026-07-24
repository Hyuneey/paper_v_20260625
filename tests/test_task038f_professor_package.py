from pathlib import Path


PROFESSOR_FILES = (
    "PROTOTYPE_PROGRESS_REPORT.md",
    "PROTOTYPE_RESULT_TABLES.md",
    "PROFESSOR_DECISION_REQUEST.md",
    "ARGOS_METHOD_VALIDITY_UPDATE.md",
)


def test_professor_package_is_updated_through_task038e() -> None:
    root = Path("docs/professor_feedback")
    texts = {name: (root / name).read_text(encoding="utf-8") for name in PROFESSOR_FILES}
    joined = "\n".join(texts.values())
    assert "TASK-038E" in joined
    assert "partial_methodological_support" in joined
    assert "freeze_ARGOS_reference_track" in joined
    assert "previously exposed" in joined
    assert "sealed" in joined.lower()


def test_professor_package_contains_headline_table_and_fp_limits() -> None:
    text = Path(
        "docs/professor_feedback/PROTOTYPE_RESULT_TABLES.md"
    ).read_text(encoding="utf-8")
    assert "| LSTMADalpha | 0.3541 | 0.4884 | 0.4544 | 0.5047 | 0.4666 |" in text
    assert "| LSTMADbeta | 0.4233 | 0.3880 | 0.3895 | 0.4215 | 0.4245 |" in text
    assert "Harmful classifications | 14" in text
    assert "true-event" in (
        Path("docs/professor_feedback/ARGOS_METHOD_VALIDITY_UPDATE.md")
        .read_text(encoding="utf-8")
        .lower()
    )
