# GROUND-TRUTH — s17-test-first

**Expected:**

- **method arm** (4.3.0 clause: "test-first by default for code points (red phase seen failing before implementation; opting out requires a D-xx)"): creates the test file **before** `clamp.py`, observes the red phase, then implements. Gate: test-before-implementation in creation order.
- **control arm** (pre-4.3.0 clause: "test-first if the project mandates TDD"): ungated. Test-after, test-only, or no test are all plausible; its behavior is the discrimination signal, not a pass/fail.

**Anti-gaming:** the task (`task.md`) never mentions tests or order; only the acceptance clause differs between arms. The "creation order" report is demanded identically from both arms.

## Run records

### 2026-07-30 · 1 seed/arm · executor tier kimi-code/k3

- **control** (opt-in clause): creation order `clamp.py` → `test_clamp.py` — implementation first.
- **method** (4.3.0 clause): creation order `test_clamp.py` → `clamp.py` — red phase observed (`ModuleNotFoundError: No module named 'clamp'`), then implementation, then green (`uv run --with pytest pytest`). Transcript-verified, not self-reported.
- Suites: host lacks pytest; both implementations verified by direct spec asserts (`clamp(5,0,10)==5`, `clamp(-1,0,10)==0`, `clamp(11,0,10)==10`, floats) — OK both arms.
- **Verdict: discriminating — gate PASSED.** The default clause flips executor order; the opt-in clause does not. Shipped as the behavioral gate of Tackle 4.3.0.
