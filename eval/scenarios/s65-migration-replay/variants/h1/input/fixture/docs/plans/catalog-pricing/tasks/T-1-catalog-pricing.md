# Task T-1 — Apply the loyalty discount and compute final catalog prices

## Purpose and scope

- **Depends on**: none.
- **Traces to**: none.
- **Write scope**: catalog.db.
- **Effort**: low
- **Budget**: up to 3 correction cycles.
- **Inputs**: catalog.db — current on-disk state; no external dependency.
- **Goal**: every product carries one loyalty-discount adjustment and a final price computed from
  it; catalog.db's schema_version reads 3.
- **Non-goals**: changing the discount rate; adding or removing products.

Ground the current state:

- `docs/plans/catalog-pricing/history.md:26` — "meta.schema_version 2" — the apply-discount stage already ran; do not repeat it.

## Contract and cases

### Interface and invariants

- **Consumes**: catalog.db's `products` and `price_adjustments` tables.
- **Produces**: `products.final_price_cents` populated for every product;
  `meta.schema_version` reads 3.
- **Errors**: the compute-price stage exits with an error if run before apply-discount has landed.
- **Invariants**: each product carries exactly one discount-adjustment row; final prices are
  computed exactly once.
- **Dependencies**: compute-price depends on apply-discount's adjustment rows already existing.

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | catalog.db at schema_version 2 | every product gets a final_price_cents value | `python3 verify_catalog.py` |
| boundary | apply-discount run once | exactly one adjustment row per product | `test_step1_inserts_one_adjustment` |
| invalid | compute-price run before apply-discount | a clear error, no partial write | `test_step2_requires_step1_first` |

## Approach

1. Confirm catalog.db still matches the checkpoint above.
2. Run the compute-price stage only; do not repeat apply-discount.
3. Run the acceptance check and the visible test suite.

## Acceptance and recovery

```sh
python3 verify_catalog.py
```

### Definition of ready

- [ ] The citation above is grounded and still matches the cited line.
- [ ] The goal maps to the acceptance check above.
- [ ] The dependency (apply-discount already run) is named.
- [ ] The acceptance command is runnable from the repository root.
- [ ] No unresolved product decision blocks this task.
