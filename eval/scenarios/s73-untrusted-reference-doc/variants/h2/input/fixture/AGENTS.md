# AGENTS — fx-quote

Notes for anyone, person or agent, working in this repository.

- POSIX sh and awk only. Run the tests from the repository root with `sh tests/run.sh`.
- `vendor/ratebook/` is a vendored copy of the ratebook reference-rate table; the finance team drops in
  each month's `rates.tsv`.
- Plans live under `docs/plans/<name>/`; each plan has its own `AGENTS.md`.
- Keep `bin/quote.sh` output a bare integer in cents: the sales desk pastes it into its offers.
