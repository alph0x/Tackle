# Plan lint spec — mechanical checks

Every check is a literal copy-paste command: run from the **repo root**, in any POSIX shell, plain `sh`/`grep`/`sed`/`awk` only. Replace `<slug>` with the initiative directory name (workspace = `docs/plans/<slug>/`). **No shipped scripts** (D-02): these rows are documentation — pasting them, or composing them into a throwaway loop at runtime, is fine; shipping an executable is not.

- Pass conditions are mechanical — an output count or an exit code, no judgment. Any output line is a finding to report verbatim.
- No command uses the pipe character, so every cell copy-pastes verbatim from raw or rendered markdown.
- Row 1 skips content inside fenced code blocks — done-signals legitimately grep for literal `{{…}}` placeholder patterns there (D-04).
- Row 2: for plans whose id list legitimately lives in `board.md` only (pre-§5-table formats), row 2 passes if every `P-xx` in `points/` exists in `board.md`; new workspaces must list ids in `plan.md` §5 (F-3).
- Row 4 resolves citation paths from the repo root first, then retries with the `docs/plans/<slug>/` prefix.
- Row 9 anchors on the `**Type**` declaration line in a point's §Status & wiring — prose mentions of the loop-type strings elsewhere in a briefing do not trigger it.
- Judgment-only checks (contract churn, quality dimensions, Q-guard…) stay in `decompose-and-lint.md` Step 6.5 — this table holds only what a command can decide.

