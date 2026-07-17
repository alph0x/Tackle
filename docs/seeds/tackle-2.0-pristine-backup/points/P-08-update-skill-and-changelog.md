# Point P-08 — Update SKILL.md routing and changelog

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone. Links are for depth, not prerequisites — EXCEPT the named
> `contract.md` trigger-table section this point implements, which IS required reading.
> Tackle plans this point; it does not implement it here.

## Status & wiring
**Status**: 🟢 done
**Depends on**: P-06 (template-resolution stack + presets exist), P-07 (`/tackle-init` creates the local customization tree) · execution status in `plan.md` §5 / `board.md`.
- **Touches (write scope)**: `SKILL.md`, `README.md`, `references/CHANGELOG.md`, `references/AGENTS.tmpl.md`, `references/README.tmpl.md`, `references/lite-plan.tmpl.md`.

## Goal (single responsibility — one loop-completable change)
Rewrite `SKILL.md` so its routing table is the single source of truth for every Tackle 2.0 trigger, document the new SDD phases + execution loop + template-resolution stack in `README.md`, record the 2.0 changes in `references/CHANGELOG.md`, and bump every `Methodology:` stamp to **Tackle 2.0**.

## Context (grounded)
- P-01..P-05 added the SDD phase templates (`references/sdd/`) and execution templates; P-06/P-07 added presets, overrides, and `/tackle-init`. The skill files still described the Tackle 1.5 surface.
- `contract.md` §Trigger table is the public API this point must reflect.
- `SKILL.md:20-55` — the new routing table and SDD phase entry points.
- `README.md:41-72` — human-facing trigger table, pipeline summary, and version line.
- `references/CHANGELOG.md:3-10` — Tackle 2.0 release notes.
- `references/AGENTS.tmpl.md:3`, `references/README.tmpl.md:3`, `references/lite-plan.tmpl.md:3` — methodology stamps bumped to **Tackle 2.0**.

## Non-goals
- Do not change the behavior of any mode; this is documentation + stamp alignment.
- Do not re-plan or restructure earlier points.
- Do not add new templates or triggers.

## Recommended approach
1. Rewrite `SKILL.md` §Routing into one authoritative table: `/tackle-init`, `/tackle-constitution`, `/tackle-specify`, `/tackle-plan`, `/tackle-tasks`, `/tackle-implement`, `/tackle-next`, `/tackle-checklist`, plus legacy triggers.
2. Add the SDD phase entry-points table and the template-resolution stack (`overrides > presets > sdd > core`).
3. Document the execution loop surface for `/tackle-implement` and `/tackle-next`.
4. Update `README.md` trigger table, pipeline summary, and version line to match `SKILL.md`.
5. Append the `## Tackle 2.0` entry to `references/CHANGELOG.md`.
6. Bump `Methodology:` stamps to **Tackle 2.0** in `AGENTS.tmpl.md`, `README.tmpl.md`, and `lite-plan.tmpl.md`.
7. Run the done-signal to verify every trigger, the changelog entry, and the three stamps.

## Alternatives / fallbacks
- **If a template copy in `references/presets/default/` still shows Tackle 1.5** → bump it too; the preset mirrors the core template.
- **If `README.md` and `SKILL.md` drift on wording** → treat `SKILL.md` as the source of truth (`contract.md` §Invariants).

## Recommended starting prompt
<!-- Ready to paste into a fresh session to attack this point. Keep it grounded and bounded. -->
```text
Resolve Point P-08 of the Tackle 2.0 plan.
Repo: ~/Developer/Tackle. Read docs/plans/tackle-2.0/points/P-08-update-skill-and-changelog.md first; it is self-contained.
Do: rewrite SKILL.md routing, update README.md, add Tackle 2.0 to references/CHANGELOG.md, and bump Methodology stamps to Tackle 2.0 in AGENTS.tmpl.md, README.tmpl.md, and lite-plan.tmpl.md.
Constraints: documentation-only change; SKILL.md is source of truth; do not modify behavior or prior points.
Acceptance: the done-signal command in the point passes.
Loop until green: run the done-signal below.
```

## Acceptance — the loop's exit gate
- **Done-signal**:
  ```bash
  python3 - <<'PY'
  import re, sys
  expected = {'init','constitution','specify','plan','tasks','implement','next','checklist'}
  for fn in ('SKILL.md','README.md'):
      cells = re.findall(r'^\| `(/tackle-[^`]+)`', open(fn).read(), re.M)
      found = {re.search(r'/tackle-(\w+)', c).group(1) for c in cells}
      if found != expected:
          print(f'{fn}: expected {expected}, found {found}'); sys.exit(1)
  assert re.search(r'^## Tackle 2\.0$', open('references/CHANGELOG.md').read(), re.M)
  for fn in ('references/AGENTS.tmpl.md','references/README.tmpl.md','references/lite-plan.tmpl.md'):
      assert 'Methodology: Tackle 2.0' in open(fn).read(), fn
  print('P-08 done-signal passed')
  PY
  ```
- [x] Meets the **universal per-point acceptance** in `plan.md` §6.1 (don't restate it here).
- [x] **Correctness**: every 2.0 trigger appears in `SKILL.md` and `README.md` (count-asserted: 8 triggers each).
- [x] **No regression**: legacy triggers (`tackle this`, `plan de acción`, resume/status/list/next/migrate/improve) remain in the routing table.
- [x] **Changelog + stamps**: `references/CHANGELOG.md` has exactly one `## Tackle 2.0` entry; the three core templates carry `Methodology: Tackle 2.0`.
- **If it fails →** identify which clause fails and patch the corresponding file; re-run. Self-correct up to the workspace iteration budget (`AGENTS.md`), then STOP + escalate.

## Open questions for this point
- None.

## Definition of Ready (the gates that can FAIL — if the rest of the briefing is filled, these are what's left to check)
- [x] **Single responsibility**: rewriting routing + README/changelog/stamps is one documentation-alignment change.
- [x] **No open decisions inside it**: none.
- [x] **Loop-ready**: the done-signal is a runnable shell command with unambiguous pass conditions.
- [x] **Cold-agent-resolvable from this file alone** — the one true test of every section above.
