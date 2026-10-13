# T-02 — Single-use redemption

> Self-contained briefing: a new worker can implement this task from this file alone.

## Purpose and scope

- **Depends on**: T-01 (`issue` and `lookup` in `src/invite.js`).
- **Traces to**: `plan.md` §3 `R2`; D-01, D-02.
- **Write scope**: `src/invite.js`; `test/invite.test.js`; this workspace's board, history, resource usage and
  `reports/T-02-report.md`.
- **Autonomy**: L2.
- **Effort**: medium
- **Budget**: 3 correction cycles.
- **Inputs**: `src/invite.js` and `test/invite.test.js` as left by T-01.
- **Goal**: the first `redeem` of a code records its redeemer; any later `redeem` returns
  `{ ok: false, reason: "already_used" }` and leaves the first redeemer in place.
- **Non-goals**: persistence; code expiry; changing `issue` or `lookup`.
- **Acceptance owner**: the repository owner.

Current state:

- `src/invite.js:12` — "entry.usedBy = user;" — redemption overwrites `usedBy` on every call.
- `test/invite.test.js:12` — "test("unknown code is refused"" — the existing test style to follow.

## Contract and cases

### Interface and invariants

- **Consumes**: a code string and a user string.
- **Produces**: `{ ok: true }` for the first redemption; `{ ok: false, reason }` otherwise (D-01).
- **Errors**: an unknown code keeps its `unknown_code` reason.
- **Invariants**: `usedBy` is written at most once per code (D-02).

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| first redeem | issued code, user ana | `{ ok: true }`, `lookup(code).usedBy` is `ana` | `node --test --test-name-pattern "first redeem" test/` exits 0 |
| unknown code | code never issued | `{ ok: false, reason: "unknown_code" }` | `node --test --test-name-pattern "unknown" test/` exits 0 |
| other code unaffected | two codes, one redeemed | the other still redeems | `node --test --test-name-pattern "other code" test/` exits 0 |

#### Scenario: Second redemption of a used code
- GIVEN a code issued to ana
- AND ana has already redeemed it
- WHEN bo redeems the same code
- THEN the result is `{ ok: false, reason: "already_used" }`
- AND `lookup(code).usedBy` is still `ana`

## Approach

1. In `redeem`, return `already_used` when `entry.usedBy` is set, before writing.
2. Add one test per case above to `test/invite.test.js`; run the file before and after.

## Acceptance and recovery

```sh
node --test test/
```

Exit status 0 means every case passes. Recovery follows the 3-cycle budget; a failure that survives it is
reported with expected and observed values.

### Definition of ready

- [x] Citations are grounded and match their cited lines.
- [x] Every requirement maps to a case.
- [x] Dependencies name the crossing artifact (`issue`, `lookup`).
- [x] The acceptance command is runnable from the repository root.
- [x] No unresolved product decision (D-01, D-02).
