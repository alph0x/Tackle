# Retro — initiative retrospective

Triggered by `retro [initiative]` or a natural phrase like "retro" / "how did it go". Retro
is optional: run it at initiative close or on demand as a clearly labelled partial retro. It does
not replace RUN closure or create an autonomy loop.

**Principle: detection before judgment.** Mine `task-board.md` + `history.md` by grep/count first; use judgment only to distill the counts into lessons. For an unindexed archive, mining reads `history-archive.md` then `history.md`. For indexed segments use the validated chronological archive index from `context-lifecycle.md`, then the active history; never count checkpoints or summaries as original events. Missing/corrupt history makes affected metrics unavailable, never zero. Read-only over the selected task board, history and `decisions.md`; writes go where [Where results go](#where-results-go) lists them, starting with `docs/plans/<initiative>/retro.md` (instantiated from `references/retro.tmpl.md`).

## Metrics — mined, not remembered

Every metric carries a copy-paste recipe; the recipes live in the template's Metrics table. What each one measures:

- **Tasks by status** — count exact task rows and their Status field in `task-board.md`, using its declared schema.
- **Attempts over budget** — count `attempt N:` journal lines per task in `history.md` against the attempt budget declared in the workspace `AGENTS.md`.
- **Blocked durations** — dates between the log entry that marks a task Blocked (legacy ⏸) and the entry that unblocks it.
- **Reopened tasks** — `Complete → In progress` or legacy `🟢 → 🟡` transitions in `history.md` (regression-sweep reopenings included).
- **Comprehension debt** — tasks recorded Complete with no human review recorded in the log: mechanically done, humanly unread. High comprehension debt is a warning even when the board is all green.
- **Gate accuracy** — the gate recorded at intake vs actual effort (tasks executed, sessions spent): Full-gate initiatives closed in ≤ 2 sessions are over-planning candidates; Lite-gate ones spanning 3+ sessions are under-planning candidates.
- **Exact-token coverage** — measured/eligible by metric and comparable scope, with `n/a` rows visible before any arithmetic.
- **Coverage-gated totals** — cohort totals and rankings only after 100% comparable coverage; otherwise report labeled observations and suppress the aggregate.
- **Coverage-gated recommendations** — tier/effort recommendations only after 100% coverage plus at least three like-for-like completed runs.
- **History growth** — lines per `history.md` session entry (recipe in `retro.tmpl.md`): resume cost compounds across every future session, unlike execution cost which is paid once per task; a rising trend routes narrative back to `decisions.md`/`reference-docs/`.

## Lifecycle-first coverage

Read the v2 ledger before any token arithmetic. For every metric and comparable scope, print
`measured/eligible` plus a percentage; no eligible rows are shown as `0/N (0%)`, never as a
zero-over-zero denominator. Duration, attempts, rework, incomplete runs, verification outcomes,
and task time-to-green remain useful when exact telemetry coverage is 0%.

- At 0% exact-token coverage, report `0/N (0%)` and suppress token totals, shares, rankings, and
  recommendations.
- Partial exact coverage may list labeled observations, but totals and rankings require 100%
  comparable coverage; mixed role/session scopes remain separate and unjoined.
- Tier/effort recommendations require 100% coverage, identical scope/source/semantics, and at
  least three completed like-for-like runs; otherwise label the result a hypothesis.

### Fixture recipe

Run `s=resource-usage.telemetry.jsonl; [ -f "$s" ] || s=/dev/null; awk 'BEGIN{FS=sprintf("%c",124)} FNR==NR{ev=$3;sub(/^[[:space:]]+/,"",ev);sub(/[[:space:]]+$/,"",ev);if(ev!="start"&&ev!="finish"&&ev!="observe-incomplete")next;rid=$2;sub(/^[[:space:]]+/,"",rid);sub(/[[:space:]]+$/,"",rid);at=$10;sub(/^[[:space:]]+/,"",at);sub(/[[:space:]]+$/,"",at);oc=$11;sub(/^[[:space:]]+/,"",oc);sub(/[[:space:]]+$/,"",oc);if(ev=="start"){if(at!=""&&at!="n/a")sok[rid]=1}else{term[rid]=1;if(ev=="finish"&&oc=="success"){fsc[rid]=1;if(at!=""&&at!="n/a")fok[rid]=1}};next} {if($0~/"scope"[[:space:]]*:[[:space:]]*"role"/){if(match($0,/"run_id"[[:space:]]*:[[:space:]]*"[^"]*"/)){seg=substr($0,RSTART,RLENGTH);n=split(seg,pp,"\"");side[pp[4]]=1}}} END{de=0;dm=0;te=0;tm=0;for(r in term){te++;if(r in side)tm++;de++;if(fsc[r]&&sok[r]&&fok[r])dm++};if(tm==0)printf "tokens 0/N (0%%)\n";else printf "tokens %d/%d (%d%%)\n",tm,te,int(100*tm/te+0.5);if(dm==0)printf "duration 0/N (0%%)\n";else printf "duration %d/%d (%d%%)\n",dm,de,int(100*dm/de+0.5)}' resource-usage.md "$s"` from a fixture workspace.

`Measured/Eligible` counts distinct `Run ID` role-instances that reached a terminal
event (`finish` or `observe-incomplete`); `duration` also needs a `finish` with `Outcome: success`
and a parseable start+finish `At` pair; `tokens` also needs a `scope: role` sidecar entry joined by
exact `run_id` (absent sidecar ⇒ `0` measured for every instance). `Result` is `M/E (P%)`,
`P = round(100·M/E)` rounded half up, printed as the literal `0/N (0%)` whenever `M = 0`, regardless
of `E`. The legacy `Point` column name (in place of `Task`) does not change any column's position.

**Lite plans** (no `task-board.md`): the retro still runs — board-derived metrics report `n/a`; log-derived ones stand.

## Cost analysis

Mined from the exact-token recipe only after the coverage gate, never remembered; report the
`n/a`-row counts alongside any permitted totals. Report `n/a` for the whole section when the
workspace has no `resource-usage.md`. `resource-usage.md` remains the only ledger source; unexposed harness fields
stay `n/a`, never estimated.

### Conclusions

- **Top-consuming tasks vs their bindings** — only within a 100%-covered comparable cohort, rank permitted exact totals by task and compare each against its bound tier/effort.
- **Phase shares** — only within a 100%-covered comparable cohort, compare permitted PLAN / EXEC / RETRO totals; otherwise report the coverage gap instead of a share.
- **Cache-write-weighted cost** — where the harness exposed cache splits, a task heavy on `cache_write` vs `cache_read` costs more under the harness's own documented cache-read/cache-write cost ratio; rank by `cache_read`/`cache_write` parity, not by input+output throughput alone.

### Recommendations

- **Downgrade candidates** — tasks whose actual work matched a lower tier/effort than bound (few tokens on an expensive binding): propose the cheaper binding for the next plan of that shape.
- **Recurring shapes worth re-defaulting** — shapes that consistently consume above or below their role default effort: candidates for the role→effort defaults in `team.md`.
- **Duration outliers vs bound effort** — tasks whose `duration_ms` sits well above their bound effort's norm (or `compactions`/`context` spikes) are candidates for re-binding or re-decomposition; a long, compacting task bound `low` signals under-scoped work.

## What worked / what didn't / lessons

Distill from the metrics plus the Decisions and Blockers sections of the log. One line each. A lesson must be actionable by a future plan ("gate X earlier", "the attempt budget was too low for tasks shaped like Y"), not a platitude.

<a id="profile-candidates-learning-loop"></a>
## Preferences and lessons candidates (profile learning loop)

The learning loop is the only mechanism that lets Tackle adapt to a user or project. It is opt-in,
per scope, and never silent. Lessons must identify an observed cause and a future action; an
unsupported opinion does not become a global rule.

### Opt-in (asked once per scope)

At the first learning opportunity, ask per scope:

- **Both scopes** if neither `~/.tackle/user-profile.md` nor `.tackle/profile.md` exists.
- **Project only** if the user profile already exists and is enabled.

A "no" writes the disabled stub (`Evolution: disabled (YYYY-MM-DD)`) in the relevant profile file and is never re-asked. The user can flip it later by enabling evolution or deleting the file.

### Distilling candidates

Mine the following sources during retro:

- `decisions.md` deltas vs recommended defaults (recurring overrides).
- `history.md` attempt-journal lines that exceed the budget or show no-progress.
- Reopened tasks (`🟢 → 🟡`) in `history.md`.
- Escalation packets from `history.md`.
- `verify` findings that recurred across tasks.

Present candidates as a batch. Each candidate must include:

- A hypothesis or directive entry, with a stable `id` (`H01`, `A01`, ... — never a task, decision or
  question shape (`[PTDQRCM]-?[0-9]{2}`), and never the workspace slug).
- The mined evidence for or against it, as this initiative's own `observations` item
  (`<initiative>:✓|✗@<date>`) — never a number chosen by the agent or the user.

### Confidence is computed, never proposed

No step in this workflow asks a human or agent to pick or type a numeric confidence. Every entry's
`confidence` is the Wilson score interval's lower bound (z=1.96), derived only by counting that
entry's own `observations` list: `k` is its ✓ count, `n` is `k` plus its ✗ count (a legacy `null`
observation, and an `assumed` acceptance with no mined support, are excluded from both). The shipped
recipe below performs this computation, the retirement check two paragraphs down, and reads all
three legacy shapes a profile may still carry; nothing here reimplements it independently.

