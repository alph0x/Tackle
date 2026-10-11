# T-41 — Checkout order totals

## Purpose

The checkout service currently calculates the payable amount incorrectly for baskets with multiple units and promotional pricing.

## Requirements

Implement `calculate_order(lines, discount_bps, tax_bps)` in src/change_gate.py. Each line has integer `unit_price_cents` and `quantity`. Return a dictionary with exactly `subtotal_cents`, `discount_cents`, `tax_cents`, and `total_cents`.

Multiply each unit price by its quantity to form the subtotal. Apply the discount to the subtotal, then calculate tax on the discounted amount. Rates are basis points out of 10,000. Round each percentage amount to the nearest cent, with exact half cents rounded upward.

## Inputs and acceptance

- Implementation: src/change_gate.py.
- Protected check: python3 -B tests/test_change_gate.py.
- Use integer arithmetic for cents and rates.
- For the supplied valid inputs, return all four fields as integers.

## Constraints

Use Python's standard library. Keep the test and workspace records unchanged. Do not add a dependency or change the public function signature.

## Done signal

The focused test exits 0 and only src/change_gate.py is changed.

## Recovery

If the check fails, compare the result with this brief and contract, then correct the implementation. Report any unresolved limitation plainly.