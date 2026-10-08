# Controlled writing

Owner texts and specifications use a controlled language. Short sentences, plain words and one idea per sentence make them easy to read and to check.

## Scope

Two kinds of text follow this guide.

- Texts the owner reads: the STATUS digest, closure receipts, blocker reports and the plan view's summary.
- Specifications: plans, briefs and contract clauses.

Other text, such as chat replies and code comments, keeps the general guidance in [communication](communication.md).

## Rule

Write about 80% of ASD-STE100, with the no-ai-slop reference that the communication guide cites. This guide copies neither source.

- Use one idea per sentence.
- Keep sentences short, at most 25 words.
- Use the active voice and name the actor.
- Use concrete terms, and use one term for one thing.
- Do not use a word from the vague-word lists below.

## Check

The recipe in [controlled-writing.md](../recipes/controlled-writing.md) reports two kinds of finding. It gives the line of each one.

- `long-sentence`: a sentence over the limit of 25 words.
- `vague`: a word or filler phrase from the lists below.

A sentence ends at a period, an exclamation mark, a question mark, a colon or a semicolon. This holds also before a closing quote, parenthesis or emphasis mark. A list item or a heading starts a new sentence. A wrapped sentence is reported at the line where it starts.

Running the recipe needs the owner's explicit authorization ([recipe consent](../recipes/README.md#consent)); prefer an equivalent harness check, and without either, check the text against the rules by reading it. With that authorization, run it as `findings(text, language)` from the recipe. Pass the language code of the text, such as `en` or `es`.

## Vague words

Vague words and filler phrases hide the fact. State the fact instead. The match ignores letter case.

English: `leverage`, `utilize`, `various`, `robust`, `synergy`, `seamless`, `holistic`, `cutting-edge`, `best-in-class`, `game-changing`, `delve`, `myriad`, `plethora`, `etc`, `and so on`, `and so forth`, `and more`, `and the like`, `in order to`, `a number of`, `a wide range of`, `a variety of`, `it is worth noting`, `it should be noted`, `needless to say`, `at the end of the day`, `basically`, `essentially`, `really`, `very`, `stuff`.

Spanish: `varios`, `varias`, `diversos`, `diversas`, `robusto`, `sinergia`, `etc`, `etcétera`, `y así sucesivamente`, `y demás`, `con el fin de`, `un gran número de`, `una amplia gama de`, `cabe destacar`, `vale la pena mencionar`, `ni qué decir tiene`, `al final del día`, `básicamente`, `esencialmente`, `realmente`, `muy`, `cosas`, `de vanguardia`.

The recipe holds the exact patterns. Add a word to the recipe and to this list together.

## Exempt text

The check skips these parts.

- Fenced code and inline code.
- Text in straight or curly double quotes.
- Blockquote lines, where compiled clauses sit byte-exact.
- HTML comment lines and anchor lines.
- Ids and hashes, which add nothing to the word count.

Table rows skip the length check only. Their words still go through the vague-word check.

A lone double quote hides nothing. Text after it stays checked.

## Languages

The length limit applies in every language. The vague-word lists cover English and Spanish. A text in any other language gets the length check only.

## When to run it

- PLAN runs the check over `plan.md`, the briefs and `design-contract.md` before it sets a task Ready. See Step 6.75 in [decompose-and-lint](decompose-and-lint.md).
- RUN runs the check over a closure receipt or a blocker report before it writes the text. See [run](run.md).
- A finding blocks readiness until the text is fixed or the owner accepts it.

The check is not a lint row. Closed workspaces and historical records stay as they are.
