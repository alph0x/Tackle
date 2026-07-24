# Step 0 — Companion skills check

Before intake, verify that the optional companion skills are available. These skills improve planning quality but are never used for execution:

- `superpowers` — for `brainstorming` and `writing-plans` depth.
- `karpathy-guidelines` — for simplicity-first discipline.
- `solid-skills` or `clean-architecture` — for architecture / SOLID decisions.

For each missing skill, suggest installing it to the user. Record the result in the log's `### Intake (context gathered)` section:

```
companion skills: superpowers [installed/missing/declined], karpathy-guidelines [installed/missing/declined], clean-architecture [installed/missing/declined]
```

If the user declines to install any missing skill, note the gap once and continue. Do not re-nag in later sessions.

## Self-update check (daily, non-blocking)

Run the Check phase of `references/guides/update.md` (cache-gated to once per day). On a newer release, follow its Update + Reload phases. Any failure → skip silently and continue intake; the check never blocks.

# Step 1 — Intake (infer first, then ask)

Extract or confirm:
- Problem
- Observable result expected
- Top 2 non-goals
- Highest-shape decision

Do not assume; ground claims in `file:line`.

## Learning-loop read (if enabled)

If a profile exists at the relevant scope with `Evolution: enabled`, read it **before** proposing defaults:

- User profile: `~/.tackle/user-profile.md`
- Project profile: `.tackle/profile.md` in the repo root

Propose any profile-derived default explicitly tagged `(from your profile)`. These are proposals, never silent decisions — the user may accept or override each one.

Apply active `directive:` entries on top of the template-resolution stack when instantiating templates or briefings; project directives outrank user directives. A directive whose target section no longer exists is flagged **stale** for re-confirm-or-retire at the next retro.

Record one tally line in the log's `### Intake (context gathered)` section:

```
profile proposals: N accepted, M overridden (<which>)
```

If the profile is absent, disabled, or no defaults apply, skip this step without logging a tally.

### Archetypes

Read `references/archetypes/` alongside the profiles. When an archetype's summary matches the incoming initiative's shape, offer its skeleton — point list, edge pattern, wave shape — as a proposal explicitly tagged `(from archetype <name>)`, flagging its trap warnings with the offer. These are proposals, never silent defaults: the user may accept, adapt, or override, and overrides are retro material.

If no archetype matches, skip without offering. There is no scoring engine — read and judge, exactly like profiles and seeds.

## Decision ownership

The user decides every doubt. Batch doubts with a recommended default each; don't drip-feed. Tag each 🔴 blocking or 🟡 proceed-on-default. Under delegation, every mandatory choice becomes a provisional `Q-xx` with your default.

# Step 1.5 — Anchor the intake before sizing

Lock the problem, observable result, top 2 non-goals, and highest-shape decision before choosing a gate.

# Step 2 — Gate sizing (Full / Lite / None)

| Gate | Use for | Example |
|---|---|---|
| **None** | One-session, one-file, no handoff | add a constant, rename a local |
| **Lite** | Single-session, bounded scope, few unknowns | add one validation to an existing endpoint |
| **Full** | Multi-session / multi-track / multi-team / high uncertainty / handoff expected | introduce a new subsystem |

**Tie-breaker**: touches ≥2 modules OR changes public API OR spans sessions/teams OR handoff expected → **Full**.

## Triviality gate

A task is **trivial** only if **all** of these are true:
- one file touched;
- fewer than ~10 changed lines;
- no new behavior introduced;
- no searching needed to know what to change.

If a task later fails any criterion, announce the gate failure and enter the full loop (Lite or Full, depending on the other signals). Do not silently upgrade a trivial task; state why the gate failed.

A **Lite** task is the smallest non-trivial plan: it still needs a `plan.md`, `log.md`, and `todo.md`. Trivial tasks skip the plan workspace entirely.
