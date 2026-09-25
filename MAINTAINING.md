# Maintaining Tackle

This file documents Tackle's own release process: the release sweep, the eight self-lint
gates, the D-13 deletion gate, and the byte-identity promise for the five legacy templates.
It does not ship with the installed skill (`SKILL.md` plus `references/`).

## Legacy templates

Old `point.tmpl.md`, `usage.tmpl.md`, `board.tmpl.md`, `log.tmpl.md` and `coordinator.tmpl.md`
remain byte-identical.

## Release sweep

Before any version tag, the owner names the workspace path(s) explicitly included in the release scope; unknown scope blocks the tag pending clarification. The agent runs every lint row on every discovered workspace (`docs/plans/*/`) plus the skill's own done-signals, then computes the lint summary from the observed row results. Release-gating workspaces are the deduplicated union of active workspaces (at least one task data row whose trimmed Status is legacy 🟡 or, under `tackle-workspace/3`, In progress, Checking or Interrupted) and explicitly selected workspaces. Selection adds obligations; it never exempts another active workspace. Mandatory failures in this union or the skill's own release gates block the tag until fixed or explicitly waived by the user; warn-severity rows retain their non-blocking severity.

The release sweep is a direct, ordered procedure: (1) record the explicit release scope and run self-lint gates 1–8 below;
(2) run catalog integrity checks over `eval/scenarios/` and answer-sheet roots;
(3) run rows 1–16 over every workspace; (4) run each initiative's done-signal;
(5) apply the release-scope rule: every active or selected workspace must pass its mandatory rows
and done-signal. Each selected workspace must additionally pass current global acceptance even
when its board has no active data row or every task is Complete (legacy 🟢); stale evidence must be revalidated against
the changed deliverable. Historical closed or parked workspaces that are neither active nor
selected report WARN on failures and are non-gating; and (6) compute and report
`sweep: N/M gates passed` from those observed results. The documented rows and gates are the only canonical contract.

D-13 trigger: if the release includes any change that deletes normative content from `SKILL.md` or a guide, the sweep additionally requires (1) a rule-inventory diff — every normative one-liner extracted before the edit must be greppable after, in `SKILL.md` or its named guide — and (2) one behavioral eval run (trap scenario, method arm = edited file) proving the skill still avoids the trap. The eval run must be a **trap dedicated to the feature being shipped** (e.g. s23-flip-gate for the double gate), not a generic pre-existing scenario — text-presence (greps) doesn't prove behavior, and a behavioral contract feature needs its own trap (proven by s23: method denied the flip without mechanical green, control flipped E1).

Migrate-chain currency: if the release changes any workspace-level contract (`AGENTS.tmpl.md`, status vocabulary, artifact names, closure protocol), the migrate guide MUST gain a checklist for the immediately previous version in the same release — a version bump without its migrate checklist is a release defect (precedent: v3.0→v3.1 and v3.3→v3.4 were both missed once).

### Skill self-lint gates

The eight gates validate the installed Markdown skill and its documentation in the same sweep. Run all eight from the repo root; each stays silent and exits 0 on pass — any echoed line blocks the tag until fixed. Every version value derives from the files; no gate hardcodes one.
The development acceptance harness pins the exact eight executable command cells independently
of this document. After a reviewed command change, update its digest in
`eval/validation-integrity/acceptance.py`; never derive that trust anchor from an unreviewed working copy.

1. **Word budget** — `SKILL.md` ≤ 1100 words:
   `[ "$(wc -w < SKILL.md)" -le 1100 ] || echo "SKILL.md over budget"`
2. **Conventions count** — exactly 11 numbered core conventions (awk anchors on the §Core conventions heading, stops at the next `##`):
   `[ "$(awk '/^## Core conventions/{f=1;next} f && /^## /{exit} f && /^[0-9]+\. /{n++} END{print n+0}' SKILL.md)" -eq 11 ] || echo "conventions count off"`
3. **Changelog currency** — newest `## Tackle X.Y.Z` heading equals the `SKILL.md` version stamp:
   `[ "$(awk '/^## Tackle /{print $3; exit}' CHANGELOG.md)" = "$(awk '/^\*\*Tackle /{gsub(/\*/,"",$2); print $2; exit}' SKILL.md)" ] || echo "changelog head mismatch"`
4. **Migrate-chain currency** — the checklist heading into the current major.minor and the
   7.3-to-8.0 transition both exist:
   `v=$(awk '/^\*\*Tackle /{gsub(/\*/,"",$2); print $2; exit}' SKILL.md); mm=${v%.*}; x=${mm%%.*}; y=${mm##*.}; if [ "$y" -gt 0 ]; then p="$x.$((y-1))"; else p="[0-9.]+"; fi; grep -Eq "^## v$p → v$mm checklist" references/guides/migrate.md || echo "missing migrate checklist → v$mm"; grep -qF "## v7.3 → v8.0 checklist" maintaining/migrations.md || echo "missing candidate migrate checklist → v8.0"`
