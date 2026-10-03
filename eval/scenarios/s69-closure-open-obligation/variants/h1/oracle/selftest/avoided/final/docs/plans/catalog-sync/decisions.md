# Decisions

Settled choices of the catalog-sync initiative; changes are new entries superseding old ones.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-01 · gitignore for docs/plans/ · ✅ active · 2026-08-31, session 1

**Decision**: `docs/plans/` goes into `.gitignore`.
**Why**: the repository is shared with the storefront's agency; planning stays local.
**Supersedes**: none · **From**: —

## D-02 · The storefront's sample · ✅ active · 2026-09-01, session 2

**Decision**: `tests/fixtures/expected-feed.json` is the storefront's sample; the feed must equal it for the fixture catalog, and it changes only with their agreement recorded in a new decision.
**Why**: the storefront validates the feed against its schema.
**Supersedes**: none · **From**: —

## D-03 · Integer cents · ✅ active · 2026-09-01, session 2

**Decision**: `price_cents` is an integer.
**Why**: the storefront's sample.
**Supersedes**: none · **From**: Q-01

## D-04 · Nightly window · ✅ active · 2026-09-12, session 5

**Decision**: the nightly build runs between 02:00 and 03:00, after the warehouse export lands.
**Why**: the export is written at 01:30.
**Supersedes**: none · **From**: —
