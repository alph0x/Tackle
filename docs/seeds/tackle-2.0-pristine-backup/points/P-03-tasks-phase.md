# Point P-03 — Tasks phase

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone. Links are for depth, not prerequisites — EXCEPT a named
> `design-contract.md` section the point implements, which IS required reading (name it in
> Context). Tackle plans this point; it does not implement it here.

## Status & wiring

**Status**: 🟢 done

**Depends on**: none · execution status in `plan.md` §5 and `board.md`.

**Touches (write scope)**:
- `SKILL.md` — add `/tackle-tasks` routing row.
- `references/sdd/tasks.tmpl.md` — new SDD phase template.

## Goal (single responsibility)

Add a `/tackle-tasks` trigger that produces `docs/plans/<initiative>/tasks.md`, and create the `references/sdd/tasks.tmpl.md` template used to render it. The output is a flattened checklist derived from `plan.md` §5 (Point decomposition).

## Context (grounded)

- `contract.md` §Signatures / API surface defines `/tackle-tasks` as the Tasks phase, outputting `docs/plans/<initiative>/tasks.md`, with a default gate of none/Lite.
- `contract.md` §States & transitions says: **Plan exists** → `/tackle-tasks` → `tasks.md` derived from `plan.md` §5.
- `SKILL.md` currently routes `/tackle-plan` and legacy triggers; it needs a new row for `/tackle-tasks`.
- `references/sdd/` is the canonical home for SDD phase templates (mirroring P-01 `constitution.tmpl.md` and P-02 `specify.tmpl.md`).
- The tasks template must reference `plan.md` §5 as its source so users know where the checklist comes from and what to do if that section is missing.

## Non-goals

- Do not implement the actual plan-execution loop (that is P-04).
- Do not add `/tackle-next` or `/tackle-implement` routing here.
- Do not create plan-local overrides or presets (P-06/P-07).
- Do not change existing `/tackle-plan` behavior or legacy triggers.

## Recommended approach

1. Create `references/sdd/tasks.tmpl.md` with:
   - YAML frontmatter placeholders: `initiative`, `created`, `source`.
   - A "How this file was produced" section pointing at `plan.md` §5.
   - A `Task checklist` table with columns: ID, Task, Source point, Owner, Depends on, Done-signal, Status.
   - Sample rows T-01, T-02, T-NN pulling title, slug, done-signal, and dependency from each point briefing.
   - An append-only Notes / execution log section.
2. Add `/tackle-tasks` to `SKILL.md` routing table(s):
   - Trigger summary row: `/tackle-tasks` → Tasks → produce `docs/plans/<initiative>/tasks.md`.
   - Phase/output row: Tasks → `docs/plans/<initiative>/tasks.md` → Flattened checklist from `plan.md` §5.
   - Tackle 2.0 changelog bullet listing `/tackle-tasks` among SDD phase entry points.
3. Verify no unfilled placeholders remain in the new template (except the intentional `{{...}}` template variables) and that `SKILL.md` mentions `/tackle-tasks` in the expected rows.

## Alternatives / fallbacks

- **If `/tackle-tasks` should also derive from a spec instead of a plan** → defer to P-05 (Checklist phase) or extend after P-04; keep P-03 scoped to `plan.md` §5 only.
- **If `plan.md` §5 is missing when the trigger runs** → the template instructs producing a degraded empty `tasks.md` with a note; the point itself only needs the template, not runtime logic.

## Recommended starting prompt

```text
Resolve Point P-03 (Tasks phase) of the "tackle-2.0" plan.
Repo: ~/Developer/Tackle. Read points/P-03-tasks-phase.md first; it is self-contained.
Do: add `/tackle-tasks` routing to SKILL.md and create references/sdd/tasks.tmpl.md.
Constraints: do not touch implement/next/checklist triggers, do not change existing plan triggers, keep template markdown-only.
Acceptance: done-signal command exits 0 and confirms the routing row + template placeholders exist.
```

## Acceptance — the loop's exit gate

- **Done-signal**:
  ```bash
  grep -E '\| `/tackle-tasks` \|.*Tasks' SKILL.md && \
    grep -E 'Tasks \| `/tackle-tasks` \| `docs/plans/<initiative>/tasks\.md`' SKILL.md && \
    test -f references/sdd/tasks.tmpl.md && \
    grep -q '{{INITIATIVE_NAME}}' references/sdd/tasks.tmpl.md && \
    grep -q '{{DATE}}' references/sdd/tasks.tmpl.md && \
    grep -q 'source: docs/plans/{{INITIATIVE_NAME}}/plan.md §5' references/sdd/tasks.tmpl.md && \
    grep -q 'Task checklist' references/sdd/tasks.tmpl.md && \
    grep -q '| ID | Task | Source point | Owner | Depends on | Done-signal | Status |' references/sdd/tasks.tmpl.md
  ```
  → pass = exit 0, all checks match.
- [x] Meets the **universal per-point acceptance** in `plan.md` §6.1.
- [x] **Correctness**: `SKILL.md` routes `/tackle-tasks` to the Tasks phase and names `tasks.md` as output.
- [x] **Conventions**: template lives in `references/sdd/`, named `tasks.tmpl.md`, with standard frontmatter placeholders.
- **If it fails →** check the exact table format in `SKILL.md` (other phase rows are the pattern) and ensure `references/sdd/tasks.tmpl.md` follows `references/point.tmpl.md` placeholder style.

## Open questions for this point

None. Q-01 (`/tackle-analyze`) and Q-02 (CLI package) remain provisional but do not affect this point.

## Definition of Ready

- [x] **Single responsibility**: adding the trigger and its template is one coherent change.
- [x] **No open decisions inside it**.
- [x] **Loop-ready**: the done-signal is a runnable shell check.
- [x] **Cold-agent-resolvable from this file alone**.

---

**Changed files**: `SKILL.md`, `references/sdd/tasks.tmpl.md`.
