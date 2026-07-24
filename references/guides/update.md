# Update — skill self-update

Triggered by `/tackle-update` (forced) or by the daily Self-update check in Step 0 of `intake-and-gate.md`. The agent performs every step; the skill ships no code. Every fetch is pinned to `https://github.com/alph0x/Tackle` — never another source — and nothing downloaded is ever executed (the artifact is markdown only).

## Check

1. **Cache gate** — if `~/.tackle/last-update-check` contains today's date (`YYYY-MM-DD`), stop; already checked. `/tackle-update` skips this gate.
2. **Fetch the latest release tag**:
   `curl -s --max-time 10 https://api.github.com/repos/alph0x/Tackle/releases/latest`
   and extract `tag_name` (e.g. `"tag_name": "v4.1.0"`).
3. **Read the local stamp** `**Tackle X.Y.Z**` from the installed `SKILL.md` (the file this skill was loaded from).
4. **Compare as semver** (4.10.0 > 4.9.0 — never string-compare). Remote ≤ local → write today's date to `~/.tackle/last-update-check` and stop. Remote > local → run Update.
5. **Degrade silently** — no network, no `curl`, or an API error: stop without a word on the daily path; say it once under `/tackle-update`. The check never blocks the user's work.

## Update

1. **Download the tag tarball**, following redirects:
   `curl -sL --max-time 60 -o <tmpdir>/tackle.tar.gz https://github.com/alph0x/Tackle/archive/refs/tags/v<X.Y.Z>.tar.gz`
2. **Extract** into a fresh temp dir (`tar -xzf`) — the root is the single directory the extraction produces (`Tackle-<version>` from a tag archive); locate it by listing the temp dir, never by an assumed name pattern.
3. **Verify the stamp** — the extracted `SKILL.md` must carry `**Tackle X.Y.Z**` matching the tag. Mismatch → abort to Fallback.
4. **Replace only the install artifact** in the skill directory (the directory containing the loaded `SKILL.md`): remove the old `references/` and copy the extracted `SKILL.md` + `references/` into place. Touch nothing else in that directory.
5. **Record the check** — write today's date to `~/.tackle/last-update-check`.

## Reload

If the harness exposes a documented skill-reload mechanism, run it. Otherwise tell the user: "Tackle updated <old> → <new> — restart the session (or reload skills) to pick it up." The current session keeps running the old version; that is expected, not an error.

## Fallback

On any failure — read-only skill directory, missing `curl`/`tar`, stamp mismatch, interrupted download — leave the current install untouched and hand the user the manual path: re-copy `SKILL.md` + `references/` from a fresh clone or download of `https://github.com/alph0x/Tackle` into the skill directory, then restart or reload. State what failed in one line.
