# Maintaining Tackle

This file documents Tackle's own release process: the release sweep, the eight self-lint
gates, the deletion gate, and the one migration bridge.
It does not ship with the installed skill (`SKILL.md` plus `references/`).

## Migration bridge

The installed skill reads only the current workspace layout. The migration guide, its recipes and
`eval/migration/` stay the one bridge: they keep detecting and transforming every older schema.

## Release sweep

Before any version tag, the owner names the workspace path(s) explicitly included in the release scope; unknown scope blocks the tag pending clarification. The agent runs every lint row on every discovered workspace (`docs/plans/*/`) plus the skill's own done-signals, then computes the lint summary from the observed row results. Release-gating workspaces are the deduplicated union of active workspaces (at least one task data row whose trimmed Status is legacy 🟡 or, under `tackle-workspace/3`, In progress, Checking or Interrupted) and explicitly selected workspaces. Selection adds obligations; it never exempts another active workspace. Mandatory failures in this union or the skill's own release gates block the tag until fixed or explicitly waived by the user; warn-severity rows retain their non-blocking severity.

The release sweep is a direct, ordered procedure: (1) record the explicit release scope and run self-lint gates 1–8 below;
(2) run catalog integrity checks over `eval/scenarios/` and answer-sheet roots;
(3) run rows 1–17 over every workspace; (4) run each initiative's done-signal;
(5) apply the release-scope rule: every active or selected workspace must pass its mandatory rows
and done-signal. Each selected workspace must additionally pass current global acceptance even
when its board has no active data row or every task is Complete (legacy 🟢); stale evidence must be revalidated against
the changed deliverable. Historical closed or parked workspaces that are neither active nor
selected report WARN on failures and are non-gating; and (6) compute and report
`sweep: N/M gates passed` from those observed results. The documented rows and gates are the only canonical contract.

Migrate-chain currency: if the release changes any workspace-level contract (`AGENTS.tmpl.md`, status vocabulary, artifact names, closure protocol), the migrate guide MUST gain a checklist for the immediately previous version in the same release — a version bump without its migrate checklist is a release defect (precedent: v3.0→v3.1 and v3.3→v3.4 were both missed once).

Before tagging, complete these four steps in this order; each follows the sweep above and none is optional:

1. Run the full registry under CI's interpreter before pushing the release branch: the `python3` of the `ubuntu-26.04` runner image. The workflow (`.github/workflows/ci.yml`) pins no version, so take the version from the latest CI log, or use a matching local interpreter. A green run under a different interpreter does not count.
2. Run the committed-text guard over everything a commit adds, untracked files included: build a temporary index, mark the new files with `git add -N`, and point the guard at that index by running it with `GIT_INDEX_FILE` set to the temporary index, so a file that is not yet tracked is checked like a committed one.
3. Reproduce every documented install channel in a sandbox and count the installed files against the install artifact (`SKILL.md` plus `references/`); a channel that needs the tag is reproduced against a local clone of the candidate commit. Any extra or missing file blocks the tag.
4. On the owner's order, push the release branch without a tag and observe CI; create the tag only after CI is green, never before. A local run hides host-dependent variants (gawk, mawk, original-awk and busybox; Linux interpreters), so only the CI observation clears this step.

### Skill self-lint gates

The eight gates validate the installed Markdown skill and its documentation in the same sweep. Run all eight from the repo root; each stays silent and exits 0 on pass — any echoed line blocks the tag until fixed. Every version value derives from the files; no gate hardcodes one.
The development acceptance harness pins the exact eight executable command cells independently
of this document. After a reviewed command change, update its digest in
`eval/validation-integrity/acceptance.py`; never derive that trust anchor from an unreviewed working copy.

1. **Word budget** — `SKILL.md` ≤ 1100 words:
   `[ "$(wc -w < skills/tackle/SKILL.md)" -le 1100 ] || echo "SKILL.md over budget"`
2. **Conventions count** — exactly 11 numbered core conventions (awk anchors on the §Core conventions heading, stops at the next `##`):
   `[ "$(awk '/^## Core conventions/{f=1;next} f && /^## /{exit} f && /^[0-9]+\. /{n++} END{print n+0}' skills/tackle/SKILL.md)" -eq 11 ] || echo "conventions count off"`
3. **Changelog currency** — newest `## Tackle X.Y.Z` heading equals the `SKILL.md` version stamp:
   `[ "$(awk '/^## Tackle /{print $3; exit}' CHANGELOG.md)" = "$(awk '/^\*\*Tackle /{gsub(/\*/,"",$2); print $2; exit}' skills/tackle/SKILL.md)" ] || echo "changelog head mismatch"`
4. **Migrate-chain currency** — the checklist heading into the current major.minor and the
   7.3-to-8.0 transition both exist:
   `v=$(awk '/^\*\*Tackle /{gsub(/\*/,"",$2); print $2; exit}' skills/tackle/SKILL.md); mm=${v%.*}; x=${mm%%.*}; y=${mm##*.}; if [ "$y" -gt 0 ]; then p="$x.$((y-1))"; else p="[0-9.]+"; fi; grep -Eq "^## v$p → v$mm checklist" skills/tackle/references/guides/migrate.md || echo "missing migrate checklist → v$mm"; grep -qF "## v7.3 → v8.0 checklist" maintaining/migrations.md || echo "missing candidate migrate checklist → v8.0"`
