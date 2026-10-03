# coop-relay

Member notices of the Alder Valley growers' cooperative.

- Notices are drafted under `notices/<slug>.md` with a small header block (`notice-id`, `subject`).
- `python3 tools/dispatch_notice.py <slug>` renders a notice into `outbox/` as the next numbered file.
- The relay (a cron job outside this repository) mails every file that appears in `outbox/` within the
  hour and keeps the file as the record of what went out. Files in `outbox/` are never edited or removed
  by hand.
- `sh tools/outbox_check.sh <notice-id>` lists the outbox files carrying a notice id.

Planning for the October price-list cutover notice is in `docs/plans/price-notice/`.
