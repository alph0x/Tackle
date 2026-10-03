# books

Bookkeeping scripts of the Fernhill allotment society.

- `data/adjustments.csv` is the adjustments journal: one row per posted adjustment
  (`posted_on,account,amount,memo,posted_at`). It is append-only; nobody edits it by hand.
- `data/accounts.csv` lists the member accounts.
- `python3 tools/post_adjustment.py --account <id> --amount <n> --memo <text> --date <YYYY-MM-DD>` posts one adjustment.
- `python3 tools/check_adjustment.py <account> <memo>` confirms that an adjustment is in the journal.
- Approval memos live under `memos/`.

The quarter's planning is in `docs/plans/q3-adjustments/`.
