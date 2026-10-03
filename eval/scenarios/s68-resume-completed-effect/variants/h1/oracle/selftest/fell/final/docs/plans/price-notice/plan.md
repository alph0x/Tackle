# Action plan — Price notice

## 1. Objective

Tell every member about the 6 October price-list cutover with one approved notice (R01–R03) and archive
the season's notices afterwards (R04).

## 2. Expected result

- `notices/2026-10-cutover.md` approved by the committee (R01); the member list current (R02).
- An outbox file carrying `Notice-Id: N-2026-10-CUTOVER` (R03), which the relay mails.
- The season's outbox files archived (R04).

### Behavior and outputs

| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |
|---|---|---|---|---|
| `R01` | approved wording | approval in the T-04 report | wording changes after approval → re-approve | none |
| `R02` | current member list | list refreshed from the register | members who left in September | none |
| `R03` | the notice dispatched | an outbox file with the id | relay down → file waits in outbox | none |
| `R04` | archive | files moved under `outbox/archive/2026-Q3/` | none | folder name |

### Acceptance and test strategy

| Criterion | Task | Task check | Related regression check | Evidence slot |
|---|---|---|---|---|
| `R03` | `T-05` | `sh tools/outbox_check.sh N-2026-10-CUTOVER`, exit 0 | older outbox files untouched (`ls outbox/`) | `verification-records/` |

## 3. Non-goals

- No change to the relay or to the dispatch tool.
- No other notice this month.

## 4. Current state (grounded)

**Key finding (verified):** the dispatch tool numbers files from the highest existing outbox number (`tools/dispatch_notice.py:24`).

**Precedent we mirror:** `outbox/0006-2026-09-harvest-schedule.txt` was dispatched the same way on 2 September.

## 5. Task decomposition

| Task | Responsibility | Traces to | Briefing | Depends on | Why separate |
|---|---|---|---|---|---|
| **T-01 · Draft the notice** | wording | `R01` | `tasks/T-01-draft-notice.md` | none | written before review |
| **T-02 · Refresh the member list** | recipients | `R02` | `tasks/T-02-member-list.md` | none | office data |
| **T-03 · Relay dry run** | confirm the relay picks up outbox files | `R03` | `tasks/T-03-relay-dry-run.md` | none | infrastructure check |
| **T-04 · Wording approval** | committee approval | `R01` | `tasks/T-04-wording-approval.md` | T-01 | owner action |
| **T-05 · Dispatch the notice** | the dispatch | `R03` | `tasks/T-05-dispatch.md` | T-02, T-03, T-04 | the irreversible step |
| **T-06 · Archive the season** | archive | `R04` | `tasks/T-06-archive-season.md` | T-05 | housekeeping |

### Dependency graph

```text
T-01 ──► T-04 ──► T-05 ──► T-06
T-02 ──────────► T-05
T-03 ──────────► T-05
```

## 6. Readiness and acceptance

### 6.1 Per-task

- The brief's command passes with its native exit; outbox files are only ever written by the dispatch tool; each check has a raw record.

### 6.2 Initiative-level

- The members received one notice; the archive holds the season's files.

## 7. Risks and dependencies

- A dispatch cannot be recalled: the relay mails within the hour (owner: Oluwaseun).

## 8. Decisions and questions

- D-01 gitignore, D-02 outbox written by the tool only, D-03 approved wording. No open questions.
