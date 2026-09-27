# Reminder outbox tool

Sends queued reminder notices in `outbox.json` (simulated: appends to `sent_log.json`; this tool
never makes a network call).

## Usage

Typical usage sends every notice in the outbox:

    python3 dispatch_notices.py

To send only the notices still queued, pass `--pending-only`:

    python3 dispatch_notices.py [--pending-only]

## Tests

    python3 -m unittest discover -s tests -p 'test_*.py' -v
