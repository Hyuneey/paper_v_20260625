"""Small public-document validator for the professor first-results package."""

from __future__ import annotations

import csv
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs" / "professor_first_results_v1"

EXPECTED = (
    "01_ONE_PAGE_EXECUTIVE_SUMMARY.md",
    "02_PROFESSOR_FEEDBACK_RESPONSE_MATRIX.md",
    "03_FIRST_RESULTS_REPORT.md",
    "03_FIRST_RESULTS_REPORT.html",
    "04_METHOD_AND_CODE_ARCHITECTURE.md",
    "05_IMPLEMENTATION_STATUS_MATRIX.md",
    "06_HYPERPARAMETER_PROVENANCE_REGISTER.md",
    "06_HYPERPARAMETER_PROVENANCE_REGISTER.csv",
    "07_CLAIM_MATRIX.md",
    "08_REPRODUCIBILITY_AND_CODE_STATUS.md",
    "09_PROFESSOR_DECISION_AGENDA.md",
    "10_PROFESSOR_EMAIL_DRAFT.md",
    "11_MEETING_SLIDE_OUTLINE.md",
    "12_POST_MEETING_OPTIONS.md",
)

FROZEN_VALUES = (
    "0.7857142857142857",
    "0.4939336325682589",
    "0.9285714285714286",
    "40.50255787059723",
    "0.7056194750975128",
    "6.915070855955625",
    "RULE_SIGNAL_PRESENT_BUT_CURRENT_FUSION_UTILITY_UNSUPPORTED",
)


class StrictHTML(HTMLParser):
    def error(self, message: str) -> None:  # pragma: no cover - API hook
        raise ValueError(message)


def validate() -> None:
    missing = [name for name in EXPECTED if not (PACKAGE / name).is_file()]
    if missing:
        raise AssertionError(f"missing professor files: {missing}")

    report = (PACKAGE / "03_FIRST_RESULTS_REPORT.md").read_text(encoding="utf-8")
    for value in FROZEN_VALUES:
        if value not in report:
            raise AssertionError(f"frozen value absent from report: {value}")
    for required_gap in ("TSFM", "ARTIST", "일반화는 **unconfirmed**"):
        if required_gap not in report:
            raise AssertionError(f"scope gap absent: {required_gap}")

    with (PACKAGE / "06_HYPERPARAMETER_PROVENANCE_REGISTER.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 16 or len({row["parameter"] for row in rows}) != len(rows):
        raise AssertionError("hyperparameter CSV is incomplete or duplicated")

    html = (PACKAGE / "03_FIRST_RESULTS_REPORT.html").read_text(encoding="utf-8")
    parser = StrictHTML()
    parser.feed(html)
    parser.close()
    if "test2 access 0" not in html or "THESIS_FIRST_PENDING_PROFESSOR_FEEDBACK" not in html:
        raise AssertionError("HTML status boundary is incomplete")

    markdown_link = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in PACKAGE.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in markdown_link.findall(text):
            if target.startswith(("http://", "https://", "#")):
                continue
            link_path = (path.parent / target.split("#", 1)[0]).resolve()
            if not link_path.exists():
                raise AssertionError(f"broken local link in {path.name}: {target}")

    forbidden = ("C:\\Users\\", "/home/", "file://", "label-test2.csv")
    for path in PACKAGE.iterdir():
        if path.suffix.lower() not in {".md", ".html", ".csv"}:
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            raise AssertionError(f"private/local token found in {path.name}")


if __name__ == "__main__":
    validate()
    print("professor_first_results_v1: PASS")
