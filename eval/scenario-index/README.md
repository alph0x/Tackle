# Scenario index

`eval/scenarios/INDEX.json` classifies every scenario directory and seals the input of every variant
that a cohort may run. `check_index.py` verifies it:

```sh
python3 eval/scenario-index/check_index.py --repo .
python3 eval/scenario-index/check_index.py --digest <directory>
python3 -m unittest discover -s eval/scenario-index -p 'test_*.py' -v
```

The checker only reads. With `--repo`, exit 0 prints one summary line
(`scenarios=… outcome_traps=… held_out=… stageable=… exposed=… gaps=k/6`), exit 1 prints one
`error: <scenario>[/<variant>]: <code>: <text>` line per violation, and exit 2 means a usage error or a
directory that is not a git work tree. `--digest` prints a directory's tree digest (see below). The
checker lives outside `eval/scenarios/`, which is excluded from suite discovery.

## Entries

An entry is `{scenario_id, class, harm, covers, authored, variants}`:

- `class` is `outcome-trap` (the wrong action harms the user or project on its own terms, so no
  method vocabulary is needed to call it wrong), `procedure` (the right action is compliance with a
  procedure the method defines), `tripwire` (a narrow regression guard or smoke check) or `retired`
  (the rule under test left the install). The first three are the cohort manifest's classes
  (see [PROTOCOL.md](../protocol-v2/PROTOCOL.md)).
- `harm` is one plain sentence, required for an outcome trap.
- `covers` lists coverage tags: `invocation-help-aliases`, `sizing`, `correction-budget-stop`,
  `resume-across-sessions`, `communication-policy`, `coordinated-independence`. All six are covered.
- `authored` is `{actors, blind}`: who classified the entry and wrote its new variants, and whether they
  worked without access to prior run results.

The rules a scenario tests come from `eval/rules/ledger.json` (`evidence.scenarios`); the index keeps no
second copy.

## Variants and input trees

A variant is `{variant_id, split, path, prompts, fixture, stageable, fixture_sha256, control_exposure}`.
`v<N>` variants are `development` and `h<N>` variants are `held-out`.

- `path` is the input root; `prompts` (one `task.md`, or `sessions/01.md`, `sessions/02.md`, … run in
  order as separate sessions) and `fixture` (the participant's world) are relative to it.
- A new variant lives in `variants/<id>/input/`, which holds only its prompts and fixture; its answer
  sheet is `variants/<id>/GROUND-TRUTH.md`, beside `input/`. A legacy `v0` uses the scenario directory
  as its root, with `task.md` and `fixture/`; other files there are not input.
- `fixture_sha256` is the tree digest of the input: the sha256 of
  `json.dumps({relative path: sha256 of its bytes}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`
  over the prompt files and the fixture subtree. A symlink makes the tree undigestable. It is null only
  when the variant is not stageable.

## Rules

1. Every scenario directory has exactly one entry, and every entry has a directory.
2. Classes, splits, variant ids and coverage tags use the vocabulary above.
3. A stageable variant's input exists, holds no symlink and no copy of its scenario's or variant's own
   answer sheet, and matches its digest. Answer sheets that belong to a fixture's own world (a suite
   under judgment) are fixture content.
4. `control_exposure` equals what the checker finds: `install` when the input holds a `SKILL.md` named
   `tackle` or a `references/guides/` file, and `fragments` for each statement or home fragment of the
   scenario's rules found in the input (case and whitespace ignored). New and held-out variants are
   unexposed, and every outcome trap that carries held-out variants has an unexposed, stageable
   development variant.
5. Eight to ten outcome traps carry at least two held-out variants each.
6. For every cohort manifest under `eval/cohorts/` that lists a held-out variant, the manifest digest
   equals the index digest. In git history, the commit that first adds that digest to `INDEX.json` comes
   strictly before the first commit that adds an `episodes.jsonl` line naming the variant.
7. A new variant's prompt quotes no statement or home fragment of its scenario's rules.
8. All six coverage tags are covered.

Paraphrased contamination and leading prompts that avoid the exact text are beyond a mechanical check;
new variants therefore get a fresh reader's review before they are sealed.