```awk
# Wilson score interval, lower bound (z=1.96): for each Hypotheses/Directives bullet (never a
# Rules or other section bullet), derive N (checked-true) and M (checked-false) by counting the
# entry own observations, then compute the lower bound over n=N+M. Two bullets that repeat one
# hypothesis or directive text merge by the union of the observations initiatives (never by
# summing two entries N/M, which would double-count a shared initiative); an assumed token is
# never counted and never occupies the union (it cannot block a later real check or cross for the
# same initiative). Read over a profile file: `.tackle/profile.md` or `~/.tackle/user-profile.md`.
function trim(s) { gsub(/^[ \t]+/, "", s); gsub(/[ \t]+$/, "", s); return s }
function between(line, left, right,   a, b) {
    a = index(line, left)
    if (a == 0) return ""
    a += length(left)
    b = index(substr(line, a), right)
    if (b == 0) return trim(substr(line, a))
    return trim(substr(line, a, b - 1))
}
function after(line, left,   a) {
    a = index(line, left)
    return a == 0 ? "" : trim(substr(line, a + length(left)))
}
function wilson_lower(k, n,   p, denom, centre, half, lower) {
    p = k / n
    denom = 1 + 3.8416 / n
    centre = (p + 3.8416 / (2 * n)) / denom
    half = 1.96 * sqrt(p * (1 - p) / n + 3.8416 / (4 * n * n)) / denom
    lower = centre - half
    if (lower < 0) lower = 0
    if (lower > 1) lower = 1
    return lower
}
function status_of(m, lower_num) { return (m >= 3 && lower_num < 0.3) ? "retired" : "active" }
function emit(id, n, m, has_evidence,   total, lower) {
    total = n + m
    if (!has_evidence || total == 0) { printf "%s n/a n/a n/a n/a unranked\n", id; return }
    lower = wilson_lower(n, total)
    printf "%s %d %d %d %.4f %s\n", id, n, m, total, lower, status_of(m, lower)
}
/^## Hypotheses/ { section = 1; next }
/^## Directives/ { section = 1; next }
/^## / { section = 0 }
{
    if (!section) next
    line = $0; stripped = trim(line)
    if (substr(stripped, 1, 2) != "- ") next
    if (index(line, "observations:") > 0) {
        id = between(line, "id:", "·")
        text = between(line, id " · ", " · confidence:")
        obslist = between(line, "observations:", "· status:")
        if (obslist == "") obslist = after(line, "observations:")
        n = 0; m = 0
        count = split(obslist, tokens, ";")
        for (i = 1; i <= count; i++) {
            tok = trim(tokens[i])
            if (tok == "") continue
            is_check = index(tok, "✓") > 0
            is_cross = index(tok, "✗") > 0
            if (!is_check && !is_cross) continue
            key = text SUBSEP substr(tok, 1, index(tok, ":") - 1)
            if (key in seen) continue
            seen[key] = 1
            if (is_check) n++; else m++
        }
        total_n[text] += n; total_m[text] += m
        emit(id, total_n[text], total_m[text], 1)
        next
    }
    if (index(line, "evidence:") > 0) {
        ev = between(line, "evidence:", "· status:")
        if (ev == "") ev = between(line, "evidence:", "·")
        if (ev == "") ev = after(line, "evidence:")
        ck = index(ev, "✓")
        n = trim(substr(ev, 1, ck - 1)) + 0
        rest = substr(ev, ck + length("✓")); sub(/^\//, "", rest)
        if (index(rest, "null") > 0) { m = 0 } else {
            cx = index(rest, "✗")
            m = trim(substr(rest, 1, cx - 1)) + 0
        }
        emit("line:" NR, n, m, 1)
        next
    }
    emit("line:" NR, 0, 0, 0)
}
```

