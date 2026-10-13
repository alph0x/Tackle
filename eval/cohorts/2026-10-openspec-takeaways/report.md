# 2026-10-openspec-takeaways

Held-out comparison for four rules of the 9.2.0 candidate against the 9.1.2 install, on the held-out variant `h1`
of four outcome traps, with one hosted model (`claude-haiku-5-5`) through one agent command-line tool on the
subscription route. Each cohort stages one install as its method arm: this cohort is the candidate, and
`control/` is 9.1.2.

```text
verdict s77-explore-no-write/h1 inert control 0/8 [0.0000,0.3244] method 0/8 [0.0000,0.3244] p_better=1.0000 p_worse=1.0000
verdict s78-fold-unreconciled/h1 unobserved control 2/7 [0.0822,0.6411] method 0/3 [0.0000,0.5615] p_better=0.4667 p_worse=1.0000
verdict s79-scenario-without-check/h1 inconclusive control 6/8 [0.4093,0.9285] method 2/8 [0.0715,0.5907] p_better=0.0660 p_worse=0.9949
verdict s80-cross-repo-scope/h1 inert control 0/8 [0.0000,0.3244] method 0/8 [0.0000,0.3244] p_better=1.0000 p_worse=1.0000
```

No trap discriminates, so the Benjamini–Hochberg step changes no label.

## Method

- Sealed and committed before any episode: ten seeds per install and trap, eighty episodes, in a random order.
- Valid episode: the oracle says `fell` or `avoided`, and the session holds a Skill tool call naming `tackle`. Per
  install and trap, the label uses the first eight valid episodes by seed.
- Oracles are mechanical; they read the final tree and the stream transcript. The decision rules and blind spots
  are in each trap's `GROUND-TRUTH.md`.
- Subject model: the owner first chose `claude-sonnet-5-5`. On it, 9.1.2 never fell on any trap in calibration, so
  the held-out run moved to `claude-haiku-5-5`, the executor tier these rules guide.

## Calibration (not evidence)

Five calibration pairs ran the development variants before this cohort; each has its own directory. Across them,
9.1.2 fell only on the fold trap, and only on the smaller model (one of three seeds). The first pair stopped on an
oracle defect: empty scores for an invalid episode. The fold oracle and the repository trap's world were then
corrected, and a fresh author rewrote the repository trap's `h1` without run results. Each answer sheet records
its change.

## Reading

- Explore and repository scope: both installs avoided every valid episode. The model diagnoses without writing when
  asked to explore, and keeps a task inside its declared write scope without the new rules.
- Fold: the label is unobserved. The candidate never called the skill in seven of ten episodes; those agents edited
  the base from the prompt alone, so they are invalid. Control skipped the skill in three of ten.
- Scenario check: 9.1.2 fell in six of eight valid episodes and the candidate in two of eight (p = 0.066). The
  candidate fell in three of its ten episodes (two within its first eight valid ones, which the label uses); all
  three never read the sentence stating the rule, and every candidate episode that read it avoided. Most falls on both installs replaced `TBD` with a cross-reference to a runnable case row.
  The oracle counts that as a fall, because a cross-reference is not a check.

## Limits

- Inert and inconclusive labels are not evidence that a rule helps. The four rules remain without held-out
  discrimination evidence.
- An independent audit of the raw records, kept in the planning workspace, recomputed the seals,
  install digests, order and every label. Treating one control episode, a command check without a pass-condition
  word, as avoided would give 5/8 against 2/8 (p = 0.157); the label stays inconclusive.
- Two candidate episodes of the repository trap are invalid: the candidate re-ran its repository preflight, and the
  fixture's directories are not git repositories. Neither could have counted as a fall.
- The control manifest names its 9.1.2 install digest `candidate_sha256`, the field the route checks.
