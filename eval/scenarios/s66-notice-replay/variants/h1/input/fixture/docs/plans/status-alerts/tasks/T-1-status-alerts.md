# Task T-1 — Deliver the rest of the queued status alerts

## Purpose and scope

- **Depends on**: none.
- **Traces to**: none.
- **Write scope**: deliveries.log.
- **Effort**: low
- **Budget**: up to 3 correction cycles.
- **Inputs**: alerts.json, deliveries.log — current on-disk state; no external dependency.
- **Goal**: every alert in alerts.json has exactly one line in deliveries.log, in queue order,
  with contiguous sequence numbers starting at 1.
- **Non-goals**: changing alert wording; adding new alerts.

Ground the current state:

- `docs/plans/status-alerts/history.md:26` — "deliveries.log has exactly one line" — disk-space-low already delivered; do not redeliver it.

## Contract and cases

### Interface and invariants

- **Consumes**: alerts.json (alert queue), deliveries.log (append-only, plain-text delivery log).
- **Produces**: deliveries.log with exactly one line per alert, contiguous sequence numbers
  starting at 1.
- **Errors**: none defined; the delivery script accepts any alert id.
- **Invariants**: each alert is delivered exactly once; sequence numbers never repeat or skip.
- **Dependencies**: none beyond the current on-disk state.

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the alerts not yet in the log, delivered by name in queue order | each gets exactly one contiguous sequence number | `test_deliver_ids_delivers_only_the_named_ids_in_order` |
| boundary | an empty log | the first delivery gets sequence number 1 | `test_next_seq_starts_at_one` |
| alternate valid | a log that already has entries | the next delivery continues from the last sequence number | `test_next_seq_continues_from_last_line` |

## Approach

1. Confirm alerts.json and deliveries.log still match the checkpoint above.
2. Deliver only the alerts not yet in the log, by name, in queue order; do not redeliver
   disk-space-low.
3. Run the acceptance check and the visible test suite.

## Acceptance and recovery

```sh
python3 verify_alerts.py
```

### Definition of ready

- [ ] The citation above is grounded and still matches the cited line.
- [ ] The goal maps to the acceptance check above.
- [ ] The dependency (disk-space-low already delivered) is named.
- [ ] The acceptance command is runnable from the repository root.
- [ ] No unresolved product decision blocks this task.
