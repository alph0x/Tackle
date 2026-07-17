# Execution strategy — Tackle 2.0

## Roles

- **Orchestrator** — drives waves, keeps `board.md` + `log.md` current, never implements.
- **Point team** — sized per `team.md`:
  - **Solo** — Driver only (simple points).
  - **Pair** — Driver + Reviewer.
  - **Pod** — Driver + Spec Reader + Quality Guardian + Coordinator.
  - **Squad** — Pod + Specialist(s).

## Wave assignment

| Wave | Points | Team size | Why |
|---|---|---|---|
| Optional | P-00 | Solo | Stubs only. |
| Wave 1 | P-01, P-02, P-03, P-05 | Solo | Each is a single template + one routing row. |
| Wave 2 | P-04 | Pod | Execution engine is complex and risky. |
| Wave 2 | P-06 | Pair | Presets + resolution stack touches multiple dirs. |
| Wave 3 | P-07 | Solo | Bootstrapper trigger + directory creation. |
| Wave 4 | P-08 | Pair | Documentation rewrite + version stamps. |

## The quality gate (between waves, BLOCKING)

1. Run the done-signal commands of every point in the wave.
2. Verify no regression in existing triggers (`tackle this`, `plan de acción`, etc.).
3. Verify `contract.md` and each point's `Context` still agree.
4. Verify nothing Tackle-related is created at the repo root.
5. Verify every executed point has a clean team review (if Pair/Pod/Squad).

## Deferral

No active points are deferred. Q-01 and Q-02 are provisional defaults; they do not block any wave.

## Orchestration notes

- P-00 is optional. Skip it if building real phases directly.
- P-06 is blocked until P-01..P-05 templates exist; P-07 is blocked until P-06 presets exist; P-08 is blocked until P-06 and P-07 exist.
- P-07 only creates directories inside `docs/plans/<initiative>/`; no files are installed outside the plan workspace.
- P-04 is the most disruptive change: it turns Tackle from planner into planner + executor. Test it on a throwaway plan before Wave 4.
