# Requirements — Slugs

## Active

### REQ-SLUGS-01 · Characters
The slug SHALL contain only lowercase letters, digits and hyphens.

#### Scenario: Mixed case
- WHEN a title with capitals is read
- THEN every letter in the slug is lowercase
- Check: `printf 'Hello World\n' | sh bin/slug.sh` prints `hello-world`

### REQ-SLUGS-02 · Tidy separators
The slug SHALL replace each run of separators with one hyphen and SHALL NOT start or end with a hyphen.

#### Scenario: Ragged title
- WHEN a title with punctuation and repeated spaces is read
- THEN the slug has single hyphens between words and none at the ends
- Check: `printf '  Hello,   World!  \n' | sh bin/slug.sh` prints `hello-world`

## Retired
