# Action plan — Overdue notices

## 1. Objective

Give each patron with overdue loans one plain-text notice in the wording the branch agreed (R01), produced
by one command from the circulation export (R02), documented (R03) and accepted against the agreed
samples (R04).

## 2. Expected result

- `python3 -m notices render <loans.json> <YYYY-MM-DD> <outdir>` writes `<card_no>.txt` per patron with an overdue loan (R01, R02).
- `docs/notice-wording.md` describes the wording and ordering (R03).
- `sh checks/accept.sh` passes: tests green and the rendered notices equal to the samples (R04).

### Behavior and outputs

| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |
|---|---|---|---|---|
| `R01` | the agreed wording, items oldest first | one text file per card | a card with nothing overdue → no file | none: the board approved the wording |
| `R02` | one command | exit 0, one summary line | wrong arguments → usage error, exit 2 | wording of the summary line |
| `R03` | wording documented | `docs/notice-wording.md` | — | layout |
| `R04` | acceptance against the samples | `accept: ok` | — | none |

### Acceptance and test strategy

| Criterion | Task | Task check | Related regression check | Evidence slot |
|---|---|---|---|---|
| `R01` | `T-01`, `T-02` | `python3 -m unittest discover -s tests -q` | — | `verification-records/` |
| `R02`, `R03` | `T-03` | `python3 -m notices render tests/fixtures/loans.json 2026-09-01 /tmp/n` exit 0 | the unit tests | `verification-records/` |
| `R04` | `T-04` | `sh checks/accept.sh` exit 0 | — | `verification-records/` |

## 3. Non-goals

- No change to the circulation export.
- No sending: the desk prints or emails the files itself.
- No wording beyond the agreed samples inside this initiative's tasks (D-02).

## 4. Current state (grounded)

**Key finding (verified):** the export carries one row per loan, keyed by `card_no` (`tests/fixtures/loans.json:2`).

**Precedent we mirror:** the reminder the desk staff wrote by hand, as approved by the board (`tests/fixtures/expected/HL-20817.txt:1`).

## 5. Task decomposition

| Task | Responsibility | Traces to | Briefing | Depends on | Why separate |
|---|---|---|---|---|---|
| **T-01 · Loan reader** | read and group the export | `R01` | `tasks/T-01-loan-reader.md` | none | reused by the command |
| **T-02 · Notice template** | the wording | `R01` | `tasks/T-02-notice-template.md` | T-01 | the wording work, reviewed by Tomás |
| **T-03 · Render command** | the command and the wording document | `R02`, `R03` | `tasks/T-03-render-command.md` | T-02 | user-facing |
| **T-04 · Acceptance run** | tests plus sample comparison | `R04` | `tasks/T-04-acceptance-run.md` | T-03 | the deliverable check |

### Dependency graph

```text
T-01 ──► T-02 ──► T-03 ──► T-04
```

## 6. Readiness and acceptance

### 6.1 Per-task

- The brief's command passes with its native exit; the samples are unchanged; each validation has a raw record.

### 6.2 Initiative-level

- `sh checks/accept.sh` passes on the integrated tree and is recorded; the README documents the command.

## 7. Risks and dependencies

- The library board meets quarterly; any wording change waits for it (owner: Tomás).

## 8. Decisions and questions

- D-01 gitignore, D-02 the agreed wording samples, D-03 the cut-off date is exclusive. Q-01 resolved.
