# Hot path

Two measures of the reading an agent must do to run one Full task, and a test that proves both on
fixtures and then applies them to this repository. Standard library only; no network or model call.

```sh
python3 eval/hot-path/load_chain.py --repo .
python3 eval/hot-path/duplicates.py --repo . --chain run
python3 -m unittest discover -s eval/hot-path -p 'test_*.py' -v
```

## The RUN chain (`load_chain.py`)

The RUN chain is the mandatory reading of one Full task:

- `SKILL.md`;
- the RUN card, `references/guides/run-card.md`;
- every file or anchored section the card links outside its closing `## Depth (on demand)` section;
- `references/task.tmpl.md`, as the proxy for the task brief.

Depth on demand is everything the card links inside that section, and `run.md` is its depth: an agent
reads it only when the card sends it there, so none of it counts.

- **Links.** An inline, reference-style or `<a href>` link without an anchor adds its whole file. A link
  with an anchor adds that section, from its heading to the next heading of the same or a higher level.
  Each file and line counts once. Links inside code fences, external links and links back to the card
  are ignored. Only the card's own links are followed; a linked guide's links are not.
- **Words** are counted as `wc -w` counts them under `LC_CTYPE=C` on macOS, the host that measured the
  brief: maximal runs of bytes other than space, tab, newline, vertical tab, form feed and carriage
  return. GNU `wc` skips non-printable bytes and can count fewer.
- **Output.** `run-chain words=<n> card=<m> mandatory=<paths>`. Exit 0 within budget, 1 when n > 4000
  or m > 800, 2 on a missing file or an unresolved link or anchor.
- `--card <path>` measures another file as the card. It showed the old route: with `run.md` as the card,
  the chain was 13,722 words.

## Duplicates (`duplicates.py`)

The single duplicate detector (D-74). T-34 runs it over the whole install with `--files`.

- **Units.** One sentence of prose outside code fences, or one table row. Headings, blank lines, HTML
  comments and anchor lines are not units. Paragraphs and list items join into one line, and a sentence
  ends at `.`, `?` or `!` followed by a space and an uppercase letter, a backtick, `*` or a digit.
- **Comparison.** Words are lowercased after link targets, `|`, backticks and emphasis are removed. A
  unit with fewer than 8 words is not compared. Every pair with a word 3-gram Jaccard similarity of
  0.5 or more is reported, except two rows of the same table.
- **Output.** One `duplicate <file>:<line> ~ <file>:<line> j=<value>` line per pair, then
  `duplicates=<k>`. Exit 0 when k = 0, 1 when k > 0, 2 on a missing file or a usage error.
- `--chain run` is the card, `references/guides/run.md` and every `references/recipes/*.md`.
- **Limit.** A paraphrase shares few 3-grams, so the detector misses it by design. Finding semantic
  duplicates is the fresh reviewer's job.

## The test (`test_hot_path.py`)

- **Fixtures**, built in temporary directories:
  - a chain over budget, a card over budget and the exact boundaries;
  - a mandatory link that adds its target, an anchored section, and ignored links;
  - a verbatim copy, a near-verbatim copy with three words changed, and two distinct sentences;
  - similar rows of one table, which never pair, and the same rows in two tables, which do;
  - a paraphrase, which is missed by design.
- **Repository cases**:
  - the chain is within budget, and the RUN chain has `duplicates=0`;
  - one `## State transitions` heading in the RUN chain, the card's;
  - the card's transition table: every state has an exit, Complete leaves only by an authorized reopening
    that keeps spent cycles, and `Waiting on owner` leaves only to its entry state or to Skipped;
  - the Pick step skips any row whose write scope meets an In progress, Checking, Interrupted or
    `Waiting on owner` row;
  - every `run.md` section is reached from the card's Depth section.
