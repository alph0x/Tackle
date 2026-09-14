# Team capabilities — {{TITLE}}

This template binds role capabilities and state ownership. The sole execution lifecycle, correction
budget, evidence contract, integration checks, and closure rules live in
`references/guides/run.md`; do not copy an execution protocol into this file. The workspace
(`board.md`, `log.md`, the Point file, and touched files) is the source of truth; messaging is only
coordination.

## Model binding

Teams bind roles to abstract, harness-agnostic tiers, never vendor models:

- **`fast`** — grounding reads, searches, lint and drift checks.
- **`standard`** — implementation, coordination and ordinary review.
- **`frontier`** — adversarial verification or architecture judgment when the risk requires it.

| Role | Tier | Effort |
|---|---|---|
| Driver | standard | medium |
| Reviewer / Coordinator | standard | medium |
| Spec Reader | fast | low |
| Verifier / Red-Teamer | frontier | high |
| Specialists | standard | medium |

The Point briefing may override a default. The workspace `AGENTS.md` model map binds tiers to the
concrete models available in that harness. Effort is `low / medium / high / max`; when effort or
model binding is unsupported, record the actual binding and `n/a` values honestly. Never silently
upgrade a role to resolve a Run failure. An independent session or human fallback is selected only
when the Run risk requires semantic independence; a renamed role or tier does not itself establish
independence.

## Team sizing

| Size | Roles | Use for |
|---|---|---|
| **Solo** | Driver | A simple, single-file change with a clear check. |
| **Pair** | Driver + Reviewer | Routing, multi-file, or review-sensitive work. |
| **Pod** | Driver + Spec Reader + Quality Guardian + Coordinator | Complex or high-risk contract work. |
| **Squad** | Pod + risk-specific Specialist | Security, performance, or other demonstrated specialist risk. |

Default to Solo unless the Point briefing requests a larger team. Add only the capability needed:
Simplicity, Architecture, Security, Performance & Concurrency, or Regression. Specialists review the
relevant risk; they do not create a second lifecycle or budget.

## Wave gates

When a plan has waves, this heading is the compatibility pointer for generated workspaces. The Run
guide owns the actual gates: before a wave, check authorization, Ready fingerprints, dependencies,
and environment; after a merge, run affected integration checks on the merged tree. There is no
separate pre-wave Verify loop or inter-wave closure protocol.

### Risk capability checks

Select only checks justified by the Point's risk; these checks supplement the Run protocol and never
create an independent closure loop.

- **Simplicity** — understand the real flow first, fix the root cause and inspect callers; reuse an
  existing function or standard-library facility before adding an abstraction or dependency.
- **Security** — validate inputs at command/query/path boundaries, keep secrets out of logs/errors/
  diffs, check authorization on every path including cross-tenant paths, and justify dependencies.
  Do not simplify away validation, data-loss protection, security, accessibility, or an explicit
  requirement. Non-trivial logic has a runnable check.
- **Correctness / repro** — check boundary behavior and ensure valid and invalid evidence can be
  distinguished; a keyword or test count is not semantic proof.
- **Performance** — inspect complexity, allocations, and concurrency only when the changed path or
  data volume makes that risk relevant.
- **Polish / regression** — inspect stale documentation, dead leftovers, and affected existing
  callers when the Point changes a user-facing or shared surface.

## State ownership

- `board.md` records the current Point status and confidence.
- `log.md` records append-only history and bounded state snapshots.
- `usage.md` records observed lifecycle events and exposed telemetry; unknowns are `n/a`.
- `coordinator.md` is a generated re-contextualization projection, never canonical.

The Coordinator owns board/log hygiene and records role boundaries. The Driver owns scoped source
changes and observations. Reviewers verify against the Point and current contract. The Run guide
defines when any of these observations permit completion; no role may flip a status by assertion.

## Capability map

| Capability | Responsibility | Run reference |
|---|---|---|
| Authorization / preflight | Check intent, Ready fingerprints, dependencies, contract and environment. | `run.md` §Authorization and preflight |
| Implementation | Work inside Touches and preserve protected expectations. | `run.md` §State transitions |
| Mechanical observation | Capture real command, process, artifact and revision evidence. | `run.md` §Evidence and recovery |
| Semantic review | Review only where risk requires independent meaning judgment. | `run.md` §Independence and evidence grades |
| Integration / acceptance | Test the merged tree, semantic consumers and global obligations. | `run.md` §Integration, global acceptance, and close |
| Recovery | Preserve counters/history; classify failures and emit packets. | `run.md` §Failure classification and correction |

For grounding, quality, and migration concerns, use the linked shared guides. Those guides may
describe their own PLAN, audit, or historical procedures, but they do not authorize source
execution; `run.md` does.
