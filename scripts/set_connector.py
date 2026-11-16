#!/usr/bin/env python3
"""Point the pipeline at a different Aquifer connector.

Usage: python3 scripts/set_connector.py <new-connector-id>
       python3 scripts/set_connector.py            (shows the current id)

Agents can only use the Aquifer tools their `tools` line names, and each tool
name carries the connector's id: mcp__<id>__get_words and so on. The id
differs between Claude accounts and between ways of adding Aquifer (as a
claude.ai connector it is a long code; added with `claude mcp add ... aquifer`
it is `aquifer`). This script replaces the id everywhere the project names
it: .claude/agents/*.md, .claude/settings.json, CLAUDE.md and README.md.

To find your id, ask a Claude Code session in this folder to list its Aquifer
tool names, or run /mcp in a terminal session: the id is the part between
"mcp__" and "__get_bible_text".
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = re.compile(r"mcp__([A-Za-z0-9_.-]+?)__(?:get_bible_text|get_words|study_passage|get_article|"
                  r"search_articles|get_entity|list_entities|book_overview|chapter_overview|"
                  r"list_resources|list_languages|<tool>|\*)")


def files():
    yield from sorted((ROOT / ".claude/agents").glob("*.md"))
    for name in (".claude/settings.json", "CLAUDE.md", "README.md"):
        if (ROOT / name).exists():
            yield ROOT / name


def main():
    found = {}
    for f in files():
        for cid in TOOL.findall(f.read_text()):
            found.setdefault(cid, set()).add(f.relative_to(ROOT).as_posix())
    if len(sys.argv) == 1:
        for cid, where in found.items():
            print(f"{cid}: {len(where)} files")
        if len(found) > 1:
            print("More than one id is in use; run this script with the right one.")
        return
    if len(sys.argv) != 2 or not re.fullmatch(r"[A-Za-z0-9_.-]+", sys.argv[1]):
        sys.exit(__doc__)
    new = sys.argv[1].removeprefix("mcp__") if hasattr(str, "removeprefix") else sys.argv[1]
    changed = 0
    for f in files():
        text = f.read_text()
        out = text
        for cid in found:
            if cid != new:
                out = out.replace(f"mcp__{cid}__", f"mcp__{new}__")
                out = out.replace(f'"mcp__{cid}"', f'"mcp__{new}"')
        if out != text:
            f.write_text(out)
            changed += 1
            print(f"updated {f.relative_to(ROOT)}")
    print(f"{changed} files updated; connector id is now {new}." if changed
          else f"Nothing to change; the id is already {new}.")
    print("Start a new Claude Code session so the agents load their new tool names.")


if __name__ == "__main__":
    main()
