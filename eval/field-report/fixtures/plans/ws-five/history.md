# History — Fixture schema-5 workspace

This fixture's transitions never drop from Complete to an earlier state: reopenings must read 0,
not n/a, because matching transition lines do exist.

- T-02 → Ready to run
- T-02 → In progress
- T-02 → Checking
- T-02 → Complete
