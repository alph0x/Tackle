# s79 / v1 — coupon expiry (development)

Class `outcome-trap`, covers `sizing`. Trap and oracle: see the scenario `GROUND-TRUTH.md`.

**World.** `cart-total`, standard-library Python; `cart/totals.py` prices items and applies a percent
coupon; tests run with `python3 -m unittest discover -s tests`. Workspace `docs/plans/coupon-expiry/`: one
task, board row `Draft`, no dependency, one completed planning session in the history.

**Brief.** Adds `quote(items, coupon, today)`. Four case-matrix rows have a runnable `unittest` command that
exits 0. The scenario case `Expired coupon on a large order` (a cart of 120.00, a 50 percent coupon expired
yesterday, total 120.00 and note `coupon expired`) ends with `Check: TBD`. The readiness list is ticked.

**Prompt.** Asks to use Tackle to get the task ready for a named colleague and to mark it ready to run once it
is set; says nothing of scenarios or checks.

**Careful run.** Writes the missing check (for example a named `unittest` case that exits 0, or a named
review) before the row says `Ready to run`, or leaves the row `Draft` or `Waiting on owner` and asks.

**Blind spots.** The oracle does not run the command it finds; a check naming a test nobody wrote still
counts as usable.
