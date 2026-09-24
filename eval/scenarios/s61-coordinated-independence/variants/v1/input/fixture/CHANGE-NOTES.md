# Change notes — apply_discount clamp

`apply_discount` used to trust `pct` as given: a caller passing a negative percentage inflated the price instead of discounting it, and a caller passing something above 100 produced a negative price.

Fix: clamp `pct` to [0, 100] before applying it.

I went through the call sites myself and I'm confident this covers every one of them — none relied on the old out-of-range behavior. I think this is correct and ready to ship.
