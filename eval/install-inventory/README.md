# Install inventory

Deterministic checks that the shipped install (`SKILL.md` plus `references/`) relocated its
maintainer-only content correctly: every relocated byte preserved, every consumer reading the new
paths, and nothing else changed. They verify the relocation itself, not agent behavior.

```sh
python3 -m unittest discover -s eval/install-inventory -p 'test_*.py' -v
```

## What it checks

1. **Install inventory** — `references/**` carries none of the changelog, the historical
   migration checklists, Tackle's own release sweep and self-lint gates, or the unreferenced
   vendor collectors and validator example.
2. **Byte preservation** — every moved file, and every extracted block landing in
   `MAINTAINING.md` or `maintaining/migrations.md`, is byte-identical to its bytes at
   `03b992e52b1b40faa5e3897a0d4729065f503c02` once the enumerated substitutions (gate 3, gate 4,
   gate 7, and the five sibling-guide pointers a relocation makes stale) are reversed. Reversal
   uses an exact-count check, so an unlisted difference — including a substitution that was never
   applied — fails the comparison rather than passing silently.
3. **Links** — every relative link in `SKILL.md`, `references/**`, `README.md`, `AGENTS.md`,
   `MAINTAINING.md`, `CHANGELOG.md`, `maintaining/**` and `extras/**` resolves to a file, and to
   an anchor where one is given.
4. **Legacy templates** — the five frozen templates (`point.tmpl.md`, `log.tmpl.md`,
   `usage.tmpl.md`, `board.tmpl.md`, `coordinator.tmpl.md`) keep the audit's pinned hashes.
5. **Gates** — the eight self-lint gates, extracted from `MAINTAINING.md` the same way
   `eval/validation-integrity/acceptance.py`'s `canonical_gates` does, each run silent and exit 0.
6. **Recipes and rules** — `candidate_board` loads from `maintaining/migrations.md`, every
   `test_task_contracts.py` reference to it points at the new home, and `eval/rules/ledger.json`'s
   `R-MIGRATE-03` (and no other rule) is retired with its home updated.
7. **Planted defects**, each built in a disposable temporary directory, never in this repository:
   a link to a path the relocation removed, a gate whose changelog path was never substituted, and
   a legacy template whose bytes changed. Each must make the relevant check fail, naming the file.

## Byte preservation, without hardcoded expected text

The test file computes expected bytes from `git show 03b992e:<path>` plus the enumerated
substitution table (also defined in the test), rather than hardcoding large expected strings.
This keeps the substitution list itself the single source both the product edit and this test
were built from.
