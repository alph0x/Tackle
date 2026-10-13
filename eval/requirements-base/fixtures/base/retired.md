# Requirements — Auth

## Active

## Retired

### REQ-AUTH-03 · Legacy login
Retired: legacy-plan · 2026-01-02 · replaced by passkeys

The system SHALL accept a legacy password form.

#### Scenario: Legacy form
- WHEN the legacy form is submitted
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_legacy_form` exits 0
