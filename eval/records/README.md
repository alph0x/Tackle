# Evidence records

This directory makes the eval's behavioral claims auditable. Its checks are deterministic: they
verify records, fixtures and harnesses, not agent behavior. A behavioral result exists only where a
record of an actual run exists.

```sh
python3 eval/records/check_currency.py --repo .
python3 -m unittest discover -s eval/records -p 'test_*.py' -v
```

The checker reads tracked files from the git index, so it checks what a commit would contain; only
local-only originals are read from the working tree. It also reads the release tags (CI fetches them
with `fetch-depth: 0`), and it never writes inside the repository. Exit 0 prints a summary and the scope note, exit 1 prints one
`error: <path>: <code>: <text>` line per violation, and exit 2 means a usage error or a directory
that is not a git work tree.

## Layout

| Path | Content |
|---|---|
| `../runs/*.md` | Historical run records, tracked exactly as written. A record is never edited; a correction is a new record. |
| `sanitized/*.md` | Tracked copies of the historical records that carried a home path, a `~/` path, an address or a key. The original stays local, is listed in `../.gitignore`, and keeps its bytes. |
| `historical-hashes.json` | Pins every historical record: sha256, byte count, whether it is tracked, the date it was recorded, and the scenarios it names that no longer have a directory. |
| `claims.json` | Classifies every scenario named in `CHANGELOG.md` and `README.md`. |
| `../cohorts/<id>/` | Protocol v2 cohorts (see [PROTOCOL.md](../protocol-v2/PROTOCOL.md)); each must pass `check.py`. |

`../rules/historical-index.json` (the rule ledger's index) says which scenarios each historical
record names; the checker reads it and keeps no second copy. An answer sheet that holds a run record
(`../scenarios/<id>/GROUND-TRUTH.md`) also names its own scenario. `../rules/check_ledger.py`, which
CI runs in the same job, verifies each index entry's basis quote against its record.

## Rules

1. Every tracked record matches its pinned sha256 and every pinned tracked record is in the git
   index. A local-only original is never tracked, carries a leak (its sanitized copy differs from it),
   and names a tracked sanitized copy whose `source_sha256` is the original's hash. `recorded_on`
   equals the file-name date, and a record without one states its `recorded_on` date in its text.
2. Every record in the historical index is pinned, and every tracked file under `../runs/` and
   `sanitized/` is pinned.
3. No tracked file under `../runs/`, `sanitized/` or `../cohorts/`, no pinned record, and neither
   `historical-hashes.json`, `claims.json`, `../rules/historical-index.json` nor
   `../rules/ledger.json` contains an absolute path, `~/`, a private key, an `sk-` key or an e-mail
   address (the patterns of PROTOCOL.md section 2). Answer sheets and the rule ledger state the
   method's own `~/.tackle/` path, so that one literal is allowed there and nowhere else.
4. Every (source, `## ` section, scenario unit) in the two claim sources has exactly one claim. A
   unit is `sN` or a range `sA–sB` outside fenced code. Claims have one of four kinds:
   - `record`: the named records are pinned and tracked, they name the scenario, and each was
     recorded on or before the release date of the section's version tag;
   - `cohort`: a tracked cohort that passes `check.py` and lists the scenario;
   - `no-record`: a historical claim whose run record was never retained, with the reason; allowed
     only in sections released at or before `gate_version` (8.4.1), so it cannot cover a new claim;
   - `mention`: the scenario is named but no run result is claimed (an introduction, a removal, a
     fixture change, a range whose members are classified individually), with the reason.

   A scenario to which the section attributes an observed run result (a verdict, an outcome such as
   avoided, fell, fired, caught, null or discriminates, a validation, or such a result cited as
   precedent) is `record`, `cohort` or `no-record`, never `mention`. For the root README and for
   sections newer than `gate_version`, the checker enforces this: a `mention` whose lines carry an
   outcome word fails. A `record` claim proves that a retained record of the run exists; it does not
   grade the claim. The historical index's `mapped_label` shows how strong each record is.
5. A pinned record's `retired_scenarios` lists exactly the scenarios it names that have no
   directory under `../scenarios/`. The checker prints them as `retired:` lines.

## Adding evidence

1. New behavioral evidence is a protocol v2 cohort under `../cohorts/<id>/`; a changelog claim about
   it uses kind `cohort`.
2. A record that carries a path, key or address is copied with
   `python3 eval/records/sanitize.py <record> eval/records/sanitized/<name>`, which replaces the
   recognized patterns, refuses when anything else remains, and never overwrites. The original is
   listed in `../.gitignore`.
3. Pin the record, add its scenarios to the historical index, classify every scenario unit the new
   changelog entry names, and run the checker.

Raw transcripts stay local; a cohort record carries their sha256 (PROTOCOL.md section 2).
