# Tackle

**Tackle 5.3.0: self-healing citations.** Anchored citations re-anchor mechanically when the code they cite moves — `tackle-check ground <workspace>` rewrites drifted line numbers by content match, never by judgment. Fragments should be unique per file; the runner gates workspaces with rows 1–12 and its done-signal executor.

## Release self-lint

7 shipped-skill gates run in the release sweep before every tag (`references/guides/lint-spec.md`): word budget (`SKILL.md` ≤ 1100 words), exactly 11 core conventions, changelog currency, migrate-chain currency, README currency, artifact-manifest currency, and README content claims. Since 5.0 the gates compose into the shipped `tackle-check` runner (POSIX sh, zero deps) — the runner IS the rows, the table is its spec; the rows stay copy-pasteable for hosts without the runner. `tackle-check sweep` runs gates 1–7 plus catalog plus the lint rows over every workspace in one command. No CI infrastructure — the release tag is the gate.

## Eval

Tackle ships a manual A/B eval in `eval/`: **3 scenarios** (`s1`–`s3`) — decision traps pitting a mid-tier model following Tackle literally against the same model free-styling at a known agent failure. The registry and workflow live in `eval/README.md`; each scenario carries its own `GROUND-TRUTH.md` answer sheet, and `tackle-check catalog` verifies scenarios ⊆ registry so the list can't drift.

## How to use

| You say | Mode |
|---|---|
| `tackle-check` | **Mechanical gate** — shipped POSIX-sh runner: `lint <workspace>` (12 lint rows), `catalog` (eval scenarios ⊆ registry), `done-signal <point>` (run the point's exit-gate), `ground <workspace>` (re-anchor drifted citations), `sweep` (release sweep: gates 1–7 + catalog + workspace lint) |
| "migrate / upgrade `<x>`" | **Migrate** — bring an old plan to the current methodology (checklist chain v2.0 → v5.3 in `references/guides/migrate.md`) |

## Version

**Version:** Tackle 5.3.0. See `references/CHANGELOG.md` for what's new.
