# Requirements — Config

## Active

### REQ-CONFIG-01 · Lookup by section and key
The tool SHALL print the value of a key from a named section.

#### Scenario: Plain lookup
- WHEN a settings file holds `name = demo` under `[app]`
- THEN looking up `app name` prints `demo`
- Check: `printf '[app]\nname = demo\n' | sh bin/cfg.sh app name` prints `demo`

## Retired
