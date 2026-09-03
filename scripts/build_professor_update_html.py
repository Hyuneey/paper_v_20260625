#!/usr/bin/env python3
"""Build the public professor-update HTML from the 13 Markdown source files."""
from __future__ import annotations
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "docs" / "professor_experiment_update_v2"
SOURCES = sorted(DIRECTORY.glob("[0-9][0-9]_*.md"))
OUTPUT = DIRECTORY / "PROFESSOR_EXPERIMENT_UPDATE_V2.html"

def main() -> int:
    if len(SOURCES) != 13:
        raise SystemExit(f"expected 13 Markdown sources, found {len(SOURCES)}")
    sections = []
    navigation = []
    for index, path in enumerate(SOURCES, 1):
        text = path.read_text(encoding="utf-8")
        title = next((line[2:] for line in text.splitlines() if line.startswith("# ")), path.stem)
        anchor = f"section-{index:02d}"
        navigation.append(f'<li><a href="#{anchor}">{html.escape(title)}</a></li>')
        sections.append(f'<section id="{anchor}"><h2>{html.escape(title)}</h2><pre>{html.escape(text)}</pre></section>')
    document = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VALIDATION V2 교수님 실험 업데이트</title><style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif;max-width:1100px;margin:auto;padding:32px;color:#18212f;line-height:1.6}}
nav,section{{border:1px solid #d9e0e8;border-radius:10px;padding:20px;margin:18px 0;background:#fff}}body{{background:#f5f7fa}}
pre{{white-space:pre-wrap;font:inherit}}a{{color:#155eef}}.warning{{border-left:5px solid #d97706;padding:12px;background:#fff7ed}}
@media print{{nav{{display:none}}body{{background:white}}section{{break-inside:avoid;border-color:#bbb}}}}
</style></head><body><h1>VALIDATION V2 교수님 실험 업데이트</h1>
<p class="warning">test1 DEVELOPMENT_ONLY 결과입니다. held-out 일반화와 human usefulness는 미확인입니다. 이메일은 전송하지 않았습니다.</p>
<nav aria-label="목차"><h2>목차</h2><ol>{''.join(navigation)}</ol></nav>{''.join(sections)}</body></html>"""
    OUTPUT.write_text(document, encoding="utf-8", newline="\n")
    print(OUTPUT.relative_to(ROOT).as_posix())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
