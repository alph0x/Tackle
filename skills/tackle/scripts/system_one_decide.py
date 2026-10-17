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
