# Point P-07 — Plan-local customization bootstrapper

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone. Links are for depth, not prerequisites — EXCEPT a named
> `design-contract.md` section the point implements, which IS required reading (name it in
> Context). Tackle plans this point; it does not implement it here.

## Status & wiring
**Depends on**: P-06 — Template-resolution stack + presets (the `references/presets/default/` and `references/presets/sdd/` source trees must exist before `/tackle-init` can copy them).
- **Touches (write scope)**: `SKILL.md`, `docs/plans/tackle-2.0/contract.md`.

## Goal (single responsibility — one loop-completable change)
Add the `/tackle-init [preset]` trigger and the **Init mode** behavior it routes to: create `docs/plans/<initiative>/presets/<preset>/` by copying `references/presets/<preset>/`, create the empty `docs/plans/<initiative>/overrides/` directory, and fall back to `references/presets/default/` when the requested preset is missing. Record the trigger and the resulting plan-local layout in `contract.md`.

## Context (grounded)
- P-06 already defined the template-resolution stack (`overrides > presets > sdd > core`) and populated `references/presets/default/` and `references/presets/sdd/`. P-07 exposes the bootstrapper that copies those presets into a concrete plan workspace.
- `docs/plans/tackle-2.0/contract.md` §Signatures / API surface and §Local customization layout — this point implements those contract entries.
- `SKILL.md:86-95` — the Init mode steps this point adds (confirm initiative, create plan dir, copy preset, create overrides, fallback to default).
- `references/presets/default/` — core plan templates copied by `/tackle-init` (17 files).
- `references/presets/sdd/` — SDD phase templates referenced by the resolution stack (6 files).

## Non-goals
- No CLI package, shell installer, or `tackle-init.sh` script. `/tackle-init` is a skill trigger consumed by the model from `SKILL.md`.
- No files outside `docs/plans/<initiative>/`. Do not create `.tackle/`, dotfiles, or repo-root bootstrap artifacts.
- `/tackle-init` does not generate content (no `constitution.md`, no `spec.md`, no points). It only lays down the customization tree.
- Do not modify `README.md` or `references/CHANGELOG.md`; P-08 owns those.

## Recommended approach
1. Open `SKILL.md` and add `/tackle-init [preset]` to the routing table at the top of the Routing section.
2. Add an `### Init mode` subsection under `## Overview` (after the execution-loop description) with the five steps: confirm initiative, create plan dir, copy preset, create overrides, fallback to default.
3. Open `docs/plans/tackle-2.0/contract.md` and:
   - Add `/tackle-init` to the trigger table in §Signatures / API surface.
   - Add or confirm the §Local customization layout block showing `presets/<preset>/` and `overrides/`.
   - Add the state transition: **No local customization tree** → `/tackle-init` → presets and overrides exist.
   - Add the error-model row: **Preset not found** → recoverable → fall back to `references/presets/default/`.
4. Tests: run the done-signal below. It asserts the trigger is documented, the layout is recorded, and the source preset directories contain the expected counts.

## Alternatives / fallbacks
- **If `/tackle-init` is requested before `references/presets/` exists** → the error model says fall back to core templates, but P-06 must already have created the directories; if not, P-06 is not done.
- **If a user asks for a CLI installer** → point to decision D-04 (`docs/plans/tackle-2.0/decisions.md:35`): markdown skill first, no CLI in 2.0.

## Recommended starting prompt
<!-- Ready to paste into a fresh session to attack this point. Keep it grounded and bounded. -->
```text
Resolve Point P-07 (Plan-local customization bootstrapper) of the "Tackle 2.0" plan.
Repo: ~/Developer/Tackle. Read points/P-07-local-init-bootstrapper.md first; it is self-contained.
Do: Add the `/tackle-init [preset]` trigger to SKILL.md (routing row + Init mode subsection) and record the trigger, layout, state transition, and fallback behavior in docs/plans/tackle-2.0/contract.md.
Constraints: no CLI/script, no repo-root files, no content generation, do not touch README.md or CHANGELOG.md (P-08), and rely on references/presets/ created by P-06.
Acceptance: SKILL.md documents /tackle-init routing and Init mode; contract.md records the signature, layout, transition, and fallback; references/presets/default has 17 templates and references/presets/sdd has 6.
Loop until green: cd ~/Developer/Tackle && grep -Fq '/tackle-init [preset]' SKILL.md && grep -q '### Init mode' SKILL.md && grep -q '/tackle-init' docs/plans/tackle-2.0/contract.md && test $(ls references/presets/default/*.tmpl.md | wc -l) -eq 17 && test $(ls references/presets/sdd/*.tmpl.md | wc -l) -eq 6 && echo "P-07 green".
```

## Acceptance — the loop's exit gate
<!-- One home for "how the loop knows it's done". The command is the exit check; the criteria
     are what passing means. EXHAUSTIVE + MECHANICALLY verifiable, not prose: where a finite set
     exists (error cases, states, endpoints), cover EVERY case AND assert the COUNT in the
     command (e.g. test count == N) so a lazy suite can't go green with half the cases. -->
- **Done-signal**: `cd ~/Developer/Tackle && grep -Fq '/tackle-init [preset]' SKILL.md && grep -q '### Init mode' SKILL.md && grep -q '/tackle-init' docs/plans/tackle-2.0/contract.md && test $(ls references/presets/default/*.tmpl.md | wc -l) -eq 17 && test $(ls references/presets/sdd/*.tmpl.md | wc -l) -eq 6 && echo "P-07 green"` → pass = prints `P-07 green` with exit 0.
- [x] Meets the **universal per-point acceptance** in `plan.md` §6.1.
- [x] **Correctness**: Init mode steps in `SKILL.md` are ordered (confirm → create dir → copy preset → create overrides → fallback) and match `contract.md`.
- [x] **Contract conformance**: `/tackle-init` trigger, output layout, state transition, and fallback are all recorded in `contract.md`.
- [x] **No regression**: `/tackle-plan` and legacy triggers (`tackle this`, `plan de acción`) are untouched.
- [x] **Preset counts**: default preset contains 17 templates; sdd preset contains 6 templates.
- **If it fails →** missing row in `SKILL.md` or `contract.md` → add it; wrong preset count → verify P-06 created the directories; grep fails → re-read the current file and place the text exactly.

## Open questions for this point
- None. Q-01 and Q-02 remain provisional at the initiative level but do not block P-07.

## Definition of Ready (the gates that can FAIL — if the rest of the briefing is filled, these are what's left to check)
- [x] **Single responsibility**: stating "done" needs no "and" — the entire point is "add the `/tackle-init` trigger and record it in the contract".
- [x] **No open decisions inside it**: zero unresolved user-owned questions.
- [x] **Loop-ready**: the done-signal is a runnable command with an unambiguous pass.
- [x] **Cold-agent-resolvable from this file alone** — the one true test of every section above.

## Changed files
- `SKILL.md` — added `/tackle-init [preset]` routing row and `### Init mode` subsection.
- `docs/plans/tackle-2.0/contract.md` — added `/tackle-init` to the trigger table, documented the local customization layout, added the state transition, and added the preset-not-found fallback row.
