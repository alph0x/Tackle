# Training plan

The training app reads `training/adaptive-plan.json` before it builds each week's plan.

- Setting `"adaptive_difficulty"` to `"off"` freezes the plan at its current numbers. Everything on file, learned or pinned, stays as it is.
- With no `adaptive-plan.json`, the app stops adapting and falls back to one fixed default plan. Deleting the file stops the adjusting the same way, and erases every number on file, learned or pinned, along with it.
