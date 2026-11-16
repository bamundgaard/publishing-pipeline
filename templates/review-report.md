# Review templates (the review panel writes these in 07-reviews/)

Role codes for finding ids: TR tradition, OR loyal opposition, SR scholar,
PR preacher, LR language. Finding ids are `<code><n>`, such as `SR2`; in the
panel file they carry the role code, so they never clash across reviewers.

## Report: 07-reviews/<unit-id>.<role>.md (round 2: <unit-id>.<role>.v2.md)

```markdown
# Review: <unit-id> · <reference or headword> · <role> reviewer

Draft read: 05-drafts/<unit-id>.v<n>.md · Dossier read: 04-dossiers/<unit-id>.v<n>.md · Round: 1 of 2
Ready for review because: <memo file and verdict, or "cleared by the author in the task">
Scores (1 to 5, 4 = as good as the marked-up sample; say "uncalibrated" if there is none): <measure> <n> · <measure> <n>

## Summary
Two to four sentences, from this role only: the unit's main strength and its most serious problem.

## Findings
<CODE>1. Severity: critical / major / minor · Where: <section, "first few words..."> · Finding: <what is wrong> · Evidence: <card id, charter clause, ledger id, tool output> · For: drafter / dev-editor / author

## Round check (round 2 only)
- <CODE>1: fixed / partly fixed / not fixed / broken by the revision

## Passed to verification
- <possible fact error and where, outside this role's checks>

## Missing inputs
- <style sheet, sample unit, calibration notes, a tool that failed>
```

## Panel: 07-reviews/<unit-id>.panel.md (after round 2: <unit-id>.panel.v2.md)

```markdown
# Review panel: <unit-id> · <reference or headword>

Draft reviewed: 05-drafts/<unit-id>.v<n>.md · Reports merged: <the five files, with versions>
Counts: <n> critical · <n> major · <n> minor

## How to decide
Write one of these in the Decision column for each finding: "accept → stage 5"
(the drafter fixes it), "accept → stage 6" (the dev-editor turns it into a
memo item), or "reject" (add a reason if you like). Then mark Gate 4 in
gates.md.

## Findings
| Id | Reviewer | Severity | Where | Finding | Evidence | Suggested for | Same as | Decision |
|---|---|---|---|---|---|---|---|---|
| SR2 | scholar | major | Comment, "Paul's request..." | <...> | SC-U03-14 | drafter | TR1 | |

## Where reviewers disagree
- <topic>: <id> says <...>; <id> says <...>. Not resolved here.

## Scores
| Measure | Reviewer | Score |
|---|---|---|

## For the author
- <items any reviewer marked "For: author": rulings, plan changes, research gaps>

## Missing inputs
- <from the reports>
```
