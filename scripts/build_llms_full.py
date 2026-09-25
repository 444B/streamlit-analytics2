"""Concatenate docs/ into llms-full.txt for AI retrieval.

uv run python scripts/build_llms_full.py          # write
uv run python scripts/build_llms_full.py --check  # fail if stale (CI)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDER = [
    "README.md",
    "getting-started.md",
    "api.md",
    "dashboard.md",
    "storage.md",
    "events.md",
    "custom-events.md",
    "query.md",
    "privacy.md",
    "multipage.md",
    "deployment.md",
    "firestore.md",
    "faq.md",
    "upgrading.md",
    "for-ai-agents.md",
]


def build() -> str:
    parts = [
        "# streamlit-analytics2: full documentation\n\n"
        "Privacy-first usage analytics for Streamlit apps. This file is every "
        "page of docs/ concatenated for retrieval by AI assistants. Source: "
        "https://github.com/444B/streamlit-analytics2/tree/main/docs\n"
    ]
    for name in ORDER:
        text = (ROOT / "docs" / name).read_text(encoding="utf-8").strip()
        parts.append(f"\n\n---\n\n<!-- docs/{name} -->\n\n{text}\n")
    return "".join(parts)


def main() -> int:
    out = ROOT / "llms-full.txt"
    content = build()
    if "--check" in sys.argv:
        if not out.exists() or out.read_text(encoding="utf-8") != content:
            print("llms-full.txt is stale: run scripts/build_llms_full.py")
            return 1
        print("llms-full.txt is up to date")
        return 0
    out.write_text(content, encoding="utf-8")
    print(f"wrote {out} ({len(content)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
