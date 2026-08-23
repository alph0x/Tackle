# Demo — usage-ledger example workspace

## Harness map

| Capability | Status |
|---|---|
| usage-reporting | partial — exposes input and output tokens only; exposes no cache, request, tool-call, or duration figures |

## Model map

| Tier | Model |
|---|---|
| fast | demo-model |

## Contract

- **Point close** — every point flips to 🟢 only after its evidence is recorded in `log.md`.
- **Usage ledger** — every run appends one row to `usage.md`; the row records what the run's tools and tokens actually consumed, and nothing more.
- **Autonomy** — L2: stop and ask on ambiguity.