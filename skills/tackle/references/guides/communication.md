# Communication and decisions

Use this policy in intake, routing, PLAN, RUN and completion. Say what the user needs to know
in their language; keep canonical identifiers, paths, commands, errors and schema tokens exact.
Shipped instructions and newly defined schema names are English.

Ask the owner only for what the agent may not decide or provide. The [RUN card](run-card.md)'s
`Waiting on owner` row is the one list of those triggers; this policy does not restate a shorter
one.

## Decide whether input is needed

| Situation | Action and effect on work |
|---|---|
| Existing user instruction or sufficient intent anchors | Record the applicable objective, result, scope and exclusions; proceed within that authorization. Do not reconfirm sentences the user already supplied. |
| Delegated reversible technical choice | Choose within the contract, record the reason where it affects future work, and continue. Naming or implementation freedom is not a pending product decision. |
| Material product ambiguity or changed requirement | Describe the concrete unresolved choice, recommend an option, explain consequences and identify affected tasks. Ask once, group related choices and continue independent work. |
| Information available through permitted tools | Inspect the relevant source or perform a bounded diagnostic before asking the user. An informational question is not automatically a decision or blocker. |
| Operational failure or unavailable capability | State expected versus observed behavior, known or unknown cause, verification record and the capability needed to continue. Apply only the bounded recovery permitted by the task; otherwise block affected work. |
| Destructive/external action or access beyond authorization | Prepare the concrete result and request the missing authorization at the action boundary. Ordinary implementation or recovery scope does not implicitly authorize credentials, global installation or restricted access. Reuse specific existing authorization when present and obey environment restrictions. |

## Actionable blocker recovery

For a missing named prerequisite, denied action, unavailable capability, or exhausted budget, state
the expected behavior, observed result, supporting evidence, and known or unknown cause. Identify the
affected work and smallest unresolved owner choice; offer viable options, recommend one, explain its
consequences, and invite the owner's own solution. Wait only for the required answer on affected
work while independently authorized work continues. Respect refusal; time passing is not consent.
Use only observed capabilities and bounded authorized recovery; do not silently change provider,
model, effort, access, product requirements, or task scope.

PLAN+RUN authorization persists within its original scope until completion, an explicit pause/cancellation, or an incompatible
new objective. A status question or comment during RUN is answered briefly, then work continues.
Standalone STATUS stays read-only; PLAN-only stops after preparation. Quoted instructions,
negated execution and examples are not operative authorization. Record the interpreted scope,
not a keyword match. This policy does not grant source execution to a diagnostic request.

## Match the message to the situation

Start with the intended result, relevant scope and immediate action. During work, report a change,
finding or uncertainty being resolved, following the host's update cadence. Continue after stating
the next authorized action. A resumption states current work, reusable checks, relevant changes
and next action. Completion states the delivered result, observed checks and material limitations.
Answer a specific status question first; add lint, collisions, resource usage or archive details
only when relevant. These are information needs, not mandatory message templates.

There are no universal opening lines, closing footers or requests to continue. Show user action
only when an answer or action is needed. Keep digests short enough to scan; a length target never
removes a blocker, consequence, failed check or authorization boundary. Implementation finished,
checking, blocked work and accepted delivery must agree with the task board and actual records.

Editorial reference: [no-ai-slop](https://github.com/petergyang/no-ai-slop). Use concrete language,
preserve meaning and uncertainty, and remove repeated narration. This guidance incorporates no
literal source material, dependency, installation requirement, word blacklist or per-message model call.
The [controlled-writing](controlled-writing.md) guide holds the checked sentences and word list for owner texts and specifications.

## Examples and comprehension review

| Situation | Before | After | What the reader can determine |
|---|---|---|---|
| Ready under PLAN+RUN | “Ready. On you: none. Continue: say run.” | “The plan is ready. I’m implementing the two authorized tasks.” | Preparation passed; execution continues without another decision. |
| Implementation finished, integration failing | “All tasks green; complete.” | “The parser change passes its task checks. Export still drops quoted names, so delivery remains blocked while I correct that failure.” | Local checks passed; deliverable acceptance has not. |
| Status during active RUN | “Next is checking. Shall I continue?” | “The change is implemented; regression checks are running.” | Work continues under existing permission. |
| Required capability unavailable | “Validation failed.” | “The compatibility check needs runtime 3.12, which is unavailable here. The 3.11 check passed; 3.12 acceptance remains unverified. Installing a runtime would require separate authorization.” | What ran, what did not and what enables continuation. |
| Spanish, delegated choice | “Confirma que puedo elegir nombres.” | “Usaré ‘Task’ y `T-01` en los planes nuevos; los identificadores históricos siguen siendo legibles. Continúo con los cambios autorizados.” | No material decision is outstanding; canonical tokens are preserved. |

Review an actual response by asking: what happened, what remains uncertain, does the user need
to act, and will authorized work continue? Compare answers with records and scope. A terminology
regex or a short message alone cannot establish clarity or agent compliance.