Run it as `awk '<the script above>' <profile-path>` to print `<id> N M n confidence status` for every
Hypotheses/Directives entry, one line each, old and new format alike. An entry with only `assumed`
acceptances and no checked observation prints `confidence: n/a`, excluded from Top-K/ranking until
`n ≥ 1`. The comparison against `0.3` always uses this raw, unrounded value; a rounded display never
feeds back into it.

### Confirming and writing

Everything is batch-confirmed by the user before writing. Never append to a profile without an explicit "yes".

For each separately confirmed candidate:

- Update counters from the intake tally line, reading it by id:
  `profile proposals: <id>✓ accepted [, <id>✓ accepted ...]; <id>✗ overridden [, <id>✗ overridden ...]`.
- An accepted suggestion appends a real `observations` item only when this retro's own mining (the
  Distilling candidates sources above) independently surfaced supporting or contradicting evidence
  for *this* hypothesis in *this* initiative; a bare acceptance with no such mined support is
  recorded `assumed` instead (kept for audit, never counted toward `N`/`M`/`n`, never moving the
  computed confidence). Two mined observations from the same initiative for the same hypothesis
  count once.
- If ✗ ≥ 3 and the entry's *computed* confidence (its Wilson lower bound, raw and unrounded) is
  < 0.3, set `status: retired` (kept, never deleted).
