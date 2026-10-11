# T-41 calculator contract

Public interface: `calculate_order(lines, discount_bps, tax_bps)`.

For each line, multiply `unit_price_cents` by `quantity`; sum the products for `subtotal_cents`. Compute `discount_cents` by applying `discount_bps / 10000` to the subtotal. Subtract that discount before applying `tax_bps / 10000`. Round both computed amounts to the nearest whole cent, using half-up rounding. `total_cents` is the discounted subtotal plus tax.

Return exactly these integer-valued keys: `subtotal_cents`, `discount_cents`, `tax_cents`, `total_cents`. The supplied inputs use nonnegative integer cents, quantities, and rates.