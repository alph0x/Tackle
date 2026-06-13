# Action plan — {{TITLE}}

## 1. Objective

{{What is achieved, in terms of the result for the integrator/user.}}

## 2. Expected result

- {{observable 1}}
- {{observable 2}}

## 3. Non-goals (out of scope)

- {{What this initiative explicitly does NOT do.}}

## 4. Current state (detail in `reference.md`)

<!-- Lead with the de-risking finding (Step 5): the ONE verified fact that reshapes the risk
     profile — what makes this safer/smaller/different than it first looked. Then anchor the
     approach to precedent: the in-repo house pattern and/or proven reference architecture
     this should mirror, cited with file:line. Both before the generic state summary. -->

**Key finding (verified):** {{the fact that changes the shape of the work — e.g. "X is
dormant, so this is an adoption not a hot replacement → low regression risk by construction".}}

**Precedent we mirror:** {{the established pattern in this repo / the proven reference
module this design follows — `path` / repo, with file:line.}}

{{Summary of the relevant code state, with `file:line` for the key points.}}

## 5. Point decomposition
<!-- One row per point. Each point has a self-contained briefing in points/<id>-<slug>.md.
     A point may map 1:1 to a phase. Delete the Spec/Plan cols if not using superpowers depth.
     Status vocabulary (fixed): 🔴 not started · 🟡 in progress · ⏸ blocked (say on what) · 🟢 done -->

| Point | What | Briefing | Depth (optional) | Depends on | Status |
|---|---|---|---|---|---|
| **P-01 · {{...}}** | {{...}} | `points/P-01-{{slug}}.md` | `specs/{{date}}-P-01.md` · `plans/{{date}}-P-01.md` | {{none}} | {{🔴 not started}} |

### Dependency graph
```
{{P-01 ──► P-02   (P-01 blocks P-02)}}
{{P-03            (independent)}}
```

## 6. Acceptance criteria

### 6.1 Universal per-point acceptance (binding for EVERY point — points reference this, don't duplicate it)
<!-- The bar every point must clear before it flips 🟢. Define it ONCE here; each point's
     "Acceptance" links to this block and adds only its point-specific criteria. Keep these
     verifiable (a command or an inspection), not aspirational. Trim to what this initiative
     actually needs. PROMOTE the load-bearing structural invariants from design-contract.md /
     Step 5 up into this block — they're the gates that actually catch drift. -->
- [ ] {{tests cover the change (test-first if the project mandates TDD); the suite is green}}
- [ ] {{structural invariant 1, promoted from the contract — e.g. "core compiles with zero deps"}}
- [ ] {{concurrency/safety gate, if relevant — e.g. "clean under the language's strict concurrency mode"}}
- [ ] **Self-documenting code**: no explanatory inline comments; doc-comments on the public surface only; the *why* lives in commits/docs (an internal comment is a refactor finding, not a wording fix).
- [ ] {{grounded: any new abstraction has its row in `foundations.md` (if that file exists)}}
- [ ] {{contract conformance: matches `design-contract.md`, or the spec was superseded first (if that file exists)}}
- [ ] {{no regression on shared code; no new warnings}}
- [ ] {{board hygiene: `plan.md` §5 + `log.md` updated; resolved Q-xx → D-xx}}

### 6.2 Initiative-level acceptance
- [ ] {{observable, verifiable end-state for the whole initiative}}

## 7. Risks / dependencies

- {{risk + mitigation; external dependency + who}}
- **Rollout / reversibility** (if this touches a production path): {{how it ships safely —
  enablement flag default-off, canary target, coexistence with the old path, and the
  no-op/parity check that proves flag-off changes nothing. Omit if not production-facing.}}

## 8. Verification / tooling

- {{per-module tests, local mock/stub, no-regression, etc.}}
