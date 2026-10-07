# Fee statements — one printed statement per plot

> Workspace of the fee-statements initiative (Tackle 9.0.1). Agreements: `AGENTS.md`.

Every spring the treasurer writes a fee statement for each plot by hand from the register, and every spring
a few of them carry the wrong rate. The society wants them rendered from the register instead.

## Objective

`python3 -m statements render <plots.csv> <season> <out.txt>` writes the agreed statements, with the layout
documented and acceptance passed against the agreed sample.

## Index

| Doc | Contents |
|---|---|
| `plan.md` | objective, exclusions, task split |
| `task-board.md` | state of each task |
| `history.md` | session journal, newest last; older entries in `history-archive.md` |
| `resource-usage.md` | lifecycle rows per run |
| `questions.md`, `decisions.md` | questions; settled choices |
| `reference.md` | code map |
| `tasks/`, `reports/`, `verification-records/` | briefs, task reports, raw check captures |

## Reading order

`AGENTS.md` → `task-board.md` → newest `history.md` entry → the reports.
