# Reference — current code and data

| Where | What | Line |
|---|---|---|
| `tools/post_adjustment.py:18` | the posting tool's argument parser | `parser = argparse.ArgumentParser(description="post one adjustment to the journal")` |
| `tools/post_adjustment.py:32` | the append to the journal | `csv.writer(handle, lineterminator="\n").writerow([args.date, args.account, "%.2f" % args.amount, args.memo, stamp])` |
| `tools/check_adjustment.py:25` | the check's match rule | `rows = [row for row in reader if len(row) == 5 and row[1] == argv[1] and row[3] == argv[2]]` |
| `data/adjustments.csv:1` | journal header | `posted_on,account,amount,memo,posted_at` |
| `data/accounts.csv:4` | ACC-1042 | `ACC-1042,Nakamura,27` |
| `memos/2026-09-22-q3-true-up.md:4` | treasurer approval | `Approved by: Rhiannon Vale, treasurer` |
