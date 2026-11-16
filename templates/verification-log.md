# Verification log template (the verifier writes this in 08-verification/)

Defect ids are `VF<n>`, numbered afresh in each log; in a re-check, refer to
earlier defects as `log VF2`.

```markdown
# Verification: <unit-id> · <reference or headword>

Draft checked: 05-drafts/<unit-id>.v<n>.md · Dossier: 04-dossiers/<unit-id>.v<n>.md · Register: 03-corpus/<file>
Round: 1 of 2 (or re-check 1, 2)
Verdict: Verified / Defects → stage 5 / Needs the author
Defects: <n> critical · <n> major · <n> minor

## Results
| Check | Result | Notes |
|---|---|---|
| 1. Script checks (count, links, markers, quotations, register) | PASS / FAIL | words <n> of <budget> |
| 2. Cards against their sources | PASS / FAIL | <n> cards checked, <n> not checkable |
| 3. Claim support and attribution | PASS / FAIL | |
| 4. Scripture | PASS / FAIL | |
| 5. Greek and Hebrew | PASS / FAIL | |
| 6. Quotation limits | PASS / limit not set | |
| 7. Consistency with ledger, charter, cross-references | PASS / FAIL | |
| 8. Handed-on items | PASS / FAIL | <n> items |

## Defects
VF1. Severity: critical / major / minor · Check: <n> · Where: <section, "first few words..."> · Failed: <what> · Evidence: <draft text> / <card excerpt, source text or tool output> · Fix by: drafter / author

## Re-check (re-checks only)
- log VF1: fixed / not fixed / broken by the revision

## Handed-on items
- <file, item>: PASS / FAIL (VF<n>) · <evidence>

## For the author
- <dossier defects, ruling problems, limits not set, checks that could not run>

## Script output
<paste the output of scripts/verify_unit.py>
```
