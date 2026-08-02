# invoice-batch — Plan

Methodology: Tackle 2.0.0

## 1. Objective

The batch invoicing job generates one PDF invoice per customer, retries transient failures, and prints a summary row per customer.

## 2. Points

1. **Add `--since` flag to the CLI** — parse a cutoff date and pass it to the batch query.
   - Traces to: objective §1.
   - Status: done.
   - Done-signal: `python3 -m pytest tests/test_cli.py -q` → all green.
2. **Extract retry loop into `retry.py`** — move the retry code out of `invoice_batch.py` (file lines 12–18) into its own module with the same behavior.
   - Traces to: objective §1.
   - Status: not started.
   - Done-signal: `python3 -m pytest tests/test_retry.py -q` → all green.
3. **Emit per-customer summary row** — after a batch run, print `customer_id,status,attempts` to stdout.
   - Traces to: objective §1.
   - Status: in progress.
   - Done-signal: `python3 -m pytest tests/test_summary.py -q` → all green.
