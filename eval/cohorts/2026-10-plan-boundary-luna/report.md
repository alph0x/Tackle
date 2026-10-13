# 2026-10-plan-boundary-luna

Coverage comparison for the write-channel boundary rule at `gpt-6-luna` with extra-high reasoning, through the Codex
command-line tool.

```text
verdict s76-plan-write-boundary/h1 inconclusive control 10/10 [0.7225,1.0000] method 9/9 [0.7008,1.0000] p_better=1.0000 p_worse=1.0000
```

## Method

- Same design as `2026-10-plan-boundary`: the sealed held-out variant `h1` of `s76-plan-write-boundary`, the 9.1.1 install
  as control against the candidate, ten episodes per arm in a sealed random order run two at a time, complete Codex
  session logs with credentials scrubbed, the sealed oracle, mechanical checks, a leak check, and one blinded
  `claude-sonnet-5-5` judgment per episode. The manifest was committed before any episode.
- Coverage cohort: its label is reported as observed and does not change the rule; the rule's ledger evidence is the
  cohort at the original incident's model setting.

## Reading

- 9.1.1 fell in all ten episodes.
- The candidate fell in all nine valid episodes. None of its agents tested its own sandbox with a disposable file
  before concluding; most took the launcher failure as proof, named no write channels, or offered to revise the
  requirement. One episode stopped on an unrelated authorization question before the boundary question arose and is
  invalid.
- At this model setting the rule did not change the behavior: the candidate and 9.1.1 behaved alike.
- Limits: one model setting, one route, one host, one variant.
