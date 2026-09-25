# Install inventory

Deterministic checks that the shipped install (`SKILL.md` plus `references/`) stays thin, and that
the relocation of its maintainer-only content was correct. They verify the install and the
relocation, not agent behavior.

- **Permanent checks** read the working tree. They hold for every later version.
- **Historical checks** read commits only: `T32_REV`
  (`b2bb990962096417548f1321964dbe2f4e35e1a9`, the commit that made the relocation) against
  `BASE_REV` (`03b992e52b1b40faa5e3897a0d4729065f503c02`). Later edits to the moved files, the
  stamps or the ledger cannot change their result, and one test checks that they never read the
  working tree.

```sh
python3 -m unittest discover -s eval/install-inventory -p 'test_*.py' -v
```

## What it checks

Permanent, on the working tree:

1. **Install inventory** — `references/**` carries none of the changelog, the historical
   migration checklists, Tackle's own release sweep and self-lint gates, or the unreferenced
   vendor collectors and validator example; `MAINTAINING.md` and `maintaining/migrations.md`
   exist, and `update.md`'s install manifest names neither.
2. **Links** — every relative link in `SKILL.md`, `references/**`, `README.md`, `AGENTS.md`,
   `MAINTAINING.md`, `CHANGELOG.md`, `maintaining/**` and `extras/**` resolves to a file, and to
   an anchor where one is given.
3. **Legacy templates** — the five frozen templates (`point.tmpl.md`, `log.tmpl.md`,
   `usage.tmpl.md`, `board.tmpl.md`, `coordinator.tmpl.md`) keep the audit's pinned hashes.
4. **Gates** — the eight self-lint gates, extracted from `MAINTAINING.md` the same way
   `eval/validation-integrity/acceptance.py`'s `canonical_gates` does, each run silent and exit 0.
5. **Planted defects**, each built in a disposable temporary directory, never in this repository:
   a link to a path the relocation removed, a gate whose changelog path was never substituted, and
   a legacy template whose bytes changed. Each must make the relevant check fail, naming the file.

Historical, at `T32_REV`:

6. **Byte preservation** — every moved file, and every extracted block landing in
   `MAINTAINING.md` or `maintaining/migrations.md`, is byte-identical to its bytes at `BASE_REV`
   once the enumerated substitutions (gate 3, gate 4, gate 7, and the five sibling-guide pointers a
   relocation makes stale) are reversed. Reversal uses an exact-count check, so an unlisted
   difference — including a substitution that was never applied — fails the comparison rather than
   passing silently. The edited guides reconstruct exactly, and the ranges that stayed are verbatim.
7. **Content kept** — `migrate.md` still held the current checklists and the pointer, and
   `lint-spec.md` its score line.
8. **Version** — the stamps and the changelog head were still 8.4.1.
9. **Recipes and rules** — `candidate_board` loaded from `maintaining/migrations.md`, every
   `test_task_contracts.py` reference to it pointed at the new home, and `eval/rules/ledger.json`'s
   `R-MIGRATE-03` (and no other rule) was retired with its home updated.

## Byte preservation, without hardcoded expected text

The test file computes expected bytes from `git show 03b992e:<path>` plus the enumerated
substitution table (also defined in the test), rather than hardcoding large expected strings.
This keeps the substitution list itself the single source both the product edit and this test
were built from.
