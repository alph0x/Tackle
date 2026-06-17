# reference-docs — snapshotted external material

> **Optional (any gate, but usual at Full).** Create `reference-docs/` only when the plan
> depends on material that lives OUTSIDE this repo — a sibling repo's source, vendor/API docs,
> diagrams, a prior initiative's rules or resolved Q&A. The point: the workspace stays
> **self-contained even if the source branch moves or the sibling repo is unavailable**, so a
> cold agent (or one on a different machine, with no network) can still resolve every point.

**Provenance**: {{source repo/URL}}, branch `{{branch}}`, snapshotted **{{YYYY-MM-DD}}**.
These are **READ-ONLY** — never edit them here. If the source evolved and it matters,
**re-snapshot** and note it in `../log.md`. Live paths (prefer them when both exist) are in
`../reference.md`.

## Index (what's here → who uses it)

| Folder / file | Contents | Used by |
|---|---|---|
| `{{source-snapshots/...}}` | {{the proven contract shapes / domain types the design derives from}} | {{P-0x · spec §y}} |
| `{{diagrams/}}` | {{visual references — sequence/flow/wireframe}} | {{P-0x · spec §y}} |
| `{{guardrails/}}` | {{rules/lint adopted from a prior review}} | {{AGENTS rules · all points}} |
| `{{docs/}}` | {{curated external/vendor knowledge, error catalogs, resolved external Q&A}} | {{P-0x}} |

## Reading hints

- {{Start with X for the full picture, then Y before touching P-0n.}}
- {{Which diagram pairs with which spec section / point.}}
