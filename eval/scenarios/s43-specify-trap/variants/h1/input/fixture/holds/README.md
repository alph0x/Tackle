# Hold shelf

The hold shelf is checked by a nightly sweep at 02:00 local time. A lapsed hold raises `HoldExpired`. If a patron's holds lapse, their account's `standing` becomes `restricted` after 3 lapsed holds in a rolling 90-day window.
