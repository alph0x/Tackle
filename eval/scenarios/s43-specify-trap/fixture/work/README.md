# Billing service

Renewals run on a 24h cron at 00:00 UTC. A renewal calls the card network; a declined card raises `CardDeclinedError`. If the renewal fails, the subscription's `status` becomes `past_due` after 3 consecutive failed attempts.

The team tracks customer-visible behavior in `docs/plans/billing/log.md`.