- If a project hypothesis is confirmed in ≥ 2 repos, propose promoting it to the user profile (ask again).

### Directives

Propose retirement or supersession of incompatible hypotheses without rewriting history. Intake already excludes them from defaults; pending cleanup does not block implementation. One isolated observation remains a hypothesis, not a mandatory global rule.

Recurring failure evidence may propose a `directive:` entry (C-20). A directive targets a named template or guide section and is considered at instantiation only when applicable and compatible with the current authority order. Project directives outrank user directives. A directive whose target section no longer exists is flagged **stale** for re-confirm-or-retire. When the failure evidence is a repeatable mid-session action (a commit message, a push, a release step), distil the directive with an `applies_to:` tag naming that action moment — instantiation-time application never reaches an action taken 30 sessions after intake (taptopaykit-integration A1: a commit-format directive written session 23, violated session 35).

### Opt-out anytime

The user can stop evolution at any moment, per scope, with any phrasing. Two modes:

- **Pause**: flip the header to `Evolution: disabled (YYYY-MM-DD)`. Counters are kept; re-enabling resumes them.
- **Purge**: delete the profile file entirely. The next learning opportunity may re-ask for opt-in.

Both take effect immediately.

<a id="plan-archetype-candidates-learning-loop"></a>
## Plan reference plan candidates (learning loop)

At initiative close, consider whether the plan itself is worth distilling into `.tackle/archetypes/` or `~/.tackle/archetypes/` — matching whichever scope the profile candidate above came from (format: `references/archetypes/README.md`).

### Eligibility

Offer extraction only when **the decomposition held**: no major replans and no D-xx rewrites of the task/edge graph after intake — tasks closed against the graph that was planned. A plan that was substantially re-shaped mid-flight has no stable skeleton to distill; skip without asking.

### Extraction template

One reference plan file per skeleton: `.tackle/archetypes/<name>.md` or `~/.tackle/archetypes/<name>.md` with the sections the README fixes — name + one-line summary, task list, edge pattern, wave shape, trap warnings, provenance (this initiative, retro link). Mine the graph from `plan.md`/`task-board.md`; mine trap warnings from attempt journals and reopened tasks; judgment only names and summarizes.

### Confirming and writing

Everything is batch-confirmed by the user before writing — present the reference plan candidate alongside the profile-candidate batch, never write it silently. Only the `retro` workflow writes reference plans.

## Where results go

- `docs/plans/<initiative>/retro.md` in the initiative workspace, one per initiative (a partial
  retro overwrites the previous partial; the close retro is final), plus one `history.md` entry
  noting the retro ran, with the Metrics values as its evidence.
- `.tackle/profile.md` (project scope) or `~/.tackle/user-profile.md` (user scope), per
  batch-confirmed profile candidate.
- `.tackle/archetypes/<name>.md` (project scope) or `~/.tackle/archetypes/<name>.md` (user scope),
  per batch-confirmed reference plan candidate.

All of the above are outside the installed skill; none is a write under the install tree. Report
the useful findings and pending consent concisely per the communication contract — link to
`retro.md`, don't paste it.
