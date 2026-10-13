# Requirements delta — Quoted values

Base revision: b05d3f1

## ADDED
### REQ-CONFIG-02 · Quoted values
Task: T-01 · State: done
A value wrapped in double quotes SHALL be printed without the quotes.

#### Scenario: Quoted value
- WHEN a settings file holds `name = "demo"` under `[app]`
- THEN looking up `app name` prints `demo`
- Check: `printf '[app]\nname = "demo"\n' | sh bin/cfg.sh app name` prints `demo`

### REQ-CONFIG-03 · Missing key status
Task: T-02 · State: done
Looking up a key that is not present SHALL print nothing and exit with status 3.

#### Scenario: Absent key
- WHEN the section exists and does not hold the key
- THEN nothing is printed and the exit status is 3
- Check: `printf '[app]\nname = demo\n' | sh bin/cfg.sh app port >/dev/null; [ $? -eq 3 ]` exits 0
