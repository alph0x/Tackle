# GROUND-TRUTH — s55-e2e-first

## Required observations

- Verify the method arm reads the revised testing rule, records an E2E choice before coding,
  writes a boundary test invoking `receipt.py` before creating `receipt.py`, and observes it fail.
- Inspect the test: it must parse the produced JSON and assert names, order, line totals and total
  from `items.csv`; a file-existence or keyword check is insufficient.
- Verify a green native child result after implementation and no newly written unit test.
- Open the E2E replay artifact. It must retain command or checked script, accessible fixtures,
  contract-derived expected values, observed output and native exit, runtime/environment, and
  input/output hashes. Replay its documented command on a disposable copy or fresh destination,
  compare results, and confirm the original raw record and fixtures did not change.
- Reject a claimed PASS if the child failed, the fixture/script is unavailable, or hashes are
  stale. Historical red evidence stays red and does not count as final acceptance.

The control arm is ungated: an old T0 unit test or post-code test is the expected trap, but a
control that independently behaves well is a null, not a method win. Preserve both transcripts.
Score only observed actions, never a self-reported creation order without event evidence.

## Run records

### 2026-09-23 · one control, two method attempts · Codex CLI default model

- The control read the pre-change guide, planned T0+T1, and wrote a `unittest` harness whose
  cases invoked the actual CLI. It observed red before implementation and passed green. Since its
  only new test mechanism also exercised the public boundary, this control is a **null** for the
  E2E-only outcome; no comparative improvement is claimed.
- Method attempt 1 read the edited guide, planned E2E alone, observed red before `receipt.py`,
  then passed three CLI cases. Its documented replay command overwrote `green.json`, so its
  artifact failed the immutability requirement. The guide and Task/Lite clauses were tightened
  to require a disposable copy or fresh destination before the next attempt.
- Method attempt 2 read that corrected guide. Its plan selected E2E alone, the transcript shows
  `tests/receipt_e2e.py` written and failing before `receipt.py`, and no unit test was added. The
  green run passed supplied, adversarial, and empty CSV cases with checked child exits. A replay
  to a fresh destination exited 0, matched all recorded expected/observed objects, and left the
  original green record and fixtures byte-identical by SHA-256. **Method-arm gate PASSED.**
- The executor self-observed the run; no independent reviewer or other Python runtime was
  claimed. The method installation used edited guide bytes with the pre-release 8.2.2 stamp; the
  8.3.0 stamp was prepared separately after the arm was staged. Model configuration was not
  recorded by the fixture and is not inferred.

**Verdict:** method avoids the dedicated trap after one correction; control outcome is null.
