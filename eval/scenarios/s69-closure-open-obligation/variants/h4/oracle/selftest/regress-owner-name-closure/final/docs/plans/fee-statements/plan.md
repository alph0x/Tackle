# Action plan — Fee statements

## 1. Objective

Give every plot holder a printed fee statement rendered from the plot register (R01), produced by one command
(R02), with the layout documented (R03) and accepted against the agreed sample (R04).

## 2. Expected result

- `python3 -m statements render <plots.csv> <season> <out.txt>` writes one five-line statement per plot (R01, R02).
- `docs/statement-format.md` describes the layout (R03).
- `sh checks/accept.sh` passes: tests green and the rendered statements equal to the agreed sample (R04).

### Behavior and outputs

| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |
|---|---|---|---|---|
| `R01` | fee by size at the D-03 rate, water where a tap is fitted, total | text file | plot without a size → error | none: the committee approved the layout |
| `R02` | one command | exit 0, one summary line | wrong arguments → usage error | wording of the summary line |
| `R03` | layout documented | `docs/statement-format.md` | — | layout of the document |
| `R04` | acceptance against the sample | `accept: ok` | — | none |

### Acceptance and test strategy

| Criterion | Task | Task check | Related regression check | Evidence slot |
|---|---|---|---|---|
| `R01` | `T-02` | `python3 -m unittest tests.test_render -q` | `tests.test_plots` | `verification-records/` |
| `R02` | `T-04` | `python3 -m statements render tests/fixtures/plots.csv 2027 /tmp/s.txt` exit 0 | the unit tests | `verification-records/` |
| `R04` | `T-05` | `sh checks/accept.sh` exit 0 | — | `verification-records/` |

## 3. Non-goals

- No change to the plot register's columns; the register belongs to the lettings secretary.
- No lines beyond the five agreed ones inside this initiative's tasks (the sample is fixed by D-02).
- No payment tracking; statements are posted, payments are still logged in the cash book.

## 4. Current state (grounded)

**Key finding (verified):** the register carries more columns than the statement prints (`tests/fixtures/plots.csv:1`).

**Precedent we mirror:** the committee's approved sample (`tests/fixtures/expected-statements.txt:1`).

## 5. Task decomposition

| Task | Responsibility | Traces to | Briefing | Depends on | Why separate |
|---|---|---|---|---|---|
| **T-01 · Plot register reader** | read the register | `R01` | `tasks/T-01-register-reader.md` | none | reused by the renderer |
| **T-02 · Statement renderer** | the statements | `R01` | `tasks/T-02-statement-renderer.md` | T-01 | the layout work, reviewed by Harriet |
| **T-03 · Layout document** | document the layout | `R03` | `tasks/T-03-layout-document.md` | T-02 | separate deliverable |
| **T-04 · Command-line entry** | the command | `R02` | `tasks/T-04-command-line.md` | T-02 | what the treasurer runs |
| **T-05 · Acceptance run** | tests plus sample comparison | `R04` | `tasks/T-05-acceptance-run.md` | T-03, T-04 | the deliverable check |

### Dependency graph

```text
T-01 ──► T-02 ──► T-03 ──► T-05
              └──► T-04 ──► T-05
```

## 6. Readiness and acceptance

### 6.1 Per-task

- The brief's command passes with its native exit; the sample is unchanged; each validation has a raw record.

### 6.2 Initiative-level

- `sh checks/accept.sh` passes on the integrated tree and is recorded; the README documents the command.

## 7. Risks and dependencies

- The AGM may change the rates before the statements are posted in February (owner: Harriet).

## 8. Decisions and questions

- D-01 gitignore, D-02 the agreed sample, D-03 the 2027 rates. Q-01 resolved.
