# Synthetic fixture profile — Wilson golden (C2)

Shapes the real, live `.tackle/profile.md` audit numbers this task's findings cite
(`.tackle/profile.md:22` is 9✓/0✗ at a hand-set 0.7; `.tackle/profile.md:54,93` are 1✓/0✗ at
hand-set 0.9/0.85), rebuilt here as synthetic new-format entries so the computed value can be
checked without ever touching the real file.

## Hypotheses

- id: H01 · Nine independently checked observations · confidence: 0.70 (Wilson lower bound, z=1.96, n=9) · observations: init-a:✓@2026-01-01; init-b:✓@2026-01-02; init-c:✓@2026-01-03; init-d:✓@2026-01-04; init-e:✓@2026-01-05; init-f:✓@2026-01-06; init-g:✓@2026-01-07; init-h:✓@2026-01-08; init-i:✓@2026-01-09 · status: active
- id: H02 · One independently checked observation · confidence: 0.21 (Wilson lower bound, z=1.96, n=1) · observations: init-a:✓@2026-01-01 · status: active
- id: H03 · Assumed acceptances only, never independently checked · confidence: n/a (no checked observation) · observations: init-a:assumed@2026-01-01; init-b:assumed@2026-01-02 · status: active
