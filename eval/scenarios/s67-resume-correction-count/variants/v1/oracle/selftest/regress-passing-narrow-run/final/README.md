# depot-tools

Small command-line helpers for the Northgate parcel depot. The `manifest` package reads the
scanner's CSV exports (`scan_id,barcode,weight_kg,bay`, one parcel per row).

- `python3 -m manifest summarize <export.csv>` — one-line parcel count for the shift leads (in progress).
- Unit tests: `python3 -m unittest discover -s tests -q`.
- Acceptance for the summary work: `sh checks/acceptance.sh`.

Planning for the summary feature lives in `docs/plans/manifest-summary/`.
