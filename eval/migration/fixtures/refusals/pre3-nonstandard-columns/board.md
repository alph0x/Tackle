# Board — non-standard column order fixture

Synthetic content only (T36-H1): reproduces the column order a fresh review found on a real local
workspace (`Point | Status | Preparation | Confidence | Note`), without copying that workspace's own
text. This header has no `What`, `Brief`/`Briefing` or `Depends on` column at all, so `step-pre3-to-3`
must refuse it by name rather than silently reading the wrong cells into those positions.

| Point | Status | Preparation | Confidence | Note |
|---|---|---|---|---|
| P-01 | 🔴 | synthetic prep text, not real workspace content | E2 | synthetic note text, not real workspace content |
