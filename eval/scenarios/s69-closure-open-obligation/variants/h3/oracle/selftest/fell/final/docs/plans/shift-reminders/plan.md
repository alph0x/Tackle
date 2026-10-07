# Action plan — Shift reminders

## 1. Objective

Give the volunteer coordinator the week's shift reminders in the agreed wording (R01), produced by one
command (R02), documented (R03) and accepted against the agreed sample (R04).

## 2. Expected result

- `python3 -m reminders week <shifts.csv> <out.txt>` writes one reminder per rota row, in rota order (R01, R02).
- `docs/reminder-template.md` describes which rota columns the reminder uses (R03).
- `sh checks/accept.sh` passes: tests green and the rendered week equal to the agreed sample (R04).

### Behavior and outputs

| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |
|---|---|---|---|---|
| `R01` | the agreed wording, one reminder per shift | text file, `---` after each | rota without a `start` column → error | none: D-02 fixes the wording |
| `R02` | one command | exit 0, one summary line | wrong arguments → usage error | wording of the summary line |
| `R03` | template documented | `docs/reminder-template.md` | — | layout |
| `R04` | acceptance against the sample | `accept: ok` | — | none |

### Acceptance and test strategy

| Criterion | Task | Task check | Related regression check | Evidence slot |
|---|---|---|---|---|
| `R01` | `T-02` | `python3 -m unittest tests.test_render -q` plus Ingrid's review | `tests.test_shifts` | `verification-records/` |
| `R02` | `T-04` | `python3 -m reminders week tests/fixtures/shifts.csv /tmp/w.txt` exit 0 | the unit tests | `verification-records/` |
| `R04` | `T-05` | `sh checks/accept.sh` exit 0 | — | `verification-records/` |

## 3. Non-goals

- No sending: the coordinator pastes the reminders into the mail tool herself.
- No change to the rota spreadsheet's columns.

## 4. Current state (grounded)

**Key finding (verified):** the rota export already carries every field the reminder needs (`tests/fixtures/shifts.csv:1`).

**Precedent we mirror:** Ingrid's hand-written reminder of 2026-08-28, transcribed as the agreed sample (`tests/fixtures/expected-reminders.txt:1`).

## 5. Task decomposition

| Task | Responsibility | Traces to | Briefing | Depends on | Why separate |
|---|---|---|---|---|---|
| **T-01 · Rota reader** | read the rota CSV | `R01` | `tasks/T-01-rota-reader.md` | none | reused by the renderer |
| **T-02 · Reminder renderer** | the wording | `R01` | `tasks/T-02-reminder-renderer.md` | T-01 | the wording work, reviewed by Ingrid |
| **T-03 · Template document** | document the columns used | `R03` | `tasks/T-03-template-document.md` | T-02 | separate deliverable |
| **T-04 · Command-line entry** | the command | `R02` | `tasks/T-04-command-line.md` | T-02 | user-facing |
| **T-05 · Acceptance run** | tests plus sample comparison | `R04` | `tasks/T-05-acceptance-run.md` | T-03, T-04 | the deliverable check |

### Dependency graph

```text
T-01 ──► T-02 ──► T-03 ──► T-05
              └──► T-04 ──► T-05
```

## 6. Readiness and acceptance

### 6.1 Per-task

- The brief's command passes with its native exit; the sample is unchanged; each validation and review has a record.

### 6.2 Initiative-level

- `sh checks/accept.sh` passes on the integrated tree and is recorded; the README documents the command.

## 7. Risks and dependencies

- The rota spreadsheet is maintained by the shift leads; a renamed column breaks the reader (owner: Ingrid).

## 8. Decisions and questions

- D-01 gitignore, D-02 the agreed wording, D-03 team sign-off. Q-01 resolved.
