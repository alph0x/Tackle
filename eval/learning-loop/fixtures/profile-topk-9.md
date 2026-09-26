# Synthetic fixture profile — 9 numeric entries + 1 n/a (C4 / F11 discriminator)

Nine numeric entries plus one assumed-only (`n/a`) entry: 10 entries total, at the Top-10 cut
exactly. A wrong implementation that merely *sorts* the `n/a` entry last (instead of excluding it
from the Top-K cut entirely) would still show all 10 entries here — the correct one shows 9.

## Hypotheses

- id: F01 · confidence: 0.21 (Wilson lower bound, z=1.96, n=1) · observations: a1:✓@2026-01-01 · status: active
- id: F02 · confidence: 0.34 (Wilson lower bound, z=1.96, n=2) · observations: a2:✓@2026-01-01; b2:✓@2026-01-02 · status: active
- id: F03 · confidence: 0.44 (Wilson lower bound, z=1.96, n=3) · observations: a3:✓@2026-01-01; b3:✓@2026-01-02; c3:✓@2026-01-03 · status: active
- id: F04 · confidence: 0.51 (Wilson lower bound, z=1.96, n=4) · observations: a4:✓@2026-01-01; b4:✓@2026-01-02; c4:✓@2026-01-03; d4:✓@2026-01-04 · status: active
- id: F05 · confidence: 0.57 (Wilson lower bound, z=1.96, n=5) · observations: a5:✓@2026-01-01; b5:✓@2026-01-02; c5:✓@2026-01-03; d5:✓@2026-01-04; e5:✓@2026-01-05 · status: active
- id: F06 · confidence: 0.61 (Wilson lower bound, z=1.96, n=6) · observations: a6:✓@2026-01-01; b6:✓@2026-01-02; c6:✓@2026-01-03; d6:✓@2026-01-04; e6:✓@2026-01-05; f6:✓@2026-01-06 · status: active
- id: F07 · confidence: 0.65 (Wilson lower bound, z=1.96, n=7) · observations: a7:✓@2026-01-01; b7:✓@2026-01-02; c7:✓@2026-01-03; d7:✓@2026-01-04; e7:✓@2026-01-05; f7:✓@2026-01-06; g7:✓@2026-01-07 · status: active
- id: F08 · confidence: 0.68 (Wilson lower bound, z=1.96, n=8) · observations: a8:✓@2026-01-01; b8:✓@2026-01-02; c8:✓@2026-01-03; d8:✓@2026-01-04; e8:✓@2026-01-05; f8:✓@2026-01-06; g8:✓@2026-01-07; h8:✓@2026-01-08 · status: active
- id: F09 · confidence: 0.70 (Wilson lower bound, z=1.96, n=9) · observations: a9:✓@2026-01-01; b9:✓@2026-01-02; c9:✓@2026-01-03; d9:✓@2026-01-04; e9:✓@2026-01-05; f9:✓@2026-01-06; g9:✓@2026-01-07; h9:✓@2026-01-08; i9:✓@2026-01-09 · status: active
- id: F10 · Assumed only, no checked observation · confidence: n/a (no checked observation) · observations: z10:assumed@2026-01-01 · status: active
