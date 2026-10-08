# Optional System One (JEV)

<a id="integration"></a>
## Integration contract

Use optional System One only when a configuration signal exists and the selected workspace has recorded `yes`. Never ask the user to install TypeSafe/JEV. The [integration recipe](../recipes/system-one.md) provides actual shell detection, selected-workspace storage and the SDK adapter. Saving or running these recipes needs the owner's explicit authorization under the [recipe consent rule](../recipes/README.md#consent); the recorded `yes` grants it for that use only.

Detect only environment-key presence, installed SDK/skill, or the case-insensitive phrase `TypeSafe System One` in project-root AGENTS/CLAUDE or selected-workspace AGENTS. Never read, print or send credential values or open credential files. A configuration signal cannot grant consent.

Record the owner's explicit `yes` or `no`, date and actor in that workspace's AGENTS. Do not inherit an answer from another workspace. In PLAN/RUN ask once, retain an unanswered question in questions.md and never repeat it during the session or after an answer; read-only STATUS only detects/reads and never starts or mutates this workflow. Malformed/conflicting records cannot authorize a send.

Send only admitted public fragments needed by one of four uses: older-history score, RUN failure-class choice, no-progress signature comparison, or Direct/Focused/Coordinated intake. Never send credentials, secrets, unknown/private fragments, sealed material or answer sheets. The agent must classify sensitivity before calling the adapter; this is no general secret detector.

Keep the cold-resume opened-history bound, spent counts and open obligations. Skip an unprotected entry only at score<0.5 and confidence>=0.6. Other uses need confidence>=0.8. Preserve the complete installed gate's deterministic minimum route, risk precedence and no-progress stops/counters; JEV never supplies authority or assigns blame. Report the actual use, model, confidence, adopted decision or local fallback reason. After a configuration signal, record each call and each local fallback as one [sidecar](usage-observability.md) record with `collector: system-one`. Use `scope: role` and the calling role's Run ID as `run_id`; without a Run ID, use `scope: session` and `run_id: n/a`. A Direct request has no workspace and writes no record. The record's metrics hold `requests` and, when the response reports them, token counts. `requests` is 1 when a request was sent and 0 when the fallback came before any send. The record's `provenance` holds the use, model, confidence and adopted decision or fallback reason. With a recorded `yes`, consult System One at every point where one of the four uses applies: each failure classification, each no-progress comparison, each cold-resume history choice and each intake sizing. Each consult keeps the thresholds and fallbacks above. A point with no admitted public fragment is a skipped point. Record a skipped point with its reason. Read-only STATUS makes no call and writes no record. A missing sidecar or a failed record write never fails the task.

Pin `jev-1.13.0`; refuse another response model or malformed/out-of-domain answer. SDK handles authentication through its configured owner environment. Use its verified TLS defaults, trusted endpoint, timeout and zero retries. Absent SDK/signal/recorded yes, low confidence, refusal or any ordinary transport error falls back to the agent's judgment without stopping the task; BaseException propagates. Never disable certificate verification or request installation.

The installed artifact remains Markdown-only SKILL+references. Native shell/file/SDK-mock checks prove their encoded integration cases; agent behavior, live service availability and held-out safety/release evidence remain separate obligations.

## Pure decision consumer

The caller supplies `system_one_decide(state, use, fragment, local_judgment,
transport=None)`. `state` is a closed builtin dictionary with a nonempty
`workspace` string, a real boolean `configured`, `consent` and `asked`. Consent is
`None` or a closed builtin dictionary containing a nonempty `workspace` and
`answer` (`yes` or `no`). `asked` is a builtin list of unique nonempty workspace
strings. The returned state preserves these entries in independent containers;
the caller owns its persistence into the selected workspace.

`configured` represents an already supplied configuration signal. Missing or
foreign-workspace consent is unanswered: the recipe returns one fixed question
per workspace and keeps the local judgment. Recorded `no` returns locally without
a question or call. A recorded `yes` authorizes only its exact workspace. With no
configuration, the recipe returns locally without a question or call. It validates
every caller input before any of these effects and raises
`ValueError("system_one_input")` for malformed input, even without configuration.

The four uses are `resume-selection`, `failure-class`, `no-progress` and
`intake-size`. A fragment is a nonempty public string selected by the caller;
its sensitivity is a separate caller obligation. A supplied in-process callable
receives exactly `model`, `use` and `fragment` with model `jev-1.13.0`, and returns
exactly `model`, `confidence` and `judgment`. These normalized dictionaries are
not the TypeSafe wire protocol. The separate integration recipe supplies the
actual adapter; this pure block performs no environment, filesystem or network
operation. Behavior of a third-party callable is outside this pure block's proof.

Judgments use only exact builtin strings, booleans, integers, finite floats,
lists, dictionaries with string keys and `None`. Container cycles, subclasses,
tuples, custom objects and nonfinite numbers are invalid; shared acyclic
containers are valid. The recipe validates nested judgments iteratively and
changes neither inputs nor transport responses.

The reference confidence minimum is `0.6` for `resume-selection` and `0.8` for the
other uses, inclusive at the boundary. These are conservative source-recipe
defaults, not provider calibration. Malformed responses, another model, insufficient
confidence, absent transport or an ordinary transport `Exception` return the exact
local judgment with a distinct fixed reason. A supplied transport is attempted at
most once. `BaseException` propagates. There is no retry.