5. **README currency** — every README version stamp equals the `SKILL.md` stamp (added 5.0.0 after the README drifted to 4.0.0 while the skill shipped 5.0.0; `sort -u` covers the stamp's two locations — header + Version line — so a half-updated README fails):
   `[ "$(grep -oE 'Tackle [0-9]+\.[0-9]+\.[0-9]+' README.md | sort -u)" = "Tackle $(awk '/^\*\*Tackle /{gsub(/\*/,"",$2); print $2; exit}' skills/tackle/SKILL.md)" ] || echo "README stamp mismatch"`
6. **Artifact-manifest and legacy-transition currency** — the delivery channel lists exactly the Markdown files that ship (`SKILL.md` + `references/`); no executable is part of the install/update copy path. The owner-controlled transition must name the exact legacy tombstone (`tackle-check`) and preserve an unrelated sentinel after verified replacement; it never deletes `tackle` or uses recursive/prefix cleanup:
   `for f in SKILL.md references; do grep -q "$f" skills/tackle/references/guides/update.md || echo "update.md missing artifact: $f"; done; m=$(grep -E '^[[:space:]]*3\. The owner-controlled installer' skills/tackle/references/guides/update.md); case "$m" in *SKILL.md*references/*) ;; *) echo "update.md install copy path missing Markdown artifact";; esac; grep -q "exact legacy basename.*tackle-check" skills/tackle/references/guides/update.md || echo "update.md missing legacy tombstone: exact legacy basename tackle-check"; grep -qi "unrelated neighboring files remain untouched" skills/tackle/references/guides/update.md || echo "update.md missing sentinel-preserving transition: unrelated neighbors"; if grep -Eq '(^|[[:space:]])(curl|tar -x)' skills/tackle/references/guides/update.md; then echo "update.md contains runtime transfer command"; fi`
7. **README content claims** — the README's self-description matches the files it describes (added 5.4.0 after the 5.2.0 pre-release review caught four content defects gate 5's stamp check can't see: lint row count, scenario counts, migrate-chain head, direct-procedure coverage; the row-count, gate-count, chain-head and procedure-coverage checks echo nothing and exit on the final grep, so any echoed line blocks the tag):
   `` n=$(grep -Ec '^\| [0-9]+ ·' skills/tackle/references/guides/lint-spec.md); grep -qF "rows 1–$n" README.md || echo "missing rows 1–$n"; grep -qF "($n lint rows)" README.md || echo "missing ($n lint rows)"; c=0; m=0; for d in eval/scenarios/*/; do [ -d "$d" ] || continue; c=$((c+1)); s=$(basename "$d"); s=${s%%-*}; s=${s#s}; [ "$s" -gt "$m" ] && m=$s; done; grep -qF "**$c scenarios** (" README.md || echo "scenario count off (**$c scenarios** ())"; grep -qF "\`s1\`–\`s$m\`" README.md || echo "scenario range off (\`s1\`–\`s$m\`)"; v=$(awk '/^\*\*Tackle /{gsub(/\*/,"",$2); print $2; exit}' skills/tackle/SKILL.md); mm=${v%.*}; grep -qF "checklist chain v2.0 → v$mm" README.md || echo "migrate-chain head off (v2.0 → v$mm)"; row=$(grep 'Mechanical gate' README.md); for t in lint catalog done-signal ground eval init; do case "$row" in *"\`$t"*) ;; *) echo "mode row missing \`$t";; esac; done; g=$(awk '/^### Skill self-lint gates/{f=1;next} f && /^##/{exit} f && /^[0-9]+\. /{n++} END{print n+0}' MAINTAINING.md); grep -qF "$g shipped-skill gates" README.md || echo "self-lint gate count off ($g shipped-skill gates)" ``

8. **Runtime update trust boundary** — ordinary runtime/update instructions and active security fixtures contain no automatic network/update clause, no unexpected-owner archive URL, and no present tracked `tackle`/`tackle-check` basename:
   `u=$(grep -Ehc 'On any invocation.*self-update|Run the Check phase.*every Tackle invocation|Remote > local.*run Update|Download the tag tarball|Replace only the install artifact' skills/tackle/SKILL.md skills/tackle/references/guides/intake-and-gate.md skills/tackle/references/guides/update.md eval/scenarios/s16-self-update-trap/skill/SKILL.md eval/scenarios/s16-self-update-trap/skill/references/guides/update.md 2>/dev/null | awk '{s+=$1} END{print s+0}'); [ "$u" -eq 0 ] || echo "Runtime update trust boundary: automatic update clause"; h=$(git grep -nE 'https://(api\.)?github\.com/(repos/)?tackle-fan/Tackle' -- eval/scenarios 2>/dev/null | wc -l | tr -d ' '); [ "$h" -eq 0 ] || echo "Runtime update trust boundary: hostile archive URL"; r=$(git ls-files | awk '/(^|\/)(tackle|tackle-check)$/ {print}' | while IFS= read -r p; do [ -e "$p" ] && printf '%s\n' "$p"; done | awk 'END{print NR+0}'); [ "$r" -eq 0 ] || echo "Runtime update trust boundary: present tracked runner basename"`

