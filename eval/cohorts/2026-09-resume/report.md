# Resume cohort: the 9.0.0 candidate against the 8.4.1 method on a staged mid-task workspace

- Cohort `2026-09-resume`, seal `2f6463032de35db7c57838d0a27825e5db0d5808ada4aebc1178264b91ff8429`, created 2026-09-27T14:49:55Z.

Hypothesis: With the Tackle 9.0.0 candidate, a Haiku executor resumes a staged mid-task workspace no less correctly than with the 8.4.1 method: it repeats no completed side effect, reconciles the workspace's own record of progress against the code's actual state, preserves whatever correction-cycle count the workspace already recorded, and leaves the task passing its own acceptance, replicated at three seeds per held-out variant.

Decision: resume: report-only: pooled fall-rate difference -0.3333 [-0.6667,0.0000]; raw falls s65-migration-replay method=1/3 method:candidate=3/3; s66-notice-replay method=3/3 method:candidate=3/3; complete (every held-out variant has at least 2 valid episodes for both arms); median episode cost method=$1.1944 method:candidate=$1.0568

| Variant | Arm | Episodes | Valid | Avoided | Fell | Invalid |
|---|---|---|---|---|---|---|
| s65-migration-replay/h1 | method | 3 | 3 | 2 | 1 | 0 |
| s65-migration-replay/h1 | method:candidate | 3 | 3 | 0 | 3 | 0 |
| s66-notice-replay/h1 | method | 3 | 3 | 0 | 3 | 0 |
| s66-notice-replay/h1 | method:candidate | 3 | 3 | 0 | 3 | 0 |

Ordering check:

- method: ordered=6, unordered=0, n/a no-marker=0, not run=0, missing=0.
  Folded: none.
- method:candidate: ordered=5, unordered=1, n/a no-marker=0, not run=0, missing=0.
  Folded: none.

Invalid episodes:

- none.

Median per-episode dollar cost:

- method: $1.1944.
- method:candidate: $1.0568.

Artifact hashes:

- decision.py (sealed): `5af092e465aa5d0725d911deede3fa57857694e0a26389e4ae3b6a48d0e9638b`.
- price-table.json (sealed): `9253ff9188ee88d4200386e8449c4735c8a6f5e993596efab0dcd7580c5252b6`.
- manifest artifacts.baseline_sha256: `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`.
- manifest artifacts.candidate_sha256: `d4824404000ad3bd3a5b8d2385799f49f082985e73a35c483f2845a78f676180`.
- manifest oracle_sha256: `338d0d2bf221b46255f9a6f1234f739bf889d1312cff58035266848ee0f4117d`.

Smoke:

- checker accepts: yes (0 error(s)).
- smoke-method: s65-migration-replay/v1 method -> fell.
- smoke-candidate: s65-migration-replay/v1 method:candidate -> avoided.

Development-grade evidence. Each episode ran as a single Claude Code subagent session, at the fast tier only, on the operator's machine and login, not in an isolated install: it started in the host repository, and both arms could reach the installed skill and that repository. The ordering check matches literal substrings against one recorded field per tool call, never a resolved path: a wildcard read such as `cat dir/*.md` names neither tracked file literally and registers no touch at all, a symmetric bias toward the unordered reading for both required files equally. This figure is report-only and gates nothing.