The closed result has `judgment`, `source`, `reason`, `state`, `question`, `model`
and `confidence`. Acceptance records source `jev`, reason `accepted`, the actual
accepted model `jev-1.13.0` and its observed numeric confidence. Every local result
records model/confidence as `None`. Local reasons are `not-configured`,
`consent-unanswered`, `consent-no`, `transport-unavailable`, `transport-failure`,
`malformed-response`, `wrong-model` or `low-confidence`.

History selection retains its score rule: an entry is skipped only below `0.5`
with confidence at least `0.6`. The existing context bound, open obligations and
spent counts remain. This generic function does not select or drop history.
Detection, persisted consent and SDK serialization belong to the separate
integration consumer; agent compliance remains an independent evidence obligation.
Source-level tests do not establish held-out safety behavior, complete optional
capability readiness or release acceptance.

The sole Python block below is the reference consumer. Functional tests extract
this block into a fresh namespace; they do not copy the decision algorithm.

<a id="system-one-functional-recipe"></a>
```python
from math import isfinite


def _system_one_json(value):
    # Iterative DFS distinguishes sharing from an ancestor cycle.
    active = set()
    completed = set()
    pending = [(False, value)]
    while pending:
        leaving, current = pending.pop()
        kind = type(current)
        if kind is list or kind is dict:
            identity = id(current)
            if leaving:
                active.remove(identity)
                completed.add(identity)
                continue
            if identity in active:
                return False
            if identity in completed:
                continue
            if kind is dict and any(type(key) is not str for key in current):
                return False
            active.add(identity)
            pending.append((True, current))
            values = current.values() if kind is dict else current
            pending.extend((False, item) for item in values)
        elif current is None or kind is str or kind is bool or kind is int:
            continue
        elif kind is float and isfinite(current):
            continue
        else:
            return False
    return True


def _system_one_state_valid(state):
    if type(state) is not dict:
        return False
    if any(type(key) is not str for key in state):
        return False
    if set(state) != {"workspace", "configured", "consent", "asked"}:
        return False
    if type(state["workspace"]) is not str or not state["workspace"]:
        return False
    if type(state["configured"]) is not bool:
        return False
    asked = state["asked"]
    if type(asked) is not list:
        return False
    if any(type(item) is not str or not item for item in asked):
        return False
    if len(asked) != len(set(asked)):
        return False
    consent = state["consent"]
    if consent is None:
        return True
    if type(consent) is not dict:
        return False
    if any(type(key) is not str for key in consent):
        return False
    if set(consent) != {"workspace", "answer"}:
        return False
    return (type(consent["workspace"]) is str and bool(consent["workspace"])
            and type(consent["answer"]) is str
            and consent["answer"] in {"yes", "no"})


def system_one_decide(state, use, fragment, local_judgment, transport=None):
    uses = {"resume-selection", "failure-class", "no-progress", "intake-size"}
    if (not _system_one_state_valid(state)
            or type(use) is not str or use not in uses
            or type(fragment) is not str or not fragment
            or not _system_one_json(local_judgment)
            or (transport is not None and not callable(transport))):
        raise ValueError("system_one_input")

    workspace = state["workspace"]
    consent = state["consent"]
    next_state = {
        "workspace": workspace,
        "configured": state["configured"],
        "consent": None if consent is None else dict(consent),
        "asked": list(state["asked"]),
    }

    def local(reason, question=None):
        return {"judgment": local_judgment, "source": "local", "reason": reason,
                "state": next_state, "question": question,
                "model": None, "confidence": None}

    if not state["configured"]:
        return local("not-configured")
    answered = consent is not None and consent["workspace"] == workspace
    if not answered:
        question = None
        if workspace not in next_state["asked"]:
            next_state["asked"].append(workspace)
            question = "Use optional System One for workspace " + workspace + "? (yes/no)"
        return local("consent-unanswered", question)
    if consent["answer"] == "no":
        return local("consent-no")
    if transport is None:
        return local("transport-unavailable")

    request = {"model": "jev-1.13.0", "use": use, "fragment": fragment}
    try:
        response = transport(request)
    except Exception:
        return local("transport-failure")

    if type(response) is not dict:
        return local("malformed-response")
    if any(type(key) is not str for key in response):
        return local("malformed-response")
    if set(response) != {"model", "confidence", "judgment"}:
        return local("malformed-response")
    confidence = response["confidence"]
    if (type(response["model"]) is not str
            or not _system_one_json(response["judgment"])
            or type(confidence) not in {int, float}
            or not 0 <= confidence <= 1
            or (type(confidence) is float and not isfinite(confidence))):
        return local("malformed-response")
    if response["model"] != "jev-1.13.0":
        return local("wrong-model")
    minimum = 0.6 if use == "resume-selection" else 0.8
    if confidence < minimum:
        return local("low-confidence")
    return {"judgment": response["judgment"], "source": "jev", "reason": "accepted",
            "state": next_state, "question": None,
            "model": response["model"], "confidence": confidence}
```
