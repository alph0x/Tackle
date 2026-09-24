# One skill, requests inside it

Tackle ships one skill named `tackle`. The host controls how a user selects that skill: a picker,
mention, or supported command. Tackle does not register separate commands for its actions.
After selection, interpret the user's request in any language. Short action names are optional.
In documentation and continuation prompts, recommend selecting Tackle and stating the action;
never promise a separate menu entry for an action or a particular prefix in every host.

## Resolve intent

1. A bare skill selection, `tackle`, or `help` with no task asks for help. Briefly offer plan, run, show status,
   validate the plan, audit the result and review lessons, with a couple of examples.
   Do not read project state or create/change files just to show help.
2. Prefer the complete request over an action token: a question about `run`, a quoted example,
   or “don't execute” does not authorize execution. If the action or its target is materially
   ambiguous, ask one short clarification before writes. Do not invent an action for an unknown
   token. If only the target is missing, use an unambiguous active context or ask.
3. Route a clear request through the table. Natural language and short forms share the same
   intent, scope, consent and evidence rules. Activation itself is never execution consent.

| Request after selecting Tackle | Route and boundary | Guide |
|---|---|---|
| `plan <task>` / “plan this” / “armá un plan” | PLAN prepares; explicit plan-and-execute intent can also authorize subsequent RUN | [Intake](intake-and-gate.md) |
| `run`, `run --one`, `run <T-id>` / “ejecutá la tarea” (legacy `run <P-id>` and “ejecutá el punto” remain readable) | RUN executes the explicitly requested scope after preflight | [Run](run.md) |
| `status [<workspace>]`, `list`, `next`, plain `resume` / “qué sigue” | STATUS inspects/selects; no source, board or log writes | [Status](status.md) |
| `status <workspace> --handoff` / “prepare a handoff” | Write only the requested handoff projection | [Status](status.md) |
| **validate the plan**, `verify [<workspace>]` / “verificá este plan sin modificarlo” | PLAN validation or explicit diagnosis; a diagnosis alone never authorizes repairs or history writes | [Verify](verify.md) |
| **audit the result**, `judge [<target>]`, `judge suite <target>` / “auditá lo implementado” | Explicit post-work audit or suite evaluation; no implied fix | [Auditor](judge.md) |
| **review lessons**, `retro [<workspace>]` / “review the lessons” | Optional learning review; profile writes require separate confirmation | [Retro](retro.md) |
| `init <name>` | PLAN scaffolding with the existing setup consent | [Scaffold](scaffold.md) |
| `migrate`, `upgrade`, “improve this plan” | Selected-workspace, copy-first migration preparation | [Migrate](migrate.md) |

## Continuing authorized work

Route the request in its conversation context. PLAN+RUN remains authorized within its original scope. A status question during active RUN receives a concise answer, then work continues; it does not become a new standalone STATUS job or cancel authorization. An explicit pause, cancellation or incompatible replacement stops dependent execution. Standalone STATUS remains read-only and PLAN-only supplies no RUN permission. Apply the [decision and communication policy](communication.md).

English and Spanish examples preserve intent: “Plan and implement this” / “Planificá e implementá esto” authorize both after readiness; “Plan only, do not execute” / “Solo el plan, no ejecutes” stop at preparation. “What does \`run\` mean?” and “El ejemplo dice \`run\`” are questions/examples, not authorization.

## Compatibility during 8.x

Previously documented slash strings remain text aliases when they reach the agent. Normalize
`/tackle-plan`, `/tackle-run`, `/tackle-status`, `/tackle-verify`, `/tackle-judge`, `/tackle-retro`
and `/tackle-init` to the matching request above, retaining the target, flags and stated intent.
For example, `/tackle-run --one` means `run --one`; `/tackle-verify` means `verify`. Typing a text
alias cannot make a host register it or show it in a picker. If a host rejects it, select Tackle
and use the request form instead.

Other legacy routes, with or without their historical `/tackle-` prefix, keep their existing
forwarding: `implement` → RUN; `ground`/`trace`/`drill` → PLAN validation;
`pulse`/`list`/`next`/`resume` → STATUS; `handoff` → STATUS `--handoff`.
Preserve the requested operation: grounding, coverage and cold-resolvability remain their own
checks within [Verify](verify.md). Forwarding never grants broader execution or write permission.
Legacy aliases retire in 9.0; retain this guidance for interpreting historical workspaces.