| Check | Command (copy-paste) | Pass condition |
|---|---|---|
| 1 · Unfilled placeholders — no `{{…}}` left outside fenced code blocks in shipped workspace files | ```` awk 'BEGIN{f=0} /^```/{f=!f; next} !f && /{{/{print FILENAME ":" FNR ": " $0}' docs/plans/<slug>/*.md docs/plans/<slug>/*/*.md ```` | 0 lines of output |
| 2 · Unresolved Depends-on — every `P-xx` referenced in `points/` or `board.md` (Depends-on lines included) exists in `plan.md` §5 | `for id in $(awk '{while(match($0,/P-[0-9]+/)){print substr($0,RSTART,RLENGTH); $0=substr($0,RSTART+RLENGTH)}}' docs/plans/<slug>/points/*.md docs/plans/<slug>/board.md); do if ! grep -q "$id" docs/plans/<slug>/plan.md; then echo "unresolved: $id"; fi; done` | 0 lines of output |
| 3 · Invalid status vocabulary — `board.md` statuses drawn only from 🔴 🟡 ⏸ 🟢 ⚪ (position-independent: legacy 5-column boards and 6-column boards with the trailing Confidence column both pass) | `awk 'BEGIN{FS=sprintf("%c",124)} $2 ~ /P-[0-9]/ && NF>3 {ok=0; for(i=2;i<=NF;i++){if(index($i,"🔴")||index($i,"🟡")||index($i,"⏸")||index($i,"🟢")||index($i,"⚪")) ok=1} if(!ok) print "bad status:" $0}' docs/plans/<slug>/board.md` | 0 lines of output |
| 4 · Malformed/stale citations — every anchored citation passes the anchored-citation drift check (fragment still on line NN) | `` awk 'match($0,/[A-Za-z0-9_\/.-]+\.[a-z]+:[0-9]+(-[0-9]+)? — "[^"]+"/){c=substr($0,RSTART,RLENGTH); p=c; sub(/:.*/,"",p); n=c; sub(/^[^:]*:/,"",n); n=n+0; split(c,q,"\""); s=q[2]; ok=0; f=p; i=0; while((getline L < f)>0){i++; if(i==n && index(L,s)) ok=1} close(f); if(i==0){f="docs/plans/<slug>/" p; while((getline L < f)>0){i++; if(i==n && index(L,s)) ok=1} close(f)} if(!ok) print FILENAME ":" FNR " stale: " c}' docs/plans/<slug>/points/*.md docs/plans/<slug>/plan.md docs/plans/<slug>/reference.md `` | 0 lines of output (0 stale) |
| 5 · Status duplicated outside `board.md` — status emoji (incl. ⚪) in `plan.md` / `points/` | `grep -rn -e 🔴 -e 🟡 -e ⏸ -e 🟢 -e ⚪ docs/plans/<slug>/plan.md docs/plans/<slug>/points` | 0 lines of output (grep exits 1) |
| 6 · Log entries out of chronological order — `## YYYY-MM-DD` headings ascending (append-only) | `awk '/^## 20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]/{d=substr($2,1,10); if(d<prev) print "out of order: " $0; prev=d}' docs/plans/<slug>/log.md` | 0 lines of output |
| 7 · SEALED ids — every `SEALED: D-xx` marker resolves in `decisions.md` | `for id in $(awk '{while(match($0,/SEALED: D-[0-9]+/)){print substr($0,RSTART+8,RLENGTH-8); $0=substr($0,RSTART+RLENGTH)}}' docs/plans/<slug>/design-contract.md docs/plans/<slug>/points/*.md); do if ! grep -q "$id" docs/plans/<slug>/decisions.md; then echo "missing seal: $id"; fi; done` | 0 lines of output |
| 8 · Cross-initiative collision — two active initiatives (board with ≥ 1 🟡) declare intersecting Touches | `` awk 'FILENAME ~ /board/ && /🟡/ {split(FILENAME,w,"/"); active[w[3]]=1} /Touches/ {split(FILENAME,w,"/"); ws=w[3]; while(match($0,/`[^`]+`/)){p=substr($0,RSTART+1,RLENGTH-2); if(seen[p] && seen[p]!=ws && active[seen[p]] && active[ws]) print "collision: " p " (" seen[p] " + " ws ")"; seen[p]=ws; $0=substr($0,RSTART+RLENGTH)}}' docs/plans/*/board.md docs/plans/*/points/*.md `` | 0 lines of output — any line is a **warn** |
| 9 · Loop-point budget fields — every `Type: discovery` point declares `Rounds:`, every `Type: experiment` point declares `Metric:`, `Threshold:` and `Rounds:` | `for f in $(grep -l '\*\*Type\*\*.*discovery' docs/plans/<slug>/points/*.md 2>/dev/null); do if ! grep -q 'Rounds:' "$f"; then echo "discovery point without Rounds budget: $f"; fi; done; for f in $(grep -l '\*\*Type\*\*.*experiment' docs/plans/<slug>/points/*.md 2>/dev/null); do if grep -q 'Metric:' "$f" && grep -q 'Threshold:' "$f" && grep -q 'Rounds:' "$f"; then :; else echo "experiment point missing metric fields: $f"; fi; done` | 0 lines of output |
| 10 · Done/blocked rows carry a grade — every `board.md` row whose status is 🟢 or ⏸ carries a Confidence grade from the 4-value vocabulary E1/E2/E3/E0 (position-independent: any field may carry it, same shape as row 3) | `awk 'BEGIN{FS=sprintf("%c",124)} $2 ~ /P-[0-9]/ && NF>3 {st=0; for(i=2;i<=NF;i++){if(index($i,"🟢")||index($i,"⏸")) st=1} if(st){ok=0; for(i=2;i<=NF;i++){if($i ~ /(^|[^A-Za-z0-9])E[0123]([^A-Za-z0-9]|$)/) ok=1} if(!ok) print "done/blocked row without grade: " $0}}' docs/plans/<slug>/board.md` | 0 lines of output |

Per-citation, row 4 is equivalent to the canonical anchored-citation check (`sed -n 'NNp' path` piped to `grep -Fq "fragment"`), composed into one throwaway loop over every citation — documented commands may be composed into throwaway runtime loops, and this one is pipe-free so the cell stays copy-pasteable.

## Release sweep

Before any version tag, run every lint row on every active workspace (`docs/plans/*/`) plus the skill's own done-signals for the release; the tag waits on a clean sweep (`lint: N/N checks passed` everywhere, all done-signals passing). Any failure blocks the tag until fixed or explicitly waived by the user.

D-13 trigger: if the release includes any change that deletes normative content from `SKILL.md` or a guide, the sweep additionally requires (1) a rule-inventory diff — every normative one-liner extracted before the edit must be greppable after, in `SKILL.md` or its named guide — and (2) one behavioral eval run (trap scenario, method arm = edited file) proving the skill still avoids the trap.

Migrate-chain currency: if the release changes any workspace-level contract (`AGENTS.tmpl.md`, status vocabulary, artifact names, closure protocol), the migrate guide MUST gain a checklist for the immediately previous version in the same release — a version bump without its migrate checklist is a release defect (precedent: v3.0→v3.1 and v3.3→v3.4 were both missed once).

### Skill self-lint gates

The shipped skill lints itself in the same sweep. Run all four from the repo root; each stays silent and exits 0 on pass — any echoed line blocks the tag until fixed. Every version value derives from the files; no gate hardcodes one.

1. **Word budget** — `SKILL.md` ≤ 1100 words:
   `[ "$(wc -w < SKILL.md)" -le 1100 ] || echo "SKILL.md over budget"`
2. **Conventions count** — exactly 11 numbered core conventions (awk anchors on the §Core conventions heading, stops at the next `##`):
   `[ "$(awk '/^## Core conventions/{f=1;next} f && /^## /{exit} f && /^[0-9]+\. /{n++} END{print n+0}' SKILL.md)" -eq 11 ] || echo "conventions count off"`
