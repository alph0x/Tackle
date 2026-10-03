# T-02 report — Fixture set

## Authorization and preflight
- Run `2026-09-17-s4/T-02/executor/1`, authorized by Imogen's "run T-02" in session 4. Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no summary fixture existed; the check expects the fixture, the contract test and the acceptance script in place with a syntax-clean script; the brief asks for the owner's sign-off.

## Implementation and target observation
- `tests/fixtures/run-04.csv` (three parcels) added from Imogen's export; `tests/test_summary.py` written from the wording review ("Parcels: <n>", one line); `checks/acceptance.sh` drafted from the same review notes.
- Validation 1: `python3 -m unittest tests.test_rows -q && sh -n checks/acceptance.sh` → exit 0. Raw: `verification-records/2026-09-17-s4_T-02_v1_20260917T150241Z.md`.
- Owner review: Imogen signed off the three files on 2026-09-17 (session 4); D-03 records them as protected from session 5.

## Correction journal
- none: the first validation passed.

## Final status
- Complete. Method: command plus owner review. Independence: the owner reviewed; the executor observed the command.

Receipt — done: fixture, contract test, acceptance script, owner sign-off. Remaining: nothing for this task. Next step: T-03 (owner: Imogen authorizes the run).
