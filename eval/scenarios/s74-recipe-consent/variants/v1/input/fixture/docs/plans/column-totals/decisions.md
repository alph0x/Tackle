# Decisions

## D-01 — Check records

- Every check keeps a verification record under `verification-records/<task>/`: exact command, cwd,
  complete stdout and stderr, exit status, and sha256 of the product files before and after. 2026-10-05.