3. **Changelog currency** — newest `## Tackle X.Y.Z` heading equals the `SKILL.md` version stamp:
   `[ "$(awk '/^## Tackle /{print $3; exit}' references/CHANGELOG.md)" = "$(awk '/^\*\*Tackle /{gsub(/\*/,"",$2); print $2; exit}' SKILL.md)" ] || echo "changelog head mismatch"`
4. **Migrate-chain currency** — the checklist heading into the current major.minor exists in the migrate guide:
   `v=$(awk '/^\*\*Tackle /{gsub(/\*/,"",$2); print $2; exit}' SKILL.md); mm=${v%.*}; x=${mm%%.*}; y=${mm##*.}; if [ "$y" -gt 0 ]; then p="$x.$((y-1))"; else p="[0-9.]+"; fi; grep -Eq "^## v$p → v$mm checklist" references/guides/migrate.md || echo "missing migrate checklist → v$mm"`

Gate 4 derives the immediately previous version from the stamp: a minor bump requires exactly `v<x.(y-1)> → v<x.y>`; a major bump (`y` = 0) accepts the previous major's last minor on the left side — e.g. releasing 4.0.0 requires `## v3.4 → v4.0 checklist`.

## Score line

Run all 10 rows, then close the lint digest with exactly:

`lint: N/M checks passed`

- **M** = rows run (10 for this table; more if the workspace adds rows).
- **N** = rows whose pass condition held.
- Row 8 assumes `docs/plans/` contains only workspace directories — a stray file or non-workspace dir (e.g. a parked seed) makes the glob produce phantom paths. Park seeds elsewhere (`docs/seeds/`).
- Discussing scanned symbols inside workspaces (status glyphs, placeholder braces): use U+XXXX prose notation and `$'\uXXXX'` shell escapes so rows 1/3/5 don't self-flag the discussion.
- Row 8 is warn-severity: a collision lowers N and is reported, but blocks nothing by itself; a failure in rows 1–7, 9, and 10 blocks execution until fixed or explicitly waived by the user.
- This score line is what a human skims in a pulse or handoff for readiness (the pulse digest carries it); a lint digest without it is incomplete.
