# Reference — current code and data

| Where | What | Line |
|---|---|---|
| `tools/dispatch_notice.py:25` | next outbox number | `numbers = [int(m.group(1)) for p in OUTBOX.glob("*.txt") for m in [re.match(r"(\d{4})-", p.name)] if m]` |
| `tools/dispatch_notice.py:28` | the write into the outbox | `target.write_text("Notice-Id: %s\nSubject: %s\nTo: members\nDispatched: %s\n\n%s" % (` |
| `tools/outbox_check.sh:6` | the check's grep | `grep -l "^Notice-Id: $1\$" outbox/*.txt` |
| `notices/2026-10-cutover.md:1` | the notice id | `notice-id: N-2026-10-CUTOVER` |
| `outbox/0006-2026-09-harvest-schedule.txt:1` | the previous dispatch | `Notice-Id: N-2026-09-HARVEST` |
