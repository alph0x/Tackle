# Synthetic fixture profile — five retirement boundary entries

Five boundary cases for "if ✗ ≥ 3 and the computed confidence is < 0.3, retire": two conjuncts,
each varied independently (N3), on each entry's raw, unrounded Wilson lower bound (N9).

## Hypotheses

- id: RB01 · Zero checks, three crosses (retires: below threshold, meets n_min) · confidence: 0.0 (Wilson lower bound, z=1.96, n=3) · observations: a:✗@2026-01-01; b:✗@2026-01-02; c:✗@2026-01-03 · status: retired
- id: RB02 · Four checks, three crosses (retires: raw ~0.2505 still below 0.3 even though a 1-decimal display rounds to 0.3) · confidence: 0.25 (Wilson lower bound, z=1.96, n=7) · observations: a:✓@2026-01-01; b:✓@2026-01-02; c:✓@2026-01-03; d:✓@2026-01-04; e:✗@2026-01-05; f:✗@2026-01-06; g:✗@2026-01-07 · status: retired
- id: RB03 · Five checks, three crosses (stays active: raw ~0.3057 is not below 0.3) · confidence: 0.31 (Wilson lower bound, z=1.96, n=8) · observations: a:✓@2026-01-01; b:✓@2026-01-02; c:✓@2026-01-03; d:✓@2026-01-04; e:✓@2026-01-05; f:✗@2026-01-06; g:✗@2026-01-07; h:✗@2026-01-08 · status: active
- id: RB04 · Zero checks, two crosses (stays active: below n_min even though the value is low) · confidence: 0.0 (Wilson lower bound, z=1.96, n=2) · observations: a:✗@2026-01-01; b:✗@2026-01-02 · status: active
- id: RB05 · One check, zero crosses (stays active: below n_min) · confidence: 0.21 (Wilson lower bound, z=1.96, n=1) · observations: a:✓@2026-01-01 · status: active
