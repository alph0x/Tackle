# Tackle

**Tackle 6.1.0.** Anchored citations re-anchor mechanically when the code they cite moves — the two-phase grounding procedure rewrites drifted line numbers by content match, never by judgment. Fragments should be unique per file; direct checks cover rows 1–15 and each point's done-signal.

## Release self-lint

7 shipped-skill gates run in the release sweep before every tag (`references/guides/lint-spec.md`): word budget (`SKILL.md` ≤ 1100 words), exactly 11 core conventions, changelog currency, migrate-chain currency, README currency, artifact-manifest currency, and README content claims. The gates remain direct, copy-pasteable checks; the release checklist composes gates 1–7, catalog, and lint rows over every workspace. No CI infrastructure — the release tag is the gate.

## Eval

Tackle ships a manual A/B eval in `eval/`: **3 scenarios** (`s1`–`s3`) — decision traps pitting a mid-tier model following Tackle literally against the same model free-styling at a known agent failure. The registry and workflow live in `eval/README.md`; each scenario carries its own `GROUND-TRUTH.md` answer sheet, and the catalog checklist verifies scenarios ⊆ registry so the list can't drift.

## How to use

| You say | Mode |
|---|---|
| Direct checks | **Mechanical gate** — run the 15 lint rows, 7 self-lint gates, catalog integrity, direct point done-signals, two-phase grounding, eval method arms, and init artifact completeness from the documented Markdown procedures |
| "migrate / upgrade `<x>`" | **Migrate** — bring an old plan to the current methodology (checklist chain v2.0 → v6.1 in `references/guides/migrate.md`) |

## Version

**Version:** Tackle 6.1.0. See `references/CHANGELOG.md` for what's new.
