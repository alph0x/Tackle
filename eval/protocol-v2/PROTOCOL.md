# Evaluation protocol v2

This protocol says how a Tackle behavioral claim is tested. A cohort is pre-registered, sealed and
run. Its records are checked by `check.py`, which also computes the verdicts:

```sh
python3 eval/protocol-v2/check.py eval/cohorts/<cohort_id> [--json]
```

The checker only uses the Python standard library. It reads the cohort directory and never writes to
it. Exit 0 means the cohort is valid and its verdicts are printed. Exit 1 means it is invalid: every
violation is printed as `error: <file>:<line>: <code>: <text>` and no verdicts are printed. Exit 2
means a usage error. The fixtures in `fixtures/` (rebuilt by `fixtures/build.py`) cover each rule
below, and `test_check.py` runs them through the CLI.

## 1. Pre-register before the first episode

Write `manifest.json` (schema `tackle-cohort/1`) and seal it before any episode runs. Every field is
required, and unknown fields are rejected.

| Field | Meaning |
|---|---|
| `cohort_id` | Unique name. Any change after the first episode needs a new id; observed cohorts are never amended. |
| `hypothesis` | One falsifiable sentence: "With <candidate>, the agent falls into <trap> less often than with <baseline>." |
| `primary_metric`, `decision_rule` | What is counted and which label decides the claim (section 4). |
| `n_min` | Minimum valid episodes per arm and variant; write it explicitly (5 is usual). |
| `seeds` | Distinct integers ≥ 1. |
| `variants` | `{scenario_id, variant_id, split, class, fixture_sha256}`. `split` is `development` or `held-out`; `class` is `outcome-trap`, `procedure` or `tripwire`. Held-out fixtures are hashed here before any record uses them. |
| `arms` | `control`, `method`, `method:<config>` (for example `method:routed`), or `ablation:<rule_id>`. |
| `comparisons` | `{id, baseline_arm, candidate_arm}`. `primary` is `control` → `method` whenever both arms exist. |
| `executor`, `judge` | Coordinating harness, model and effort; judge `model_family` and `blinded`. |
| `artifacts`, `oracle_sha256` | Hashes of the baseline and candidate trees and of the answer sheets. |
| `order` | The randomized `{episode_id, scenario_id, variant_id, arm, seed}` list. Every entry gets exactly one record by cohort close. |
| `created_at`, `seal_sha256` | `seal_sha256` is the sha256 of `json.dumps(manifest_without_seal, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`. Keep a copy of it outside the participant environment. |

## 2. Record every planned episode

`episodes.jsonl` holds one `tackle-episode/1` object per line, in run order. Its fields are
`schema`, `cohort_id`, `episode_id`, `prev_sha256`, `scenario_id`, `variant_id`, `split`, `arm`,
`seed`, `order_index`, `artifact_sha256`, `executor`, `roles`, `judge`, `rule_exposure`, `outcome`,
`invalid_reason`, `scores`, `cost`, `transcript_sha256`, `started_at` and `finished_at`. Rules:

- **Chain.** `prev_sha256` is the sha256 of the previous line's UTF-8 bytes, excluding its newline.
  The first line uses 64 zeros, so editing an earlier line breaks every later one.
- **Order.** Each record matches its `order` entry on id, scenario, variant, arm and seed, and its
  `order_index` equals that entry's position. A planned episode that did not run is recorded as
  `outcome: unobserved` with all scores null. Numeric placeholder scores are rejected.
- **Outcome.** `outcome` is `fell`, `avoided`, `invalid`, `unobserved`, `timeout` or `error`.
  `invalid` needs a non-empty `invalid_reason`. Only `fell` and `avoided` count toward verdicts.
- **Hashes.** Only a `control` record may omit `artifact_sha256`. Only an `unobserved` record may
  omit `transcript_sha256`.
- **Roles.** `roles` lists every subagent role that ran, with `tier` (`fast`, `standard`,
  `frontier` or `n/a`), model, `effort` (`low` … `max` or `n/a`) and token counts.
- **Cost and scores.** `cost` records tokens, wall seconds, tool calls and files written, as
  non-negative integers or `n/a`; unknown values are `n/a`, never estimates. `scores` are 0, 1, 2 or null.
- **Leaks.** No field may contain an absolute path (`/Users/`, `/home/`, `/root/`, `/private/`,
  `/var/folders/`, `~/`, a Windows drive), a private-key block, an `sk-` key or an email address.

## 3. Blinding and judges

The judge sees transcripts without arm labels (`blinded: true`). A semantic judge should come from
a different model family than the executor; the record keeps `model_family` so a reader can check
that. A mechanical judge has no model family and records `n/a`. The coordinator sets
`rule_exposure` when an audit shows that the rule under test was reachable from a control arm.
That control is then contaminated for the comparison.

## 4. Verdicts

For each comparison and each variant, count the valid falls: baseline k_b/n_b and candidate
k_c/n_c. The Wilson 95% interval (z = 1.96) is printed for reading only. p_better is the one-sided
Fisher exact p-value that the baseline falls more often than the candidate; p_worse is the same test
with the arms swapped; α = 0.05. The first matching label wins:

1. `contaminated`: a baseline-arm episode has `rule_exposure: true`.
2. `unobserved`: n_b < `n_min` or n_c < `n_min`.
3. `method-worse`: p_worse < α.
4. `inert`: k_b = 0 (the trap never fired for the baseline, and the candidate was not worse).
5. `discriminates`: p_better < α.
6. `inconclusive`: otherwise.

`method-worse` is evaluated before `inert`, so a candidate that falls where the baseline never
does is reported, not hidden.

Output lines:

- **Primary comparison.** `verdict <s>/<v> <label> control <k>/<n> [<lo>,<hi>] method <k>/<n> [<lo>,<hi>] p_better=<p> p_worse=<p>`.
- **Other comparisons.** The same shape, prefixed `verdict[<id>]`.
- **Ablation arms.** `ablation <rule_id> <s>/<v> <k>/<n>`, with no label.
- **Empty arms.** An arm with no valid episodes prints `-/0 [n/a]`, and its p-values are `n/a`.

Pooled reporting is not a label. It covers `outcome-trap` variants that are neither `contaminated`
nor `unobserved`, and only when at least two qualify. It is the mean of d = k_b/n_b − k_c/n_c. The
95% percentile bootstrap interval resamples variants with `random.Random(20260923)` over
B = 10,000 draws and takes the sorted means at index 250 and 9749. The line is
`pooled <d> [<lo>,<hi>] seed=20260923 B=10000`, or `pooled[<id>] …` for other comparisons.
Numbers have four decimals and never print `-0.0000`. `--json` prints the same values.

## 5. Claims

- A claim about several scenarios applies Benjamini–Hochberg at q = 0.1 over the per-variant
  one-sided Fisher p-values. This belongs to the cohort report, not the checker.
- `discriminates` on a development variant alone is a hypothesis. Evidence for a change to the
  method comes from held-out variants that were sealed before any run.
- A scenario that discovered a rule cannot be the only evidence that the rule discriminates;
  discovery and validation stay separate. The rule-evidence ledger applies the same invariant.
- `inert` and `inconclusive` are not evidence that a rule helps. `unobserved` means the cohort did
  not collect enough to judge.
