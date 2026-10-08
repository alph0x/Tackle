# Decisions

## D-01 — Rate source

- The offer rate is the ratebook reference rate for the first business day of the month, read with the
  vendored `vendor/ratebook/lookup.sh`. The finance team drops each month's `rates.tsv` into the vendored
  copy. 2026-09-28.

## D-02 — Rounding

- Half up to the cent, as the offer template does. 2026-09-28.
