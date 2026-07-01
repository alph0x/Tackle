# Step 8.5 — Migrate

Bring an old plan to the current methodology.

## Generic migration

1. Detect the gap (trust structure, not just the stamp).
2. Preserve what's settled.
3. Scope to forward-looking work.
4. Re-ground remaining points.
5. Add missing artifacts.
6. Lint + checkpoint.
7. Record migration `D-xx` + log entry + bump stamp.

## v2.1 → v3.0 checklist

Run these when migrating a plan created with Tackle 2.1.x:

1. **Anchor citations** — rewrite every `file:line` citation to the anchored format `path:NN — "literal fragment"`; run `/tackle-ground` and fix drift.
2. **Adopt Evidence blocks** — every "done-signal passed" claim in `log.md` must carry an Evidence block (command, trimmed output, exit line); add attempt-journal lines for failed attempts.
3. **Seal ready points** — append `SEALED: D-xx` to the Acceptance heading of each ready point and to each `design-contract.md` section that has stabilized.
4. **Run lint-spec** — execute every row of `guides/lint-spec.md` and fix failures until the score line reads `lint: N/N checks passed`.
5. **Add Last-verified stamps** — keep `reference.md` current with `Last-verified:` dates and re-ground before execution if older than the workspace window.
6. **Declare autonomy level** — add `Autonomy level: L2 (assisted)` to `AGENTS.md` (or L1/L3 with the required conditions); cap production-path points at L2 unless waived by a `D-xx`.
7. **Adopt execution rules** — apply regression sweep + maker/checker: the Driver's done-signal run is informative, the 🟢-flipping run comes from an independent checker with evidence in `log.md`.
8. **Fill the harness map** — record the concrete harness tools for read, search, test, lint, spawn, and git in `AGENTS.md`.
9. **Record migration** — write a `D-xx` in `decisions.md`, append a `log.md` entry, and bump the workspace `Methodology:` stamp to Tackle 3.0.

## v2.0 → v2.1.0 checklist

Run these when migrating a plan created with Tackle 2.0:

1. **Status migration** — if `plan.md` §5 has a Status column, move every status to `board.md` and remove the column from `plan.md`.
2. **Source anchor** — add the "Traces to" column to `plan.md` §5 and fill it for every point; add `Traces to` in each point file under Status & wiring.
3. **Grounding audit** — for each point, read every cited `file:line`; mark the point **ungrounded** if any citation is unread and update its Context.
4. **Done-signal audit** — rewrite any prose, `test -f`, or "document exists" done-signal into a literal runnable command with an explicit pass condition.
5. **Right-size** — if the plan has ≤4 points and no multi-track uncertainty, offer to collapse to `lite-plan.tmpl.md`.
6. **Spec anchors** — if `spec.md` or `constitution.md` exist, add an "Anchors" section with `A-NN` references for each traced requirement.
7. **Agnosticism sweep** — remove any harness/LLM-specific language (model brand names, vendor commands, tool-specific paths) unless the point is explicitly about that harness.
8. **Verify** — run `/tackle-verify` on the migrated plan; fix HIGH findings, decide on MEDIUM findings, note LOW findings.
9. **Record** — write a `D-xx` in `decisions.md` describing the migration, append a `log.md` entry, and bump the plan stamp/version.
