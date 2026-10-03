# Lessons review — {{TITLE}}

Optional PLAN learning review. This artifact records
observed causes and lessons without changing the execution procedure. Profile and reference-plan writes
remain separately confirmed and owned by the `retro` workflow.

Written at initiative close (or mid-flight as a partial retro — say so here) by mining `task-board.md` + `history.md`. Every metric is mechanical: run the recipe from the workspace root, paste the value. In a Focused (Lite) plan (no `task-board.md`), task-board metrics report `n/a`; history-derived ones stand. Note: comprehension debt counts tasks that reached Complete with no human review recorded in the history.

## Metrics

| Metric | How to mine (copy-paste) | Value |
|---|---|---|
| Tasks by status | `b=task-board.md; awk 'BEGIN{FS=sprintf("%c",124)} function cell(i,c){c=$i; sub(/^[[:space:]]+/,"",c); sub(/[[:space:]]+$/,"",c); return c} function colof(name,i){for(i=2;i<=NF;i++) if(cell(i)==name) return i; return 0} FNR==1{col=0; pend=0} pend && $2 ~ /^[[:space:]]*:?-+:?[[:space:]]*$/ {col=pend} {pend=0} $2 !~ /[PT]-[A-Za-z0-9]/ && colof("Status"){pend=colof("Status")} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {n[cell(col ? col : 6)]++} END{for(s in n) print s,n[s]}' "$b"` | {{...}} |
| Attempts over budget | `h=history.md; grep -n "attempt [0-9]*:" "$h"` — count per task against the RUN card's fixed cap of three failed correction-validation cycles per task (`guides/run-card.md`, step 7) | {{...}} |
| Blocked durations | `b=task-board.md; h=history.md; grep -nE "^## [0-9]{4}-" "$h"; grep -n -e Blocked -e ⏸ "$h"` — inspect actual state events and pair each blocked event with the entry dates around it | {{...}} |
| Reopened tasks | `b=task-board.md; h=history.md; grep -n -e "Complete[[:space:]]*→[[:space:]]*In progress" -e "🟢[[:space:]]*→[[:space:]]*🟡" "$h"` | {{...}} |
| Comprehension debt | `b=task-board.md; h=history.md; awk 'BEGIN{FS=sprintf("%c",124)} function cell(i,c){c=$i; sub(/^[[:space:]]+/,"",c); sub(/[[:space:]]+$/,"",c); return c} function colof(name,i){for(i=2;i<=NF;i++) if(cell(i)==name) return i; return 0} FNR==1{col=0; pend=0} pend && $2 ~ /^[[:space:]]*:?-+:?[[:space:]]*$/ {col=pend} {pend=0} $2 !~ /[PT]-[A-Za-z0-9]/ && colof("Status"){pend=colof("Status")} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {s=cell(col ? col : 6); if(s=="Complete") print cell(2)}' "$b"` — for each listed task, check `history.md` for its verification record; **real debt** = Complete with NO required verification record; **accepted debt (informational)** = verified but no human review line (`grep -in "review" history.md`) — report both counts separately | {{...}} |
| Gate accuracy | `h=history.md; grep -in "gate" "$h" plan.md` — read the gate recorded at intake (session 1 / plan header); `grep -cE "^## [0-9]{4}-" history.md` sessions spent; `awk 'BEGIN{FS=sprintf("%c",124)} function cell(i,c){c=$i; sub(/^[[:space:]]+/,"",c); sub(/[[:space:]]+$/,"",c); return c} function colof(name,i){for(i=2;i<=NF;i++) if(cell(i)==name) return i; return 0} FNR==1{col=0; pend=0} pend && $2 ~ /^[[:space:]]*:?-+:?[[:space:]]*$/ {col=pend} {pend=0} $2 !~ /[PT]-[A-Za-z0-9]/ && colof("Status"){pend=colof("Status")} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {s=cell(col ? col : 6); if(s=="Complete") n++} END{print n+0}' task-board.md` tasks completed (`n/a` in Lite) — Full gate closed in ≤ 2 sessions = over-planning candidate; Lite gate spanning 3+ sessions = under-planning candidate | {{...}} |
| History growth | `if [ -f history-archive.md ]; then a=history-archive.md; else a=/dev/null; fi; awk 'function flush(n){n=last-start+1; if(open) print file ":" start ": " n " lines"} FNR==1{flush(); open=0; file=FILENAME} /^## /{flush(); open=($0 ~ /^## 20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]/); start=FNR; last=FNR; next} open && $0 !~ /^[[:space:]]*$/ {last=FNR} END{flush()}' "$a" history.md` — lines per session entry, the archive first and then the active history (for indexed segments, run it on each segment in index order); a rising trend routes narrative to `decisions.md` | {{...}} |
| **Lifecycle coverage** | `u=resource-usage.md; if [ -f resource-usage.telemetry.jsonl ]; then s=resource-usage.telemetry.jsonl; elif [ -f usage.telemetry.jsonl ]; then s=usage.telemetry.jsonl; else s=/dev/null; fi; awk 'BEGIN{FS=sprintf("%c",124)} function clock(v,alt){alt=sprintf("%c",124);return v~("^[0-9][0-9][0-9][0-9]-(0[1-9]" alt "1[0-2])-(0[1-9]" alt "[12][0-9]" alt "3[01])T([01][0-9]" alt "2[0-3]):[0-5][0-9]:[0-5][0-9]" "([.][0-9]+)?(Z" alt "[+-]" "([01][0-9]" alt "2[0-3]):[0-5][0-9])$")} FNR==NR{ev=$3;sub(/^[[:space:]]+/,"",ev);sub(/[[:space:]]+$/,"",ev);rid=$2;sub(/^[[:space:]]+/,"",rid);sub(/[[:space:]]+$/,"",rid);if(rid=="")next;if(rid=="Run ID")next;if(rid=="---")next;if(ev!="start"&&ev!="finish"&&ev!="observe-incomplete"){if(NF==16)bad[rid]=1;next};at=$10;sub(/^[[:space:]]+/,"",at);sub(/[[:space:]]+$/,"",at);oc=$11;sub(/^[[:space:]]+/,"",oc);sub(/[[:space:]]+$/,"",oc);task=$4;role=$5;sub(/^[[:space:]]+/,"",task);sub(/[[:space:]]+$/,"",task);sub(/^[[:space:]]+/,"",role);sub(/[[:space:]]+$/,"",role);if(!(rid in firsttask)){firsttask[rid]=task;firstrole[rid]=role}else if(firsttask[rid]!=task)bad[rid]=1;else if(firstrole[rid]!=role)bad[rid]=1;if(ev=="start"){scount[rid]++;if(oc!="running")bad[rid]=1;if(clock(at))sok[rid]=1}else{term[rid]=1;tcount[rid]++;if(scount[rid]==0)bad[rid]=1;if(ev=="finish"){if(oc!="success"&&oc!="failed"&&oc!="blocked"&&oc!="aborted")bad[rid]=1;if(oc=="success"){fsc[rid]=1;if(clock(at))fok[rid]=1}}else if(oc!="incomplete")bad[rid]=1};next} {if($0~/"scope"[[:space:]]*:[[:space:]]*"role"/){if(match($0,/"run_id"[[:space:]]*:[[:space:]]*"[^"]*"/)){seg=substr($0,RSTART,RLENGTH);n=split(seg,pp,"\"");side[pp[4]]=1}}} END{de=0;dm=0;te=0;tm=0;for(r in term){te++;if(r in side)tm++;de++;if(fsc[r]&&sok[r]&&fok[r]&&!bad[r]&&scount[r]==1&&tcount[r]==1)dm++};if(tm==0)printf "tokens 0/N (0%%)\n";else printf "tokens %d/%d (%d%%)\n",tm,te,int(100*tm/te+0.5);if(dm==0)printf "duration 0/N (0%%)\n";else printf "duration %d/%d (%d%%)\n",dm,de,int(100*dm/de+0.5)}' "$u" "$s"` — report measured/eligible before arithmetic | {{...}} |
| **Exact-token coverage** | `u=resource-usage.md; if [ -f resource-usage.telemetry.jsonl ]; then s=resource-usage.telemetry.jsonl; elif [ -f usage.telemetry.jsonl ]; then s=usage.telemetry.jsonl; else s=/dev/null; fi; awk 'BEGIN{FS=sprintf("%c",124)} FNR==NR{ev=$3;sub(/^[[:space:]]+/,"",ev);sub(/[[:space:]]+$/,"",ev);if(ev!="start"&&ev!="finish"&&ev!="observe-incomplete")next;rid=$2;sub(/^[[:space:]]+/,"",rid);sub(/[[:space:]]+$/,"",rid);if(ev!="start")term[rid]=1;next} {if($0~/"scope"[[:space:]]*:[[:space:]]*"role"/){if(match($0,/"run_id"[[:space:]]*:[[:space:]]*"[^"]*"/)){seg=substr($0,RSTART,RLENGTH);n=split(seg,pp,"\"");side[pp[4]]=1}}} END{te=0;tm=0;for(r in term){te++;if(r in side)tm++};if(tm==0)printf "tokens 0/N (0%%)\n";else printf "tokens %d/%d (%d%%)\n",tm,te,int(100*tm/te+0.5)}' "$u" "$s"` — zero coverage is written `0/N`, never inferred as zero usage | {{...}} |
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

Filled only when evolution is enabled — see the learning-loop section of `guides/retro.md`. Every candidate requires explicit, batched user confirmation before being recorded anywhere, with a stable `id` and a computed confidence (never proposed or hand-set).

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
