# Requirements delta — Slug limits

Base revision: 7c2e91d

## ADDED
### REQ-SLUGS-02 · Tidy separators
Task: T-01 · State: done
The slug SHALL replace each run of separators with one hyphen and SHALL NOT start or end with a hyphen.

#### Scenario: Ragged title
- WHEN a title with punctuation and repeated spaces is read
- THEN the slug has single hyphens between words and none at the ends
- Check: `printf '  Hello,   World!  \n' | sh bin/slug.sh` prints `hello-world`

### REQ-SLUGS-03 · Default length limit
Task: T-02 · State: done
A slug longer than 40 characters SHALL be cut to at most 40 characters, with no trailing hyphen.

#### Scenario: Long title
- WHEN a title that produces a slug longer than 40 characters is read
- THEN the slug is at most 40 characters
- Check: `printf 'the quick brown fox jumps over the lazy dog again and again\n' | sh bin/slug.sh | awk '{ exit length($0) > 40 }'` exits 0
