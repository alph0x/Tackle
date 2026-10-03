# glasshouse-kit

Scripts for the Brackenfield glasshouses. `rollup` turns the logger's weekly CSV
(`zone,taken_at,temp_c`) into per-zone figures for the growers' sheet.

- `python3 -m rollup zones <readings.csv>` — per-zone mean temperature, CSV on stdout (in progress).
- Unit tests: `python3 -m unittest discover -s tests -q`.
- Verification of the zones work: `sh checks/verify.sh`.

The plan for the rollup lives in `docs/plans/zone-rollup/`.
