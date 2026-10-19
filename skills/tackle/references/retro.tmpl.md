# Lessons review — {{TITLE}}

Optional PLAN learning review: it records observed causes and lessons without changing the execution
procedure. Profile and reference-plan writes stay separately confirmed and owned by the `retro` workflow.

Written at initiative close (or mid-flight as a partial retro — say so here) by mining `task-board.md` + `history.md`. Every metric is mechanical: run the recipe from the workspace root, paste the value. In a Focused (Lite) plan (no `task-board.md`), task-board metrics report `n/a`; history-derived ones stand. Comprehension debt counts tasks that reached Complete with no human review recorded in the history.

## Metrics

| Metric | How to mine (copy-paste) | Value |
|---|---|---|
| Tasks by status | `b=task-board.md; awk 'BEGIN{FS=sprintf("%c",124)} function cell(i,c){c=$i; sub(/^[[:space:]]+/,"",c); sub(/[[:space:]]+$/,"",c); return c} function colof(name,i){for(i=2;i<=NF;i++) if(cell(i)==name) return i; return 0} FNR==1{col=0; pend=0} pend && $2 ~ /^[[:space:]]*:?-+:?[[:space:]]*$/ {col=pend} {pend=0} $2 !~ /[PT]-[A-Za-z0-9]/ && colof("Status"){pend=colof("Status")} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {n[cell(col ? col : 6)]++} END{for(s in n) print s,n[s]}' "$b"` | {{...}} |
| Attempts over budget | `if [ -f history-archive.md ]; then a=history-archive.md; else a=/dev/null; fi; awk 'function note(id) { if (!((ent SUBSEP id) in seen)) { seen[ent SUBSEP id] = 1; elst[++eln] = id } } function endentry(  k, j) { for (k = 1; k <= pn; k++) { if (eln == 0) print "unattributed " pl[k]; else for (j = 1; j <= eln; j++) cnt[elst[j]]++ } pn = 0; eln = 0; ent++ } FNR == 1 { endentry(); snap = 0 } /^## / { endentry(); snap = 0; next } /^### / { snap = (tolower($0) ~ "^### state snapshot"); next } /^#/ { next } snap { next } { n = 0; s = " " $0 " "; while (match(s, "[^A-Za-z0-9][PT]-[A-Za-z0-9]+")) { ids[++n] = substr(s, RSTART + 1, RLENGTH - 1); s = substr(s, RSTART + RLENGTH) } for (j = 1; j <= n; j++) note(ids[j]); x = tolower($0); hit = 0; if (x ~ "attempt [1-9][0-9]*:") hit = 1; if (x ~ "correction cycle [1-9][0-9]*") hit = 1; if (x ~ "correction [1-9][0-9]* of [0-9]") hit = 1; if (hit) { tot++; print FILENAME ":" FNR ": " $0; if (n == 0) { pn++; pl[pn] = FILENAME ":" FNR } else for (j = 1; j <= n; j++) if (!((FILENAME SUBSEP FNR SUBSEP ids[j]) in onl)) { onl[FILENAME SUBSEP FNR SUBSEP ids[j]] = 1; cnt[ids[j]]++ } } } END { endentry(); for (id in cnt) { print id " " cnt[id]; if (cnt[id] > 3) print "over cap: " id } if (tot == 0) print "none" }' "$a" history.md` — count journal lines per task against the RUN card's fixed cap of three failed correction-validation cycles per task (`guides/run-card.md`, step 7). Counts `attempt N:`, `correction cycle N` and `correction N of M` lines (N ≥ 1) in `history-archive.md` (when present) and then `history.md`; `### State snapshot` blocks are skipped. | {{...}} |
| Blocked durations | `awk 'FNR == 1 { snap = 0 } /^## / { snap = 0; if ($0 ~ "^## [0-9][0-9][0-9][0-9]-") print FILENAME ":" FNR ": " $0; next } /^### / { snap = (tolower($0) ~ "^### state snapshot"); next } snap { next } { hit = 0; if (index($0, "Blocked")) hit = 1; if (index($0, "⏸")) hit = 1; if (hit) print FILENAME ":" FNR ": " $0 }' history.md` — inspect actual state events (`### State snapshot` lines excluded) and pair each blocked event with the entry dates around it | {{...}} |
| Reopened tasks | `b=task-board.md; h=history.md; grep -n -e "Complete[[:space:]]*→[[:space:]]*In progress" -e "🟢[[:space:]]*→[[:space:]]*🟡" "$h"` | {{...}} |
| Comprehension debt | `b=task-board.md; h=history.md; awk 'BEGIN{FS=sprintf("%c",124)} function cell(i,c){c=$i; sub(/^[[:space:]]+/,"",c); sub(/[[:space:]]+$/,"",c); return c} function colof(name,i){for(i=2;i<=NF;i++) if(cell(i)==name) return i; return 0} FNR==1{col=0; pend=0} pend && $2 ~ /^[[:space:]]*:?-+:?[[:space:]]*$/ {col=pend} {pend=0} $2 !~ /[PT]-[A-Za-z0-9]/ && colof("Status"){pend=colof("Status")} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {s=cell(col ? col : 6); if(s=="Complete") print cell(2)}' "$b"` — for each listed task, check `history.md` for its verification record; **real debt** = Complete with NO required verification record; **accepted debt (informational)** = verified but no human review line (`grep -in "review" history.md`) — report both counts separately | {{...}} |
| Gate accuracy | `awk '/^Gate: / && !g { print; g = 1 } END { if (!g) print "gate n/a" }' plan.md; if [ -f history-archive.md ]; then a=history-archive.md; else a=/dev/null; fi; awk 'FNR == 1 { fence = 0; comment = 0 } { t = " " tolower($0) " "; was = (fence + comment > 0); if (!was && substr($0, 1, 3) == "## ") { h = tolower($0); dated = ($0 ~ "^## [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]"); key = ""; if (match(h, "session [1-9][0-9]*")) key = "label:" substr(h, RSTART + 8, RLENGTH - 8); else if (dated) key = "date:" substr($0, 4, 10); if (key != "" && !(key in seen)) { seen[key] = 1; nk++ } if (!dated) print "undated heading: " FILENAME ":" FNR } if (substr($0, 1, 3) == sprintf("%c%c%c", 96, 96, 96)) fence = !fence; if (substr($0, 1, 3) == "~~~") fence = !fence; if (!fence && index($0, "<!--")) comment = 1; if (comment && index($0, "-->")) comment = 0; if (t ~ "[^a-z]gate[^a-z]") print FILENAME ":" FNR ": " $0 } END { print "sessions " (nk + 0) }' "$a" history.md; if [ -f task-board.md ]; then awk 'BEGIN{FS=sprintf("%c",124)} function cell(i,c){c=$i; sub(/^[[:space:]]+/,"",c); sub(/[[:space:]]+$/,"",c); return c} function colof(name,i){for(i=2;i<=NF;i++) if(cell(i)==name) return i; return 0} FNR==1{col=0; pend=0} pend && $2 ~ /^[[:space:]]*:?-+:?[[:space:]]*$/ {col=pend} {pend=0} $2 !~ /[PT]-[A-Za-z0-9]/ && colof("Status"){pend=colof("Status")} $2 ~ /^[[:space:]]*[PT]-[A-Za-z0-9-]+[[:space:]]*$/ {s=cell(col ? col : 6); if(s=="Complete") n++} END{print "completed " n+0}' task-board.md; else echo "completed n/a"; fi` — read the gate recorded at intake (the first `Gate:` line of `plan.md`, else `gate n/a`) against the sessions spent (distinct `session N` labels or dates over the archive and history; an undated `## ` heading is listed for review) and the tasks completed (`completed n/a` without `task-board.md`, as in Lite). Full gate closed in ≤ 2 sessions = over-planning candidate; Lite gate spanning 3+ sessions = under-planning candidate. | {{...}} |
| History growth | `if [ -f history-archive.md ]; then a=history-archive.md; else a=/dev/null; fi; awk 'function flush(n){n=last-start+1; if(open) print file ":" start ": " n " lines"} FNR==1{flush(); open=0; file=FILENAME} /^## /{flush(); open=($0 ~ /^## 20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]/); start=FNR; last=FNR; next} open && $0 !~ /^[[:space:]]*$/ {last=FNR} END{flush()}' "$a" history.md` — lines per session entry, the archive first and then the active history (for indexed segments, run it on each segment in index order); a rising trend routes narrative to `decisions.md` | {{...}} |
| **Lifecycle coverage** | `u=resource-usage.md; if [ -f resource-usage.telemetry.jsonl ]; then s=resource-usage.telemetry.jsonl; elif [ -f usage.telemetry.jsonl ]; then s=usage.telemetry.jsonl; else s=/dev/null; fi; awk 'BEGIN{FS=sprintf("%c",124)} function clock(v,alt){alt=sprintf("%c",124);return v~("^[0-9][0-9][0-9][0-9]-(0[1-9]" alt "1[0-2])-(0[1-9]" alt "[12][0-9]" alt "3[01])T([01][0-9]" alt "2[0-3]):[0-5][0-9]:[0-5][0-9]" "([.][0-9]+)?(Z" alt "[+-]" "([01][0-9]" alt "2[0-3]):[0-5][0-9])$")} FNR==NR{ev=$3;sub(/^[[:space:]]+/,"",ev);sub(/[[:space:]]+$/,"",ev);rid=$2;sub(/^[[:space:]]+/,"",rid);sub(/[[:space:]]+$/,"",rid);if(rid=="")next;if(rid=="Run ID")next;if(rid=="---")next;if(ev!="start"&&ev!="finish"&&ev!="observe-incomplete"){if(NF==16)bad[rid]=1;next};at=$10;sub(/^[[:space:]]+/,"",at);sub(/[[:space:]]+$/,"",at);oc=$11;sub(/^[[:space:]]+/,"",oc);sub(/[[:space:]]+$/,"",oc);task=$4;role=$5;sub(/^[[:space:]]+/,"",task);sub(/[[:space:]]+$/,"",task);sub(/^[[:space:]]+/,"",role);sub(/[[:space:]]+$/,"",role);if(!(rid in firsttask)){firsttask[rid]=task;firstrole[rid]=role}else if(firsttask[rid]!=task)bad[rid]=1;else if(firstrole[rid]!=role)bad[rid]=1;if(ev=="start"){scount[rid]++;if(oc!="running")bad[rid]=1;if(clock(at))sok[rid]=1}else{term[rid]=1;tcount[rid]++;if(scount[rid]==0)bad[rid]=1;if(ev=="finish"){if(oc!="success"&&oc!="failed"&&oc!="blocked"&&oc!="aborted")bad[rid]=1;if(oc=="success"){fsc[rid]=1;if(clock(at))fok[rid]=1}}else if(oc!="incomplete")bad[rid]=1};next} {if($0~/"scope"[[:space:]]*:[[:space:]]*"role"/){if(match($0,/"run_id"[[:space:]]*:[[:space:]]*"[^"]*"/)){seg=substr($0,RSTART,RLENGTH);n=split(seg,pp,"\"");side[pp[4]]=1}}} END{de=0;dm=0;te=0;tm=0;for(r in term){te++;if(r in side)tm++;de++;if(fsc[r]&&sok[r]&&fok[r]&&!bad[r]&&scount[r]==1&&tcount[r]==1)dm++};if(tm==0)printf "tokens 0/N (0%%)\n";else printf "tokens %d/%d (%d%%)\n",tm,te,int(100*tm/te+0.5);if(dm==0)printf "duration 0/N (0%%)\n";else printf "duration %d/%d (%d%%)\n",dm,de,int(100*dm/de+0.5)}' "$u" "$s"` — report measured/eligible before arithmetic | {{...}} |
| **Exact-token coverage** | `u=resource-usage.md; if [ -f resource-usage.telemetry.jsonl ]; then s=resource-usage.telemetry.jsonl; elif [ -f usage.telemetry.jsonl ]; then s=usage.telemetry.jsonl; else s=/dev/null; fi; awk 'BEGIN{FS=sprintf("%c",124)} FNR==NR{ev=$3;sub(/^[[:space:]]+/,"",ev);sub(/[[:space:]]+$/,"",ev);if(ev!="start"&&ev!="finish"&&ev!="observe-incomplete")next;rid=$2;sub(/^[[:space:]]+/,"",rid);sub(/[[:space:]]+$/,"",rid);if(ev!="start")term[rid]=1;next} {if($0~/"scope"[[:space:]]*:[[:space:]]*"role"/){if(match($0,/"run_id"[[:space:]]*:[[:space:]]*"[^"]*"/)){seg=substr($0,RSTART,RLENGTH);n=split(seg,pp,"\"");side[pp[4]]=1}}} END{te=0;tm=0;for(r in term){te++;if(r in side)tm++};if(tm==0)printf "tokens 0/N (0%%)\n";else printf "tokens %d/%d (%d%%)\n",tm,te,int(100*tm/te+0.5)}' "$u" "$s"` — zero coverage is written `0/N`, never inferred as zero usage | {{...}} |
| **Totals and recommendations** | Gate totals/rankings at 100% comparable coverage; gate tier/effort recommendations at 100% plus at least three like-for-like completed runs | {{...}} |


