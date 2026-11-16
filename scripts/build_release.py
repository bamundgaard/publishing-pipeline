#!/usr/bin/env python3
"""Deterministic part of stage 11 (production): turn signed units into the
release text and the provisional JSON.

Usage: python3 scripts/build_release.py projects/<slug>

Reads the unit files listed, one path per line, in
projects/<slug>/10-signoff/signed-units.txt (the managing editor writes it at
Gate 5). For each unit it:
  - converts card links to numbered notes (Chicago short form: source, ref),
  - drops ledger links, charter links and [BT] (the author's own positions and
    the base text need no note; the front matter names the base text),
  - collects verse milestones, Greek and Hebrew terms with their glosses,
    Scripture references and cross-references.
Book details (title, author, base translation, license, disclosure ...) come
from the labelled lines in the charter's "Book details" block; a label the
charter lacks is written as "not stated in charter". A unit's reference comes
from its title line, in USFM ("PHM 1:4-7", "GEN 1:1-2:3").
Writes 11-release/manuscript.md and 11-release/release.json, and prints a
proof summary. It never edits the inputs. The production-editor agent adds
the bibliography, indexes, front and back matter, and checks the proof.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify_unit import links_in, newest, parse_cards  # noqa: E402

SCHEMA = "pipeline-release/0.2-provisional"
GREEK_CH = "\u0370-\u03FF\u1F00-\u1FFF\u0300-\u036F"
HEBREW_CH = "\u0591-\u05F4\uFB1D-\uFB4F"
TERM = rf"(?:[{GREEK_CH}]+(?:\s+[{GREEK_CH}]+)*|[{HEBREW_CH}]+(?:[\s\u05BE]+[{HEBREW_CH}]+)*)"

# USFM code: (OSIS code, English name)
BOOK_TABLE = {
    "GEN": ("Gen", "Genesis"), "EXO": ("Exod", "Exodus"), "LEV": ("Lev", "Leviticus"),
    "NUM": ("Num", "Numbers"), "DEU": ("Deut", "Deuteronomy"), "JOS": ("Josh", "Joshua"),
    "JDG": ("Judg", "Judges"), "RUT": ("Ruth", "Ruth"), "1SA": ("1Sam", "1 Samuel"),
    "2SA": ("2Sam", "2 Samuel"), "1KI": ("1Kgs", "1 Kings"), "2KI": ("2Kgs", "2 Kings"),
    "1CH": ("1Chr", "1 Chronicles"), "2CH": ("2Chr", "2 Chronicles"), "EZR": ("Ezra", "Ezra"),
    "NEH": ("Neh", "Nehemiah"), "EST": ("Esth", "Esther"), "JOB": ("Job", "Job"),
    "PSA": ("Ps", "Psalms"), "PRO": ("Prov", "Proverbs"), "ECC": ("Eccl", "Ecclesiastes"),
    "SNG": ("Song", "Song of Songs"), "ISA": ("Isa", "Isaiah"), "JER": ("Jer", "Jeremiah"),
    "LAM": ("Lam", "Lamentations"), "EZK": ("Ezek", "Ezekiel"), "DAN": ("Dan", "Daniel"),
    "HOS": ("Hos", "Hosea"), "JOL": ("Joel", "Joel"), "AMO": ("Amos", "Amos"),
    "OBA": ("Obad", "Obadiah"), "JON": ("Jonah", "Jonah"), "MIC": ("Mic", "Micah"),
    "NAM": ("Nah", "Nahum"), "HAB": ("Hab", "Habakkuk"), "ZEP": ("Zeph", "Zephaniah"),
    "HAG": ("Hag", "Haggai"), "ZEC": ("Zech", "Zechariah"), "MAL": ("Mal", "Malachi"),
    "MAT": ("Matt", "Matthew"), "MRK": ("Mark", "Mark"), "LUK": ("Luke", "Luke"),
    "JHN": ("John", "John"), "ACT": ("Acts", "Acts"), "ROM": ("Rom", "Romans"),
    "1CO": ("1Cor", "1 Corinthians"), "2CO": ("2Cor", "2 Corinthians"),
    "GAL": ("Gal", "Galatians"), "EPH": ("Eph", "Ephesians"), "PHP": ("Phil", "Philippians"),
    "COL": ("Col", "Colossians"), "1TH": ("1Thess", "1 Thessalonians"),
    "2TH": ("2Thess", "2 Thessalonians"), "1TI": ("1Tim", "1 Timothy"),
    "2TI": ("2Tim", "2 Timothy"), "TIT": ("Titus", "Titus"), "PHM": ("Phlm", "Philemon"),
    "HEB": ("Heb", "Hebrews"), "JAS": ("Jas", "James"), "1PE": ("1Pet", "1 Peter"),
    "2PE": ("2Pet", "2 Peter"), "1JN": ("1John", "1 John"), "2JN": ("2John", "2 John"),
    "3JN": ("3John", "3 John"), "JUD": ("Jude", "Jude"), "REV": ("Rev", "Revelation"),
}
BOOKS = "|".join(sorted((re.escape(n) for _, n in BOOK_TABLE.values()), key=len, reverse=True))
NOT_STATED = "not stated in charter"


def charter_field(charter: str, *labels: str):
    """Value of a labelled charter line, "- **Label:** value" (bold optional).
    A value runs on over following lines until a blank line, bullet or heading.
    Surrounding quotation marks are removed. None if no label is found."""
    for label in labels:
        m = re.search(rf"^[ \t]*[-*]?[ \t]*\**{re.escape(label)}:\**[ \t]*(.*)$", charter, re.M | re.I)
        if not m:
            continue
        lines = [m.group(1)]
        for nxt in charter[m.end():].split("\n")[1:]:
            if not nxt.strip() or re.match(r"\s*([-*]|#|\|)", nxt):
                break
            lines.append(nxt.strip())
        value = " ".join(l.strip() for l in lines).strip()
        quoted = re.match(r'^["“](.*)["”]\.?$', value)
        if quoted:
            value = quoted.group(1).strip()  # quoted wording is kept verbatim
        else:
            value = re.sub(r"(?<!\.)\.$", "", value)  # a trailing full stop, not "..."
        if value and not value.startswith("<"):  # "<...>" is an unfilled template slot
            return value
    return None


def unit_ref(title: str):
    """USFM reference in a unit title: "PHM 1:4-7", "GEN 1:1-2:3", "PSA 23"."""
    m = re.search(r"\b([1-3]?[A-Z]{2,3})\s+(\d+)(?::(\d+))?(?:[–-](?:(\d+):)?(\d+))?", title)
    if not m or m.group(1) not in BOOK_TABLE:
        return None
    book, ch, a, ch2, b = m.groups()
    osis_b = BOOK_TABLE[book][0]
    ch = int(ch)
    if a is None:  # whole chapter(s)
        end_ch = int(b) if b else ch
        return {"book": book, "chapter": ch, "start": None, "end": None,
                "osis": f"{osis_b}.{ch}" + (f"-{osis_b}.{end_ch}" if end_ch != ch else "")}
    a = int(a)
    end_ch = int(ch2) if ch2 else ch
    end = int(b) if b else a
    return {"book": book, "chapter": ch, "start": a, "end": end, "end_chapter": end_ch,
            "osis": f"{osis_b}.{ch}.{a}" + (f"-{osis_b}.{end_ch}.{end}"
                                             if (end_ch, end) != (ch, a) else "")}


def note_text(card: dict) -> str:
    """Chicago short note from a card: source name, then its locator (resource
    code, article id, title or tool call), without the excerpt."""
    head = card["ref"].split('"')[0].split("“")[0]
    head = re.sub(r"\((?:re-run|rows)[^)]*\)", "", head)
    parts = [p.strip(" .;:") for p in re.split(r"\s*\|\s*|,\s+|\.\s+", head)]
    seen, keep = {card["source"].lower()}, [card["source"]]
    for p in parts:
        if p and p.lower() not in seen and not p.lower().startswith(("rows ", "sc-")):
            keep.append(p)
            seen.add(p.lower())
    return ", ".join(keep)


def convert(par: str, cards: dict, notes: list, unit: str):
    """Replace claim links in one paragraph; return new text and note ids."""
    out, last, ids = [], 0, []
    for (a, b), toks in links_in(par):
        out.append(par[last:a].rstrip())
        card_toks = [t for t in toks if t.startswith("SC-")]
        if card_toks:
            n = len(notes) + 1
            parts = []
            for c in card_toks:
                card = cards.get(c)
                parts.append(note_text(card) if card else f"{c} (card not found)")
            notes.append({"n": n, "unit": unit, "cards": card_toks,
                          "text": "; ".join(parts) + "."})
            out.append(f"[^{n}]")
            ids.append(n)
        last = b
    out.append(par[last:])
    # Only the space a removed link leaves before punctuation is closed up;
    # the signed text is never otherwise touched (e.g. "in ... Christ").
    return "".join(out), ids


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    proj = Path(sys.argv[1])
    listing = proj / "10-signoff/signed-units.txt"
    if not listing.exists():
        sys.exit(f"missing {listing}")
    unit_files = [proj / l.strip() for l in listing.read_text().split("\n") if l.strip()]
    charter = (proj / "01-charter/charter.md").read_text()
    title_m = re.search(r"^#\s*Project Charter:\s*(.+)$", charter, re.M)

    def field(*labels):
        return charter_field(charter, *labels) or NOT_STATED

    work = {
        "title": charter_field(charter, "Title") or (title_m.group(1).strip() if title_m else NOT_STATED),
        "author": field("Author"),
        "genre": field("Genre"),
        "base_translation": field("Base translation"),
        "original_language_text": field("Original-language text", "Greek text", "Hebrew text"),
        "citation_style": field("Citation style"),
        "license": field("Output license"),
        "source_license_terms": field("Source license terms"),
        "disclosure": charter_field(charter, "Disclosure statement"),
        "built": date.today().isoformat(),
    }
    missing_fields = [k for k, v in work.items() if v in (NOT_STATED, None)]
    release = {
        "schema": SCHEMA,
        "status": "provisional: the downstream platform's data requirements are not yet known",
        "work": work,
        "units": [], "notes": [], "bibliography": [], "indexes": {},
        "errata": {"policy": field("Release and errata plan"), "entries": []},
    }
    md, notes, problems = [], [], []
    for f in unit_files:
        text = f.read_text()
        unit = re.match(r"#\s*(U\d+)", text).group(1)
        dossier = newest(proj / "04-dossiers", unit)
        cards = parse_cards(dossier.read_text())
        title = text.split("\n", 1)[0].lstrip("# ").strip()
        q = re.search(r"^Question:\s*(.+)$", text, re.M)
        ref = unit_ref(title)
        osis_b = BOOK_TABLE[ref["book"]][0] if ref else None
        name_b = BOOK_TABLE[ref["book"]][1] if ref else None
        u = {"id": unit, "title": title, "reference": ref,
             "question": q.group(1).strip() if q else None,
             "source_file": str(f.relative_to(proj)), "sections": [],
             "verse_milestones": [], "language_terms": [], "scripture_refs": [],
             "cross_links": []}
        if not ref:
            problems.append(f"{unit}: no USFM reference in the title line; "
                            "verse milestones and v./vv. references skipped")
        headings = [h[3:].strip() for h in re.findall(r"^## .+$", text, re.M)]
        see_heads = "|".join(re.escape(h) for h in headings) or "(?!)"
        md.append(f"# {title}\n")
        for part in re.split(r"\n(?=## )", text)[1:]:
            head, _, body = part.partition("\n")
            sec = {"type": head[3:].strip().lower(), "heading": head[3:].strip(),
                   "paragraphs": []}
            md.append(head + "\n")
            for par in [p for p in re.split(r"\n\s*\n", body) if p.strip()]:
                if par.lstrip().startswith("#"):
                    md.append(par.strip() + "\n")
                    sec["paragraphs"].append({"subheading": par.strip().lstrip("# ")})
                    continue
                new, ids = convert(par.strip(), cards, notes, unit)
                pi = len(sec["paragraphs"])
                if ref:
                    # Verse labels such as "**4 ..." or "**vv. 4" at a
                    # paragraph's start; in a translation, every verse number.
                    verses = [int(v) for v in re.findall(r"^\*\*(?:vv?\. )?(\d+)\b", new)]
                    if sec["type"] == "translation":
                        verses = [int(v) for v in re.findall(r"(?:^|\s)(\d{1,3}) (?=\S)(?!\d)", new)]
                    for v in verses:
                        u["verse_milestones"].append({"osis": f"{osis_b}.{ref['chapter']}.{v}",
                                                      "section": sec["type"],
                                                      "paragraph": pi})
                for m in re.finditer(rf"({TERM})\s*\(\s*[\"“]([^\"”]+)[\"”]\s*\)", new):
                    form = m.group(1)
                    script = "hebrew" if re.search(f"[{HEBREW_CH}]", form) else "greek"
                    u["language_terms"].append({"form": form, "script": script,
                                                "gloss": m.group(2),
                                                "section": sec["type"], "paragraph": pi})
                for m in re.finditer(rf"\b({BOOKS})\s+(\d+):(\d+)(?:[–-](\d+))?", new):
                    u["scripture_refs"].append(m.group(0))
                if ref:
                    for m in re.finditer(r"\bvv?\. \d+(?:[a-z])?(?:\s*[–-]\s*\d+|(?:,\s*(?:and\s+)?\d+)+|\s+and\s+\d+)?", new):
                        verses = re.sub(r"^vv?\.\s*", "", m.group(0))
                        u["scripture_refs"].append(f"{name_b} {ref['chapter']}:{verses}")
                for m in re.finditer(rf"\b(U\d{{2,3}})\b|\b[Ss]ee (?:the )?(?:{see_heads}) on vv?\. \d+", new):
                    u["cross_links"].append(m.group(0))
                if re.search(r"\[(?:SC-|U\d+-D|S\d|X\d|BT|Charter)", new):
                    problems.append(f"{unit}: claim link left in text: {new[:80]}")
                sec["paragraphs"].append({"text": new, "notes": ids})
                md.append(new + "\n")
            u["sections"].append(sec)
        unote = [n for n in notes if n["unit"] == unit]
        if unote:
            md.append("## Notes for this section\n")
            md += [f"[^{n['n']}]: {n['text']}" for n in unote]
            md.append("")
        md.append("---\n")
        u["scripture_refs"] = sorted(set(u["scripture_refs"]))
        u["cross_links"] = sorted(set(u["cross_links"]))
        release["units"].append(u)
    release["notes"] = notes
    out = proj / "11-release"
    out.mkdir(exist_ok=True)
    (out / "manuscript.md").write_text("\n".join(md))
    (out / "release.json").write_text(json.dumps(release, ensure_ascii=False, indent=2))
    missing = [n for n in notes if "card not found" in n["text"]]
    print(f"# build_release proof summary\nunits: {len(release['units'])} · notes: {len(notes)}"
          f" · Greek/Hebrew terms: {sum(len(u['language_terms']) for u in release['units'])}"
          f" · verse milestones: {sum(len(u['verse_milestones']) for u in release['units'])}")
    print("notes with missing cards: " + (", ".join(str(n['n']) for n in missing) or "none"))
    print("charter fields not stated: " + (", ".join(missing_fields) or "none"))
    print("problems: " + ("\n- " + "\n- ".join(problems) if problems else "none"))


if __name__ == "__main__":
    main()
