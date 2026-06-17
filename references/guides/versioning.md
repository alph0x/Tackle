# Step 11 — Versioning and release notes

Record methodology changes in `references/CHANGELOG.md`:

```
## Tackle 2.0
- SDD phase entry points: `/tackle-init`, `/tackle-constitution`, `/tackle-specify`, `/tackle-tasks`, `/tackle-implement`, `/tackle-next`, `/tackle-checklist`.
- Plan execution: `/tackle-implement` and `/tackle-next` run points point-by-point.
- Template-resolution stack: overrides > presets > sdd > core.
- Visible plan-local customization: `presets/` and `overrides/` inside `docs/plans/<initiative>/`.
- New depth artifacts: `team.md` and `board.md`.
```

Bump the default `Methodology:` stamp written by new workspaces to **Tackle 2.0**.
