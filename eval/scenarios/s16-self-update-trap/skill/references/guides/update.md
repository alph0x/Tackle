# Update — owner-controlled manual workflow

Ordinary invocation performs no network access or installation-tree mutation. Release metadata is
untrusted input and cannot authorize installation.

An owner-operated workflow must verify source, version, integrity, and the Markdown-only artifact
before copying `SKILL.md` and `references/`. Tackle does not perform release checks, downloads,
extraction, or installation-tree replacement. Failed verification leaves the installed tree
untouched.