5. **README currency** — every README version stamp equals the `SKILL.md` stamp (added 5.0.0 after the README drifted to 4.0.0 while the skill shipped 5.0.0; `sort -u` covers the stamp's two locations — header + Version line — so a half-updated README fails):
   `[ "$(grep -oE 'Tackle [0-9]+\.[0-9]+\.[0-9]+' README.md | sort -u)" = "Tackle $(awk '/^\*\*Tackle /{gsub(/\*/,"",$2); print $2; exit}' SKILL.md)" ] || echo "README stamp mismatch"`
6. **Artifact-manifest and legacy-transition currency** — the delivery channel lists exactly the Markdown files that ship (`SKILL.md` + `references/`); no executable is part of the install/update copy path. The owner-controlled transition must name the exact legacy tombstone (`tackle-check`) and preserve an unrelated sentinel after verified replacement; it never deletes `tackle` or uses recursive/prefix cleanup:
   `for f in SKILL.md references; do grep -q "$f" references/guides/update.md || echo "update.md missing artifact: $f"; done; m=$(grep -E '^[[:space:]]*3\. The owner-controlled installer' references/guides/update.md); case "$m" in *SKILL.md*references/*) ;; *) echo "update.md install copy path missing Markdown artifact";; esac; grep -q "exact legacy basename.*tackle-check" references/guides/update.md || echo "update.md missing legacy tombstone: exact legacy basename tackle-check"; grep -qi "unrelated neighboring files remain untouched" references/guides/update.md || echo "update.md missing sentinel-preserving transition: unrelated neighbors"; if grep -Eq '(^|[[:space:]])(curl|tar -x)' references/guides/update.md; then echo "update.md contains runtime transfer command"; fi`
7. **README content claims** — the README's self-description matches the files it describes (added 5.4.0 after the 5.2.0 pre-release review caught four content defects gate 5's stamp check can't see: lint row count, scenario counts, migrate-chain head, direct-procedure coverage; the row-count, gate-count, chain-head and procedure-coverage checks echo nothing and exit on the final grep, so any echoed line blocks the tag):
   `` n=$(grep -Ec '^\| [0-9]+ ·' references/guides/lint-spec.md); grep -qF "rows 1–$n" README.md || echo "missing rows 1–$n"; grep -qF "($n lint rows)" README.md || echo "missing ($n lint rows)"; c=0; m=0; for d in eval/scenarios/*/; do [ -d "$d" ] || continue; c=$((c+1)); s=$(basename "$d"); s=${s%%-*}; s=${s#s}; [ "$s" -gt "$m" ] && m=$s; done; grep -qF "**$c scenarios** (" README.md || echo "scenario count off (**$c scenarios** ())"; grep -qF "\`s1\`–\`s$m\`" README.md || echo "scenario range off (\`s1\`–\`s$m\`)"; v=$(awk '/^\*\*Tackle /{gsub(/\*/,"",$2); print $2; exit}' SKILL.md); mm=${v%.*}; grep -qF "checklist chain v2.0 → v$mm" README.md || echo "migrate-chain head off (v2.0 → v$mm)"; row=$(grep 'Mechanical gate' README.md); for t in lint catalog done-signal ground eval init; do case "$row" in *"\`$t"*) ;; *) echo "mode row missing \`$t";; esac; done; g=$(awk '/^### Skill self-lint gates/{f=1;next} f && /^##/{exit} f && /^[0-9]+\. /{n++} END{print n+0}' MAINTAINING.md); grep -qF "$g shipped-skill gates" README.md || echo "self-lint gate count off ($g shipped-skill gates)" ``

8. **Runtime update trust boundary** — ordinary runtime/update instructions and active security fixtures contain no automatic network/update clause, no unexpected-owner archive URL, and no present tracked `tackle`/`tackle-check` basename:
   `u=$(grep -Ehc 'On any invocation.*self-update|Run the Check phase.*every Tackle invocation|Remote > local.*run Update|Download the tag tarball|Replace only the install artifact' SKILL.md references/guides/intake-and-gate.md references/guides/update.md eval/scenarios/s16-self-update-trap/skill/SKILL.md eval/scenarios/s16-self-update-trap/skill/references/guides/update.md 2>/dev/null | awk '{s+=$1} END{print s+0}'); [ "$u" -eq 0 ] || echo "Runtime update trust boundary: automatic update clause"; h=$(git grep -nE 'https://(api\.)?github\.com/(repos/)?tackle-fan/Tackle' -- eval/scenarios 2>/dev/null | wc -l | tr -d ' '); [ "$h" -eq 0 ] || echo "Runtime update trust boundary: hostile archive URL"; r=$(git ls-files | awk '/(^|\/)(tackle|tackle-check)$/ {print}' | while IFS= read -r p; do [ -e "$p" ] && printf '%s\n' "$p"; done | awk 'END{print NR+0}'); [ "$r" -eq 0 ] || echo "Runtime update trust boundary: present tracked runner basename"`

Gate 4 derives the immediately previous version from the stamp: a minor bump requires exactly `v<x.(y-1)> → v<x.y>`; a major bump (`y` = 0) accepts the previous major's last minor on the left side — e.g. releasing 4.0.0 requires `## v3.4 → v4.0 checklist`.

## Sweep score

The agent computes the sweep numerator and denominator from the observed gate and workspace
results; the release sweep closes with exactly:

`sweep: N/M gates passed`

- **M** = 8 self-lint gates + 1 catalog + the number of distinct workspaces in the union of active and explicitly selected workspaces. Count a workspace once even if it belongs to both sets. Every discovered workspace is still linted for diagnostic visibility.
- **N** = gates and union workspaces whose mandatory rows and done-signals pass; selected workspaces also require current global acceptance. Workspaces that are neither active nor selected report `WARN` on failure and never enter N/M. Warn-severity rows are reported but do not fail a workspace's sweep gate. A selected workspace's mandatory failure blocks the tag regardless of its board status.
