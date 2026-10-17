import json
import os
from pathlib import Path
import re
import stat
import tempfile
from datetime import date
from math import isfinite


MODEL = "jev-1.13.0"
FAILURE_CLASSES = (
    "implementation", "missing or ambiguous requirement", "incomplete output",
    "required edge case", "dependency or integration", "contradictory spec",
    "validator", "environment", "capability", "undetermined",
)
CONSENT = re.compile(r'^System One consent: (yes|no) · date=(\d{4}-\d{2}-\d{2}) · actor=(.+)$')
PENDING = "[system-one-consent]"


def _workspace(workspace):
    path = Path(workspace).resolve(strict=True)
    if not path.is_dir():
        raise ValueError("system-one-workspace")
    return path


def _read(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return ""
    except OSError as error:
        raise ValueError("system-one-storage") from error
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("system-one-storage")
        with os.fdopen(fd, "r", encoding="utf-8", closefd=False) as stream:
            return stream.read()
    finally:
        os.close(fd)


def _write(path, text):
    # Refuse nonregular targets before atomic replacement; leave other files alone.
    _read(path)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=".system-one-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(text)
    try:
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _consent(text):
    lines = [line for line in text.splitlines() if line.startswith("System One consent")]
    if not lines:
        return None
    if len(lines) != 1:
        raise ValueError("system-one-consent")
    match = CONSENT.fullmatch(lines[0])
    if not match:
        raise ValueError("system-one-consent")
    answer, day, raw_actor = match.groups()
    try:
        actor = json.loads(raw_actor)
        if date.fromisoformat(day).isoformat() != day or type(actor) is not str or not actor.strip():
            raise ValueError("system-one-consent")
    except (ValueError, TypeError) as error:
        raise ValueError("system-one-consent") from error
    return {"answer": answer, "date": day, "actor": actor}


def _pending(text):
    lines = [line for line in text.splitlines() if PENDING in line]
    if len(lines) > 1 or (lines and not lines[0].startswith("- Open " + PENDING + " ")):
        raise ValueError("system-one-question")
    return bool(lines)


def load_state(workspace, configured, asked):
    path = _workspace(workspace)
    consent = _consent(_read(path / "AGENTS.md"))
    pending = _pending(_read(path / "questions.md"))
    state = {"workspace": str(path), "configured": configured, "consent": None,
             "asked": list(asked)}
    if consent is not None:
        state["consent"] = {"workspace": str(path), "answer": consent["answer"]}
    if pending and str(path) not in state["asked"]:
        state["asked"].append(str(path))
    return state, consent


def record_consent(workspace, answer, actor, day):
    if answer not in {"yes", "no"} or type(actor) is not str or not actor.strip():
        raise ValueError("system-one-answer")
    if type(day) is not str or date.fromisoformat(day).isoformat() != day:
        raise ValueError("system-one-date")
    path = _workspace(workspace)
    agents = _read(path / "AGENTS.md")
    questions = _read(path / "questions.md")
    _pending(questions)
    prior = _consent(agents)
    if prior is not None and prior["answer"] != answer:
        raise ValueError("system-one-conflict")
    if prior is None:
        line = f"System One consent: {answer} · date={day} · actor={json.dumps(actor, ensure_ascii=False)}\n"
        _write(path / "AGENTS.md", agents + ("\n" if agents and not agents.endswith("\n") else "") + line)
        prior = {"answer": answer, "date": day, "actor": actor}
    if _pending(questions):
        _write(path / "questions.md", "".join(line for line in questions.splitlines(keepends=True) if PENDING not in line))
    return prior


def _unavailable(workspace, configured, asked, use, fragment, local_judgment, decide, reason):
    state = {"workspace": str(Path(workspace).resolve()), "configured": configured,
             "consent": None, "asked": list(asked)}
    result = decide(state, use, fragment, local_judgment)
    result.update(reason=reason, question=None, state=state)
    return result


def prepare_consent(workspace, configured, asked, mode, decide):
    if mode not in {"PLAN", "RUN", "STATUS"}:
        raise ValueError("system-one-mode")
    try:
        state, metadata = load_state(workspace, configured, asked)
        result = decide(state, "failure-class", "Public consent preparation", "undetermined")
        if mode == "STATUS":
            result["question"] = None
            result["state"] = state
        elif result["question"] is not None:
            path = _workspace(workspace) / "questions.md"
            text = _read(path)
            _write(path, text + ("\n" if text and not text.endswith("\n") else "")
                   + "- Open " + PENDING + " " + result["question"] + "\n")
        return result
    except (ValueError, OSError, UnicodeError):
        return _unavailable(workspace, configured, asked, "failure-class",
                            "Public consent preparation", "undetermined", decide, "malformed-consent")


def _question(use):
    from typesafe_sdk import Choice, Score
    if use == "resume-selection":
        return Score(criteria=["Not needed to resume this work", "Needed to resume this work"])
    if use == "failure-class":
        return Choice(criteria={label: None for label in FAILURE_CLASSES})
    if use == "no-progress":
        return Choice(instructions="Do these two observations share the normalized no-progress signature?",
                      criteria={"same": "Same command, class, failing assertion and normalized output",
                                "different": "At least one of those signature fields differs"})
    if use == "intake-size":
        return Choice(criteria={"Direct": "Bounded local edit", "Focused": "Bounded single-session task",
                                "Coordinated": "Cross-module, public API, multiple sessions or coordination"})
    raise ValueError("system-one-use")


def _normalized(response, use):
    answer = response.answers["judgment"]
    confidence = answer.confidence
    if type(response.model) is not str or type(confidence) not in {float, int} or not isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("system-one-response")
    if use == "resume-selection":
        judgment = answer.score
        if answer.type != "score" or type(judgment) not in {float, int} or not isfinite(judgment) or not 0 <= judgment <= 1:
            raise ValueError("system-one-response")
    else:
        if answer.type != "choice" or type(answer.choice) is not str:
            raise ValueError("system-one-response")
        domains = {"failure-class": FAILURE_CLASSES, "no-progress": ("same", "different"),
                   "intake-size": ("Direct", "Focused", "Coordinated")}
        if answer.choice not in domains[use]:
            raise ValueError("system-one-response")
        judgment = answer.choice == "same" if use == "no-progress" else answer.choice
    return {"model": response.model, "confidence": confidence, "judgment": judgment}


def system_one_use(workspace, configured, asked, use, fragment, local_judgment,
                   sensitivity, decide, client_factory=None):
    try:
        state, metadata = load_state(workspace, configured, asked)
    except (ValueError, OSError, UnicodeError):
        return _unavailable(workspace, configured, asked, use, fragment,
                            local_judgment, decide, "malformed-consent")
    result = decide(state, use, fragment, local_judgment)
    if result["reason"] != "transport-unavailable":
        return result
    if type(sensitivity) is not str or sensitivity != "public":
        result["reason"] = "fragment-not-public"
        return result
    if client_factory is None:
        result["reason"] = "client-unavailable"
        return result
    issue = []
    def transport(request):
        try:
            from typesafe_sdk import RetryPolicy
            client = client_factory(model=MODEL, timeout=10.0, retry=RetryPolicy(max_retries=0))
        except ModuleNotFoundError:
            issue.append("sdk-unavailable")
            raise
        try:
            response = client.system_one(state={"fragment": request["fragment"]},
                                         questions={"judgment": _question(use)}, model=MODEL)
            normalized = _normalized(response, use)
        except BaseException:
            try:
                client.close()
            except Exception:
                pass
            raise
        else:
            client.close()
            return normalized
    result = decide(state, use, fragment, local_judgment, transport)
    if issue:
        result["reason"] = issue[0]
    return result


def select_history(entries, allowed_ids, score_entry):
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)) or not set(ids) <= allowed_ids:
        raise ValueError("system-one-history-bound")
    for entry in entries:
        if (type(entry["spent_count"]) is not int or entry["spent_count"] < 0
                or type(entry["open_obligations"]) is not list):
            raise ValueError("system-one-history-entry")
    kept = []
    for entry in entries:
        if entry["spent_count"] > 0 or entry["open_obligations"]:
            kept.append(entry)
            continue
        signal = score_entry(entry)
        score, confidence = signal.get("judgment"), signal.get("confidence")
        skip = (signal.get("source") == "jev" and signal.get("model") == MODEL
                and type(score) in {float, int} and isfinite(score) and 0 <= score < 0.5
                and type(confidence) in {float, int} and isfinite(confidence) and 0.6 <= confidence <= 1)
        if not skip:
            kept.append(entry)
    return kept


def _usable_signal(signal):
    confidence = signal.get("confidence")
    return (signal.get("source") == "jev" and signal.get("model") == MODEL
            and signal.get("reason") == "accepted" and type(confidence) in {int, float}
            and isfinite(confidence) and 0.8 <= confidence <= 1)


def intake_route(local_route, signal, modules, public_api, spans_sessions, handoff):
    routes = ("Direct", "Focused", "Coordinated")
    if local_route not in routes:
        raise ValueError("system-one-route")
    if modules >= 2 or public_api or spans_sessions or handoff:
        return "Coordinated"
    recommendation = signal.get("judgment")
    if (_usable_signal(signal) and recommendation in routes
            and routes.index(recommendation) >= routes.index(local_route)):
        return recommendation
    return local_route


def no_progress_same(deterministic_same, signal):
    return deterministic_same or (_usable_signal(signal) and signal.get("judgment") is True)
