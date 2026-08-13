# Update — skill self-update

Triggered by `/tackle-update` (forced) or by the daily Self-update check that opens **any Tackle invocation**. The agent performs every step; the skill ships no LLM code — the artifact includes the `tackle-check` shell runner (POSIX sh, zero deps), which is copied in place but never executed against fetched content. Every fetch is pinned to `https://github.com/alph0x/Tackle` — never another source.

## Check

1. **Cache gate** — read `~/.tackle/last-update-check`: if it contains today's date, stop; already checked. The file may not exist — absence means run the check.
2. **Fetch the latest release tag** via the GitHub API and extract `tag_name`.
3. **Read the local stamp** from the installed `SKILL.md`.
4. **Compare as semver** — remote ≤ local → record the check and stop; remote > local → run Update.
5. **Degrade silently** — no network, no `curl`, or an API error: stop without a word; the check never blocks the user's work.

## Update

1. **Download the tag tarball** (`curl -sL`), extract into a fresh temp dir; locate the root by listing the dir, never by an assumed name.
2. **Verify the stamp and the runner** — the extracted `SKILL.md` must carry the tag's version, and a 5.x tag must ship a `tackle-check`. Either mismatch → abort to Fallback.
3. **Replace only the install artifact** — remove the old `references/` and copy the extracted `SKILL.md` + `references/` + `tackle-check` into place, then `chmod +x tackle-check`. Touch nothing else.
4. **Record the check** — write today's date to `~/.tackle/last-update-check`.

## Fallback

On any failure — read-only skill directory, missing `curl`/`tar`, stamp mismatch, interrupted download — leave the current install untouched and hand the user the manual path: re-copy `SKILL.md` + `references/` + `tackle-check` (chmod +x) from a fresh clone or download of `https://github.com/alph0x/Tackle` into the skill directory, then restart or reload. State what failed in one line.
