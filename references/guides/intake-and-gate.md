# Step 1 — Intake (infer first, then ask)

Extract or confirm:
- Problem
- Observable result expected
- Top 2 non-goals
- Highest-shape decision

Do not assume; ground claims in `file:line`.

# Step 1.5 — Anchor the intake before sizing

Lock the problem, observable result, top 2 non-goals, and highest-shape decision before choosing a gate.

# Step 2 — Gate sizing (Full / Lite / None)

| Gate | Use for | Example |
|---|---|---|
| **None** | One-session, one-file, no handoff | add a constant, rename a local |
| **Lite** | Single-session, bounded scope, few unknowns | add one validation to an existing endpoint |
| **Full** | Multi-session / multi-track / multi-team / high uncertainty / handoff expected | introduce a new subsystem |

**Tie-breaker**: touches ≥2 modules OR changes public API OR spans sessions/teams OR handoff expected → **Full**.
