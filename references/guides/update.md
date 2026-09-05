# Update — owner-controlled manual workflow

## Boundary

Ordinary Tackle invocation performs no network access or installation-tree mutation. Tackle never
performs release checks, downloads, extraction, or installation-tree replacement, even when a newer
release may exist. This guide is reference material for a user-controlled, out-of-band workflow
only. In this document, ordinary invocation performs no network access or installation-tree mutation.

## Owner-controlled workflow

1. Select an approved release through the owner's normal distribution process and verify its source,
   version, and integrity before touching the installed skill.
2. Confirm that the candidate artifact contains only the Markdown install artifact: `SKILL.md` and
   `references/`. Do not execute fetched content.
3. The owner-controlled installer may copy only `SKILL.md` and `references/` into the skill directory
   after verification. Once that replacement succeeds, remove the exact legacy basename `tackle-check`
   if present. Never remove a file named `tackle`, use recursive or prefix cleanup. Unrelated neighboring files remain untouched, including sentinels.
4. Reload the skill through the harness's documented mechanism, or restart the session when reload is
   unavailable.

## Failure and rollback

Any failed source, version, integrity, or artifact check leaves the current install untouched. The
owner must resolve the failure through the approved distribution process; Tackle does not retry,
download, extract, or mutate the installation tree.
