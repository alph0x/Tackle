# Board — Fixture pre-3 workspace

Canonical status board. Updated only by `/tackle-implement`, `/tackle-next`, or manually during a session.

| Point | What | Briefing | Depends on | Status |
|---|---|---|---|---|
| **P-00 · Draft (emoji)** | not started yet | points/P-00.md | none | 🔴 not started |
| **P-01 · In progress (emoji)** | mid work | points/P-01.md | P-00 | 🟡 implementing |
| **P-02 · In progress (word: preflight)** | mid work | points/P-02.md | P-00 | preflight |
| **P-03 · In progress (word: correction)** | mid work | points/P-03.md | P-00 | correction |
| **P-04 · Ready to run (word)** | queued | points/P-04.md | none | Ready |
| **P-05 · Checking (word: target validation)** | validating | points/P-05.md | P-04 | target validation |
| **P-06 · Checking (word: validating)** | validating | points/P-06.md | P-04 | validating |
| **P-07 · Checking (word: integrating)** | validating | points/P-07.md | P-04 | integrating |
| **P-08 · Checking (word: accepting)** | validating | points/P-08.md | P-04 | accepting |
| **P-09 · Blocked (emoji)** | stuck | points/P-09.md | none | ⏸ blocked |
| **P-10 · Complete (emoji)** | shipped | points/P-10.md | none | 🟢 done |
| **P-11 · Interrupted (word: observe-incomplete)** | cut short | points/P-11.md | none | observe-incomplete |
| **P-12 · Interrupted (word: interrupted)** | cut short | points/P-12.md | none | interrupted |
| **P-13 · Skipped (emoji + reason)** | not needed | points/P-13.md | none | ⚪ skipped — optional slice; real phases built directly |
| **P-14 · Unverifiable (word: UNVERIFIABLE)** | can't check | points/P-14.md | none | UNVERIFIABLE |
| **P-15 · Unverifiable (word: unavailable required check)** | can't check | points/P-15.md | none | unavailable required check |
| **P-16 · Unmapped garbage status** | unknown token | points/P-16.md | none | 🤷 dunno |
| **P-17 · Ragged row missing Status** | short row | points/P-17.md | none |

### Dependency graph

```
P-00 ──► P-01
```
