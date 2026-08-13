# Plan lint spec — mechanical checks

Every check is a literal copy-paste command: run from the **repo root**, in any POSIX shell, plain `sh`/`grep`/`sed`/`awk` only. Since 5.0 the shipped `tackle-check` runner composes exactly these rows: the runner IS the rows, this table is its spec.

## Release sweep

Before any version tag, run every lint row on every active workspace (`docs/plans/*/`) plus the skill's own done-signals for the release; the tag waits on a clean sweep (`lint: N/N checks passed` everywhere, all done-signals passing). Any failure blocks the tag until fixed or explicitly waived by the user.

The shipped runner composes the sweep as one command: `tackle-check sweep` runs the self-lint gates 1–7 below, `catalog`, and the lint rows over every workspace (active workspaces — boards with a 🟡 data row — gate the exit code; closed ones report WARN, non-gating), closing with `sweep: N/M gates passed`. The documented rows and gates remain the fallback for hosts without the runner.

### Skill self-lint gates

The shipped skill lints itself in the same sweep. Run all seven from the repo root; each stays silent and exits 0 on pass — any echoed line blocks the tag until fixed. Every version value derives from the files; no gate hardcodes one.

1. **Word budget** — `SKILL.md` ≤ 1100 words.
2. **Conventions count** — exactly 11 numbered core conventions.
3. **Changelog currency** — newest `## Tackle X.Y.Z` heading equals the `SKILL.md` version stamp.
4. **Migrate-chain currency** — the checklist heading into the current major.minor exists in the migrate guide.
5. **README currency** — every README version stamp equals the `SKILL.md` stamp.
6. **Artifact-manifest currency** — the delivery channel lists exactly the files that ship.
7. **README content claims** — row count, scenario count/range, migrate-chain head, runner subcommands, and self-lint gate count, every expected value derived from the files it describes.

## Score line

The release sweep (`tackle-check sweep`) closes with exactly:

`sweep: N/M gates passed`

- **M** = 7 self-lint gates + 1 catalog + the number of active workspaces linted.
- **N** = gates/workspaces whose pass condition held. Closed workspaces are linted but report `WARN` on failure and never enter N/M — a closed workspace cannot block a tag; an active workspace's failure does.
