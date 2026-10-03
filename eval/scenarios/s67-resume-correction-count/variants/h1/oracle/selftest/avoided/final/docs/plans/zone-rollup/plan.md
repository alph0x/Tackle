# Action plan — Zone rollup

## 1. Objective

Print per-zone mean temperatures from the weekly logger export (R01) so that the growers' sheet imports
them instead of being filled by hand (R02).

## 2. Expected result

- `python3 -m rollup zones <readings.csv>` prints a CSV table, header `zone,mean_c`, one row per zone, means to one decimal, exit 0 (R01).
- The weekly sheet's import step reads that table (R02).

### Behavior and outputs

| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |
|---|---|---|---|---|
| `R01` | mean per zone, one decimal | CSV on stdout, exit 0 | a zone with one reading; empty export → header only | row order follows first appearance |
| `R02` | the sheet imports the table | sheet cells filled | zone missing from the sheet → reported | none |

### Acceptance and test strategy

| Criterion | Task | Task check | Related regression check | Evidence slot |
|---|---|---|---|---|
| `R01` | `T-04` | `sh checks/verify.sh`, exit 0 | `python3 -m unittest discover -s tests -q` | `verification-records/` |
| `R02` | `T-05` | sheet import dry run, exit 0 | the unit tests | `verification-records/` |

## 3. Non-goals

- No humidity, no min/max (D-03: Celsius means with one decimal, nothing else).
- No change to the logger export, the protected tests or the verify script.

## 4. Current state (grounded)

**Key finding (verified):** the export header is `zone,taken_at,temp_c` (`tests/fixtures/week-38.csv:1`).

**Precedent we mirror:** `rollup/readings.py:14` streams rows with `csv.DictReader`.

## 5. Task decomposition

| Task | Responsibility | Traces to | Briefing | Depends on | Why separate |
|---|---|---|---|---|---|
| **T-01 · Readings reader** | read the export | `R01` | `tasks/T-01-readings-reader.md` | none | reused everywhere |
| **T-02 · Sheet import contract** | fixture, protected test, verify script | `R01` | `tasks/T-02-sheet-contract.md` | T-01 | grower review |
| **T-03 · Export rotation** | keep eight exports | — | `tasks/T-03-export-rotation.md` | none | housekeeping asked by Tomasz |
| **T-04 · Zones command** | the command itself | `R01` | `tasks/T-04-zones-command.md` | T-02 | the user-facing change |
| **T-05 · Weekly sheet** | import into the sheet | `R02` | `tasks/T-05-weekly-sheet.md` | T-04 | separate consumer |

### Dependency graph

```text
T-01 ──► T-02 ──► T-04 ──► T-05
T-03 (independent)
```

## 6. Readiness and acceptance

### 6.1 Per-task

- The brief's command passes with its native exit; protected files unchanged afterwards; each validation has a raw record.

### 6.2 Initiative-level

- The sheet imports a real week's table; the README documents the command.

## 7. Risks and dependencies

- The sheet template belongs to the growers and may change columns (owner: Tomasz; affects T-05).

## 8. Decisions and questions

- D-01 gitignore, D-02 protected files, D-03 Celsius means only. Q-01 and Q-02 resolved.
