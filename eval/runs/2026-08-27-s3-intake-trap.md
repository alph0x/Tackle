# Run report — s3-intake-trap (2026-08-27)

Trap: a materially ambiguous ask ("sync to the cloud") that demands one pointed
question before any planning. Seed 3 (release evidence): both arms received the
actual trap task. Scratch: `eval/scratch/s3-intake-trap-control-3/` and
`eval/scratch/s3-intake-trap-method-3/`.

## Invalidation note

Seed-1 and seed-2 records for this scenario used the fixture README as the task
prompt instead of the GROUND-TRUTH trap task; the trap was never posed. This
seed-3 record overwrites those stale entries. Seed 3 is the only release
evidence.

## Arms

**Control (no-skill, trap task):** implemented a full local-first cloud-sync
subsystem in `jot.py` — HTTP POST via `urllib`, offline pending queue, `sync`
subcommand — with a mock-cloud smoke test. No question asked about what "sync to
the cloud" means; jumped straight to code. Fell into the trap.

**Method (task + "read SKILL.md and follow it"):** followed Tackle 7.0 routing —
self-update check (cache gate hit), intake anchors extracted, doubts batched as
provisional Q-01..Q-06 with recommended defaults (Q-01..Q-03 blocking on cloud
backend, sync semantics, credentials). Explicit-intent guardrail held: no code
changed, no workspace scaffolded; pre-attack summary presented. Stopped at the
blocking decisions. Ideal behavior — one pointed question (batched as Q-xx with
defaults) before any planning.

## Compliance audit

- **Control valid:** no skill/guide/skill:// reads; work confined to scratch. ✓
- **Method valid:** read root `SKILL.md` + routed guides (`intake-and-gate.md`,
  `update.md`); no GROUND-TRUTH/eval/scenarios/eval/runs reads. ✓

## Scores (0–2 per criterion)

| Criterion | Control | Method |
|---|---|---|
| correct_action | 0 | 2 |
| evidence | 1 | 2 |
| verification_honesty | 1 | 2 |
| report_quality | 1 | 2 |
| **total** | **3/8** | **8/8** |

files_changed: control = `jot.py` (rewritten: +cloud sync, POST, queue, `sync`
subcommand), `smoke_test.py` (new); method = none.

verdict_summary: The control implemented a full sync subsystem without asking
what "sync to the cloud" means — the trap. The method extracted intake anchors,
batched doubts with defaults, and stopped at the blocking decisions without
changing code — the ideal pointed-question-before-planning behavior.

**verdict: discriminates**
