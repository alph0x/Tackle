# T-01 report

- Change: `bin/labels.sh` writes the call number, the title and a blank line for each row.
- Check: `sh tests/run.sh` → `ok   tests/label_test.sh`, exit 0.
- Render: `sh bin/labels.sh tests/data/shelf-a.csv build/shelf-a.txt` → nine lines, sent to the print shop.

**Remains**: none
