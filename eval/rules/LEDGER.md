# Rule ledger

`ledger.json` names every normative rule that `SKILL.md` states, plus the rules that the trap
scenarios test elsewhere in the install. For each rule it records where the rule lives, what kind of
rule it is and what evidence exists for it. `historical-index.json` maps the historical run records to
the labels of [evaluation protocol v2](../protocol-v2/PROTOCOL.md). The checker validates both files
against the repository:

```sh
python3 eval/rules/check_ledger.py --repo .
python3 -m unittest discover -s eval/rules -p 'test_*.py' -v
```

Exit 0 prints one warning per hot-path rule that is neither a safety invariant nor `discriminates`,
then `rules=<n> hot_path=<n> untested=<n> warnings=<n>`. Exit 1 prints `error: <reason>` lines. Exit 2
means a usage error. The checker only reads; it uses the Python standard library.

## Coverage units

The ledger covers the `SKILL.md` sections Public surface, PLAN and RUN, Compatibility and state, Core
conventions and Output. A section runs from its `## ` heading to the next level-1 or level-2 heading.
Inside those sections:

1. Skip headings, blank lines, HTML comments, anchor lines, and each table's header and delimiter rows.
2. Strip list markers (`- `, `* `, `+ `, `1. `). Join each paragraph or list item into one line with
   single spaces. A table body row is its own line, with its cells joined by single spaces.
3. Split that line after `.`, `?` or `!` when a space follows and then an uppercase letter, a
   backtick, `*` or a digit.

Each resulting sentence is a unit. Its **coverage key** is its first 48 characters. The key must
appear exactly once across all `rules[].units` and `non_normative[].unit` entries. The checker
rejects:

- an uncovered sentence;
- a sentence covered twice;
- a key that matches no sentence;
- two sentences that share a key;
- a listed section that is missing or repeated.

`python3 eval/rules/inventory.py units --repo .` prints every unit.
`python3 eval/rules/inventory.py uncovered --repo .` prints the ones the ledger does not name yet.

## Ledger entries

`{"schema": "tackle-rule-ledger/1", "rules": [...], "non_normative": [...]}`. Unknown fields are
rejected.

| Field | Rule |
|---|---|
| `rule_id` | `R-<AREA>-<NN>`; AREA is ENTRY, INTAKE, PLAN, RUN, EVID, STATE, STATUS, LEARN, MIGRATE, COMM or REL. Unique within the ledger. Retired ids stay in it, so an id is never reused; the checker reads one revision and cannot detect a deleted id. |
| `statement`, `statement_sha256` | One normalized sentence and the sha256 of its UTF-8 bytes. A changed statement needs a new hash. |
| `home`, `home_fragment` | `path:line` of the line stating the rule, and at most 60 characters of it. The fragment must be on that line. |
| `units` | Coverage keys of the `SKILL.md` sentences the rule covers. Only rules homed in `SKILL.md` may have units. |
| `mirrors` | Other `path:line` places that restate the rule. The list is not exhaustive. |
| `class` | `safety-invariant`, `behavioral`, `format` or `maintainer`, as defined below. |
| `hot_path` | True exactly when the home is `SKILL.md` and the rule is not retired. |
| `origin` | `added_in` (the release whose changelog introduces the rule, or `unknown`), `trigger` (the source of that claim), `discovered_by` (the scenarios that exposed the gap). |
| `evidence` | `status` (`untested` or a protocol v2 label), `scenarios` (the scenarios that test the rule), `cohort_id` (null exactly when untested) and `as_of` (a date). A tested status must name a cohort with an `eval/cohorts/<cohort_id>/manifest.json` that carries the same `cohort_id`; the cohort's own report writes the status. |
| `historical` | `{record, label, seeds}`: every index entry for the rule's evidence scenarios, with the label as the record states it. This list is informative only. `inventory.py sync --repo . --write` regenerates it. |
| `retired_in` | Optional. The version that retired the rule. A retired rule keeps its id and evidence and has no units. Its home is pinned to the last revision that stated it (`path@<tag>:line`), and the checker does not resolve it. |

A `discriminates` status cannot rest only on the scenarios in `discovered_by`. Discovery and
validation stay separate.

Classes:

- **safety-invariant**: breaking the rule causes an unauthorized side effect, widens authority, or
  loses or falsifies records or evidence.
- **behavioral**: what the agent does (routing, sequencing, asking, checking) when breaking it causes
  none of the safety harms.
- **format**: the shape of an artifact or a report.
- **maintainer**: applies only to maintaining Tackle itself.

`non_normative` lists `{unit, reason}` for sentences that state no rule.

## Historical index

`{"schema": "tackle-historical-index/1", "records": {<record path>: [<entry>, ...]}}`. A record is
one of two things:

- a file in `eval/runs/`;
- an answer sheet whose run record appears in no `eval/runs/` file.

Records are read, never edited. Each entry holds `scenario_id`, `recorded_label`, `mapped_label`,
`seeds`, `comparison`, `baseline`, `candidate`, `contamination` and `basis`.

- `comparison` names the baseline: `no-skill` (a control without Tackle), `ablation` (Tackle without
  the rule), `prior-version` (an older Tackle) or `method-only` (no baseline ran).
- `baseline` and `candidate` are `{outcome, seeds}`. The candidate pools every seed of the method arm
  in the record, except seeds the record itself excludes from scoring. The outcome comes from
  `correct_action`: 0 is `fell`, 2 is `avoided`, and 1, or seeds that disagree, is `partial`. When a
  record has no score, its binary gate or explicit statement decides `fell` or `avoided`.
  `placeholder` marks unscored placeholder values. `absent` (zero seeds) marks an arm that never ran.
- `contamination` explains why the rule under test was reachable from the baseline arm: the fixture
  ships the install or the rule text, or the record states a contamination. Reachable is enough; the
  arm need not have read it. A capability fact the task needs, such as `usage-reporting: unsupported`,
  is not the rule. It needs an observed baseline arm.
- `mapped_label` is the first match of: `contaminated`, then `unobserved` (a placeholder or absent
  arm), then `method-worse` (the candidate fell and the baseline avoided), then `inert` (both
  avoided), then `discriminates` (the baseline fell and the candidate avoided), then `inconclusive`.
- `seeds` is the seed count shared by the arms that ran, or `n/a` when they differ or none ran.
- `basis` lists `{line, quote}` pairs, one for each record line that states an outcome or the
  contamination. When the record file is present, the checker verifies that each quote is on its
  line and that `recorded_label` occurs in the record. A record file that is absent, such as an
  untracked run record in a fresh clone, is skipped.

A historical label comes from single-seed records. It is never protocol v2 evidence: `evidence.status`
changes only through a protocol v2 cohort.
