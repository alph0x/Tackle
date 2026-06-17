# SDD preset

This preset intentionally starts empty. SDD phase templates resolve through the stack (`overrides > presets > sdd > core`), so absent files here fall through to `references/sdd/` and then `references/`.

Add phase-specific overrides here; they will shadow the core SDD templates for this preset.
