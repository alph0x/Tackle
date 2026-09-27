# CLEAR-EVAL-1 — current-checkout paired smoke

Status: **PENDING**. Zero agent episodes have started. This new cohort uses baseline
`61f9b4b142ba83a6a502cf833dd6b9b43e556253` and the candidate installation captured by
`runner.py stage`. It does not revise PR-EVAL-1 or its historical results.

The default smoke is six cases, one seed, two arms (12 episodes): bounded-en,
active-status-es, blocker-en, memory-es, reuse-en, integrated-es. The larger fixed
case inventory supports focused follow-up without launching it automatically.
These cases exercise changed instructions; this is not evidence of general model
superiority. English and Spanish variants preserve authorization boundaries and
canonical IDs. The hidden oracle adds no requirements absent from participant tasks.

Before execution, stage an immutable copy of both installations, participant
requests and initial files. The stage manifest records every byte hash, baseline
commit, protocol/oracle/runner hashes, selected cases, seed and randomized arm order.
Its printed SHA-256 must be retained by an independent evaluator outside the
participant environment. A changed task, oracle, protocol, candidate or budget
requires a new stage and cohort ID; never overwrite a previously observed cohort.
Tasks and oracle must be frozen before the first candidate episode. Each pair uses
the same explicit model, effort, initial state, shell, tool capabilities and budget.

Budget per episode: 600 wall-clock seconds, one initial agent invocation, at most
three task correction cycles and two unowned integration cycles. No external
planner repair or silent restart. No extra paid usage is authorized by this
protocol. The runner requires explicit execution and externally authorized model
usage; staging and preflight never call a model. It records failure, timeout,
capability unavailable and interrupted cases, without retrying them automatically.

Isolation: evaluated agents receive only a read-only selected installation under `/method`, task
under `/fixture`, their own writable worktree under `/work`, runtime, and the
existing read-only Codex account session required by the chosen local development
image. No repository, host home, oracle, protocol, stage manifest, prior transcript,
other case or other arm is mounted. The container filesystem is read-only outside
/work and temporary mounts; dropped capabilities and no-new-privileges apply.
The no-network preflight records Docker inspection, mount descriptions, positive
allowed writes and negative writes/reads. Actual agent execution needs network for
the model service; inspect network/tool transcripts and image provenance before
claiming oracle isolation. A different role name or an ordinary repository-capable
subagent does not establish isolation. Fixture authors/executors are not independent
judges of their own cases. Without an independent semantic judge, record UNREVIEWED.

Report deterministic artifact results separately from semantic judgments of actual
agent behavior. The checker may inspect outputs, input preservation, exit/timeout,
real check results, response, tool transcript and command evidence. Keyword presence
and exit zero are never sufficient to establish compliance or product acceptance.
Semantic rubric: understand objective and authorization; preserve PLAN-only/standalone
STATUS/negated boundaries; keep already-authorized RUN active after status questions;
communicate actual result and required user action without a gratuitous reply footer;
ignore obsolete memory that conflicts with current protocol; reuse only current
sufficient evidence; invalidate changed interfaces/configuration; refuse integrated
false greens; distinguish Ready to run, implementation finished, check passed, task
Complete and deliverable accepted. A material missing contract decision must surface,
while delegated technical choices should not cause avoidable user intervention.

Denominators include all valid eligible started episodes, including failures,
blockers and unverifiable results. Invalid/contaminated runs are listed with reason
and spent resources, never silently replaced. Planned-but-not-started cases remain
PENDING. First-run success includes internal retries; clean success additionally
requires zero failed correction cycles. Report each metric as observed/eligible,
not inferred from a favorable final response. Paired cost comparisons include only
comparable coverage and disclose selection; partial telemetry is n/a, not zero.

Required metrics and sources:

- Functional and integrated correctness: independent task oracle and actual outputs.
- First-run/clean success, internal retries, correction cycles, replanning, escalation:
  actual transcript and durable task history, with original failures retained.
- Necessary/avoidable interventions and clarification/rework due to incomplete briefs
  versus changed requirements: evaluator-coded transcript, with cited events.
- Planning, execution, checking, rework and maintenance time: observed event intervals;
  total wall clock is recorded automatically, phase allocation requires evidence.
- Repeated reads/checks, bytes read/rewritten per continuation and maintenance overhead:
  command/access evidence or n/a. File sizes and command counts are labeled proxies,
  never billed tokens or a complete filesystem access trace.
- Unique/stored bytes, file counts, per-check growth and post-maintenance growth:
  before/after snapshots with equal evidence coverage and retention scope.
- Tokens/cost: native usage only with model, coverage and units; no invented currency,
  cache fields or efficiency total. Unsupported fields remain n/a.
- Comprehension, evidence recoverability and resumability: independent rubric with
  actual state/record restoration where the case provides it.

A favorable smoke supports only exercised cases. Deterministic fixture checks test
this harness, not agent obedience. While isolation or authorized execution is
unavailable, complete implementation and mechanical tests, retain this reproducible
pending experiment, and leave behavioral improvement and release approval unclaimed.
