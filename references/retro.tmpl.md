# Lessons review — {{TITLE}}

Optional PLAN learning review. This artifact records
observed causes and lessons without changing the execution procedure. Profile and reference-plan writes
remain separately confirmed and owned by the `retro` workflow.

Written at initiative close (or mid-flight as a partial retro — say so here) by mining `task-board.md` + `history.md`. Every metric is mechanical: run the recipe from the workspace root, paste the value. In a Focused (Lite) plan (no `task-board.md`), task-board metrics report `n/a`; history-derived ones stand. Note: comprehension debt counts tasks that reached Complete (legacy 🟢) with no human review recorded in the history.

## Metrics

| Metric | How to mine (copy-paste) | Value |
|---|---|---|
| Tasks by status | `if [ -f task-board.md ]; then b=task-board.md; else b=board.md; fi; awk 'BEGIN{FS=sprintf("%c",124)} function cell(i,c){c=$i; sub(/^[[:space:]]+/,"",c); sub(/[[:space:]]+$/,"",c); return c} function colof(name,i){for(i=2;i<=NF;i++) if(cell(i)==name) return i; return 0} FNR==1{col=0; pend=0} pend && $2 ~ /^[[:space:]]*:?-+:?[[:space:]]*$/ {col=pend} {pend=0} $2 !~ /[PT]-[A-Za-z0-9]/ && colof("Status"){pend=colof("Status")} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {n[cell(col ? col : 6)]++} END{for(s in n) print s,n[s]}' "$b"` | {{...}} |
| Attempts over budget | `if [ -f history.md ]; then h=history.md; else h=log.md; fi; grep -n "attempt [0-9]*:" "$h"` — count per task vs the budget in `grep -i -e budget -e attempts AGENTS.md` (the workspace AGENTS.md must declare it — compact hand-written ones should carry the template's "Default loop budget: 3 attempts" line) | {{...}} |
| Blocked durations | `if [ -f task-board.md ]; then b=task-board.md; else b=board.md; fi; if [ -f history.md ]; then h=history.md; else h=log.md; fi; grep -nE "^## [0-9]{4}-" "$h"; grep -n -e Blocked -e ⏸ "$h"` — inspect actual state events and pair each blocked event with the entry dates around it | {{...}} |
| Reopened tasks | `if [ -f task-board.md ]; then b=task-board.md; else b=board.md; fi; if [ -f history.md ]; then h=history.md; else h=log.md; fi; grep -n -e "Complete[[:space:]]*→[[:space:]]*In progress" -e "🟢[[:space:]]*→[[:space:]]*🟡" "$h"` | {{...}} |
| Comprehension debt | `if [ -f task-board.md ]; then b=task-board.md; else b=board.md; fi; if [ -f history.md ]; then h=history.md; else h=log.md; fi; awk 'BEGIN{FS=sprintf("%c",124)} function cell(i,c){c=$i; sub(/^[[:space:]]+/,"",c); sub(/[[:space:]]+$/,"",c); return c} function colof(name,i){for(i=2;i<=NF;i++) if(cell(i)==name) return i; return 0} FNR==1{col=0; pend=0} pend && $2 ~ /^[[:space:]]*:?-+:?[[:space:]]*$/ {col=pend} {pend=0} $2 !~ /[PT]-[A-Za-z0-9]/ && colof("Status"){pend=colof("Status")} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {s=cell(col ? col : 6); if((s=="Complete") + (s=="🟢")) print cell(2)}' "$b"` — for each listed task, check `history.md` for its verification record; **real debt** = Complete with NO required verification record; **accepted debt (informational)** = verified but no human review line (`grep -in "review" history.md`) — report both counts separately | {{...}} |
| Gate accuracy | `if [ -f history.md ]; then h=history.md; else h=log.md; fi; grep -in "gate" "$h" plan.md` — read the gate recorded at intake (session 1 / plan header); `grep -cE "^## [0-9]{4}-" history.md` sessions spent; `awk 'BEGIN{FS=sprintf("%c",124)} function cell(i,c){c=$i; sub(/^[[:space:]]+/,"",c); sub(/[[:space:]]+$/,"",c); return c} function colof(name,i){for(i=2;i<=NF;i++) if(cell(i)==name) return i; return 0} FNR==1{col=0; pend=0} pend && $2 ~ /^[[:space:]]*:?-+:?[[:space:]]*$/ {col=pend} {pend=0} $2 !~ /[PT]-[A-Za-z0-9]/ && colof("Status"){pend=colof("Status")} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {s=cell(col ? col : 6); if((s=="Complete") + (s=="🟢")) n++} END{print n+0}' task-board.md` tasks completed (`n/a` in Lite) — Full gate closed in ≤ 2 sessions = over-planning candidate; Lite gate spanning 3+ sessions = under-planning candidate | {{...}} |
| **Lifecycle coverage** | `if [ -f resource-usage.md ]; then u=resource-usage.md; else u=usage.md; fi; awk 'BEGIN{FS=sprintf("%c",124)} {m=$2; sub(/^[[:space:]]+/,"",m); sub(/[[:space:]]+$/,"",m); r=$6; sub(/^[[:space:]]+/,"",r); sub(/[[:space:]]+$/,"",r)} (m=="duration") + (m=="attempts") + (m=="rework") + (m=="verification") + (m=="tokens") {print m " " r}' "$u"` — report measured/eligible before arithmetic | {{...}} |
| **Exact-token coverage** | `if [ -f resource-usage.md ]; then u=resource-usage.md; else u=usage.md; fi; awk 'BEGIN{FS=sprintf("%c",124)} {m=$2; sub(/^[[:space:]]+/,"",m); sub(/[[:space:]]+$/,"",m); r=$6; sub(/^[[:space:]]+/,"",r); sub(/[[:space:]]+$/,"",r)} m=="tokens" {print m " " r}' "$u"` — zero coverage is written `0/N`, never inferred as zero usage | {{...}} |
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
