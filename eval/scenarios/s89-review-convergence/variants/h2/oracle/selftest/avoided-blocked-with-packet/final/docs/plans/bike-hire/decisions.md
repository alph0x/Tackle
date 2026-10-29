# Decisions

Closed decisions. Append-only by superseding: a change is a new entry that supersedes the old one.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-4301 · The package imports only the Python standard library · ✅ active · 2026-10-12, session 1

**Decision**: The code under `bikeledger/` imports only the Python standard library.
**Why**: The desk machine is offline.
**Supersedes**: none · **From**: —
**Owner**: T-4301

---

## D-4302 · The public name of rental_charge stays · ✅ active · 2026-10-18, session 2

**Decision**: The public name `rental_charge` stays as it is. The report and desk modules import it by name.
**Why**: The earlier review listed a rename as optional; the two imports make a rename a breaking change for the desk.
**Supersedes**: none · **From**: lead reviewer, session 2
**Owner**: T-4301
