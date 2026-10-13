# Requirements — Config

## Active

### REQ-CONFIG-01 · Lookup by section and key
The tool SHALL print the value of a key from a named section.

#### Scenario: Plain lookup
- WHEN a settings file holds `name = demo` under `[app]`
- THEN looking up `app name` prints `demo`
- Check: `printf '[app]\nname = demo\n' | sh bin/cfg.sh app name` prints `demo`

### REQ-CONFIG-02 · Quoted values
A value wrapped in double quotes SHALL be printed without the quotes.

#### Scenario: Quoted value
- WHEN a settings file holds `name = "demo"` under `[app]`
- THEN looking up `app name` prints `demo`
- Check: `printf '[app]\nname = "demo"\n' | sh bin/cfg.sh app name` prints `demo`

### REQ-CONFIG-03 · Missing key status
Looking up a key that is not present SHALL print nothing and exit with status 1.

#### Scenario: Absent key
- WHEN the section exists and does not hold the key
- THEN nothing is printed and the exit status is 1
- Check: `printf '[app]\nname = demo\n' | sh bin/cfg.sh app port >/dev/null; [ $? -eq 1 ]` exits 0

## Retired
