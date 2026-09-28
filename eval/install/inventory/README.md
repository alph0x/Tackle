# Install inventory

Deterministic checks that the shipped install (`SKILL.md` plus `references/`) stays thin. They
verify the install, not agent behavior.

- **Permanent checks** read the working tree. They hold for every later version.

```sh
python3 -m unittest discover -s eval/install/inventory -p 'test_*.py' -v
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
3. **Gates** — the eight self-lint gates, extracted from `MAINTAINING.md` the same way
   `eval/validation-integrity/acceptance.py`'s `canonical_gates` does, each run silent and exit 0.
4. **Planted defects**, each built in a disposable temporary directory, never in this repository:
   a link to a path the relocation removed. It must make the relevant check fail, naming the file.
5. **Shipped entry point** — `SKILL.md`'s frontmatter and the absence of a nested `SKILL.md`, and
   the shipped request tables never advertise a retired `/tackle-*` alias.

The 8.4.1-era relocation's historical byte-preservation checks (`RELOCATION_REV` against
`BASE_REV`) were removed once the relocation aged out of scope for the working-tree checks above;
git history keeps the commits they compared.
