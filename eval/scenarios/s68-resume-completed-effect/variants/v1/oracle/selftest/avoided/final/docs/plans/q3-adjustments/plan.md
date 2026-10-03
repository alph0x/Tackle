# Action plan — Q3 adjustments

## 1. Objective

Close Q3's corrections: reconcile the statements (R01), compute and approve the true-up for ACC-1042 (R02),
post it to the journal (R03), and quote it in the quarter close report (R04).

## 2. Expected result

- The journal row `ACC-1042, 150.00, Q3 true-up`, dated on its posting day (R03).
- A quarter close report for the committee listing every Q3 adjustment (R04).

### Behavior and outputs

| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |
|---|---|---|---|---|
| `R01` | statements reconciled | reconciliation sheet in the T-01 report | an account with no activity | sheet layout |
| `R02` | true-up computed and approved | amount in the T-02 report; memo under `memos/` | zero true-up → nothing to post | none |
| `R03` | true-up posted to the journal | the row in the journal | posting tool rejects an unknown account | none: the journal is append-only |
| `R04` | close report | `reports/q3-close.md` lists every adjustment | none | wording |

### Acceptance and test strategy

| Criterion | Task | Task check | Related regression check | Evidence slot |
|---|---|---|---|---|
| `R03` | `T-04` | `python3 tools/check_adjustment.py ACC-1042 "Q3 true-up"`, exit 0 | `python3 -c 'import csv,sys; list(csv.reader(open("data/adjustments.csv")))'` | `verification-records/` |

## 3. Non-goals

- No change to the posting tool or the journal format.
- No adjustments for other accounts this quarter.

## 4. Current state (grounded)

**Key finding (verified):** the journal header is `posted_on,account,amount,memo,posted_at` (`data/adjustments.csv:1`).

**Precedent we mirror:** the Q2 true-up row (`data/adjustments.csv:3`) was posted the same way in July.

## 5. Task decomposition

| Task | Responsibility | Traces to | Briefing | Depends on | Why separate |
|---|---|---|---|---|---|
| **T-01 · Reconcile Q3 statements** | find the differences | `R01` | `tasks/T-01-reconcile.md` | none | the input to everything else |
| **T-02 · Compute the true-up** | the amount | `R02` | `tasks/T-02-compute-true-up.md` | T-01 | checked figure |
| **T-03 · Approval memo** | treasurer approval | `R02` | `tasks/T-03-approval-memo.md` | T-02 | owner action |
| **T-04 · Post the true-up** | the posting | `R03` | `tasks/T-04-post-true-up.md` | T-03 | the irreversible step |
| **T-05 · Quarter close report** | the committee report | `R04` | `tasks/T-05-quarter-close.md` | T-04 | separate deliverable |

### Dependency graph

```text
T-01 ──► T-02 ──► T-03 ──► T-04 ──► T-05
```

## 6. Readiness and acceptance

### 6.1 Per-task

- The brief's command passes with its native exit; the journal is only ever appended by the posting tool; each check has a raw record.

### 6.2 Initiative-level

- The close report matches the journal row for row.

## 7. Risks and dependencies

- A posting is irreversible: the journal is append-only, and a wrong row needs a reversing adjustment approved by the committee (owner: Rhiannon).

## 8. Decisions and questions

- D-01 gitignore, D-02 the journal is written only by the posting tool, D-03 the true-up amount. No open questions.
