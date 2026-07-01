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


# Step 1.5 — Anchor the intake before sizing

Lock the problem, observable result, top 2 non-goals, and highest-shape decision before choosing a gate.

# Step 2 — Gate sizing (Full / Lite / None)

| Gate | Use for | Example |
|---|---|---|
| **None** | One-session, one-file, no handoff | add a constant, rename a local |
| **Lite** | Single-session, bounded scope, few unknowns | add one validation to an existing endpoint |
| **Full** | Multi-session / multi-track / multi-team / high uncertainty / handoff expected | introduce a new subsystem |

**Tie-breaker**: touches ≥2 modules OR changes public API OR spans sessions/teams OR handoff expected → **Full**.
