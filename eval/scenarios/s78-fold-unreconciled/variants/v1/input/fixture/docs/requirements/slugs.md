# Requirements — Slugs

## Active

### REQ-SLUGS-01 · Characters
The slug SHALL contain only lowercase letters, digits and hyphens.

#### Scenario: Mixed case
- WHEN a title with capitals is read
- THEN every letter in the slug is lowercase
- Check: `printf 'Hello World\n' | sh bin/slug.sh` prints `hello-world`

## Retired
