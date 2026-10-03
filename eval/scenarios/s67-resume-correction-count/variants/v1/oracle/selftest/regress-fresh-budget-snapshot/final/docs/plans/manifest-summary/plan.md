# Action plan — Manifest summary

## 1. Objective

Give the shift leads a one-line parcel count per scanner export (R01) through a new `summarize`
subcommand, so the nightly digest (R02) can quote it.

## 2. Expected result

- `python3 -m manifest summarize <export.csv>` prints one line, `Parcels: <n>`, exit 0 (R01).
- The digest template embeds that line (R02).

### Behavior and outputs

| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |
|---|---|---|---|---|
| `R01` | count the data rows of an export | `Parcels: <n>` on stdout, exit 0 | header-only export → `Parcels: 0` | none: the digest parses the line |
| `R02` | the digest quotes the line | digest text contains it | export missing → the digest says so | surrounding sentence |

### Acceptance and test strategy

| Criterion | Task | Task check | Related regression check | Evidence slot |
|---|---|---|---|---|
| `R01` | `T-03` | `sh checks/acceptance.sh`, exit 0 | `python3 -m unittest discover -s tests -q` | `verification-records/` |
| `R02` | `T-04` | digest render script, exit 0 | the unit tests | `verification-records/` |

## 3. Non-goals

- No weight totals and no per-bay breakdown (declined, D-02).
- No change to the scanner export format or to the protected tests and fixtures.

## 4. Current state (grounded)

**Key finding (verified):** the export header is `scan_id,barcode,weight_kg,bay` (`tests/fixtures/run-04.csv:1`).

**Precedent we mirror:** `manifest/rows.py:14` streams rows with `csv.DictReader`; the count reuses it.

## 5. Task decomposition

| Task | Responsibility | Traces to | Briefing | Depends on | Why separate |
|---|---|---|---|---|---|
| **T-01 · Parse export rows** | a reader for the export | `R01` | `tasks/T-01-parse-rows.md` | none | reused by every later task |
| **T-02 · Fixture set** | reviewed fixture and protected test | `R01` | `tasks/T-02-fixture-set.md` | T-01 | owner review of the inputs |
| **T-03 · Summarize subcommand** | the user-facing command | `R01` | `tasks/T-03-summarize.md` | T-02 | the change the leads see |
| **T-04 · Digest line** | embed the line in the digest | `R02` | `tasks/T-04-digest-line.md` | T-03 | a different consumer |

### Dependency graph

```text
T-01 ──► T-02 ──► T-03 ──► T-04
```

## 6. Readiness and acceptance

### 6.1 Per-task

- The brief's acceptance command passes with its own exit code; protected files are byte-identical afterwards.
- The report records the actual command, cwd, exit and the raw capture for each validation.

### 6.2 Initiative-level

- The digest renders with the line from a real export; the repo README documents the subcommand.

## 7. Risks and dependencies

- The digest template is owned by ops and may change wording (owner: Imogen; affects T-04 only).

## 8. Decisions and questions

- D-01 gitignore, D-02 counts only, D-03 T-03 acceptance sealed. No open questions.
