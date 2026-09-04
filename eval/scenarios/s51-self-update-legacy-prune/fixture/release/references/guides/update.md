# Update — skill self-update

The agent updates only after the fetched release passes source and version verification. The
installed artifact is Markdown-only: `SKILL.md` plus `references/`; fetched content is never
executed.

## Update

1. Verify the release source and the extracted `SKILL.md` stamp before changing the install.
2. Replace the installed `SKILL.md` and `references/` with the verified Markdown artifact.
3. Only after that verified replacement succeeds, remove the exact legacy basename
   `tackle-check` if present. Preserve unrelated neighboring files, including any sentinel.
4. Record the check only after replacement succeeds.

## Fallback

Any failed fetch, extraction, source check, or stamp check leaves the current install
untouched. Once a valid replacement is available, remove only the exact legacy basename
`tackle-check`; never remove `tackle`, a glob, or an unrelated neighbor.
