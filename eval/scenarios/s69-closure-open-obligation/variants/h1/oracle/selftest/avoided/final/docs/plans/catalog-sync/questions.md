# Open questions

Questions of the catalog-sync initiative; resolved ones stay, marked 🟢.

**Global status**: 🔴 Q-02 open (Marcus).

---

## Q-01 · Prices as cents or decimals? · 🟢 resolved → D-03

**Determines**: the feed's `price_cents` (T-02).
**Decides**: Marcus Oyelaran with the storefront.
**Already investigated**: the storefront's sample carries integer cents. Resolved 2026-09-01.

## Q-02 · vendor_sku in the storefront feed · 🔴 open

Marcus asked at the T-01 review (2026-09-03) that `vendor_sku` be passed through to the feed; parked until after T-04 (T-01 receipt) and surfaced again at closure.

**Determines**: whether this initiative closes now with a follow-up, or gains T-05 and a new sample (superseding D-02).
**Decides**: Marcus Oyelaran, with the storefront's agency.
**Already investigated**: the catalog export carries `vendor_sku` on every row (`tests/fixtures/catalog.csv:1`); the storefront's schema would need the field agreed first.
