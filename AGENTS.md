# AGENTS — Tackle repo

Contract for any agent working in this repository (the Tackle skill itself), in any session — planning or not.

## Learning intake (session start, always)

Persisted learning from past retros MUST be considered before proposing defaults or starting work:

1. `.tackle/profile.md` — project learning-loop hypotheses (read if present; apply active entries, tagged `(from your profile)` when they shape a proposal).
2. `~/.tackle/user-profile.md` — user-level hypotheses (same rule).
3. `docs/seeds/*.md` — parked initiatives and the pending-skill-fixes intake list (offer applicable items when planning or when the user asks what is pending).

Write paths are exclusive: profiles are written ONLY by `/tackle-retro` (batch-confirmed); seeds are created/updated deliberately, never as a side effect. Never write either silently.

## Repo conventions

- The skill source is `SKILL.md` + `references/`; the entry file has a ≤1100-word budget and 11 core conventions (incl. authority order) — preserve both when editing.
- `docs/plans/` and `docs/seeds/` are both gitignored and local-only: this machine is the single publishing point for Tackle, so workspaces and backlog stay here, unexposed. Convention for any repo using Tackle: `docs/seeds/` gets the same gitignore decision as `docs/plans/` (convention 9) — a seed leaks an initiative's shape just like a plan does.
- The install artifact is `SKILL.md` + `references/` ONLY; `docs/` (plans, seeds) never ships to installers.
- Any change that deletes normative content from `SKILL.md` or a guide requires the D-13 gate: rule-inventory diff + one behavioral eval run before release (see `references/guides/lint-spec.md` §Release sweep).
- Releases follow `references/CHANGELOG.md` discipline: granular commits, tag, GitHub release with the changelog entry as notes.

<!-- graft:start -->
## Graft — repo context graph

This repo is indexed in `graft/`: small linked markdown nodes that explain each
system and carry exact file:line spans, kept in sync with the code through git.

For ANY task here — understanding how something works, finding where code lives,
or scoping a change — get context from the graph before grepping or opening
source files. Re-ask freely (it's cheap) and reuse literal identifiers you
already have (symbol, error string, file name) as the query. New to this repo?
Run `graft map` first — a token-budgeted orientation (dir clusters, hubs,
hotspots), no LLM, no key.

- Run `graft ask "<your question>" --source` → ranked nodes with the relevant
  code spans inlined (each hit's ≤8-line crux by default; `--full` for whole
  definitions when the crux isn't enough). Match the tool to the task shape:
  for understanding or editing, the top node IS the answer — cite its
  `covers:` file:line spans and edit straight from `--source`. For
  exhaustive tasks ("every occurrence / every caller of this pattern"), ranked
  results are top-N, not complete — run `graft grep "<literal>"` instead
  (exhaustive over indexed files, grouped by enclosing symbol), falling back
  to raw `grep -rn` only for unindexed files.
- `graft skeleton <file>` → every definition's signature + span, ~10× cheaper
  than reading the file; use it to skim an API surface.
- `graft callers <symbol>` gives precomputed, exact edges — who calls this.
  Add `--direction out` for what it calls, or `--depth N` to walk
  transitively for the full blast radius. For structural questions, skip
  ranking and use this directly.
- Or browse: `graft/INDEX.md` lists every node; follow the links.
- Monorepos and folders of multiple repos rank fairly across sub-projects —
  hits carry `[scope/]` labels naming which one they're from. Narrow with
  `graft ask "<task>" --in <scope>/` once you know where you're working.

If a returned span is truncated ("+N more lines"), open the file at that exact
range before finalizing. Only open source files when a node genuinely lacks a
needed detail, and then at the exact file:line the node points to — never
re-read whole files.

After big code changes, refresh the graph with `graft build` (deterministic,
no API key, $0).
<!-- graft:end -->
