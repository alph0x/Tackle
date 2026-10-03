# Action plan — Roster export

## 1. Objective

Give the regatta registration desk the club roster as a CSV in the agreed format (R01), produced by one
command (R02), documented (R03) and accepted against the desk's sample (R04).

## 2. Expected result

- `python3 -m export roster <members.json> <out.csv>` writes `member_id,name,joined,tier` rows (R01, R02).
- `docs/export-format.md` describes the columns (R03).
- `sh checks/accept.sh` passes: tests green and the rendered export equal to the agreed sample (R04).

### Behavior and outputs

| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |
|---|---|---|---|---|
| `R01` | the four agreed columns, in order | CSV file | member without a tier → error | none: the desk's importer is strict |
| `R02` | one command | exit 0, one summary line | missing file → usage error | wording of the summary line |
| `R03` | format documented | `docs/export-format.md` | — | layout |
| `R04` | acceptance against the sample | `accept: ok` | — | none |

### Acceptance and test strategy

| Criterion | Task | Task check | Related regression check | Evidence slot |
|---|---|---|---|---|
| `R01` | `T-02` | `python3 -m unittest tests.test_roster -q` | `tests.test_members` | `verification-records/` |
| `R02` | `T-04` | `python3 -m export roster tests/fixtures/members.json /tmp/r.csv` exit 0 | the unit tests | `verification-records/` |
| `R04` | `T-05` | `sh checks/accept.sh` exit 0 | — | `verification-records/` |

## 3. Non-goals

- No change to the membership file format.
- No columns beyond the four agreed ones inside this initiative's tasks (the sample is fixed by D-02).

## 4. Current state (grounded)

**Key finding (verified):** the membership file carries more fields than the desk imports (`tests/fixtures/members.json:3`).

**Precedent we mirror:** the desk's sample export (`tests/fixtures/expected-roster.csv:1`).

## 5. Task decomposition

| Task | Responsibility | Traces to | Briefing | Depends on | Why separate |
|---|---|---|---|---|---|
| **T-01 · Member reader** | read the membership file | `R01` | `tasks/T-01-member-reader.md` | none | reused by the writer |
| **T-02 · Roster writer** | the CSV | `R01` | `tasks/T-02-roster-writer.md` | T-01 | the format work, reviewed by Priya |
| **T-03 · Format document** | document the columns | `R03` | `tasks/T-03-format-document.md` | T-02 | separate deliverable |
| **T-04 · Command-line entry** | the command | `R02` | `tasks/T-04-command-line.md` | T-02 | user-facing |
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

- The desk's importer may change columns before the spring regatta (owner: Priya).

## 8. Decisions and questions

- D-01 gitignore, D-02 the agreed sample, D-03 junior/senior tiers only. Q-01 resolved.
