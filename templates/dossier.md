# Unit dossier template (the research assistant writes this in 04-dossiers/)

File: `04-dossiers/<unit-id>.md`; a revision is `<unit-id>.v2.md`, `.v3.md`,
... and never overwrites. Keep the nine section headings and their numbers
exactly, and keep each source card on one line in the layout shown: the check
script (`scripts/verify_unit.py`) reads the "Base text" and "Source cards"
sections by these headings.

```markdown
# Dossier: <unit-id> · <reference or headword>

Version: v<n>, <date> · Register read: 03-corpus/<file> · Changed from the previous version: <what and why, or "first version">

## 1. Header
Unit: <unit-id> · Reference: <ref> · Question: <from the plan> · Tier: <A/B/C, from the plan>

## 2. Base text
<the base translation for the reference, copied from tool output, with verse numbers> (SC-<unit>-01)

## 3. Original-language data
| Form | Lemma | Strong's | Gloss | Part of speech | Card | Flag |
|---|---|---|---|---|---|---|
| <form in its own script> | <lemma> | <number> | <gloss> | <pos> | SC-<unit>-02 | <"carries interpretive weight: why", or blank> |

Not in source data: <tense, voice, mood, case, syntax, counts ... whatever the tools don't give>

## 4. Textual variants
<only what a registered source reports, with card ids; otherwise "none in corpus">

## 5. Background
- <one point of historical, cultural or literary context> (SC-<unit>-NN)

## 6. Position map
### Crux 1: <the question, asked open>
- Option A, <the view>: <who holds it, as the source states> · strongest case, in the source's terms: <...> (SC-<unit>-NN)
- Option B, <the view>: <...> (SC-<unit>-NN)

## 7. Source cards
One card per line. The excerpt is copied verbatim from the tool result, in
quotation marks; two separate passages from one article are two quoted
excerpts separated by a semicolon, never joined.

- SC-<unit>-01 | <source name as the register writes it> | <Aquifer code>, <tool call or article id> | "<exact excerpt>" | <locator: verse or section>
- SC-<unit>-02 | <source name> | <Aquifer code>, get_words <ref> | "<row copied verbatim>"; "<another row>" | <locator>

## 8. Gaps and questions for Gate 3
### Gaps
- <a missing view, thin coverage, a registered source that couldn't be reached, a useful resource that isn't registered, "possible view, unsourced: ...">

### Questions for the author
1. <the decision needed, asked open> · Options: <as the position map gives them> · Evidence: <crux and card ids>

## 9. Tier check
<agree with the plan's tier, or propose a change, with one reason>
```
