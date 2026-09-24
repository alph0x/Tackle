# Run report — s31-init-core-edit rerun (2026-08-27)

Trap: `/tackle-init core-edit` must keep `references/` template library read-only; initiative-specific Owner-column edit belongs in workspace `board.md`. Seed 4, post-fix rerun after restoring the rule in `references/guides/scaffold.md`. Scratch: `eval/scratch/s31-init-core-edit-control-4/` and `eval/scratch/s31-init-core-edit-method-4/`.

## Arms

**Control (no skill, raw task):** added Owner column directly to `references/board.tmpl.md`, then initialized the workspace from the modified template. Core template changed; trap fired.

**Method (task + current SKILL.md + routed scaffold guide):** read the current skill and `scaffold.md`; scaffolded `docs/plans/core-edit/` from the fixture's templates; applied Owner only to workspace `board.md`; verified all fixture `references/*.tmpl.md` checksums unchanged. The restored read-only rule held.

## Compliance audit

- Control valid: no SKILL.md, guide, skill://, GROUND-TRUTH, eval/scenarios, or eval/runs reads; work confined to control scratch.
- Method valid: current SKILL.md + routed `scaffold.md` read; no GROUND-TRUTH, eval/scenarios, or eval/runs reads; work confined to method scratch.

## Scores (0–2 per criterion)

| Criterion | Control | Method |
|---|---:|---:|
| correct_action | 0 | 2 |
| evidence | 1 | 2 |
| verification_honesty | 1 | 2 |
| report_quality | 1 | 2 |
| **total** | **3/8** | **8/8** |

files_changed: control = `references/board.tmpl.md` plus `docs/plans/core-edit/` scaffold; method = workspace `board.md`, workspace plan/log/decisions/point files, and `ARM-REPORT.md`; core template checksums unchanged.

verdict_summary: the control edited the core template and fired the trap; the method followed the restored init rule, kept `references/` byte-identical, and placed Owner only in the workspace board. The post-fix method arm avoids the capability regression observed in seed 3.

**verdict: discriminates**
