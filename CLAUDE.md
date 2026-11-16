# Publishing house pipeline

This repo turns a commissioned book (commentary, dictionary, study guide) into a
finished study resource through 11 stages and 6 human gates. Agents draft and
critique, source data verifies, and Ben decides and owns every position.

## How work moves
- Each book lives in `projects/<slug>/`. Stage folders are numbered 00 to 11.
- Files are the handoff. A stage reads only the files listed as its inputs and
  writes only to its own folder.
- `projects/<slug>/gates.md` records the six gates. Only Ben edits it. Before
  starting, an agent checks that the gate before its stage reads "approved" (or
  "waived"); if not, it stops and says which gate is open.
- `projects/<slug>/key.md` (from `templates/key.md`) explains every code in
  plain words: units, ledger rulings in short form, card and finding codes. An
  agent that adds a new kind of code, or new units, adds its line there. In
  chat with Ben, describe things in words; give a code only in parentheses,
  when he'd need it to find something.
- Every agent run appends one line to `projects/<slug>/log.md`: date, agent,
  stage, files written, open issues.

## Rules every agent follows
- Never mark a gate, and never decide an interpretive position. Present options
  and evidence; Ben rules in `decision-ledger.md`.
- Nothing is cited from model memory. Cite only sources in the "Registered
  sources" table of the project's `03-corpus/corpus-register.md` (newest
  version), through source cards with exact excerpts. Sources proposed under
  "For Ben" are not citable.
- Original-language facts (lemma, gloss, parsing, counts) come from tool or
  dataset output, never from recall. If the data doesn't give it, write
  "not in source data".
- Greek and Hebrew in their own script. No transliteration.
- Revisions never overwrite. A new version is a new file (`U02.v2.md`,
  `U02.v3.md`, ...), and an agent reads only the newest version of any file.
- The charter (`01-charter/charter.md`) governs everything downstream. If a task
  conflicts with it, stop and flag the conflict.

## Stages
1 Intake (Gate 1) · 2 Planning (Gates 2a, 2b) · 3 Corpus · 4 Research dossiers (Gate 3)
· 5 Drafting · 6 Developmental edit · 7 Review (Gate 4) · 8 Verification
· 9 Copyedit · 10 Sign-off (Gate 5) · 11 Production (Gate 6)

Agents live in `.claude/agents/`. Templates live in `templates/`.
Built: intake-agent (1), planner (2), librarian (3), research-assistant (4),
drafter (5), dev-editor (6), reviewer and language-reviewer (7, the five-role
review panel), verifier (8, the verification desk; it runs
`scripts/verify_unit.py` first), copyeditor (9; a volume consistency job,
then one job per unit, with tracked changes), production-editor (11; runs
`scripts/build_release.py` first), and managing-editor (runs as the main
session; orchestrates every stage, keeps
`projects/<slug>/managing-editor-record.md`, and does the Gate 5 helper
jobs).

Main-session agents (intake-agent, managing-editor): in the Claude Code
desktop app, open a session in this folder and ask it to follow the agent's
file, for example "Follow .claude/agents/managing-editor.md and continue the
<slug> project." In a terminal, `claude --agent <name>` does the same.
All other agents run as subagents that the main session starts.

Aquifer is the BibleAquifer connector. Its tools are named
`mcp__e614c1c4-0f5e-4355-805f-07621f9022c9__<tool>`; list them by name in an
agent's `tools` line.
