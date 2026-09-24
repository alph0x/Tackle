# sitehop — migration journal

**2026-04-02** — Audited all pages and found three page types that need different front-matter
treatment: guides, API reference, and the changelog. Decided to start with the guide pages since
they're simplest and most numerous. Next up: migrate the guide pages.

**2026-04-09** — All guide pages are migrated to the new front-matter format and the site's lint script
passes on the guides folder. Started the API-reference pages: parameter tables are converted,
return-value tables aren't yet. Decided to leave the changelog section in the old format entirely — the
new generator can read either format there, so migrating it isn't worth the risk right now. Three things
are still unresolved, all owned by Lianne (see `questions.md`).

Current status: guides finished; API reference underway (parameter tables done, return-value tables
outstanding); changelog left alone on purpose; pick back up at the return-value tables in
`pages/api-reference.md`.
