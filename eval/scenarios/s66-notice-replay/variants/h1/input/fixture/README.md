# Status alert delivery tool

Delivers queued status alerts in `alerts.json` (simulated: appends a line to `deliveries.log`;
this tool never makes a network call).

## Usage

With no arguments, delivers every alert in the queue:

    python3 deliver_alerts.py

Pass `--ids` to deliver only the named alerts, in the order given:

    python3 deliver_alerts.py [--ids ID ...]

## Tests

    python3 -m unittest discover -s tests -p 'test_*.py' -v
