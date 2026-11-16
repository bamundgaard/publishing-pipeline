# Publishing house pipeline

A Claude Code project that turns a commissioned book (a commentary, a
dictionary, a study guide) into a finished study resource. It works like a
publishing house in software: 11 stages, 6 human gates, and an agent for each
editorial role.

The core rule: **agents draft and critique, source data verifies, and the
author decides.** Nothing is cited from a model's memory. Every factual
sentence links to a source card holding an exact excerpt from a registered
source, or to one of the author's rulings. Greek and Hebrew facts come from
dataset output, never from recall. The author approves each gate and owns
every position the book takes.

The rules every agent follows are in [CLAUDE.md](CLAUDE.md). The files
name the author as Ben, who wrote the pipeline for his own books; change the
name in `CLAUDE.md` and the agent files to make it yours.

## The stages

| # | Stage | Agent | Writes to | Gate (the author) |
|---|---|---|---|---|
| 1 | Intake | [intake-agent](.claude/agents/intake-agent.md) | `00-intake/`, `01-charter/` | **1**: approve the charter |
| 2 | Planning | [planner](.claude/agents/planner.md) | `02-plan/` | **2a**: approve the plan and style sheet · **2b**: mark up the sample unit |
| 3 | Corpus | [librarian](.claude/agents/librarian.md) | `03-corpus/` | approve sources in the register |
| 4 | Research dossiers | [research-assistant](.claude/agents/research-assistant.md), one per unit | `04-dossiers/` | **3**: rule on the questions in `decision-ledger.md` |
| 5 | Drafting | [drafter](.claude/agents/drafter.md), one per unit | `05-drafts/` | |
| 6 | Developmental edit | [dev-editor](.claude/agents/dev-editor.md), one per unit, plus a volume memo | `06-dev-edit/` | |
| 7 | Review panel | [reviewer](.claude/agents/reviewer.md) (tradition, opposition, scholar, preacher) and [language-reviewer](.claude/agents/language-reviewer.md), then a merge | `07-reviews/` | **4**: decide each reviewer finding |
| 8 | Verification | [verifier](.claude/agents/verifier.md), one per unit | `08-verification/` | |
| 9 | Copyedit | [copyeditor](.claude/agents/copyeditor.md): one volume job, then one job per unit | `09-copyedit/` | |
| 10 | Sign-off | managing editor's helper jobs | `10-signoff/` | **5**: sign the manuscript |
| 11 | Production | [production-editor](.claude/agents/production-editor.md) | `11-release/` | **6**: approve release |

Over all of them sits the [managing-editor](.claude/agents/managing-editor.md).
It starts each stage's agents, checks their work against the files and the
scripts, routes send-backs, brings the author only the decisions that are
his, keeps the project's record, and commits and pushes to GitHub at each
gate. It writes no content and decides no position.

**Two loops.** Review findings the author accepts go back to drafting
(stage 5) or the developmental edit (stage 6). Verification failures go back
to drafting. Each source can send a unit back at most twice; after that the
unit goes to the author.

**The sample unit.** One unit, chosen by the planner, runs ahead of the rest:
its dossier and draft are made once Gate 2a is approved, the author marks it
up, and the planner turns the markup into calibration rules for Gate 2b.
Every other unit waits for Gate 2b.

## Getting started

### One-time setup
1. **Aquifer.** The research agents get their data from the BibleAquifer
   connector. If it's a connector on your claude.ai account, Claude Code
   loads it automatically. Its tools are named
   `mcp__e614c1c4-0f5e-4355-805f-07621f9022c9__*`, and the agents that use
   Aquifer list those names in their `tools` line. If yours differs, check
   `/mcp` in a terminal session and change those lines to match. To add it
   by hand instead:

   ```bash
   claude mcp add --scope project --transport http aquifer <your Aquifer MCP URL>
   ```

2. **Google Chrome**, in `/Applications`, if you want a print PDF at stage 11.

### Start or continue a book
Run the managing editor as your main session, because it talks with you and
starts the other agents. In the Claude Code desktop app, open a session in
this folder and type:

> Follow .claude/agents/managing-editor.md and start a new book.

or, for a book already under way:

> Follow .claude/agents/managing-editor.md and continue the <slug> project.

(In a terminal: `claude --agent managing-editor`.)

For a new book it runs intake with you first: 21 questions from
[templates/questionnaire.md](templates/questionnaire.md), a few at a time,
which become the charter. From there it moves stage by stage, stopping at
each gate. For a book under way it reads the project's record, log and gates
and picks up where it stopped.

### What you do at each gate
You approve a gate by editing `projects/<slug>/gates.md` yourself: write
"approved YYYY-MM-DD, initials", or "waived (reason)". Only you edit that
file.

| Gate | What you read | What you write |
|---|---|---|
| 1 | `01-charter/charter.md` | Edits to the charter, then the gate |
| 2a | `02-plan/volume-plan.md` and `style-sheet.md` | Answers under "For Ben" in the plan, then the gate |
| 2b | The sample unit's draft | Your marked-up copy as `02-plan/sample-unit.md` (edit the text; comments in `[Ben: ...]`); check the calibration notes, then the gate |
| 3 | The dossiers' position maps, tier A first | Your rulings in `decision-ledger.md`, replacing each `Ruling: OPEN`, then the gate |
| 4 | Each unit's `07-reviews/<unit>.panel.md` | In the Decision column: "accept → stage 5", "accept → stage 6" or "reject", then the gate |
| 5 | `10-signoff/manuscript.md` and `open-items.md` | "reject" against any copyedit change you don't want, then the gate |
| 6 | The package in `11-release/` | The gate |

