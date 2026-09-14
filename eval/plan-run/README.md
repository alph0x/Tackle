# Plan → Run evaluation fixtures

These nine synthetic families are development fixtures for the Plan → Run refactor. They are not additional numbered Tackle scenarios and do not measure an executor by themselves. Each family has a visible task contract under `fixtures/` and a protected oracle under `oracle/`.

The evaluator stages only `fixtures/Txx/task.md` and `input.json`. `measurement.stage_participant` creates that exact copy and rejects unexpected files and symlinks. This is a copy check, **not filesystem isolation**. Before either planner or executor starts, use a separate machine/container with read roots limited to this copy, its selected method installation and necessary runtime. Do not mount this repository, evaluator home, oracle, protocol, previous transcripts or another arm's output. Audit mounts, allowed roots and access/transcript evidence. If this cannot be established, record unavailable; a fresh subagent with repository access is insufficient.

Run `python3 -m unittest discover eval/plan-run/tests -p 'test_*.py'` from the repository root with Python 3.10+ on POSIX. These checks execute positive and negative synthetic traces, trusted code examples, real child failures/signals/timeouts, staging and mutation checks. No helper launches a model or controls Tackle execution. The code probe executes only reviewed synthetic snippets; it is not a sandbox for arbitrary submissions. Its traversal counter detects the supplied quadratic implementation, not arbitrary asymptotic complexity. Review actual code for the full stated complexity/no-dependency rubric.

`oracle/answers.json` contains individually named cases and expected acceptance, derived from each visible task. Functional and artifact checks compare against task requirements. Procedural cases project observed state into structured traces: they test the measurement predicates, not whether an agent obeyed a rule. For real arms the evaluator extracts these fields from actual files, process results and transcript evidence and records each source; an agent's self-reported PASS is insufficient. Semantic coverage and equivalent approaches receive independent review; the structured T03 projection is not a natural-language semantic judge.

`rule-inventory.json` covers every nonblank source line in the 53 captured documents other than the historical changelog, grouped into paragraphs, examples, headings and table rows. This is an intentionally inclusive **source-unit count, not a count of normative rules**. Each record has a literal span/hash, decided disposition, destination, safety purpose, owner and regression. Preserve means keep the literal obligation at its named existing section; merge/replace names a planned canonical section and its preserved purpose. Planned sections need not exist before the refactor. Owner names designate work areas, not private plan IDs. Behavioral evidence for the changed method remains explicitly pending; deterministic trace checks cannot discharge it. Downstream edits must reconcile actual changes against these records, including any newly discovered conflict; do not silently relabel a deleted rule as preserved.

`baseline-sources.json` records the original 7.3.0 snapshot, including disclosed preexisting dirty documentation. `manifest.json` binds those source hashes, every task/oracle/protocol/measurement artifact, case IDs and participant allowlists. The manifest excludes itself to avoid a circular hash. Before observing arms, an independent evaluator stores its SHA-256 **outside the candidate's writable world**, verifies baseline sources against the captured snapshot, and pins the complete candidate installation by version, commit and file hashes. Do not regenerate an outcome cohort's manifest: changes require a new frozen cohort/protocol revision and separate results. No candidate-provided allowlist grants permission to change baseline sources. Hash checks detect drift relative to a trusted seal; someone able to edit both artifacts and the external seal is outside this protection.

The primary 54-episode comparison remains **not started**. No first-episode success, efficiency improvement or model obedience is claimed by this suite. The existing numbered trap registry is unchanged. Release still requires the applicable normative-rule inventory diff and feature-specific behavioral run.

## Integrated acceptance

P-06 development acceptance ran the complete 133-test suite against the source tree and an
isolated Markdown-only install; both passed. The eight shipped-skill self-lint gates passed on the
source and installed copies, and the catalog matched 50 scenario directories with no answer-sheet
leak at a scratch arm root. The read-only workspace sweep covered 27 board workspaces and captured two active
workspaces with findings; this historical snapshot is not a clean release sweep. A fresh read-only execution
of all 16 rows over the 27 board workspaces (global row 8 once) classified 325 valid passes, 55
failed checks, and 25 execution errors; exit 2 and child-stderr cases are never passes, while the
canonical silent exit 1 cases for rows 5 and 15 remain valid. The preregistered 54-episode
comparison remains **UNMEASURED** (0 started): the local executor profile is Luna High, but fresh
isolated evaluated-arm binding, oracle isolation, and external budget authorization were unavailable.
Fresh independent per-Point semantic reviews passed after the sweep classification repair.
No benchmark or improvement claim is made; dedicated feature-specific D-13 behavioral evidence
and resolution of active workspace findings remain required before release. See
[`p06-integrated-acceptance.json`](results/p06-integrated-acceptance.json) for the aggregate record.
