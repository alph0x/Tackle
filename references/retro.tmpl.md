# Lessons review — {{TITLE}}

Optional PLAN learning review. This artifact records
observed causes and lessons without changing the execution procedure. Profile and reference-plan writes
remain separately confirmed and owned by the `retro` workflow.

Written at initiative close (or mid-flight as a partial retro — say so here) by mining `task-board.md` + `history.md`. Every metric is mechanical: run the recipe from the workspace root, paste the value. In a Focused (Lite) plan (no `task-board.md`), task-board metrics report `n/a`; history-derived ones stand. Note: comprehension debt counts tasks that reached Complete (legacy 🟢) with no human review recorded in the history.

## Metrics

| Metric | How to mine (copy-paste) | Value |
|---|---|---|
| Tasks by status | `b=task-board.md; [ -f "$b" ] || b=board.md; awk 'BEGIN{FS=sprintf("%c",124)} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {s=$6;gsub(/^[[:space:]]+|[[:space:]]+$/,"",s);n[s]++} END{for(s in n) print s,n[s]}' "$b"` | {{...}} |
| Attempts over budget | `h=history.md; [ -f "$h" ] || h=log.md; grep -n "attempt [0-9]*:" "$h"` — count per task vs the budget in `grep -i "budget\|attempts" AGENTS.md` (the workspace AGENTS.md must declare it — compact hand-written ones should carry the template's "Default loop budget: 3 attempts" line) | {{...}} |
| Blocked durations | `b=task-board.md; [ -f "$b" ] || b=board.md; h=history.md; [ -f "$h" ] || h=log.md; grep -nE "^## [0-9]{4}-" "$h"; grep -nE "Blocked|⏸" "$h"` — inspect actual state events and pair each blocked event with the entry dates around it | {{...}} |
| Reopened tasks | `b=task-board.md; [ -f "$b" ] || b=board.md; h=history.md; [ -f "$h" ] || h=log.md; grep -nE "Complete[[:space:]]*→[[:space:]]*In progress|🟢[[:space:]]*→[[:space:]]*🟡" "$h"` | {{...}} |
| Comprehension debt | `b=task-board.md; [ -f "$b" ] || b=board.md; h=history.md; [ -f "$h" ] || h=log.md; awk 'BEGIN{FS=sprintf("%c",124)} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {s=$6;gsub(/^[[:space:]]+|[[:space:]]+$/,"",s);if(s=="Complete" || s=="🟢") print $2}' "$b"` — for each listed task, check `history.md` for its verification record; **real debt** = Complete with NO required verification record; **accepted debt (informational)** = verified but no human review line (`grep -in "review" history.md`) — report both counts separately | {{...}} |
| Gate accuracy | `h=history.md; [ -f "$h" ] || h=log.md; grep -in "gate" "$h" plan.md` — read the gate recorded at intake (session 1 / plan header); `grep -cE "^## [0-9]{4}-" history.md` sessions spent; `awk 'BEGIN{FS=sprintf("%c",124)} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {s=$6;gsub(/^[[:space:]]+|[[:space:]]+$/,"",s);if(s=="Complete" || s=="🟢") n++} END{print n+0}' task-board.md` tasks completed (`n/a` in Lite) — Full gate closed in ≤ 2 sessions = over-planning candidate; Lite gate spanning 3+ sessions = under-planning candidate | {{...}} |
| **Lifecycle coverage** | `u=resource-usage.md; [ -f "$u" ] || u=usage.md; awk -F'|' '/^\\| (duration|attempts|rework|verification|tokens)/ {m=$2; gsub(/^ +| +$/,"",m); printf "%s %s/%s (%s)\\n", m,$4,$5,$6}' "$u"` — report measured/eligible before arithmetic | {{...}} |
| **Exact-token coverage** | `u=resource-usage.md; [ -f "$u" ] || u=usage.md; awk -F'|' '/^\\| tokens / {printf "tokens %s/%s (%s)\\n",$4,$5,$6}' "$u"` — zero coverage is written `0/N`, never inferred as zero usage | {{...}} |
| **Totals and recommendations** | Gate totals/rankings at 100% comparable coverage; gate tier/effort recommendations at 100% plus at least three like-for-like completed runs | {{...}} |


These history searches identify candidates, not automatic event counts: exclude examples, checkpoints and duplicate summaries; pair original task events and dates. Use the validated chronological history index when archives exist. Missing, ambiguous or unsupported history makes the affected metric `n/a`, never an inferred zero.

Resource usage metrics report `n/a` when the workspace has no `resource-usage.md` (same convention as Focused task-board metrics). Missing values remain `n/a`; no recipe prints an invalid zero-over-zero denominator.

## What worked

- {{...}}

## What didn't

- {{...}}

## Lessons

- {{one line each, actionable by a future plan}}

<a id="profile-candidates"></a>
## Preferences and lessons candidates

Filled only when evolution is enabled — see the learning-loop section of `guides/retro.md`. Every candidate requires explicit, batched user confirmation before being recorded anywhere.

- {{none}}

<a id="plan-archetype-candidate"></a>
## Reference plan candidate

Filled only when the decomposition held — see the archetype section of `guides/retro.md`; format fixed by `references/archetypes/README.md`. Like profile candidates: explicit, batched user confirmation before writing; only the `retro` workflow writes archetypes.

- **Name**: {{kebab-case name}}
- **Summary**: {{one line}}
- **Task list**: {{titles + one-line responsibility each}}
- **Edge pattern**: {{dependency-graph shape}}
- **Wave shape**: {{execution waves}}
- **Trap warnings**: {{what nearly or did break}}
- **Provenance**: {{this initiative, retro link}}

{{none}}