Between gates the managing editor brings you only real decisions, a few at a
time, in plain words. Corpus proposals at stage 3 are answered in the
register itself ("approved" or "rejected" under each item).

## Running one agent by hand
Every agent except intake and the managing editor runs as a subagent. You can
start one yourself from any session in this folder, for example:

- "Use the planner subagent to plan projects/<slug>." (or "... to calibrate projects/<slug>.")
- "Use the librarian subagent to build the corpus register for projects/<slug>."
- "Use the research-assistant subagent to build dossiers for U01, U02 and U03 in projects/<slug>, one subagent per unit, in parallel."
- "Use the drafter subagent to draft U02 in projects/<slug>." (or "... to revise U02 from its edit memo.")
- "Use the dev-editor subagent to edit U02 in projects/<slug>." (or "... to write the volume memo.")
- "Use the reviewer subagent with roles tradition, opposition, scholar and preacher, and the language-reviewer subagent, to review U02 in projects/<slug>, one per role, in parallel." Then: "Use the reviewer subagent to merge the reviews for U02."
- "Use the verifier subagent to verify U02 in projects/<slug>."
- "Use the copyeditor subagent to run the volume job for projects/<slug>", then one unit job per unit.
- "Use the production-editor subagent to build the release for projects/<slug>."

Every agent checks the gate before its stage and stops if it is open. If a
new agent isn't offered, start a new session so it picks up the file.

**Quick test without stages 2 and 3.** Copy
[templates/volume-plan.stub.md](templates/volume-plan.stub.md) to
`02-plan/volume-plan.md` and
[templates/corpus-register.stub.md](templates/corpus-register.stub.md) to
`03-corpus/corpus-register.md`, and mark Gates 2a and 2b "waived (test with
stub plan)". Still have the planner write the style sheet before drafting;
without it, units drift apart in voice, naming and length.

## How a project is laid out

```text
projects/<slug>/
├── gates.md                    # the six gates; only the author edits it
├── decision-ledger.md          # the author's rulings, with ids drafts link to
├── key.md                      # every code in plain words
├── log.md                      # one line per agent run
├── managing-editor-record.md   # what the managing editor did, and why
├── 00-intake/                  # questionnaire answers
├── 01-charter/                 # the charter → Gate 1
├── 02-plan/                    # plan, style sheet, sample markup → Gates 2a, 2b
├── 03-corpus/                  # corpus register: the only citable sources
├── 04-dossiers/                # one dossier per unit → Gate 3
├── 05-drafts/                  # drafts with claim links, drafter's notes, dictation/
├── 06-dev-edit/                # edit memos, volume memo
├── 07-reviews/                 # five reports per unit, the panel file → Gate 4
├── 08-verification/            # verification logs
├── 09-copyedit/                # copyedited text and change lists
├── 10-signoff/                 # assembled manuscript, open items → Gate 5
└── 11-release/                 # release text, indexes, JSON, PDF → Gate 6
```

**Files are the handoff.** Each stage reads named files from earlier folders
and writes only to its own.

**Revisions never overwrite.** A new version is a new file (`U02.v2.md`,
`corpus-register.v2.md`), and agents read only the newest.

## Scripts
Three scripts do the checks that shouldn't depend on a model's judgment. The
agents run them; you can too.

- [scripts/verify_unit.py](scripts/verify_unit.py) `projects/<slug> <unit>`:
  word count against the plan, claim links that don't resolve, editorial
  markers left in, quotations not found in their cards, unregistered sources,
  words quoted per source, and sentences with no link. Read-only. The
  sections that count toward the budget come from the style sheet's
  "Counted sections:" line.
- [scripts/build_release.py](scripts/build_release.py) `projects/<slug>`:
  turns the signed units into the release text with numbered notes and the
  provisional release data (`release.json`). Book details come from the
  charter's "Book details" block.
- [scripts/build_pdf.py](scripts/build_pdf.py) `projects/<slug>`: prints the
  release package to a PDF with Chrome. Changes no text.

## Templates
Agents build their files from [templates/](templates/): the
[questionnaire](templates/questionnaire.md), [charter](templates/charter.md),
[gates](templates/gates.md), [key](templates/key.md),
[decision ledger](templates/decision-ledger.md),
[volume plan](templates/volume-plan.md),
[style sheet](templates/style-sheet.md),
[corpus register](templates/corpus-register.md),
[unit draft](templates/unit-draft.md), [edit memo](templates/edit-memo.md),
[review report](templates/review-report.md),
[verification log](templates/verification-log.md) and
[copyedit changes](templates/copyedit-changes.md), plus the two stubs for
quick tests.

## Git and GitHub
The git history is the book's provenance trail: it shows what every file
said when each gate was approved. The managing editor commits and pushes to
your GitHub repository at each gate. Keep a repository that holds your
books private unless their sources' licences allow redistribution. To see
the history, run
`git log --oneline` in this folder, or open the commits list on GitHub.

## Status
- **Built:** every agent and stage, 1 to 11, and the three scripts.
- **Tested end to end:** a three-unit Philemon commentary (not included
  here), through Gate 6. It used the stub
  plan and stub register, so the planner, the librarian and the sample-unit
  calibration for Gate 2b have not yet run on a real book.
- **Known limits:**
  - Sources must be in Aquifer: the register, the source cards and the
    verifier all work through it, so a licensed print work can't yet be
    cited.
  - Aquifer's word data gives lemma, gloss and part of speech but not full
    parsing, so tense, voice, mood and case are "not in source data".
  - License terms and quotation limits are not yet checked.
  - Gates 3 and 4 cover the whole book, not one unit at a time.
  - Sections the author writes himself leave a placeholder that no stage
    yet fills.

## Licence
MIT. See [LICENSE](LICENSE).
