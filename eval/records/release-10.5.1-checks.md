# Tackle 10.5.1 checks and evidence limits

This report describes the checks behind the 10.5.1 release notes. Final candidate registries, install inventories, local CI replay and publication observations are separate release gates. No held-out behavioral result is claimed.

## Maintainer tests

The concurrent-recorder test of the evaluation rounds keeps the store's zero busy timeout. It now runs three phases: both recorders against a held writer lock, where both must report the store busy and nothing is committed; a free race, where at most one recorder may commit and the stored count must match the winners; and a sequential progress check that leaves exactly one committed start, a refused second start and a store that computes and replays as running. The test passed 60 sequential runs on two interpreters and nine concurrent runs, and a mutant that removes the start admission guards failed it in all five runs.

The harness signal-window cases restore the default interrupt handler, write a readiness marker naming the signal and its handler before signalling, and are launched with SIGINT ignored. With an ignored inherited SIGINT, the 13 SIGINT cases had failed the exit-130 assertion before the change; after it they pass alone, on the 3.10 floor and in three rounds of three concurrent runs, and a mutant without the handler restore fails exactly those 13 cases with the marker naming the ignored handler.

## Plan view

The template's license comment no longer ends in a space, so a built view has no line ending in whitespace; a real view built before and after differs only in that line, the template digest and the print styles. Printed with the engine Safari uses, the earlier template split two sections across pages and started the progress part near the bottom of a page; the new print styles keep every section that fits on a page whole, never split a list item or summary card, start the progress part on a new page and let a section taller than a page flow across pages, with all 70 items and 24 cards of a long synthetic report present.

## Release procedure

`MAINTAINING.md` names the PLAN rehearsal of every standing phase on a disposable copy of the real plans tree, base-pinned citations and README currency. The rehearsal for this release made three attempts on such a copy. The first failed at the changelog part, which required a claims change even when a release has no claims; the second and third ran every coordinator phase through both registries, the local CI replay and the mechanical review, the reviewer sentinel ran in the second, and the second showed that a release base equal to the previous tag would mis-stamp. The first finding is fixed; the second does not arise from a real integration base. The `readme` part refuses a README whose install count or scripts inventory differs from the candidate's tracked skill tree, the README lists every shipped script, and the `changelog` part keeps its configured prose inside the release workspace. The notes phase refuses glued tokens before writing any output: the 21 glued tokens of the 10.5.0 pre-recut prose are refused, and the published changelog and the 10.5.0 report give none.

## Records

The usage guide states how a role session reused after its finish records each later moment: a new run with its own start and finish, the same session named in Source, and the session's usage recorded once at its end. A three-moment demonstration passes the lifecycle lint row and measures three durations, and a second finish of a finished run is refused as a duplicate terminal. The rule is ledgered as behavioral and the three release-procedure rules as maintainer rules: `gate: added=4 changed=0 deleted=0`, with no applied exception and no evidence cohort.

## Security

The security guide now matches the scripts: a check's argument list may name a shell, the lint rows are fixed multi-line programs, the captured lint-row runner and the retro recipe run fixed program text, each script's write protections are described as implemented, and consent comes only from the owner. The record writer gives a new file `0o666` minus the umask and keeps only permission bits when it rewrites a file; migration modes are unchanged.
