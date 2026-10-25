import json
import hashlib
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


def _question(use, support_policy=None):
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
    if use == "bounded-recovery":
        return Choice(criteria={label: None for label in list(support_policy["eligible"]) + ["defer"]})
    if use == "evidence-signal":
        return Choice(criteria={label: None for label in support_policy["choices"]})
    raise ValueError("system-one-use")


def _normalized(response, use, support_policy=None):
    answer = response.answers["judgment"]
    confidence = answer.confidence
    if type(response.model) is not str or type(confidence) not in {float, int} or not isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("system-one-response")
    if use == "resume-selection":
        judgment = answer.score
        if answer.type != "score" or type(judgment) not in {float, int} or not isfinite(judgment) or not 0 <= judgment <= 1:
            raise ValueError("system-one-response")
    elif use in {"bounded-recovery", "evidence-signal"}:
        domain = (set(support_policy["eligible"]) | {"defer"} if use == "bounded-recovery"
                  else {"supports", "partial", "insufficient", "contradictory"})
        if answer.type != "choice" or type(answer.choice) is not str or answer.choice not in domain:
            raise ValueError("system-one-response")
        judgment = {"choice": answer.choice, "confidence": confidence}
    else:
        if answer.type != "choice" or type(answer.choice) is not str:
            raise ValueError("system-one-response")
        domains = {"failure-class": FAILURE_CLASSES, "no-progress": ("same", "different"),
                   "intake-size": ("Direct", "Focused", "Coordinated")}
        if answer.choice not in domains[use]:
            raise ValueError("system-one-response")
        judgment = answer.choice == "same" if use == "no-progress" else answer.choice
    return {"model": response.model, "confidence": confidence, "judgment": judgment}


def _canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _closed_scope(scope):
    return (type(scope) is dict and set(scope) == {"owner", "identity", "contract_sha256"}
            and all(type(scope[key]) is str and scope[key] for key in scope)
            and re.fullmatch(r"T-[A-Za-z0-9]+", scope["owner"]) is not None
            and re.fullmatch(r"[0-9a-f]{64}", scope["contract_sha256"]) is not None)


def _budget_dirs(workspace, scope):
    root = Path(workspace)
    parts = ["verification-records", scope["owner"], "judgment-budget",
             hashlib.sha256(scope["identity"].encode("utf-8")).hexdigest()]
    current = root
    for part in parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir(mode=0o700)
            except FileExistsError:
                pass
            try:
                metadata = current.lstat()
            except OSError:
                raise ValueError("system-one-budget-path")
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("system-one-budget-path")
    return current


def _read_budget_file(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as error:
        raise ValueError("system-one-budget-file") from error
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("system-one-budget-file")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            return stream.read()
    finally:
        os.close(fd)


def _exclusive_json(path, value, sync=True):
    data = _canonical(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("system-one-budget-file")
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short budget write")
            view = view[written:]
        if sync:
            os.fsync(fd)
    finally:
        os.close(fd)
    return data


def _reserve(workspace, scope, use, policy):
    directory = _budget_dirs(workspace, scope)
    scope_record = {"schema": "tackle-judgment-budget/1", "workspace": str(Path(workspace).resolve()),
                    "owner": scope["owner"], "identity": scope["identity"],
                    "contract_sha256": scope["contract_sha256"],
                    "limits": {"bounded-recovery": 1, "evidence-signal": 1}}
    scope_bytes = _canonical(scope_record)
    scope_path = directory / "scope.json"
    try:
        _exclusive_json(scope_path, scope_record)
    except FileExistsError:
        if _read_budget_file(scope_path) != scope_bytes:
            raise ValueError("system-one-budget-scope")
    reservation = {"scope_sha256": hashlib.sha256(scope_bytes).hexdigest(),
                   "policy_sha256": hashlib.sha256(_canonical(policy)).hexdigest(),
                   "use": use, "status": "reserved"}
    reservation_path = directory / (use + ".reservation.json")
    _exclusive_json(reservation_path, reservation)
    return directory


def _terminal(directory, use, status, reason):
    _exclusive_json(directory / (use + ".terminal.json"),
                    {"status": status, "reason": reason})


def _new_use(workspace, state, use, fragment, local_judgment, sensitivity, decide,
             client_factory, support_policy, budget_scope):
    try:
        result = decide(state, use, fragment, local_judgment, support_policy=support_policy)
    except (ValueError, TypeError):
        return {"judgment": local_judgment, "source": "local", "reason": "invalid-support-policy",
                "state": state, "question": None, "model": None, "confidence": None}
    if result["reason"] != "transport-unavailable":
        return result
    if type(sensitivity) is not str or sensitivity != "public":
        result["reason"] = "fragment-not-public"
        return result
    if client_factory is None:
        result["reason"] = "client-unavailable"
        return result
    if not _closed_scope(budget_scope):
        result["reason"] = "budget-unavailable"
        return result
    try:
        from typesafe_sdk import Choice, RetryPolicy, Score
    except ModuleNotFoundError:
        result["reason"] = "sdk-unavailable"
        return result
    try:
        directory = _reserve(workspace, budget_scope, use, support_policy)
    except (OSError, ValueError, TypeError):
        result["reason"] = "budget-unavailable"
        return result
    progress = {"status": "known-unsent", "reason": "client-construction-failed"}

    def transport(request):
        nonlocal progress
        progress = {"status": "unknown", "reason": "request-outcome-unknown"}
        client = client_factory(model=MODEL, timeout=10.0, retry=RetryPolicy(max_retries=0))
        try:
            response = client.system_one(state={"fragment": request["fragment"]},
                                         questions={"judgment": _question(use, support_policy)}, model=MODEL)
            progress = {"status": "observed-response", "reason": "response-received"}
            normalized = _normalized(response, use, support_policy)
        except BaseException:
            try:
                client.close()
            except Exception:
                pass
            raise
        else:
            client.close()
            return normalized

    result = decide(state, use, fragment, local_judgment, transport, support_policy=support_policy)
    try:
        _terminal(directory, use, progress["status"], progress["reason"])
    except (OSError, ValueError):
        result = dict(result, judgment=local_judgment, source="local", reason="budget-record-failure",
                      model=None, confidence=None)
    return result


def system_one_use(workspace, configured, asked, use, fragment, local_judgment,
                   sensitivity, decide, client_factory=None, *, support_policy=None, budget_scope=None):
    try:
        state, metadata = load_state(workspace, configured, asked)
    except (ValueError, OSError, UnicodeError):
        if use in {"bounded-recovery", "evidence-signal"}:
            try:
                selected = str(Path(workspace).resolve())
            except (OSError, ValueError, TypeError):
                selected = str(workspace)
            state = {"workspace": selected, "configured": configured, "consent": None,
                     "asked": list(asked)}
            return {"judgment": local_judgment, "source": "local", "reason": "malformed-consent",
                    "state": state, "question": None, "model": None, "confidence": None}
        return _unavailable(workspace, configured, asked, use, fragment,
                            local_judgment, decide, "malformed-consent")
    if use in {"bounded-recovery", "evidence-signal"}:
        if support_policy is None:
            return {"judgment": local_judgment, "source": "local", "reason": "invalid-support-policy",
                    "state": state, "question": None, "model": None, "confidence": None}
        return _new_use(workspace, state, use, fragment, local_judgment, sensitivity, decide,
                        client_factory, support_policy, budget_scope)
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
