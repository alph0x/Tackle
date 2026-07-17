# Retro — {{TITLE}}

Written at initiative close (or mid-flight as a partial retro — say so here) by mining `board.md` + `log.md`. Every metric is mechanical: run the recipe from the workspace root, paste the value. In a Lite plan (no `board.md`), board-derived metrics report `n/a`; log-derived ones stand. Note: comprehension debt counts points that flipped 🟢 with no human review recorded in the log.

## Metrics

| Metric | How to mine (copy-paste) | Value |
|---|---|---|
| Points by status | `for s in 🔴 🟡 ⏸ 🟢; do echo "$s $(grep -c -- "$s" board.md)"; done` | {{...}} |
| Attempts over budget | `grep -n "attempt [0-9]*:" log.md` — count per point vs the budget in `grep -i "budget" AGENTS.md` | {{...}} |
| Blocked durations | `grep -nE "^## [0-9]{4}-" log.md; grep -n "⏸" log.md` — pair each ⏸ line with the entry dates around it | {{...}} |
| Reopened points | `grep -n "🟢 → 🟡" log.md` | {{...}} |
| Comprehension debt | `awk -F'\|' '/🟢/ {print $2}' board.md` — for each listed point, `grep -in "review" log.md`; 🟢 with no review line = debt | {{...}} |
| Gate accuracy | `grep -in "gate" log.md plan.md` — read the gate recorded at intake (session 1 / plan header); `grep -cE "^## [0-9]{4}-" log.md` sessions spent; `grep -c "🟢" board.md` points executed (`n/a` in Lite) — Full gate closed in ≤ 2 sessions = over-planning candidate; Lite gate spanning 3+ sessions = under-planning candidate | {{...}} |

## What worked

- {{...}}

## What didn't

- {{...}}

## Lessons

- {{one line each, actionable by a future plan}}

## Profile candidates

Filled only when evolution is enabled — see the learning-loop section of `guides/retro.md`. Every candidate requires explicit, batched user confirmation before being recorded anywhere.

- {{none}}
