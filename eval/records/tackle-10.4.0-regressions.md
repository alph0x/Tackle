# Tackle 10.4.0 deterministic regressions

This report summarizes the targeted regression checks behind the 10.4.0 entry of the changelog. Their inputs are temporary synthetic workspaces, copies of the shipped files and the frozen evaluator's own records. A passing case establishes its encoded assertion at its actual consumer. It is not a behavioral cohort, and it does not accept or migrate any private workspace.

Twelve new test methods guard the shipped changes. Each was run against the unchanged file it guards and failed there, then passed on the changed file; a guarding family that did not pass on the changed copy invalidated the check. A thirteenth method preserves the former entry bytes for a source without a snapshot, so it passes on both and was judged by review. The observations below were repeated on the integrated tree before the release stamp, on macOS. The final full registry runs separately on the stamped candidate.

## Migration entry

`eval/tests/product/migration/test_compact_migration.py` holds three new methods among its twelve. A source history that carries State snapshots yields a candidate whose appended entry carries the newest snapshot's bullets, and lint row 13, run alone on the candidate, prints nothing. Repeating the same operation leaves the bytes unchanged. A source without a snapshot yields exactly the former entry bytes. The completion review migrated a real copy of a workspace that carries State snapshots and observed row 13 silent on the candidate.

## Close and coordinator guidance

`eval/tests/product/run/card/test_run.py` holds four new methods among its seven. The close-lint step is linked from step 8 of the RUN card and orders the lint after the board, history and usage writes. The coordinator guidance names reading records by their facts and preferring pinned generators for artifacts that later tasks consume. Removing any of these sentences fails its method.

## Task template

`eval/tests/product/templates/test_brief_template.py` holds two new methods among its five: the numbered block of commands the reviewer runs first, and the records-root line. The shortened template and run-guide sentences that offset the new words each carry a reworded disposition whose note is present in the current text, and the unit gate accounts for every one of them.

## Role sessions

`eval/tests/product/templates/test_model_routing_text.py` holds four new methods among its thirty-one. The usage guide records the billed models of every role session or `n/a`; the template declares role capabilities; the decomposition guide probes them in the role's own sandbox before lock. A fourth method reads every line about billed models or role capabilities in those three files and fails when one names a host or harness; injecting a host name into the billed-model sentence fails it.

## Review-convergence evaluator

The evaluator under `eval/behavior/review_convergence/` and the scenario `s89-review-convergence` are maintainer tooling and do not ship. `eval/tests/tooling/behavior/review-convergence/` holds 67 methods across three files: catalog expectations are judged by the frozen scorer; missing, malformed or contradictory evidence records and altered consumer bytes are rejected; the four variant oracles are byte-identical and their selftests pass. `eval/tests/tooling/scenario-index/test_index.py` (32 methods) admits the new held-out cap of 16. The seal records calibration as invalid: before a bounded change to the case, both arms fell only on two over-strict oracle rules; after it, the control avoided the trap and the method arm left no room. No held-out episode was admitted.

## Observation fingerprints

The SHA-256 values below identify the complete unittest error streams of the integrated-tree repetition before the release stamp, on CPython 3.10.7. Each run exited 0, reported its method count and printed `OK`; standard output was empty. They are traceability aids, not substitutes for the assertions or for the final release checks.

| Test file | Methods | stderr SHA-256 |
|---|---:|---|
| `eval/tests/product/migration/test_compact_migration.py` | 12 | `0411ffdd7c8b812bf499e471eae6a4aeebb256a593da6668f5cc584ab1b83cf5` |
| `eval/tests/product/run/card/test_run.py` | 7 | `ec2653eddf6572deb484e8054628ae12df2f96f9411bd1b9a09b60047202023a` |
| `eval/tests/product/templates/test_brief_template.py` | 5 | `d4dd674967513df5481cc8d70a388652edd5f67ecb28c5833339ea3d1d14c473` |
| `eval/tests/product/templates/test_model_routing_text.py` | 31 | `6ffded67cfab59dc11d5b4fa35531a7d3ab02826ab509431e1d2ceb12d70b095` |
| `eval/tests/tooling/behavior/review-convergence/test_cases.py` | 21 | `2c2c6b14d2504b1a45f69caa4ff6cd841f2ea854fc7e80da8408a9d93986ea52` |
| `eval/tests/tooling/behavior/review-convergence/test_composite_oracle.py` | 7 | `a706835afb0d52badf712b24ff5bfab65c3d2b1d0037c4a52feaae276f94f7c3` |
| `eval/tests/tooling/behavior/review-convergence/test_evidence.py` | 39 | `4ede762af2bf43ae6802cbe3525ecc84eca443015bbf285b8813b7d6168449b8` |
| `eval/tests/tooling/scenario-index/test_index.py` | 32 | `1e2b7c0297afe262bccf21b7990e80f903ee5b80240a0f7b4cd15fad22b22564` |

## Maintainer tools

These tools and tests are maintainer tooling and do not ship. `eval/tests/tooling/maintaining/ci-mechanical/` holds three methods: the named CI block runs and its first failure is named, a missing step fails, and a nested command trace is filtered on success while a failure still names its command. `eval/tests/tooling/maintaining/record-rows/` holds two: a generated workspace passes the lint rows, and a row without evidence is refused. `eval/tests/tooling/maintaining/release/` holds six: the install inventory records every file with its size and hash, removes its sandbox and fails on a count mismatch; the per-release configuration is refused when a field is missing or mistyped; part titles and runtime versions follow it; a relative configuration path works from outside the candidate; and the driver's help runs. The four protected migration and template tests read the catalog target and check it against the `SKILL.md` stamp. Before integration, the release procedure was rehearsed end to end with these tools on a disposable clone, and every phase passed.

## Scope and limits

These are deterministic observations of shipped guides, the task template, the migration script and maintainer tooling on macOS. Linux awks and the hosted CI run first observe them on the release candidate. The text checks verify the shipped instructions, not whether an agent follows them. The development calibration is invalid, no held-out behavioral cohort was run, and no result here establishes fewer review rounds, fewer tokens, an improvement in agent behavior or a completed private migration.
