#!/usr/bin/env python3
"""Make a print PDF of a project's release package (stage 11).

Usage: python3 scripts/build_pdf.py projects/<slug>

Joins 11-release/front-matter.md, manuscript.md and back-matter.md, converts
the markdown they use (headings, paragraphs, emphasis, lists, tables, rules,
footnotes) to HTML with a small built-in converter, and prints it with
headless Google Chrome to 11-release/<slug>.pdf. The HTML is kept beside it
as 11-release/<slug>.print.html. No text is changed; only layout is added.
Needs Google Chrome in /Applications. Uses system fonts that cover polytonic
Greek (Times New Roman as the fallback).
"""
from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: 6in 9in; margin: 0.8in 0.7in 0.85in 0.7in;
  @bottom-center { content: counter(page); font: 9pt "Iowan Old Style", "Times New Roman", serif; color: #444; } }
@page :first { @bottom-center { content: none; } }
html { font-family: "Iowan Old Style", "Palatino", "Times New Roman", serif; font-size: 10.5pt; line-height: 1.42; color: #111; }
body { margin: 0; hyphens: auto; -webkit-hyphens: auto; }
.greek, :lang(grc) { font-family: "Times New Roman", "Iowan Old Style", serif; }
h1 { font-size: 17pt; font-weight: normal; margin: 0 0 1.2em; break-before: page; letter-spacing: .02em; }
h2 { font-size: 12.5pt; margin: 1.4em 0 .5em; break-after: avoid; }
h3 { font-size: 11pt; font-style: italic; font-weight: normal; margin: 1.1em 0 .4em; break-after: avoid; }
p { margin: 0 0 .6em; text-align: justify; orphans: 2; widows: 2; }
p.translation { font-style: italic; text-align: left; }
hr { border: 0; border-top: .5pt solid #999; width: 30%; margin: 1.4em auto; }
ul, ol { margin: 0 0 .6em 1.2em; padding: 0; }
li { margin: 0 0 .2em; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: .4em 0 1em; }
th, td { border-bottom: .4pt solid #bbb; padding: 2pt 4pt; text-align: left; vertical-align: top; }
th { font-weight: bold; }
code { font-family: Menlo, monospace; font-size: 8.5pt; }
sup.fn { font-size: 6.5pt; line-height: 0; }
sup.fn a { color: inherit; text-decoration: none; }
section.notes { font-size: 8.5pt; line-height: 1.3; }
section.notes h2 { font-size: 10pt; }
section.notes ol { margin-left: 1.6em; }
.titlepage { text-align: center; padding-top: 2.2in; break-after: page; hyphens: none; -webkit-hyphens: none; }
.titlepage .t { font-size: 24pt; margin-bottom: .4em; }
.titlepage .s { font-size: 12pt; font-style: italic; margin-bottom: 1.6in; }
.titlepage .a { font-size: 13pt; margin-bottom: 1.2in; }
.titlepage .n { font-size: 8.5pt; color: #444; }
.part { break-before: page; }
"""

GREEK = re.compile(r"([Ͱ-Ͽἀ-῿][Ͱ-Ͽἀ-῿̀-ͯ’ ]*[Ͱ-Ͽἀ-῿])|([Ͱ-Ͽἀ-῿])")


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[\^(\d+)\]", r'<sup class="fn"><a href="#fn\1" id="r\1">\1</a></sup>', s)
    s = GREEK.sub(lambda m: f'<span class="greek" lang="grc">{m.group(0)}</span>', s)
    return s


def convert(md: str) -> str:
    out, i = [], 0
    lines = md.split("\n")
    notes: list[tuple[str, str]] = []

    def flush_notes():
        if notes:
            out.append('<section class="notes"><ol>')
            for n, txt in notes:
                out.append(f'<li value="{n}" id="fn{n}">{inline(txt)}</li>')
            out.append("</ol></section>")
            notes.clear()

    while i < len(lines):
        line = lines[i]
        m = re.match(r"^\[\^(\d+)\]:\s*(.*)$", line)
        if m:
            notes.append((m.group(1), m.group(2)))
            i += 1
            continue
        flush_notes()
        if not line.strip():
            i += 1
            continue
        h = re.match(r"^(#{1,4})\s+(.*)$", line)
        if h:
            lvl, txt = len(h.group(1)), h.group(2)
            cls = ' class="notes"' if txt.startswith("Notes for this section") else ""
            out.append(f"<h{lvl}{cls}>{inline(txt)}</h{lvl}>")
            i += 1
            continue
        if re.match(r"^-{3,}\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>")
            out += ["<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body]
            out.append("</tbody></table>")
            continue
        lm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if lm:
            tag = "ol" if lm.group(2)[0].isdigit() else "ul"
            items: list[str] = []
            while i < len(lines):
                m2 = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                if m2:
                    items.append(m2.group(3))
                elif lines[i].startswith("  ") and lines[i].strip() and items:
                    items[-1] += " " + lines[i].strip()
                else:
                    break
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(t)}</li>" for t in items) + f"</{tag}>")
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|\||-{3,}\s*$|\s*([-*]|\d+\.)\s|\[\^\d+\]:)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        text = " ".join(para)
        cls = ' class="translation"' if re.match(r"^\d+ [A-Za-z]", text) else ""
        out.append(f"<p{cls}>{inline(text)}</p>")
    flush_notes()
    return "\n".join(out)


def title_page(front: str) -> tuple[str, str]:
    """Lift the front matter's title page into a designed page."""
    m = re.search(r"## Title page\n(.*?)\n---\n", front, re.S)
    if not m:
        return "", front
    paras = [p.strip() for p in m.group(1).split("\n\n") if p.strip()]
    t = paras[0].strip("*") if paras else ""
    s, a = (paras + ["", ""])[1:3]
    n = " ".join(paras[3:])
    page = (f'<div class="titlepage"><div class="t">{inline(t)}</div>'
            f'<div class="s">{inline(s)}</div><div class="a">{inline(a)}</div>'
            f'<div class="n">{inline(n)}</div></div>')
    rest = front[:m.start()] + front[m.end():]
    rest = re.sub(r"^# Front matter\s*\n", "", rest)
    return page, rest


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    proj = Path(sys.argv[1]).resolve()
    rel = proj / "11-release"
    front = (rel / "front-matter.md").read_text()
    manu = (rel / "manuscript.md").read_text()
    back = (rel / "back-matter.md").read_text()
    tp, front_rest = title_page(front)
    front_rest = re.sub(r"(?m)^---\s*$", "", front_rest)
    body = (tp + '<div class="part">' + convert(front_rest) + "</div>"
            + convert(re.sub(r"(?m)^---\s*$", "", manu))
            + convert(back))
    title = re.sub(r"<[^>]+>", "", tp.split("</div>")[0]) or proj.name
    doc = (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
           f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
           f"<body>{body}</body></html>")
    html_p = rel / f"{proj.name}.print.html"
    pdf_p = rel / f"{proj.name}.pdf"
    html_p.write_text(doc)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_p}", html_p.as_uri()],
                   check=True, capture_output=True)
    print(f"wrote {pdf_p} ({pdf_p.stat().st_size // 1024} KB) and {html_p.name}")


if __name__ == "__main__":
    main()
