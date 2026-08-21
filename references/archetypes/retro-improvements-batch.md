# Archetype: retro-improvements-batch

Ship a batch of adopted retro improvements into the skill itself, with behavioral traps proving the two rule changes.

## Point list

- **P-01 · spec+runner change** — the mechanical rows (spec table cells + shipped runner) land in one change; a latent bug in an adjacent row fixes bundled.
- **P-02 · behavioral trap #1** — a trap scenario proving the first rule, fixture embedding the post-edit guide the rule lives in; registered in `eval/README.md`.
- **P-03 · template/guide change #1** — the first convention change across the reference templates/guides (grep-verified, convention-only).
- **P-04 · behavioral trap #2** — a trap proving the second rule, fixture embedding the post-edit guide; registered after P-02.
- **P-05/P-06/P-07 · template/guide changes #2..#4** — the remaining convention changes, each independent, each with its own grep done-signal.
- **P-08 · gates** — README content claims updated to the shipped reality, D-13 rule-inventory diff, trap runs (1 seed/arm, real executor tier), full `tackle-check sweep`.

## Edge pattern

Two independent feature spines, each feeding a trap that embeds the post-feature guide, converging on a single gates point:

```
P-01 ──► P-02   (trap #1 embeds post-P-01 output)
P-03 ──► P-04   (trap #2 embeds post-P-03 output)
P-01..P-07 ──► P-08   (README claims, D-13, trap runs, sweep)
```

Template/guide changes are mutually independent (disjoint Touches) unless two touch the same guide file — then serialize them.

## Wave shape

- **Wave 1 (parallel)** — P-01 ∥ P-03 ∥ P-05 ∥ P-06 ∥ P-07: the features and convention changes, disjoint Touches.
- **Wave 2 (parallel)** — P-02 ∥ P-04: the traps, whose fixtures embed Wave-1 outputs.
- **Wave 3 (sequential)** — P-08: README claims, D-13, trap runs, sweep.

## Trap warnings

- Briefings must use the runner-extractable `**Done-signal**: \`cmd\`` same-line form — any other layout silently no-ops `tackle-check done-signal` at the double gate.
- Trap fixtures embed the post-feature guide file, never a stale copy; the trap's G2-style observables should tolerate short (2-turn) sessions where intake and the action moment collapse into adjacent turns.
- A spec cell naming a convention location ships with that convention present in the same change (row 15 named `reference-docs-README.tmpl.md` as home of `captured:` — the template didn't document it until a post-close advisory).
- Workspace files (`plan.md`, `points/`) must not carry raw status glyphs — use U+1F7E2/U+1F7E1 notation and octal `printf` escapes so lint rows 1/3/5 don't self-flag.

## Provenance

tackle-session-friction, closed 2026-08-21 (retro: `docs/plans/tackle-session-friction/retro.md`).
