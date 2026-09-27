# Tackle 8.2 development evaluation

Observed on September 22, 2026. This report summarizes twelve paired episodes and ten focused
follow-up episodes. It records improvements in exercised cases, earlier failures and coverage
limits. It does not establish general reliability, speed or delivery-efficiency improvement.

## Paired observation

The [protocol](protocol.md), visible cases, private evaluator oracle, installations and execution
order were frozen before each model invocation. The baseline was 8.1.0 at commit
`61f9b4b142ba83a6a502cf833dd6b9b43e556253`; its candidate was an earlier development snapshot,
not the final 8.2 release artifact. Six English/Spanish cases ran in both arms.

Both arms met all six functional expectations. Expected missing-input blocks and rejection of
a deliberately defective integration count as appropriate task outcomes, not successful exporter
or integration delivery. Each arm required one internal implementation correction; those initial
failures remain recorded. First-invocation success does not mean no rework.

The candidate avoided gratuitous closing footers: zero versus four in the baseline. It also read
unnecessary guides, repeated a known failed check and constructed two checks that could mask an
intermediate assertion failure. Independent byte inspection established the observed artifact
results. Native input tokens were lower, while summed wall time, command count and command-output
text volume were higher. Different cache coverage and one observation per case limit comparison.

## Focused corrections

The follow-ups tested only affected candidate cases, without rerunning the baseline. Two variants
made previously ambiguous obligations explicit before execution: an actual retained failed check
on resume, and preservation comparisons distinguished from invoking a named prior checker.
Historical inputs and ambiguous results were not rewritten or regraded.

| Round | Episodes | Observed outcome |
|---|---:|---|
| Bounded checks, blocking, failed-evidence resume and reuse | 4 | Functional expectations met; bounded/reuse gates pass; blocker discovery and resume preload fail. |
| Reading-order correction | 2 | Functional expectations met; both loading gates fail. Resume also adds a failing helper and unnecessary checker repetition. |
| Explicit ordering and check reuse | 2 | Resume passes; blocker still inventories after absence inside one compound command. |
| Batch-guard clarification | 1 | Functional blocking passes; discovery continues after absence. |
| Isolated prerequisite probe | 1 | Original stopping gate passes: the actor checks only the required input, observes absence and reports the blocker without further commands. |

The four failed source-validation rounds remain preserved. The final round also follows the new
isolated-probe instruction, assessed separately from the unchanged stopping criterion. A correctly
guarded batch would not fail a newly invented stricter oracle. The series stopped after this pass.

Four additional offline shell replays used the actual old and new generated check commands on
correct and incorrect bytes. The old command incorrectly returned success on bad bytes; the new
command rejected them. Both accepted correct bytes. Original observations were untouched. Actual
unrelated-file preservation was checked independently; sentinel-check robustness was not exercised
where no such assertion was claimed.

Earlier bounded-check, resume and reuse passes support unchanged mechanisms. They are not fresh
complete-case trials of the final wording. Release-only version and documentation edits did not
change the successful stopping procedure. The final one-case observation took 24.401 seconds and
two commands; this narrow observation is not a general performance estimate.

## Provenance and limits

Episodes used the same pinned Docker image, Codex CLI 0.154.0 and requested
`gpt-5.6-luna`/high settings. Native events do not independently attest a resolved server model.
Each actor had read-only method/fixture mounts, a separate writable work directory and an offline
isolation probe. Live inference used the authorized existing subscription session. Visible
commands show no prohibited oracle, credential or other-case access; network traffic was not
packet-audited.

Reviewers did not author the evaluated source/fixtures or execute the models, but shared the host;
reviewer OS isolation is not claimed. Native streams, commands, hashes, failures and source stages
are retained by the maintainer. This public summary omits private workspace paths and account
details; the [runner and documentation](README.md) support new separately authorized observations.

Native usage was available for all completed episodes. Input totals include cached input; output
totals include reasoning output. Command-output bytes are a limited reading proxy, not filesystem
I/O. Storage lengths, complete read/write volume and billing are different measures. Currency cost
and detailed phase timing are unavailable. Deterministic recipe measurements elsewhere in the
repository do not establish agent behavior. One final focused pass provides evidence for that
case, with the historical failures and these limits attached.