History searches find candidates, not automatic event counts: exclude examples, checkpoints and duplicate summaries; pair original task events and dates; use the validated chronological history index when archives exist. Missing, ambiguous or unsupported history makes the affected metric `n/a`, never an inferred zero.

Resource usage metrics report `n/a` without a `resource-usage.md`, as Focused task-board metrics do. Missing values stay `n/a`; no recipe prints an invalid zero-over-zero denominator.

## What worked

- {{...}}

## What didn't

- {{...}}

## Lessons

- {{one line each, actionable by a future plan}}

<a id="profile-candidates"></a>
## Preferences and lessons candidates

Filled only when evolution is enabled (learning-loop section of `guides/retro.md`). Every candidate requires explicit, batched user confirmation before being recorded anywhere, with a stable `id` and a computed confidence (never proposed or hand-set).

- {{none}}

<a id="plan-archetype-candidate"></a>
## Reference plan candidate

Filled only when the decomposition held (archetype section of `guides/retro.md`; format fixed by `references/archetypes/README.md`). Like profile candidates: explicit, batched user confirmation before writing; only the `retro` workflow writes archetypes.

- **Name**: {{kebab-case name}}
- **Summary**: {{one line}}
- **Task list**: {{titles + one-line responsibility each}}
- **Edge pattern**: {{dependency-graph shape}}
- **Wave shape**: {{execution waves}}
- **Trap warnings**: {{what nearly or did break}}
- **Provenance**: {{this initiative, retro link}}

{{none}}
