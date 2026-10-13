"""Billing rates."""

# Late fee: basis points (1 bp = 0.01%) per started 30-day period, with a cap.
# The storefront shows the same rate in web/js/fees.js.
LATE_FEE_BP = 150
LATE_FEE_CAP_BP = 2500
PERIOD_DAYS = 30
