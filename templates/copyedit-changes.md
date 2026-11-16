# Copyedit change list template (the copyeditor writes this in 09-copyedit/)

Change ids are `CE<n>` and author queries `AQ<n>`, numbered afresh in each
file. They are not ledger codes.

```markdown
# Copyedit: <unit-id> · <reference or headword>

Draft: 05-drafts/<unit-id>.v<n>.md (verified in 08-verification/<log file>)
Copyedited text: 09-copyedit/<unit-id>.md
Words: <before> → <after> (budget <n>, allowed <lo>–<hi>)
Script checks: draft <all pass / which failed> · copyedit <all pass / which failed>
Changes: <n> · Queries: <n>

## How to review
Each change can be rejected: write "reject" in the Decision column, with a
reason if you like. Blank means accepted. Answer each query under "Queries".

## Changes
| Id | Where | Before | After | Rule | Decision |
|---|---|---|---|---|---|
| CE1 | Comment v. 6, "Paul's prayer..." | <exact text> | <exact text> | style sheet, Words to watch | |

## Queries
AQ1. Where: <...> · Question: <...> · Why it may touch substance: <...> · Answer:

## For the drafter
- <fixes the drafter should make from the dossier, if any>

## Script output
<both runs, draft and copyedit>
```
