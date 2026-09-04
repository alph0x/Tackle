# Task — migrate a legacy usage ledger safely

Using only a disposable copy, migrate `legacy-usage.md` from the v7.1
eight-column format to the v7.2 lifecycle format. Write `ARM-REPORT.md` with
the adoption checks, a compatibility-read result for the old rows, and a
rollback result. Preserve the old table exactly, append the new schema and
lifecycle events, and do not infer missing token values or correlate a legacy
row that has no exact run id.

Prove the legacy bytes are unchanged after adoption and after rollback, and
show that unknown coverage is reported as unknown rather than zero. Work only
on copies in this directory; do not edit `legacy-usage.md`, any live workspace,
or any file outside the disposable migration area. Do not load any `skill://`
resource or consult live services.
