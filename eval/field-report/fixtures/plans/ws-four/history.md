# History — Fixture schema-4 workspace

Append-only history. This fixture exercises the strict `- <task id> → <State>` reopening pattern:
two genuine reopenings, plus one prose line that carries a from-state and must NOT match.

- T-01 → Ready to run
- T-01 In progress → Complete.
- T-01 → In progress
- T-01 → Complete
- T-01 → In progress
- T-01 → Complete
- T-01 → Draft
