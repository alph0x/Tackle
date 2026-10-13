# 2026-10-openspec-takeaways-reach

Re-measurement of the scenario-check rule after it was mirrored into the readiness reading path (the PLAN card's
readiness step and the task template's scenario paragraph). It compares the candidate at that tree against the
9.1.2 install on the held-out variant `h1` of `s79-scenario-without-check`, with `claude-haiku-5-5` through one
agent command-line tool on the subscription route. This cohort is the candidate; `2026-10-openspec-takeaways-reach-control`
is 9.1.2.

```text
verdict s79-scenario-without-check/h1 inconclusive control 5/8 [0.3057,0.8632] method 2/8 [0.0715,0.5907] p_better=0.1573 p_worse=0.9797
```

## Method

- Sealed and committed before any episode: ten seeds per install, in a random order. Same validity rule and label
  rule as `2026-10-openspec-takeaways`: the first eight valid episodes by seed, protocol-v2 `verdict.label`.
- This is a re-measurement, not a fresh held-out result. `h1` was already observed in `2026-10-openspec-takeaways`,
  and the new text was written after reading that result.

## Reading

- Every agent on both installs noticed the `Check: TBD` line.
- The five 9.1.2 falls replaced it with a cross-reference to a case row, which the new text calls not a Check.
- The candidate's two falls replaced it with a runnable `node --test` command, but without a stated pass condition.
  The rule asks for a command with its pass condition, and the oracle requires one, so both count as falls.
- Six of ten candidate episodes read the new PLAN card sentence; none read the new task template sentence.
  Several avoided episodes cite the PLAN card when they refuse Ready.

## Limits

- The label is inconclusive. Scoring the two candidate falls as avoided would give a different label. This oracle
  was fixed before the run and is not changed after it.
- The candidate differs from 9.1.2 in more than these two sentences. The pair measures the whole candidate against
  9.1.2, not the reading-path change alone.
- The manifest's `oracle_sha256` digests the scenario index's oracle digest for s79, not the oracle files directly.
