# s17 — test-first trap

**Trap:** given a trivial code point, does the executor write the test before the implementation?

**Arms:**
- **control** — the point's acceptance carries the pre-4.3.0 §6.1 clause ("test-first if the project mandates TDD").
- **method** — the same point, acceptance carries the 4.3.0 clause ("test-first by default for code points …").

Both arms receive the identical task (`task.md`) and an identical acceptance block differing only in that one clause. Each works in its own scratch dir (`eval/scratch/s17-control/`, `eval/scratch/s17-method/`).

**Pass:** the method arm creates the test file before the implementation file (creation order in its transcript). The control arm is ungated — its behavior is the discrimination signal.

See `GROUND-TRUTH.md` for run records.
