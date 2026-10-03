# Action plan — Catalog sync

## 1. Objective

Build the storefront feed from the warehouse catalog export (R01) with one command (R02), run it nightly
(R03) and accept it against the storefront's sample (R04).

## 2. Expected result

- `python3 -m sync feed <catalog.csv> <feed.json>` writes items with `product_id,title,price_cents,stock` (R01, R02).
- `tools/nightly.sh` runs the build in the 02:00–03:00 window (R03, D-04).
- `sh checks/accept.sh` passes (R04).

### Behavior and outputs

| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |
|---|---|---|---|---|
| `R01` | the four storefront fields | JSON feed | stock 0 → item kept with 0 | key order |
| `R02` | one command | exit 0, one summary line | missing file → usage error | wording |
| `R03` | nightly build | cron entry and script | window missed → next night | none |
| `R04` | acceptance against the sample | `accept: ok` | — | none |

### Acceptance and test strategy

| Criterion | Task | Task check | Related regression check | Evidence slot |
|---|---|---|---|---|
| `R01` | `T-02` | `python3 -m unittest tests.test_feed -q` | `tests.test_catalog` | `verification-records/` |
| `R03` | `T-03` | `sh -n tools/nightly.sh` | — | `verification-records/` |
| `R04` | `T-04` | `sh checks/accept.sh` exit 0 | — | `verification-records/` |

## 3. Non-goals

- No change to the catalog export.
- No fields beyond the storefront's four inside this initiative (D-02 fixes the sample).

## 4. Current state (grounded)

**Key finding (verified):** the catalog export carries a `vendor_sku` column the storefront does not take (`tests/fixtures/catalog.csv:1`).

**Precedent we mirror:** the storefront's sample feed (`tests/fixtures/expected-feed.json:1`).

## 5. Task decomposition

| Task | Responsibility | Traces to | Briefing | Depends on | Why separate |
|---|---|---|---|---|---|
| **T-01 · Catalog reader** | read the export | `R01` | `tasks/T-01-catalog-reader.md` | none | reviewed by Marcus |
| **T-02 · Feed builder** | the feed and the command | `R01`, `R02` | `tasks/T-02-feed-builder.md` | T-01 | the format work |
| **T-03 · Nightly runner** | cron script | `R03` | `tasks/T-03-nightly-runner.md` | T-02 | operations |
| **T-04 · Acceptance run** | tests plus sample comparison | `R04` | `tasks/T-04-acceptance-run.md` | T-02, T-03 | the deliverable check |

### Dependency graph

```text
T-01 ──► T-02 ──► T-03 ──► T-04
```

## 6. Readiness and acceptance

### 6.1 Per-task

- The brief's command passes with its native exit; the sample is unchanged; each validation has a raw record.

### 6.2 Initiative-level

- `sh checks/accept.sh` passes on the integrated tree and is recorded; the README documents the command.

## 7. Risks and dependencies

- The storefront may add fields next season (owner: Marcus).

## 8. Decisions and questions

- D-01 gitignore, D-02 the sample, D-03 integer cents, D-04 nightly window. Q-01 resolved.
