"""Lightweight validation for the professor-facing submission package."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs" / "professor_submission_v1"
SOURCE_REPORT = ROOT / "docs" / "professor_first_results_v1" / "03_FIRST_RESULTS_REPORT.md"

EXPECTED = (
    "00_READ_ME_FIRST.md",
    "01_EXECUTIVE_SUMMARY.md",
    "02_PROFESSOR_FEEDBACK_AND_RESPONSE.md",
    "03_FIRST_RESULTS_REPORT.md",
    "03_FIRST_RESULTS_REPORT.html",
    "04_DECISIONS_REQUESTED.md",
    "05_EMAIL_DRAFT.md",
    "appendix/A_METHOD_ARCHITECTURE.md",
    "appendix/B_IMPLEMENTATION_STATUS.md",
    "appendix/C_HYPERPARAMETER_REGISTER.md",
    "appendix/D_CLAIM_MATRIX.md",
    "appendix/E_REPRODUCIBILITY_STATUS.md",
)

RESULTS = (
    "0.7857142857142857",
    "0.4939336325682589",
    "0.9285714285714286",
    "40.50255787059723",
    "0.7056194750975128",
    "6.915070855955625",
)


class SubmissionHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)


def _read(relative: str) -> str:
    return (PACKAGE / relative).read_text(encoding="utf-8")


def validate() -> None:
    missing = [name for name in EXPECTED if not (PACKAGE / name).is_file()]
    if missing:
        raise AssertionError(f"missing submission files: {missing}")

    summary = _read("01_EXECUTIVE_SUMMARY.md")
    report = _read("03_FIRST_RESULTS_REPORT.md")
    html = _read("03_FIRST_RESULTS_REPORT.html")
    decision = _read("04_DECISIONS_REQUESTED.md")
    source_report = SOURCE_REPORT.read_text(encoding="utf-8")
    combined = summary + report + html

    for value in RESULTS:
        if value not in source_report:
            raise AssertionError(f"frozen source result is absent: {value}")
        if value not in summary or value not in report or value not in html:
            raise AssertionError(f"frozen result is inconsistent: {value}")

    required_claims = (
        "RULE_SIGNAL_PRESENT_BUT_CURRENT_FUSION_UTILITY_UNSUPPORTED",
        "PROVISIONAL_PENDING_PROFESSOR_APPROVAL",
        "42",
        "TSFM",
        "ARTIST",
        "INNER",
    )
    for claim in required_claims:
        if claim not in combined:
            raise AssertionError(f"required scope statement absent: {claim}")

    if len(re.findall(r"^## Decision [1-4] ", decision, flags=re.MULTILINE)) != 4:
        raise AssertionError("decision page must contain exactly four primary decisions")
    if "## Decision 5" in decision:
        raise AssertionError("decision page contains an unauthorized fifth decision")

    outer_boundaries = (
        "과학 결과를 만들지 못했습니다",
        "현재 실증 주장은 INNER 평가로 제한됩니다",
        "부정적 OUTER 과학 결과가 아닙니다",
    )
    for statement in outer_boundaries:
        if statement not in report:
            raise AssertionError(f"OUTER boundary missing: {statement}")

    if "통계적 우월성" not in report or "주장하지" not in report:
        raise AssertionError("small-event-count limitation is missing")
    if "root cause를 증명하지" not in report:
        raise AssertionError("causal claim boundary is missing")

    parser = SubmissionHTMLParser()
    parser.feed(html)
    parser.close()
    for required_tag in ("html", "head", "body", "main", "table"):
        if required_tag not in parser.tags:
            raise AssertionError(f"HTML structure missing: {required_tag}")
    if "<meta name=\"viewport\"" not in html or "@media print" not in html:
        raise AssertionError("HTML screen/print rendering support is incomplete")

    markdown_link = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in PACKAGE.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in markdown_link.findall(text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists():
                raise AssertionError(f"broken local link in {path.relative_to(PACKAGE)}")

    forbidden_tokens = (
        "C:\\Users\\",
        "/home/",
        "file://",
        "label-test1.csv",
        "label-test2.csv",
        "TASK-039",
    )
    long_hash = re.compile(r"\b[0-9a-f]{40,64}\b")
    for path in PACKAGE.rglob("*"):
        if path.suffix.lower() not in {".md", ".html"}:
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden_tokens):
            raise AssertionError(f"internal/private token found in {path.relative_to(PACKAGE)}")
        if long_hash.search(text):
            raise AssertionError(f"long internal hash found in {path.relative_to(PACKAGE)}")

    if "TSFM은 현재 사용하지 않았" not in report:
        raise AssertionError("TSFM implementation gap is not explicit")
    if "ARTIST식 세그먼트 선택도 구현하지" not in report:
        raise AssertionError("ARTIST implementation gap is not explicit")
    if "current fusion utility" in report.lower():
        raise AssertionError("unexpected English fallback in Korean conclusion")


if __name__ == "__main__":
    validate()
    print("professor_submission_v1: PASS")
