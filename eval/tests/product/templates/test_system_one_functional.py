"""Functional consumer of the public Markdown System One reference recipe."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]
GUIDE = ROOT / "skills/tackle/references/guides/system-one.md"
ANCHOR = '<a id="system-one-functional-recipe"></a>\n```python\n'
RESULT_KEYS = {"judgment", "source", "reason", "state", "question", "model", "confidence"}
THRESHOLDS = {"resume-selection": 0.6, "failure-class": 0.8,
              "no-progress": 0.8, "intake-size": 0.8}


def recipe_source():
    text = GUIDE.read_text(encoding="utf-8")
    assert text.count('id="system-one-functional-recipe"') == 1
    assert text.count("```python\n") == 1
    assert text.count(ANCHOR) == 1, "anchor immediately precedes the sole Python block"
    tail = text.split(ANCHOR)[1]
    assert tail.count("\n```") == 1
    return tail.split("\n```")[0]


def load_recipe(source=None):
    source = recipe_source() if source is None else source
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            raise AssertionError("recipe uses only the admitted math.isfinite import")
        if isinstance(node, ast.ImportFrom):
            assert node.module == "math" and node.level == 0
            assert [(alias.name, alias.asname) for alias in node.names] == [("isfinite", None)]
        if isinstance(node, ast.Name):
            assert node.id not in {"open", "eval", "exec", "__import__", "input"}
    namespace = {"__name__": "system_one_reference"}
    exec(compile(source, str(GUIDE), "exec"), namespace)
    assert callable(namespace["system_one_decide"])
    return namespace["system_one_decide"]


def snapshot(value):
    """Capture container contents and aliases without recursion, even for bad inputs."""
    seen = {}
    pending = []
    rows = []

    def link(item):
        if isinstance(item, (dict, list, tuple)):
            identity = id(item)
            if identity not in seen:
                seen[identity] = len(seen)
                pending.append(item)
            return ("container", seen[identity])
        if type(item) in {str, int, float, bool, type(None)}:
            return (type(item).__name__, repr(item))
        return ("opaque", type(item).__name__, id(item))

    head = link(value)
    while pending:
        current = pending.pop(0)
        if isinstance(current, dict):
            contents = tuple((link(key), link(item)) for key, item in current.items())
        else:
            contents = tuple(link(item) for item in current)
        rows.append((seen[id(current)], type(current).__name__, contents))
    return head, tuple(rows)


def state(configured=True, consent="yes", workspace="public-work", asked=None):
    return {"workspace": workspace, "configured": configured,
            "consent": None if consent is None else {"workspace": workspace, "answer": consent},
            "asked": [] if asked is None else list(asked)}


def response(confidence=0.9, model="jev-1.13.0", judgment=None):
    return {"model": model, "confidence": confidence,
            "judgment": {"task": "public-task", "choice": "continue"} if judgment is None else judgment}


class CallSpy:
    def __init__(self, answer=None, error=None):
        self.answer = response() if answer is None else answer
        self.error = error
        self.calls = []

    def __call__(self, request):
        self.calls.append(snapshot(request))
        if self.error is not None:
            raise self.error
        return self.answer


class CustomString(str):
    pass


class CustomInt(int):
    pass


class CustomFloat(float):
    pass


class CustomList(list):
    pass


class CustomDict(dict):
    pass


class SystemOneFunctionalTests(unittest.TestCase):
    def assert_local(self, result, local, reason, expected_state, question=None):
        self.assertIs(type(result), dict)
        self.assertEqual(set(result), RESULT_KEYS)
        self.assertIs(result["judgment"], local)
        self.assertEqual(result["source"], "local")
        self.assertEqual(result["reason"], reason)
        self.assertEqual(result["state"], expected_state)
        self.assertIsNot(result["state"], expected_state)
        self.assertEqual(result["question"], question)
        self.assertIsNone(result["model"])
        self.assertIsNone(result["confidence"])

    def assert_accepted(self, result, observed, expected_state):
        self.assertIs(type(result), dict)
        self.assertEqual(set(result), RESULT_KEYS)
        self.assertIs(result["judgment"], observed["judgment"])
        self.assertEqual(result["source"], "jev")
        self.assertEqual(result["reason"], "accepted")
        self.assertEqual(result["state"], expected_state)
        self.assertIsNot(result["state"], expected_state)
        self.assertIsNone(result["question"])
        self.assertEqual(result["model"], "jev-1.13.0")
        self.assertEqual(result["confidence"], observed["confidence"])
        self.assertIs(type(result["confidence"]), type(observed["confidence"]))

    def assert_same_workspace_accepts(self, decide):
        original = state(workspace="workspace-B")
        answer = response(confidence=0.91)
        spy = CallSpy(answer)
        result = decide(original, "intake-size", "Public task list B", {"size": "Focused"}, spy)
        self.assert_accepted(result, answer, original)
        self.assertEqual(len(spy.calls), 1)

    def assert_foreign_consent(self, decide):
        original = state(workspace="workspace-B")
        original["consent"]["workspace"] = "workspace-A"
        local = {"size": "Direct"}
        spy = CallSpy()
        before = snapshot((original, local, spy.answer))
        result = decide(original, "intake-size", "Public task list B", local, spy)
        expected = state(consent=None, workspace="workspace-B", asked=["workspace-B"])
        expected["consent"] = {"workspace": "workspace-A", "answer": "yes"}
        self.assertEqual(len(spy.calls), 0)
        self.assert_local(result, local, "consent-unanswered", expected,
                          "Use optional System One for workspace workspace-B? (yes/no)")
        self.assertEqual(snapshot((original, local, spy.answer)), before)

    def assert_below_threshold(self, decide, use="resume-selection"):
        original = state()
        local = {"choice": "keep"}
        answer = response(confidence=THRESHOLDS[use] - 0.000001)
        spy = CallSpy(answer)
        result = decide(original, use, "Public task list", local, spy)
        self.assert_local(result, local, "low-confidence", original)
        self.assertEqual(len(spy.calls), 1)

    def assert_at_threshold(self, decide, use="resume-selection"):
        original = state()
        answer = response(confidence=THRESHOLDS[use])
        spy = CallSpy(answer)
        result = decide(original, use, "Public task list", {"choice": "keep"}, spy)
        self.assert_accepted(result, answer, original)
        self.assertEqual(len(spy.calls), 1)

    def test_recipe_extraction_is_unique_and_pure(self):
        source = recipe_source()
        tree = ast.parse(source)
        self.assertEqual(sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                             and node.name == "system_one_decide" for node in ast.walk(tree)), 1)
        first, second = load_recipe(), load_recipe()
        self.assertIsNot(first.__globals__, second.__globals__)
        self.assertNotIn("open", first.__globals__)
        self.assertNotIn("os", first.__globals__)
        self.assertNotIn("requests", first.__globals__)

    def test_no_configuration_preserves_local_and_inputs(self):
        for consent in (None, "yes", "no"):
            with self.subTest(consent=consent):
                original = state(configured=False, consent=consent, asked=["earlier-work"])
                local = {"task": {"labels": ["public", 2, True, None, 0.5]}}
                spy = CallSpy()
                before = snapshot((original, local, spy.answer))
                result = load_recipe()(original, "intake-size", "Public task list", local, spy)
                self.assert_local(result, local, "not-configured", original)
                self.assertEqual(spy.calls, [])
                self.assertEqual(snapshot((original, local, spy.answer)), before)
                self.assert_same_workspace_accepts(load_recipe())

    def test_unanswered_consent_asks_once_per_workspace(self):
        for foreign_answer in (None, "yes", "no"):
            with self.subTest(foreign_answer=foreign_answer):
                original = state(consent=None, workspace="workspace-B", asked=["workspace-A"])
                if foreign_answer is not None:
                    original["consent"] = {"workspace": "workspace-A", "answer": foreign_answer}
                local = {"size": "Direct"}
                spy = CallSpy()
                before = snapshot(original)
                first = load_recipe()(original, "intake-size", "Public list", local, spy)
                expected = dict(original, asked=["workspace-A", "workspace-B"])
                self.assert_local(first, local, "consent-unanswered", expected,
                                  "Use optional System One for workspace workspace-B? (yes/no)")
                second = load_recipe()(first["state"], "intake-size", "Public list", local, spy)
                self.assert_local(second, local, "consent-unanswered", first["state"])
                third_state = dict(second["state"], workspace="workspace-C")
                third = load_recipe()(third_state, "intake-size", "Public list C", local, spy)
                third_expected = dict(third_state, asked=["workspace-A", "workspace-B", "workspace-C"])
                self.assert_local(third, local, "consent-unanswered", third_expected,
                                  "Use optional System One for workspace workspace-C? (yes/no)")
                self.assertEqual(spy.calls, [])
                self.assertEqual(snapshot(original), before)
                self.assert_same_workspace_accepts(load_recipe())

    def test_recorded_no_does_not_ask_or_send(self):
        original, local, spy = state(consent="no"), {"size": "Direct"}, CallSpy()
        before = snapshot(original)
        first = load_recipe()(original, "intake-size", "Public list", local, spy)
        self.assert_local(first, local, "consent-no", original)
        second = load_recipe()(first["state"], "intake-size", "Public list", local, spy)
        self.assert_local(second, local, "consent-no", first["state"])
        self.assertEqual(spy.calls, [])
        self.assertEqual(snapshot(original), before)
        self.assert_same_workspace_accepts(load_recipe())

    def test_foreign_consent_requires_exact_workspace(self):
        self.assert_foreign_consent(load_recipe())
        self.assert_same_workspace_accepts(load_recipe())

    def test_normalized_payload_varies_with_each_use_and_fragment(self):
        for use in THRESHOLDS:
            for fragment in ("Public task alpha: continue", "Public task beta: inspect"):
                with self.subTest(use=use, fragment=fragment):
                    original, local = state(asked=["previous"]), {"choice": "keep"}
                    answer = response(confidence=0.83456789)
                    spy = CallSpy(answer)
                    before = snapshot((original, fragment, local, answer))
                    result = load_recipe()(original, use, fragment, local, spy)
                    self.assertEqual(spy.calls, [snapshot({"model": "jev-1.13.0", "use": use,
                                                          "fragment": fragment})])
                    self.assert_accepted(result, answer, original)
                    self.assertEqual(snapshot((original, fragment, local, answer)), before)

    def test_transport_unavailable_and_exception_fall_back_without_retry(self):
        original, local = state(), {"choice": "keep"}
        result = load_recipe()(original, "failure-class", "Public failure", local)
        self.assert_local(result, local, "transport-unavailable", original)
        for error in (Exception("unavailable"), RuntimeError("failure"), ValueError("error")):
            with self.subTest(error=type(error).__name__):
                spy = CallSpy(error=error)
                before = snapshot((original, local, spy.answer))
                result = load_recipe()(original, "failure-class", "Public failure", local, spy)
                self.assert_local(result, local, "transport-failure", original)
                self.assertEqual(len(spy.calls), 1)
                self.assertEqual(snapshot((original, local, spy.answer)), before)
                self.assert_same_workspace_accepts(load_recipe())

    def test_baseexception_propagates_without_retry(self):
        for error in (KeyboardInterrupt("interrupt"), SystemExit("stop"), BaseException("halt")):
            with self.subTest(error=type(error).__name__):
                original, local, spy = state(), {"choice": "keep"}, CallSpy(error=error)
                before = snapshot((original, local, spy.answer))
                with self.assertRaises(type(error)) as caught:
                    load_recipe()(original, "failure-class", "Public failure", local, spy)
                self.assertIs(caught.exception, error)
                self.assertEqual(len(spy.calls), 1)
                self.assertEqual(snapshot((original, local, spy.answer)), before)
                self.assert_same_workspace_accepts(load_recipe())

    def test_threshold_boundaries_and_actual_provenance_for_every_use(self):
        for use in THRESHOLDS:
            with self.subTest(use=use):
                self.assert_below_threshold(load_recipe(), use)
                self.assert_at_threshold(load_recipe(), use)
                for confidence in (0, 1, 1.0, 0.99999):
                    original, local = state(), {"choice": "keep"}
                    answer, spy = response(confidence=confidence), None
                    spy = CallSpy(answer)
                    result = load_recipe()(original, use, "Public task", local, spy)
                    if confidence == 0:
                        self.assert_local(result, local, "low-confidence", original)
                    else:
                        self.assert_accepted(result, answer, original)
                    self.assertEqual(len(spy.calls), 1)

    def test_malformed_response_matrix_uses_local_fallback(self):
        cycle = []
        cycle.append(cycle)
        bad_responses = [None, [], (), "answer", CustomDict(response()), {},
                         {"confidence": 0.9, "judgment": "continue"},
                         dict(response(), extra=True),
                         {1: "model", "confidence": 0.9, "judgment": "continue"}]
        bad_responses += [dict(response(), model=value)
                          for value in (None, 7, True, CustomString("jev-1.13.0"))]
        bad_responses += [dict(response(), confidence=value)
                          for value in (None, True, False, "0.9", (), float("nan"),
                                        float("inf"), -float("inf"), -0.1, 1.1,
                                        CustomInt(1), CustomFloat(0.9))]
        bad_responses += [dict(response(), judgment=value)
                          for value in ((), object(), cycle, {1: "bad-key"},
                                        {"nested": [float("nan")]}, CustomList([1]),
                                        {"nested": [CustomString("public")]})]
        bad_responses += [dict(response(model="other-model"), confidence=True)]
        for index, bad in enumerate(bad_responses):
            with self.subTest(response=index):
                original, local = state(), {"choice": "keep", "notes": ["public"]}
                spy = CallSpy()
                spy.answer = bad
                before = snapshot((original, local, bad))
                result = load_recipe()(original, "intake-size", "Public list", local, spy)
                self.assert_local(result, local, "malformed-response", original)
                self.assertEqual(len(spy.calls), 1)
                self.assertEqual(snapshot((original, local, bad)), before)
                self.assert_same_workspace_accepts(load_recipe())

    def test_invalid_caller_matrix_is_admitted_before_all_effects(self):
        cycle = []
        cycle.append(cycle)
        dict_cycle = {}
        dict_cycle["self"] = dict_cycle
        cases = []
        for key in ("workspace", "configured", "consent", "asked"):
            cases.append(("missing-" + key, lambda args, key=key: args["state"].pop(key)))
        cases.append(("extra-state", lambda args: args["state"].update(extra=True)))
        for value in (None, [], (), CustomDict(state())):
            cases.append(("state-type-" + type(value).__name__,
                          lambda args, value=value: args.update(state=value)))
        for field, values in (
            ("workspace", ("", None, 7, True, CustomString("public-work"))),
            ("configured", (None, 0, 1, "yes")),
            ("asked", (None, (), ["same", "same"], [""], [7], [CustomString("work")], CustomList([]))),
            ("consent", (False, "yes", [], CustomDict({"workspace": "public-work", "answer": "yes"}),
                         {}, {"workspace": "public-work"}, {"answer": "yes"},
                         {"workspace": "public-work", "answer": "yes", "extra": True},
                         {"workspace": "", "answer": "yes"},
                         {"workspace": 1, "answer": "yes"},
                         {"workspace": CustomString("public-work"), "answer": "yes"},
                         {"workspace": "public-work", "answer": "maybe"},
                         {"workspace": "public-work", "answer": True},
                         {"workspace": "public-work", "answer": CustomString("yes")}))):
            for index, value in enumerate(values):
                cases.append((field + "-" + str(index),
                              lambda args, field=field, value=value: args["state"].update({field: value})))
        for field, values in (
            ("use", ("unknown", "", None, 2, CustomString("intake-size"))),
            ("fragment", ("", None, 2, CustomString("Public list"))),
            ("local_judgment", ((), object(), cycle, dict_cycle, {1: "bad"},
                                {"nested": [float("nan")]}, float("inf"), -float("inf"),
                                CustomInt(1), CustomFloat(0.9), CustomList([]),
                                CustomDict({}), {"nested": [CustomString("public")]})),
            ("transport", (0, False, "call", object()))):
            for index, value in enumerate(values):
                cases.append((field + "-" + str(index),
                              lambda args, field=field, value=value: args.update({field: value})))
        for configured, consent, good_reason in ((False, "yes", "not-configured"),
                                                 (True, None, "consent-unanswered"),
                                                 (True, "yes", "accepted")):
            for label, patch in cases:
                with self.subTest(branch=good_reason, invalid=label):
                    spy = CallSpy()
                    args = {"state": state(configured=configured, consent=consent),
                            "use": "intake-size", "fragment": "Public list",
                            "local_judgment": {"size": "Direct"}, "transport": spy}
                    patch(args)
                    before = snapshot(args)
                    with self.assertRaises(ValueError) as caught:
                        load_recipe()(**args)
                    self.assertIs(type(caught.exception), ValueError)
                    self.assertEqual(caught.exception.args, ("system_one_input",))
                    self.assertEqual(spy.calls, [])
                    self.assertEqual(snapshot(args), before)
                    good_state = state(configured=configured, consent=consent)
                    good_local, good_spy = {"size": "Direct"}, CallSpy()
                    good = load_recipe()(good_state, "intake-size", "Public list", good_local, good_spy)
                    if good_reason == "accepted":
                        self.assert_accepted(good, good_spy.answer, good_state)
                        self.assertEqual(len(good_spy.calls), 1)
                    else:
                        expected = dict(good_state, asked=["public-work"]) if consent is None else good_state
                        question = "Use optional System One for workspace public-work? (yes/no)" if consent is None else None
                        self.assert_local(good, good_local, good_reason, expected, question)
                        self.assertEqual(good_spy.calls, [])

    def test_shared_and_deep_json_values_are_valid_but_cycles_are_not(self):
        shared = {"labels": ["public", None, True, 1, 0.4]}
        aliased = {"left": shared, "right": shared}
        deep = ["public"]
        for _ in range(2000):
            deep = [deep]
        for judgment in (aliased, deep, "public", 7, True, 0.4, None):
            with self.subTest(kind=type(judgment).__name__):
                original = state()
                spy = CallSpy()
                spy.answer = {"model": "jev-1.13.0", "confidence": 0.9, "judgment": judgment}
                before = snapshot((original, judgment, spy.answer))
                result = load_recipe()(original, "intake-size", "Public list", judgment, spy)
                self.assert_accepted(result, spy.answer, original)
                self.assertEqual(len(spy.calls), 1)
                self.assertEqual(snapshot((original, judgment, spy.answer)), before)
                local = load_recipe()(state(configured=False), "intake-size", "Public list", judgment)
                self.assertIs(local["judgment"], judgment)
        cycle = [deep]
        deep.append(cycle)
        spy, original = CallSpy(), state(configured=False)
        before = snapshot((original, deep))
        with self.assertRaises(ValueError) as caught:
            load_recipe()(original, "intake-size", "Public list", deep, spy)
        self.assertEqual(caught.exception.args, ("system_one_input",))
        self.assertEqual(spy.calls, [])
        self.assertEqual(snapshot((original, deep)), before)
        self.assert_at_threshold(load_recipe(), "intake-size")

    def test_nested_values_response_and_returned_state_remain_independent(self):
        for accepted in (False, True):
            with self.subTest(accepted=accepted):
                original = state(asked=["previous-work"])
                local = {"tasks": [{"label": "public-local", "notes": ["keep"]}]}
                answer = response(confidence=0.9 if accepted else 0.2,
                                  judgment={"tasks": [{"label": "public-provider", "notes": ["continue"]}]})
                spy = CallSpy(answer)
                before = snapshot((original, local, answer))
                result = load_recipe()(original, "no-progress", "Public observations", local, spy)
                if accepted:
                    self.assert_accepted(result, answer, original)
                else:
                    self.assert_local(result, local, "low-confidence", original)
                self.assertEqual(snapshot((original, local, answer)), before)
                self.assertEqual(len(spy.calls), 1)
                self.assertIsNot(result["state"]["asked"], original["asked"])
                self.assertIsNot(result["state"]["consent"], original["consent"])
                result["state"]["asked"].append("later-work")
                result["state"]["consent"]["answer"] = "no"
                result["state"]["workspace"] = "later-work"
                self.assertEqual(snapshot((original, local, answer)), before)

    def test_structurally_valid_wrong_model_is_distinct_from_low_confidence(self):
        for confidence in (0, 0.59, 0.8, 1):
            with self.subTest(confidence=confidence):
                original, local = state(), {"choice": "keep"}
                answer = response(confidence=confidence, model="other-model")
                spy = CallSpy(answer)
                before = snapshot(answer)
                result = load_recipe()(original, "resume-selection", "Public list", local, spy)
                self.assert_local(result, local, "wrong-model", original)
                self.assertEqual(len(spy.calls), 1)
                self.assertEqual(snapshot(answer), before)
                neighbor = response(confidence=confidence)
                neighbor_spy = CallSpy(neighbor)
                neighbor_result = load_recipe()(original, "resume-selection", "Public list", local, neighbor_spy)
                if confidence < 0.6:
                    self.assert_local(neighbor_result, local, "low-confidence", original)
                else:
                    self.assert_accepted(neighbor_result, neighbor, original)
                self.assertEqual(len(neighbor_spy.calls), 1)

    def test_workspace_fault_is_detected_by_normal_oracle_with_valid_neighbor(self):
        source = recipe_source()
        target = 'consent["workspace"] == workspace'
        self.assertEqual(source.count(target), 1)
        faulted = source.replace(target, "True", 1)
        decide = load_recipe(faulted)
        original = state(workspace="workspace-B")
        original["consent"]["workspace"] = "workspace-A"
        spy = CallSpy()
        exhibited = decide(original, "intake-size", "Public list B", {"size": "Direct"}, spy)
        self.assert_accepted(exhibited, spy.answer, original)
        self.assertEqual(len(spy.calls), 1)
        with self.assertRaises(AssertionError):
            self.assert_foreign_consent(decide)
        self.assert_same_workspace_accepts(decide)
        self.assert_foreign_consent(load_recipe())
        self.assert_same_workspace_accepts(load_recipe())

    def test_confidence_fault_is_detected_by_normal_oracle_with_valid_neighbor(self):
        source = recipe_source()
        target = "confidence < minimum"
        self.assertEqual(source.count(target), 1)
        faulted = source.replace(target, "False", 1)
        for use in THRESHOLDS:
            with self.subTest(use=use):
                decide = load_recipe(faulted)
                original = state()
                answer = response(confidence=THRESHOLDS[use] - 0.000001)
                spy = CallSpy(answer)
                exhibited = decide(original, use, "Public list", {"choice": "keep"}, spy)
                self.assert_accepted(exhibited, answer, original)
                self.assertEqual(len(spy.calls), 1)
                with self.assertRaises(AssertionError):
                    self.assert_below_threshold(decide, use)
                self.assert_at_threshold(decide, use)
                self.assert_below_threshold(load_recipe(), use)
                self.assert_at_threshold(load_recipe(), use)


if __name__ == "__main__":
    unittest.main()
