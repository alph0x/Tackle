# Focused grey-area corrections

Development-only checks; not part of the installed Markdown artifact.

`python3 eval/grey-fixes/test_evidence_capture.py` executes the literal code fence from
`references/guides/evidence-capture.md` against controlled success, child failure, binary output,
timeout, signal, changed inputs, missing artifacts and repeated-capture cases. It validates the
recipe, not model obedience. CI runs the same command.

`fixtures/H01` (durable evidence), `H02` (new serialization feature) and `H03` (bounded restoration)
are fresh synthetic inputs for separate post-fix sessions. Their criteria and raw results are kept
in the local-only correction workspace. They do not rerun or amend the six-arm pilot or the
unstarted 54-episode comparison. Behavioral outcomes must be judged from actual sessions and
artifacts; no outcome is implied by these fixtures' existence. No reusable LLM runner is shipped.

`fixtures/H04` is a separately registered Lite closure check after the first three sessions.
It exercises the follow-up guidance and does not replace their outcomes or establish a speedup.
