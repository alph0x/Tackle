# Optional Judgement Layer

Judgement Layer is the provider-independent optional judgment capability. The current adapter uses TypeSafe System One / Jev; its existing consent records, identifiers and compatibility paths retain their meaning.

<a id="integration"></a>
## Integration contract

Use optional System One only when a configuration signal exists and the selected workspace has recorded `yes`. Never ask the user to install TypeSafe/JEV. Tackle itself opens no network connection: a judgment goes through the host's `typesafe-ai` skill. Build the client under that skill and pass its constructor as `client_factory` to [system_one_state.py](../../scripts/system_one_state.py), which provides selected-workspace storage, the local consent logic and the SDK adapter. Running or importing these scripts needs the owner's explicit authorization under the [script consent rule](../../scripts/README.md#consent); the recorded `yes` grants it for that use only. Before the workspace's recorded `yes`, fetch no TypeSafe documentation or SDK material; the installed SDK's own types are enough.

A configuration signal is the host offering the `typesafe-ai` skill, the presence of the `TYPESAFE_API_KEY` environment variable, or the case-insensitive phrase `TypeSafe System One` in project-root AGENTS/CLAUDE or selected-workspace AGENTS. Check presence only and probe no home folder. Never read, print or send credential values or open credential files. A configuration signal cannot grant consent.

Record the owner's explicit `yes` or `no`, date and actor in that workspace's AGENTS. Do not inherit an answer from another workspace. In PLAN/RUN ask once, retain an unanswered question in questions.md and never repeat it during the session or after an answer; read-only STATUS only detects/reads and never starts or mutates this workflow. Malformed/conflicting records cannot authorize a send. The consent functions `load_state`, `prepare_consent` and `record_consent` run before any recorded `yes`: they only read the workspace's record, write the pending question or record the owner's answer, and send nothing. The owner's answer to the System One question authorizes recording it; the recorded `yes` authorizes only `system_one_use`.

Send only admitted public fragments needed by one of four uses: older-history score, RUN failure-class choice, no-progress signature comparison, or Direct/Focused/Coordinated intake. Never send credentials, secrets, unknown/private fragments, sealed material or answer sheets. The agent must classify sensitivity before calling the adapter; this is no general secret detector.

Keep the cold-resume opened-history bound, spent counts and open obligations. Skip an unprotected entry only at score<0.5 and confidence>=0.6. Other uses need confidence>=0.8. Preserve the complete installed gate's deterministic minimum route, risk precedence and no-progress stops/counters; JEV never supplies authority or assigns blame. Report the actual use, model, confidence, adopted decision or local fallback reason. After a configuration signal, record each call and each local fallback as one [sidecar](usage-observability.md) record with `collector: system-one`. Use `scope: role` and the calling role's Run ID as `run_id`; without a Run ID, use `scope: session` and `run_id: n/a`. A Direct request has no workspace and writes no record. The record's metrics hold `requests` and, when the response reports them, token counts. `requests` is 1 when a request was sent and 0 when the fallback came before any send. The record's `provenance` holds the use, model, confidence and adopted decision or fallback reason. With a recorded `yes`, consult System One at every point where one of the four uses applies: each failure classification, each no-progress comparison, each cold-resume history choice and each intake sizing. Each consult keeps the thresholds and fallbacks above. A point with no admitted public fragment is a skipped point. Record a skipped point with its reason. Read-only STATUS makes no call and writes no record. A missing sidecar or a failed record write never fails the task.

Pin `jev-1.13.0`; refuse another response model or malformed/out-of-domain answer. SDK handles authentication through its configured owner environment. Use its verified TLS defaults, trusted endpoint, timeout and zero retries. Absent SDK/signal/recorded yes, low confidence, refusal or any ordinary transport error falls back to the agent's judgment without stopping the task; BaseException propagates. Never disable certificate verification or request installation.

The install carries no network client: the two scripts hold the local logic and the caller supplies the client. Native file/SDK-mock checks prove their encoded integration cases; agent behavior, live service availability and held-out safety/release evidence remain separate obligations.

## Pure decision consumer

The caller supplies `system_one_decide(state, use, fragment, local_judgment,
transport=None)`. `state` is a closed builtin dictionary with a nonempty
`workspace` string, a real boolean `configured`, `consent` and `asked`. Consent is
`None` or a closed builtin dictionary containing a nonempty `workspace` and
`answer` (`yes` or `no`). `asked` is a builtin list of unique nonempty workspace
strings. The returned state keeps these entries in independent containers;
the caller owns persisting it into the selected workspace.

`configured` represents an already supplied configuration signal. Missing or
foreign-workspace consent is unanswered: the function returns one fixed question
per workspace and keeps the local judgment. Recorded `no` returns locally without
a question or call. A recorded `yes` authorizes only its exact workspace. With no
configuration, the function returns locally without a question or call. It validates
every caller input before any of these effects and raises
`ValueError("system_one_input")` for malformed input, even without configuration.

The four uses are `resume-selection`, `failure-class`, `no-progress` and
`intake-size`. A fragment is a nonempty public string selected by the caller;
its sensitivity is a separate caller obligation. A supplied in-process callable
receives exactly `model`, `use` and `fragment` with model `jev-1.13.0`, and returns
exactly `model`, `confidence` and `judgment`; these normalized dictionaries are
not the TypeSafe wire protocol. The separate state script supplies the
actual adapter; this pure function performs no environment, filesystem or network
operation, and a third-party callable's behavior is outside its proof.

Judgments use only exact builtin strings, booleans, integers, finite floats,
lists, dictionaries with string keys and `None`. Container cycles, subclasses,
tuples, custom objects and nonfinite numbers are invalid; shared acyclic
containers are valid. The function validates nested judgments iteratively and
changes neither inputs nor transport responses.

The reference confidence minimum is `0.6` for `resume-selection` and `0.8` for the
other uses, inclusive at the boundary: conservative reference defaults, not
provider calibration. Malformed responses, another model, insufficient
confidence, absent transport or an ordinary transport `Exception` return the exact
local judgment with a distinct fixed reason. A supplied transport is attempted at
most once. `BaseException` propagates. There is no retry.

The closed result has `judgment`, `source`, `reason`, `state`, `question`, `model`
and `confidence`. Acceptance records source `jev`, reason `accepted`, the actual
accepted model `jev-1.13.0` and its observed numeric confidence. Every local result
records model/confidence as `None`. Local reasons are `not-configured`,
`consent-unanswered`, `consent-no`, `transport-unavailable`, `transport-failure`,
`malformed-response`, `wrong-model` or `low-confidence`.

History selection keeps its score rule: an entry is skipped only below `0.5`
with confidence at least `0.6`. The existing context bound, open obligations and
spent counts remain; this generic function never selects or drops history.
Detection, persisted consent and SDK serialization belong to the separate
integration consumer; agent compliance stays an independent evidence obligation.
Source-level tests establish neither held-out safety behavior, complete optional
capability readiness nor release acceptance.

### Bounded new-use extension

The optional Judgement Layer adds only `bounded-recovery` and `evidence-signal`. The original four
uses, their positional calls, consent question, SDK/model pin, collector name, result keys and
policies remain unchanged. Only these two extensions accept the keyword-only `support_policy`;
`system_one_use` additionally accepts keyword-only `budget_scope`. The pure signature is
`system_one_decide(state, use, fragment, local_judgment, transport=None, *, support_policy=None)`;
the adapter signature is
`system_one_use(workspace, configured, asked, use, fragment, local_judgment, sensitivity, decide, client_factory=None, *, support_policy=None, budget_scope=None)`.

The caller supplies a closed builtin policy `{choices, eligible, fallback, resolved}`. Its lists
contain unique nonempty exact strings and `eligible` is a subset of `choices`. For
`bounded-recovery`, choices are public recovery IDs declared by the planner; `retry-after-correction`
and `rerun-read-only` are examples. `defer` is reserved and is sent only as an allowed stop choice. The fallback is
an eligible choice or `defer`; an empty eligible list requires `defer` and skips consultation.
For `evidence-signal`, choices and eligible are exactly `supports`, `partial`, `insufficient` and
`contradictory`, and fallback is `requires-review`. A non-null `resolved` value is an explicit
planner-declared deterministic result. It returns the local judgment before client construction or
budget effects. A sole eligible recovery choice with `resolved=None` remains consultable.

The new local judgment is exactly `{choice, confidence}`, where choice is the explicit resolved
value or policy fallback and confidence is `None`. The accepted judgment has the same keys, with an
eligible choice (or `defer` for bounded recovery) and finite numeric confidence from 0 through 1.
The outer and inner confidence values must match; booleans, nonfinite values and values outside
that range are invalid. Both new uses require confidence at least `0.8`, inclusive. Any refusal,
transport error, wrong model, malformed response or out-of-domain choice returns the exact local
judgment. New advice never clears a failed check, changes a correction count, grants permission or
supplies acceptance.

Only an explicitly declared extension may call either new use. Before sending, the caller must
classify the fragment and all outbound choice labels as public. Do not send task/scope identity,
paths, private or unknown material, sealed evidence or answers. Invalid policy is rejected by the
pure consumer before transport; the adapter returns local fallback for invalid policy or unavailable
budget. A deterministic resolution and an empty eligible set create no budget record and invoke
neither factory nor request. The existing adapter still owns consent, configuration and client
construction; the host-supplied factory keeps the pinned ten-second timeout and zero retries.

For a new use, `budget_scope` is the closed builtin dictionary
`{owner, identity, contract_sha256}`. The owner is a Task ID and the identity is stable across
sessions; it is not a Run ID. The digest is 64 lowercase hexadecimal characters. The adapter stores
the fixed limits and exact scope metadata under
`verification-records/<owner>/judgment-budget/<sha256(identity)>/`. Existing metadata must match;
unsafe links, malformed or mismatched files and unavailable storage fall back locally.

After consent, public-content, policy, client and SDK checks, create the per-use reservation
exclusively and write, flush and fsync it before invoking the client factory. One reservation file
per new use enforces at most one consultation each and two total across imports/processes. Never
rewrite, refund or reset a reservation. Every post-reservation outcome consumes its slot. Write a
separate exclusive terminal receipt with `known-unsent`, `observed-response` or `unknown` and a
reason. If interrupted or a `BaseException` escapes, keep the reservation without inventing a
receipt; after restart, a missing or truncated receipt remains consumed. A failed reservation
write permits no factory or send. A terminal-receipt failure returns local `budget-record-failure`
and never unlocks the slot. Optional telemetry is separate from reservation/receipt state: its
failure cannot fail the task, refund a slot or change an unknown request outcome.

<a id="system-one-functional-recipe"></a>
## The scripts

Both scripts are import-only modules with no command line. Insert `<skill>/scripts/` at the front of
`sys.path` and import them by name, under the [script consent rule](../../scripts/README.md#consent).

- [system_one_decide.py](../../scripts/system_one_decide.py) holds the pure decision consumer
  `system_one_decide(state, use, fragment, local_judgment, transport=None, *, support_policy=None)` described above. It
  imports only `math.isfinite` and returns the closed result.
- [system_one_state.py](../../scripts/system_one_state.py) holds the selected-workspace state and the
  SDK adapter, receiving `system_one_decide` as `decide` rather than copying its algorithm.

`load_state(workspace, configured, asked)` reads only the selected workspace's `AGENTS.md` and
`questions.md`; no parent or project consent is inherited. `record_consent(workspace, answer, actor, day)`
requires the owner's explicit answer, date and actor, refuses conflicts/malformed records, and preserves
unrelated text. `prepare_consent(workspace, configured, asked, mode, decide)` writes one pending question
only in PLAN/RUN. STATUS only reads and suppresses the prompt. The caller carries the returned `asked`
list through the session; a persisted pending question also prevents a duplicate across resumes.

`system_one_use(workspace, configured, asked, use, fragment, local_judgment, sensitivity, decide,
client_factory=None, *, support_policy=None, budget_scope=None)` returns the closed result. Before calling it, the caller must classify the minimal
fragment's sensitivity. Only a fragment admitted as public may be sent. Unknown, private, credential,
secret, sealed-case and answer-sheet material is forbidden; the label is an explicit caller obligation,
not an automatic secret detector. `client_factory` is the client constructor built under the host's
`typesafe-ai` skill; the script calls it with the pinned model, a ten-second timeout and zero retries,
and never constructs a client, names an endpoint or reads a key itself. Without `client_factory` the
result is the local judgment with reason `client-unavailable`: nothing is imported or sent. Missing
SDK/configuration/consent, malformed storage or unavailable transport produce a local result with a
named reason (`sdk-unavailable`, `malformed-consent`, `fragment-not-public` or a reason above). No
optional failure stops the user's task. Never retry an optional request or disable certificate
verification.

<a id="building-the-client"></a>
The client is `typesafe_sdk.TypeSafeClient`, from the SDK that the host's `typesafe-ai` skill documents.
Pass the class itself, uncalled, as `client_factory`. A factory must accept the keywords `model=`,
`timeout=` and `retry=`, because `system_one_state.py` calls it with exactly those; `TypeSafeClient`
accepts them as is. The SDK reads its own key from the environment; Tackle never reads, prints or passes
it. `workspace` is the selected workspace path, `asked` the session's list of workspaces already asked,
`sensitivity` exactly `"public"` for an admitted fragment, and `decide` is `system_one_decide`. The call
returns the closed result: with a recorded `yes`, a public fragment and an accepted answer, `source` is
`jev` and `reason` `accepted`, with the model and confidence; otherwise it is the local judgment with a
named reason. Without a factory the result is the local judgment with reason `client-unavailable`.

**Stop before the example below.** Import or run the scripts it names only with the owner's explicit
authorization for this use ([script consent](../../scripts/README.md#consent)).

```python
import sys
sys.path.insert(0, "<skill>/scripts")
try:
    from typesafe_sdk import TypeSafeClient
except ImportError:  # no SDK: the judgment stays local
    TypeSafeClient = None
from system_one_decide import system_one_decide
from system_one_state import system_one_use

result = system_one_use(workspace, True, asked, "failure-class", fragment, "implementation",
                        "public", system_one_decide, client_factory=TypeSafeClient)
```

The adapter constructs typed Score/Choice questions and sends only the fragment, pinned model and one
narrow question. Confidence defaults are inclusive: 0.6 for history, 0.8 otherwise. The optional SDK
stays owner-installed; Tackle never requests installation. Official SDK 0.7.2 is the pinned local
serializer check, using in-process MockTransport and fictitious authentication; it is no
live/provider or held-out evidence.

`select_history(entries, allowed_ids, score_entry)` receives only entries already admitted/opened under
the [cold-resume bound](status.md#cold-resume-read-order), plus their admitted ids. It makes no file
reads. Pass a `score_entry` closure calling `system_one_use` with use `resume-selection`, the entry
fragment/sensitivity and the agent's local score. Counts and open obligations bypass scoring and remain
visible. Report every returned signal's use, actual model/confidence, adopted decision or local reason;
optional classifications do not create evidence, consent or authority.

`intake_route(local_route, signal, modules, public_api, spans_sessions, handoff)` receives `local_route`
as the deterministic minimum from the complete
[installed gate](intake-and-gate.md#step-2--gate-sizing-full--lite--none), including every Coordinated
trigger and Direct eligibility condition. An optional answer can keep or raise this floor; it cannot
lower it. The four explicit Full triggers still force Coordinated. `no_progress_same(deterministic_same,
signal)` preserves an already matching deterministic signature; optional advice cannot erase the stop
or change/reset any counter. Failure-class choices are exactly the RUN card's classes and never assign
blame.