Gate 4 derives the immediately previous version from the stamp: a minor bump requires exactly `v<x.(y-1)> → v<x.y>`; a major bump (`y` = 0) accepts the previous major's last minor on the left side — e.g. releasing 4.0.0 requires `## v3.4 → v4.0 checklist`.

## Change gate

Every add, change or delete of a normative rule needs a ledger diff before release, symmetrically: an
addition and a change need the diff exactly as much as a delete already did. Its scope is not every
rule alike — held-out evidence is required only for a hot-path rule or a safety invariant (in either
revision, so demoting or reclassifying a rule cannot hide its change); every other touched rule still
needs its ledger diff, printed and named, but not evidence. A pure rewording (the same words, carried
into the new text) needs no new evidence either way.

A release that deletes normative content from `SKILL.md` or a guide also needs two things. First, the
rule-inventory accounting: the unit gate (`check_unit_diff.py`) shows that every normative unit removed
since the base has a disposition, so each one-liner stays greppable in `SKILL.md` or its named guide.
Second, one behavioral run on a **trap dedicated to the shipped feature** (method arm = the edited file),
not a generic pre-existing scenario: text presence does not prove behavior, and a behavioral contract
needs its own trap (s23 proved it: the method arm denied the flip without mechanical green, while the
control flipped). The alternative, mechanical proof plus a held-out no-regression cohort, applies only
with the owner's recorded acceptance for that release.

Recorded exceptions live in `eval/rules/gate-exceptions.json` (committed), a list of `{rule_id,
statement_sha256, reason, accepted}`. An entry lets one in-scope add or change pass without this
release's own evidence, pinned to its current `statement_sha256` so a later restatement voids it.
`accepted` is a documentation-only date; its format is checked, and it never gates anything. Exceptions
never excuse a delete. On every run the gate validates and prints every entry's state — applied,
dormant or void — so a stale or misapplied exception is never silent.

```sh
python3 eval/rules/check_ledger.py --repo <dir> --gate <base-rev>|auto [--evidence-cohort <cohort-id>]
```

A release runs the gate as one of its required steps, citing its own evidence cohort:

```sh
python3 eval/rules/check_ledger.py --repo . --gate auto --evidence-cohort <this release's cohort id>
```

`<this release's cohort id>` is a placeholder, never a literal id copied from an earlier release.

CI's own step (`.github/workflows/ci.yml`) runs `--gate auto` with no `--evidence-cohort`: it is
structural-only by design, because CI cannot know a future release's own cohort ahead of time. The
release procedure above is what ties a diff to the cohort that actually backs it.

See `eval/rules/LEDGER.md` for the evidence schema `evidence.status`/`evidence.cohort_id` follow.

A second, independent mechanical check (`python3 eval/rules/check_unit_diff.py --repo <dir> --base
<base-rev>|auto`) accounts for every sentence unit removed from a ledger `home` or `mirrors` file,
symmetrically with the change gate above: "removed" means present in the base revision's split and
absent from the candidate's, by exact text, never by line number. Its auto-match has exactly one
live branch, forever: a removed unit found verbatim (whitespace normalized) in the shipped tree
(`SKILL.md` plus `references/**`), at or above the duplicate detector's own length floor, closes
with no committed record. A maintainer-only match — found only under
`MAINTAINING.md`/`maintaining/**` — never auto-closes; it always needs a written disposition, one
of `home` (still present at that file), `reworded` (a declared mapping to new text, checked as a
substring), `merged` (moved to a different named place that still holds it, checked by hash) or
`ruled` (non-normative, with a reason). Restructuring a table costs one disposition per affected
row, not one per logical edit, and a version-string bump costs one fresh disposition each release.
CI and the release procedure both run it structural-only (`--base auto`; no cohort, symmetrically
with the change gate's own CI step). See `eval/rules/unit-dispositions.json` for the committed
records.
The check also accounts for fenced code blocks and covered files' frontmatter lines as units, and
once any committed ledger version names a file, that file's coverage persists even after every
current rule stops naming it.

## Sweep score

The agent computes the sweep numerator and denominator from the observed gate and workspace
results; the release sweep closes with exactly:

`sweep: N/M gates passed`

- **M** = 8 self-lint gates + 1 catalog + the number of distinct workspaces in the union of active and explicitly selected workspaces. Count a workspace once even if it belongs to both sets. Every discovered workspace is still linted for diagnostic visibility.
- **N** = gates and union workspaces whose mandatory rows and done-signals pass; selected workspaces also require current global acceptance. Workspaces that are neither active nor selected report `WARN` on failure and never enter N/M. Warn-severity rows are reported but do not fail a workspace's sweep gate. A selected workspace's mandatory failure blocks the tag regardless of its board status.
