# Unit draft template (the drafter writes two files per unit)

## File 1: 05-drafts/<unit-id>.md

```markdown
# <unit-id> · <reference or headword>

Status: DRAFT v1, stage 5, not yet edited
Question: <exegetical question or headword scope, from the plan>
Genre template: <from the plan> · Tier: <A/B/C> · Words: <n> of <budget>
Inputs: dossier <unit-id>.md · ledger entries used: <ledger ids, e.g. X1, U02-D1, S5> · style sheet: yes/no · sample unit: yes/no
Sent back by: <revisions only: e.g. 06-dev-edit/<unit-id>.memo.md, or the review or verification file>

## <Section 1 from the genre template>

Prose. Each factual sentence ends with its claim link. [SC-U02-04]
The author's own position links to the ruling. [U02-D1]
A base-text quotation copied from the dossier takes [BT].

## <Section 2: one the dial gives to the author, still waiting>

[AWAITING AUTHOR: <section name>]

## <Section 2, once the author's file exists>

[AUTHOR-WRITTEN]

The author's text, word for word. Sentences here are the author's own claims
and need no link. A quotation of a source still needs its card. [SC-U02-11]

(A dictated section starts with [AUTHOR-DICTATED] and is lightly edited.)

## <Section 3>

[OPEN CRUX: <name>] Option A ... [SC-U02-06] Option B ... [SC-U02-09]
[NEEDS SOURCE: <claim>]
[CONFLICT: <short description>]
```

## File 2: 05-drafts/<unit-id>.note.md

```markdown
# Drafter's note: <unit-id> v1

## Open cruxes
## Unsupported claims
## Deviations from the plan
## Conflicts
## Author's sections
## Quotation use
## Missing inputs
## Response to revision requests (revisions only)
```

## The author's files: 05-drafts/author/<unit-id>.<section>.md

The author writes these; the drafter merges them. `<section>` is the section's
name in lower case with hyphens (`U02.explanation.md`).

```markdown
Mode: written        (or: dictated)

Plain prose. No codes are needed. To cite a source, put its card code in
brackets after the sentence.
```
