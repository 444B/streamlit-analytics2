"""Mirror docs/ into a checkout of the GitHub wiki.

    uv run python scripts/sync_wiki.py ../streamlit-analytics2.wiki

Page names are Title-Case with hyphens (what GitHub wiki uses in URLs), links
between docs pages are rewritten to wiki links, and Home.md is generated from
docs/README.md. Commit and push the wiki checkout afterwards.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def page_name(doc: str) -> str:
    stem = Path(doc).stem
    if stem == "README":
        return "Home"
    return "-".join(
        w.capitalize() if i == 0 else w for i, w in enumerate(stem.split("-"))
    )


def rewrite(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        target, anchor = m.group(2), m.group(3) or ""
        return f"{m.group(1)}({page_name(target)}{anchor})"

    text = re.sub(r"(\[[^\]]*\])\(([a-z0-9-]+\.md)(#[^)]*)?\)", repl, text)
    text = text.replace(
        "(../llms.txt)",
        "(https://github.com/444B/streamlit-analytics2/blob/main/llms.txt)",
    )
    text = text.replace(
        "(../llms-full.txt)",
        "(https://raw.githubusercontent.com/444B/streamlit-analytics2/main/llms-full.txt)",
    )
    return text


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    if not (wiki / ".git").exists():
        print(f"{wiki} is not a git checkout of the wiki")
        return 2
    for old in wiki.glob("*.md"):
        old.unlink()
    for doc in sorted(DOCS.glob("*.md")):
        out = wiki / f"{page_name(doc.name)}.md"
        body = rewrite(doc.read_text(encoding="utf-8"))
        note = (
            "<!-- Generated from docs/%s in the main repository by scripts/sync_wiki.py. "
            "Edit there, not here. -->\n\n" % doc.name
        )
        out.write_text(note + body, encoding="utf-8")
        print("wrote", out.name)
    sidebar = ["**Docs**", ""]
    for doc in sorted(DOCS.glob("*.md")):
        if doc.name == "README.md":
            continue
        name = page_name(doc.name)
        sidebar.append(f"- [[{name.replace('-', ' ')}|{name}]]")
    (wiki / "_Sidebar.md").write_text("\n".join(sidebar) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
