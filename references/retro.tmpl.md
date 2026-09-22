# Lessons review — {{TITLE}}

Optional PLAN learning review. This artifact records
observed causes and lessons without changing the execution procedure. Profile and reference-plan writes
remain separately confirmed and owned by the `retro` workflow.

Written at initiative close (or mid-flight as a partial retro — say so here) by mining `board.md` + `log.md`. Every metric is mechanical: run the recipe from the workspace root, paste the value. In a Lite plan (no `board.md`), board-derived metrics report `n/a`; log-derived ones stand. Note: comprehension debt counts tasks that reached Complete (legacy 🟢) with no human review recorded in the log.

## Metrics

| Metric | How to mine (copy-paste) | Value |
|---|---|---|
| Tasks by status | `awk 'BEGIN{FS=sprintf("%c",124)} $2 ~ /^[[:space:]]*P-[A-Za-z0-9-]+[[:space:]]*$/ {s=$6;gsub(/^[[:space:]]+|[[:space:]]+$/,"",s);n[s]++} END{for(s in n) print s,n[s]}' board.md` | {{...}} |
| Attempts over budget | `grep -n "attempt [0-9]*:" log.md` — count per task vs the budget in `grep -i "budget\|attempts" AGENTS.md` (the workspace AGENTS.md must declare it — compact hand-written ones should carry the template's "Default loop budget: 3 attempts" line) | {{...}} |
| Blocked durations | `grep -nE "^## [0-9]{4}-" log.md; grep -nE "Blocked|⏸" log.md` — inspect actual state events and pair each blocked event with the entry dates around it | {{...}} |
| Reopened tasks | `grep -nE "Complete[[:space:]]*→[[:space:]]*In progress|🟢[[:space:]]*→[[:space:]]*🟡" log.md` | {{...}} |
| Comprehension debt | `awk 'BEGIN{FS=sprintf("%c",124)} $2 ~ /^[[:space:]]*P-[A-Za-z0-9-]+[[:space:]]*$/ {s=$6;gsub(/^[[:space:]]+|[[:space:]]+$/,"",s);if(s=="Complete" || s=="🟢") print $2}' board.md` — for each listed task, check `log.md` for its verification record; **real debt** = Complete with NO required verification record; **accepted debt (informational)** = verified but no human review line (`grep -in "review" log.md`) — report both counts separately | {{...}} |
| Gate accuracy | `grep -in "gate" log.md plan.md` — read the gate recorded at intake (session 1 / plan header); `grep -cE "^## [0-9]{4}-" log.md` sessions spent; `awk 'BEGIN{FS=sprintf("%c",124)} $2 ~ /^[[:space:]]*P-[A-Za-z0-9-]+[[:space:]]*$/ {s=$6;gsub(/^[[:space:]]+|[[:space:]]+$/,"",s);if(s=="Complete" || s=="🟢") n++} END{print n+0}' board.md` tasks completed (`n/a` in Lite) — Full gate closed in ≤ 2 sessions = over-planning candidate; Lite gate spanning 3+ sessions = under-planning candidate | {{...}} |
| **Lifecycle coverage** | `awk -F'|' '/^\\| (duration|attempts|rework|verification|tokens)/ {m=$2; gsub(/^ +| +$/,"",m); printf "%s %s/%s (%s)\\n", m,$4,$5,$6}' usage.md` — report measured/eligible before arithmetic | {{...}} |
| **Exact-token coverage** | `awk -F'|' '/^\\| tokens / {printf "tokens %s/%s (%s)\\n",$4,$5,$6}' usage.md` — zero coverage is written `0/N`, never inferred as zero usage | {{...}} |
| **Totals and recommendations** | Gate totals/rankings at 100% comparable coverage; gate tier/effort recommendations at 100% plus at least three like-for-like completed runs | {{...}} |


These history searches identify candidates, not automatic event counts: exclude examples, checkpoints and duplicate summaries; pair original task events and dates. Use the validated chronological history index when archives exist. Missing, ambiguous or unsupported history makes the affected metric `n/a`, never an inferred zero.

Usage metrics report `n/a` when the workspace has no `usage.md` (same convention as Lite board metrics). Missing values remain `n/a`; no recipe prints an invalid zero-over-zero denominator.

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
