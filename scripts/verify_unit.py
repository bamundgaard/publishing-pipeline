#!/usr/bin/env python3
"""Deterministic checks for one drafted unit (stage 8, verification desk).

Usage: python3 scripts/verify_unit.py projects/<slug> <unit-id> [path/to/text.md]

With no third argument it checks the newest draft in 05-drafts/. The
copyeditor passes its own file (for example 09-copyedit/U01.md) to confirm
that copyediting broke no link, quotation or count.

Reads only project files, prints a markdown report to stdout, and writes
nothing. The verification-desk agent runs it first and reports its results;
the checks that need judgment or source lookups (claim support, attribution,
quotations against the full source, Greek against the dataset) are the
agent's.

Checks:
  1. Word count, words only, against the plan's budget. The sections that
     count come from the style sheet's "Word counts" section: a line
     "Counted sections: A, B, C" (or the sentence "Count the A, B and C
     sections"). If it names none, every section counts and the report says so.
  2. Claim links resolve: card ids to the newest dossier, ledger ids to
     decision-ledger.md headings whose "Ruling:" line is filled in (a link to
     a question still OPEN or deferred fails). [BT] and [Charter: ...] are
     listed. If the dossier's source cards can't be read at all, that fails.
  3. Editorial markers left in the text ([OPEN CRUX], [NEEDS SOURCE], ...).
  4. Every quotation in the prose appears verbatim in a card the same
     paragraph links to (or in the base text, for [BT]).
  8. The author's own sections (a line "[AUTHOR-WRITTEN]" or
     "[AUTHOR-DICTATED]" under the section heading): their length and how
     many sentences carry no link, as notes. Sentences there are the
     author's own claims and need no link, so check 7 skips them; links and
     quotations the author did use are still checked in 2 and 4.
  Checks 2 to 6 read every section of the unit; check 7 reads only the
  counted sections, where every factual sentence needs a link.
  5. Every cited card's source is in the corpus register.
  6. Words quoted per source, for the register's quotation limits.
  7. Sentences with no claim link, for the agent to judge (transitions and
     structure need none).
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

LINK_TOKEN = re.compile(
    r"^(SC-U\d+-\d+|BT|[A-Z]\d+|U\d+-D\d+|D: .+|Charter: .+)$")
# Ledger rulings are headings "## X1. ..." or "### U02-D1. ..." (2 to 4 #).
LEDGER_ID = re.compile(r"^#{2,4}\s+([A-Z]\d+|U\d+-D\d+)\.", re.M)


def newest(folder: Path, stem: str, suffix: str = ".md") -> Path | None:
    """Newest version of <stem>.md / <stem>.vN.md (not notes or memos)."""
    best, best_n = None, 0
    for p in folder.glob(f"{stem}*{suffix}"):
        m = re.fullmatch(re.escape(stem) + r"(?:\.v(\d+))?" + re.escape(suffix), p.name)
        if m:
            n = int(m.group(1) or 1)
            if n >= best_n:
                best, best_n = p, n
    return best


AUTHOR_MARK = re.compile(r"^[ \t]*\[AUTHOR-(WRITTEN|DICTATED)\][ \t]*$", re.M)
WAITING = r"\[(?:AWAITING AUTHOR|HUMAN-WRITTEN|HUMAN-DICTATED)[^\]]*\]"


def author_mode(body: str):
    """"written" or "dictated" if the section's first line is the author's
    marker, else None."""
    first = next((l for l in body.split("\n") if l.strip()), "")
    m = AUTHOR_MARK.match(first)
    return m.group(1).lower() if m else None


def counted_sections(style: str) -> list[str] | None:
    """Section names the style sheet says count toward the budget."""
    m = re.search(r"\n#+ *Word counts?[^\n]*\n(.*?)(?=\n#+ |\Z)", "\n" + style, re.S | re.I)
    text = m.group(1) if m else ""
    m = (re.search(r"^[-*\s]*Counted sections:\**\s*(.+)$", text, re.M | re.I)
         or re.search(r"\bCount (?:only )?the (.+?) sections?\b", text, re.S))
    if not m:
        return None
    names = re.split(r",\s*(?:and\s+)?|\s+and\s+", m.group(1).replace("\n", " "))
    names = [n.strip(" .*`") for n in names if n.strip(" .*`")]
    return names or None


def base_codes(register: str) -> set:
    """Codes (and names) of registered sources whose Use is the base text."""
    out = set()
    for line in register.split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and re.search(r"\bbase\b", cells[2], re.I):
            out.update(c for c in cells[:2] if c)
    return out


def links_in(text: str):
    """Yield (span, [tokens]) for brackets that are claim links."""
    for m in re.finditer(r"\[([^\[\]]+)\]", text):
        toks = [t.strip() for t in m.group(1).split(";")]
        if toks and all(LINK_TOKEN.match(t) for t in toks):
            yield m.span(), toks


def strip_links(text: str) -> str:
    out, last = [], 0
    for (a, b), _ in links_in(text):
        out.append(text[last:a])
        last = b
    out.append(text[last:])
    return "".join(out)


def norm(s: str) -> str:
    s = s.replace("\\", "")
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    s = s.replace("**", "").replace("*", "")
    s = s.replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def sections(draft: str) -> dict:
    out = {}
    for part in re.split(r"\n(?=## )", draft):
        head = part.split("\n", 1)[0]
        if head.startswith("## "):
            out[head[3:].strip()] = part.split("\n", 1)[1] if "\n" in part else ""
    return out


def count_words(body: str) -> int:
    body = AUTHOR_MARK.sub("", strip_links(body))
    lines = [l for l in body.split("\n") if not l.lstrip().startswith("#")]
    return len([w for w in " ".join(lines).split() if re.search(r"\w", w)])


def parse_cards(dossier: str) -> dict:
    """Cards are defined in the dossier's "Source cards" section. The layout
    in templates/dossier.md is one card per line:
        - SC-Uxx-NN | source | code, locator | "excerpt"
    Also read: "SC-Uxx-NN. Source, ref. excerpts", and a card under its own
    heading ("### SC-Uxx-NN") with "Source:" and "Excerpt:" lines below it.
    Lines after a card, up to the next card, belong to it, and the whole card
    is searched for quotations."""
    m = re.search(r"\n## [^\n]*[Ss]ource cards[^\n]*\n(.*?)(?=\n## |\Z)", dossier, re.S)
    section = m.group(1) if m else dossier
    blocks, cur = {}, None
    for line in section.split("\n"):
        m = re.match(r"^[-|*#\s]*\**(SC-U\d+-\d+)\**\s*[.|:]?\s*(.*)$", line)
        if m:
            cur = m.group(1)
            blocks[cur] = [m.group(2)] if m.group(2).strip() else []
        elif cur and line.strip():
            blocks[cur].append(line.strip())
    cards = {}
    for cid, lines in blocks.items():
        rest = " ".join(lines)
        src = re.search(r"Source:\**\s*([^|\n]+)", "\n".join(lines))
        source = (src.group(1) if src and not lines[0].count("|")
                  else re.split(r"\s*[|,.]\s", rest, maxsplit=1)[0]).strip(" -*")
        cards[cid] = {"source": source, "ref": rest[:200], "excerpt": rest}
    return cards


def ledger_rulings(ledger: str) -> dict:
    """Ledger id -> the text of its "Ruling:" line ("" if it has none)."""
    out = {}
    heads = list(LEDGER_ID.finditer(ledger))
    for i, h in enumerate(heads):
        body = ledger[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(ledger)]
        r = re.search(r"^\**Ruling:\**\s*(.*)$", body, re.M)
        out[h.group(1)] = r.group(1).strip() if r else ""
    return out


def unruled(text: str) -> bool:
    return not text or bool(re.match(r"(OPEN|deferred)\b", text, re.I))


def card_codes(card: dict, reg: set, base: set = frozenset()) -> set:
    ref = card["ref"].replace("'", "'").lower()
    found = {c for c in reg if re.search(r"(?<!\w)" + re.escape(c.lower()) + r"(?!\w)", ref)}
    # Cards made from the base text or its word data (get_bible_text,
    # get_words) belong to the registered base translation.
    if not found and re.search(r"get_words|get_bible_text", card["ref"]):
        found = set(base)
    return found


def base_text(dossier: str) -> str:
    m = re.search(r"\n## \d*\.?\s*Base text[^\n]*\n(.*?)(?=\n## )", dossier, re.S)
    return m.group(1) if m else ""


def register_codes(register: str) -> set:
    """Codes and names in the "Registered sources" table. Rows under any other
    heading (proposals for the author, exclusions) never count, whatever the
    heading is called. A stub register with no "Registered" heading counts
    every row."""
    has_heading = bool(re.search(r"^#+ .*registered", register, re.I | re.M))
    codes, in_reg = set(), not has_heading
    for line in register.split("\n"):
        if re.match(r"^#+ ", line):
            in_reg = bool(re.match(r"^#+ .*registered", line, re.I)) or not has_heading
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if in_reg and len(cells) >= 2 and re.fullmatch(r"[A-Za-z][\w.-]*", cells[1] or ""):
            codes.add(cells[1])
            codes.add(cells[0])  # full name, for cards that give the name, not the code
    return codes


def quotes_in(par: str):
    """Curly quotes pair unambiguously. Straight quotes are paired only when
    the paragraph has an even number of them; otherwise the paragraph is
    reported as unbalanced (yielded as None)."""
    for m in re.finditer(r"“([^”]{2,})”", par):
        yield m.group(1)
    straight = re.sub(r"“[^”]*”", "", par)
    if straight.count('"') % 2:
        yield None
        return
    for m in re.finditer(r"\"([^\"]{2,})\"", straight):
        yield m.group(1)


def quote_found(q: str, hay: str) -> bool:
    """Match allowing ellipses as gaps and [bracketed] editorial insertions."""
    hay_n = norm(hay)
    parts = re.split(r"\s*(?:\.\.\.|…)\s*", q)
    pos = 0
    for part in parts:
        part_n = norm(part).strip(" .,;:")
        if not part_n:
            continue
        pat = re.escape(part_n)
        pat = re.sub(r"\\\[[^\]]*\\\]", r".{0,40}?", pat)  # [you] etc.
        m = re.compile(pat).search(hay_n, pos)
        if not m:
            return False
        pos = m.end()
    return True


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    proj, unit = Path(sys.argv[1]), sys.argv[2]
    draft_p = (Path(sys.argv[3]) if len(sys.argv) == 4
               else newest(proj / "05-drafts", unit))
    if len(sys.argv) == 4 and not draft_p.is_absolute() and not draft_p.exists():
        draft_p = proj / draft_p
    dossier_p = newest(proj / "04-dossiers", unit)
    reg_p = newest(proj / "03-corpus", "corpus-register")
    if not draft_p or not dossier_p:
        sys.exit(f"missing draft or dossier for {unit}")
    draft = draft_p.read_text()
    dossier = dossier_p.read_text()
    ledger_p = proj / "decision-ledger.md"
    ledger = ledger_p.read_text() if ledger_p.exists() else ""
    plan = newest(proj / "02-plan", "volume-plan").read_text()
    style_p = newest(proj / "02-plan", "style-sheet")
    counted = counted_sections(style_p.read_text()) if style_p else None
    cards = parse_cards(dossier)
    bt = base_text(dossier)
    rulings = ledger_rulings(ledger)
    ledger_ids = set(rulings)
    reg_text = reg_p.read_text() if reg_p else ""
    reg = register_codes(reg_text)
    base = base_codes(reg_text)

    print(f"# Script checks: {unit}")
    print(f"Draft: {draft_p.relative_to(proj)} · Dossier: {dossier_p.relative_to(proj)}"
          f" · Register: {reg_p.relative_to(proj) if reg_p else 'MISSING'}\n")
    if not cards:
        print("**FAIL: no source cards could be read from the dossier.** Cards must be"
              " in its \"Source cards\" section, laid out as templates/dossier.md shows."
              " Checks 2, 4 and 5 below can't be trusted until this is fixed.\n")

    # 1. word count
    secs = sections(draft)

    def is_counted(h: str) -> bool:
        return counted is None or any(h.lower().startswith(c.lower()) for c in counted)

    counts = {h: count_words(b) for h, b in secs.items() if is_counted(h)}
    total = sum(counts.values())
    budget = None
    for line in plan.split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == unit:
            nums = [c.replace(",", "") for c in cells if re.fullmatch(r"[\d,]+", c)]
            budget = int(nums[0]) if nums else None
    print("## 1. Word count (words only)")
    if counted is None:
        print("The style sheet names no counted sections (add \"Counted sections: ...\""
              " under Word counts); every section is counted. **CHECK**")
    else:
        print("Counted sections (style sheet): " + ", ".join(counted))
    print(" · ".join(f"{h} {n}" for h, n in counts.items()) + f" · **total {total}**")
    if budget:
        lo, hi = round(budget * 0.9), round(budget * 1.1)
        verdict = "PASS" if lo <= total <= hi else "FAIL"
        if verdict == "FAIL" and any(author_mode(b) for b in secs.values()):
            verdict = "OUTSIDE THE RANGE: a note for the author, not a defect (the unit has an author's section)"
        print(f"Budget {budget} (allowed {lo}–{hi}): **{verdict}**")
    hdr = re.search(r"Words:\s*([^·\n]*)", draft)
    if hdr:
        print(f"Header says: {hdr.group(1).strip()}")
    print()

    body = "\n".join(secs.values())  # checks 2-6: every section
    counted_body = "\n".join(b for h, b in secs.items()
                             if is_counted(h) and not author_mode(b))  # check 7

    # 2. links resolve
    print("## 2. Claim links")
    used_cards, used_ledger, charter, bad, open_links = set(), set(), set(), [], []
    for _, toks in links_in(body):
        for t in toks:
            if t.startswith("SC-"):
                used_cards.add(t)
                if t not in cards:
                    bad.append(t)
            elif t == "BT":
                pass
            elif t.startswith("Charter:"):
                charter.add(t)
            elif t.startswith("D:"):
                bad.append(t + " (ledger has ids; use them)")
            else:
                used_ledger.add(t)
                if t not in ledger_ids:
                    bad.append(t)
                elif unruled(rulings[t]) and t not in open_links:
                    open_links.append(t)
    print(f"Cards cited: {len(used_cards)} · ledger ids: {', '.join(sorted(used_ledger)) or 'none'}"
          f" · charter links: {', '.join(sorted(charter)) or 'none'}")
    print("Unresolved: " + (", ".join(sorted(set(bad))) + " **FAIL**" if bad else "none **PASS**"))
    if open_links:
        print("Linked to a question not yet ruled (Ruling: OPEN, deferred or missing): "
              + ", ".join(open_links) + " **FAIL**")
    print()

    # 3. markers
    print("## 3. Editorial markers")
    marks = re.findall(r"\[(?:OPEN CRUX|NEEDS SOURCE|CONFLICT)[^\]]*\]", draft)
    waiting = re.findall(WAITING, draft)
    for m in marks:
        print(f"- {m}")
    for m in waiting:
        print(f"- {m}: waiting for the author's text (05-drafts/author/); not a drafter defect")
    print("**FAIL**" if marks or waiting else "none **PASS**")
    print()

    # 4. quotations
    print("## 4. Quotations against linked cards")
    fails, ok, quoted_by_src = [], 0, {}
    headings = {norm(h.lstrip("#").strip()) for h in draft.split("\n") if h.lstrip().startswith("#")}
    author_pars = {par.strip() for h, b in secs.items() if author_mode(b)
                   for par in re.split(r"\n\s*\n", b)}
    for par in re.split(r"\n\s*\n", body):
        par = AUTHOR_MARK.sub("", par)
        own = " (author's section: a quotation of a source needs its card)" \
            if par.strip() in {AUTHOR_MARK.sub("", a).strip() for a in author_pars} else ""
        par_cards = set()
        par_has_bt = any("BT" in toks for _, toks in links_in(par))
        for _, toks in links_in(par):
            for t in toks:
                if t.startswith("SC-"):
                    par_cards.add(t)
        for q in quotes_in(strip_links(par)):
            if q is not None and norm(q) in headings:
                continue  # a cross-reference to a heading in this unit
            if q is None:
                fails.append(f'- unbalanced straight quotation marks in paragraph "{par.strip()[:60]}...": check by hand')
                continue
            where = None
            # A quotation of the base text in a paragraph that links [BT]
            # counts as the base text, even if a card happens to contain it.
            if par_has_bt and quote_found(q, bt):
                where = "BT"
            for c in ([] if where else sorted(par_cards)):
                if c in cards and quote_found(q, cards[c]["excerpt"]):
                    where = c
                    break
            if not where and quote_found(q, bt):
                where = "BT"
            if where:
                ok += 1
                src = cards[where]["source"] if where in cards else "Base text"
                quoted_by_src[src] = quoted_by_src.get(src, 0) + len(q.split())
                continue
            elsewhere = [c for c, v in cards.items() if quote_found(q, v["excerpt"])]
            short = q if len(q) < 90 else q[:87] + "..."
            if elsewhere:
                fails.append(f'- "{short}": not in this paragraph\'s cards '
                             f'({", ".join(sorted(par_cards)) or "none"}); found in {", ".join(elsewhere)}{own}')
            else:
                fails.append(f'- "{short}": not found in any card or the base text '
                             f'(paragraph cites {", ".join(sorted(par_cards)) or "no card"}){own}')
    print(f"{ok} quotations matched.")
    print("\n".join(fails) + "\n**FAIL** (or a gloss/term in quotation marks: the agent judges)"
          if fails else "**PASS**")
    print()

    # 5. register
    print("## 5. Cited sources in the corpus register")
    missing = []
    for c in sorted(used_cards):
        if c not in cards:
            missing.append(f"{c} (card not found in the dossier, so its source can't be checked)")
        elif not card_codes(cards[c], reg, base):
            missing.append(f"{c} ({cards[c]['ref'][:60]})")
    print("\n".join(f"- {m}" for m in missing) + " **FAIL**" if missing else "all registered **PASS**")
    print()

    # 6. quotation words per source
    print("## 6. Words quoted per source")
    for s, n in sorted(quoted_by_src.items(), key=lambda x: -x[1]):
        print(f"- {s}: {n}")
    print("Compare with the register's quotation limits (Terms column).\n")

    # 7. sentences without a link
    print("## 7. Sentences with no claim link (agent judges: transitions need none)")
    n = 0
    for par in re.split(r"\n\s*\n", counted_body):
        if par.lstrip().startswith("#"):
            continue
        for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z“\"])", par.strip()):
            if len(sent.split()) >= 6 and not any(True for _ in links_in(sent)):
                n += 1
                print(f"- {sent[:140]}")
    if not n:
        print("none")
    print()

    # 8. the author's own sections
    print("## 8. The author's sections (notes for the author, not defects)")
    own_secs = {h: author_mode(b) for h, b in secs.items() if author_mode(b)}
    if not own_secs:
        print("none")
    for h, mode in own_secs.items():
        text = AUTHOR_MARK.sub("", secs[h])
        unlinked = [sent for par in re.split(r"\n\s*\n", text) if not par.lstrip().startswith("#")
                    for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z“\"])", par.strip())
                    if len(sent.split()) >= 6 and not any(True for _ in links_in(sent))]
        print(f"- {h}: {mode} by the author · {count_words(secs[h])} words"
              f"{'' if is_counted(h) else ' (not counted toward the budget)'}"
              f" · {len(unlinked)} sentences stand as the author's own claims (no link)")


if __name__ == "__main__":
    main()
