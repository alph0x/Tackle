# Synthetic fixture profile — 11 numeric entries + 1 n/a (C4)

Eleven distinct-confidence entries plus one assumed-only (`n/a`) entry, ids `E01`..`E11` in
ascending computed-confidence order. `E01` (rank 11, just below the Top-10 cut) and `E02` (rank 10,
just above it, the weakest entry the cut currently keeps) are the pair the mutation case targets.

## Hypotheses

- id: E01 · Rank eleven, lowest, just excluded by the Top-10 cut · confidence: 0.21 (Wilson lower bound, z=1.96, n=1) · observations: a1:✓@2026-01-01 · status: active
- id: E02 · Rank ten, weakest entry the Top-10 cut currently keeps · confidence: 0.21 (Wilson lower bound, z=1.96, n=3) · observations: a2:✓@2026-01-01; b2:✓@2026-01-02; c2:✗@2026-01-03 · status: active
- id: E03 · Rank nine · confidence: 0.30 (Wilson lower bound, z=1.96, n=4) · observations: a3:✓@2026-01-01; b3:✓@2026-01-02; c3:✓@2026-01-03; d3:✗@2026-01-04 · status: active
- id: E04 · Rank eight · confidence: 0.38 (Wilson lower bound, z=1.96, n=5) · observations: a4:✓@2026-01-01; b4:✓@2026-01-02; c4:✓@2026-01-03; d4:✓@2026-01-04; e4:✗@2026-01-05 · status: active
- id: E05 · Rank seven · confidence: 0.44 (Wilson lower bound, z=1.96, n=6) · observations: a5:✓@2026-01-01; b5:✓@2026-01-02; c5:✓@2026-01-03; d5:✓@2026-01-04; e5:✓@2026-01-05; f5:✗@2026-01-06 · status: active
- id: E06 · Rank six · confidence: 0.49 (Wilson lower bound, z=1.96, n=7) · observations: a6:✓@2026-01-01; b6:✓@2026-01-02; c6:✓@2026-01-03; d6:✓@2026-01-04; e6:✓@2026-01-05; f6:✓@2026-01-06; g6:✗@2026-01-07 · status: active
- id: E07 · Rank five · confidence: 0.65 (Wilson lower bound, z=1.96, n=7) · observations: a7:✓@2026-01-01; b7:✓@2026-01-02; c7:✓@2026-01-03; d7:✓@2026-01-04; e7:✓@2026-01-05; f7:✓@2026-01-06; g7:✓@2026-01-07 · status: active
- id: E08 · Rank four · confidence: 0.68 (Wilson lower bound, z=1.96, n=8) · observations: a8:✓@2026-01-01; b8:✓@2026-01-02; c8:✓@2026-01-03; d8:✓@2026-01-04; e8:✓@2026-01-05; f8:✓@2026-01-06; g8:✓@2026-01-07; h8:✓@2026-01-08 · status: active
- id: E09 · Rank three · confidence: 0.70 (Wilson lower bound, z=1.96, n=9) · observations: a9:✓@2026-01-01; b9:✓@2026-01-02; c9:✓@2026-01-03; d9:✓@2026-01-04; e9:✓@2026-01-05; f9:✓@2026-01-06; g9:✓@2026-01-07; h9:✓@2026-01-08; i9:✓@2026-01-09 · status: active
- id: E10 · Rank two · confidence: 0.72 (Wilson lower bound, z=1.96, n=10) · observations: a10:✓@2026-01-01; b10:✓@2026-01-02; c10:✓@2026-01-03; d10:✓@2026-01-04; e10:✓@2026-01-05; f10:✓@2026-01-06; g10:✓@2026-01-07; h10:✓@2026-01-08; i10:✓@2026-01-09; j10:✓@2026-01-10 · status: active
- id: E11 · Rank one, highest · confidence: 0.74 (Wilson lower bound, z=1.96, n=11) · observations: a11:✓@2026-01-01; b11:✓@2026-01-02; c11:✓@2026-01-03; d11:✓@2026-01-04; e11:✓@2026-01-05; f11:✓@2026-01-06; g11:✓@2026-01-07; h11:✓@2026-01-08; i11:✓@2026-01-09; j11:✓@2026-01-10; k11:✓@2026-01-11 · status: active
- id: E12 · Assumed only, no checked observation, excluded from Top-K entirely (F11) · confidence: n/a (no checked observation) · observations: z12:assumed@2026-01-01 · status: active
