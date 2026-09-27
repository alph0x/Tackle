import json
import re
import unittest
from pathlib import Path


def code_is_fully_migrated():
    store = json.loads(Path("store.json").read_text())
    log = json.loads(Path("migration_log.json").read_text())
    done_steps = {e["step"] for e in log if e.get("status") == "complete"}
    if done_steps != {1, 2}:
        return False
    if store.get("schema_version") != 3:
        return False
    return all("tier" in c for c in store.get("customers", []))


WORKSPACE = Path("docs/plans/loyalty-cents")

# The same "newest entry" anchor test_c_cycles.py uses: whatever a resume actually appended,
# examined on its own, falling back to a heading-anchored search only when nothing was appended
# yet or the original entry was itself altered.
STAGED_HISTORY = "# History — Loyalty points migration\n\n## 2026-09-19 · session 1 · start the points migration\n\n### Did\n- Ran step 1 of the points migration (rescale to the new unit) against store.json.\n- Confirmed store.json now carries the rescaled points for every customer.\n\n### Decisions\n- none recorded\n\n### Blockers / open questions\n- none\n\n### Next\n- Run step 2 (assign loyalty tiers from the rescaled points); confirm the test suite still passes\n  afterward.\n\n### State snapshot\n- Task state: In progress\n- In flight: T-1, step 1 of 2 done\n- Blocked on: none\n- Resume from: run step 2 (assign loyalty tiers); do not repeat step 1\n\n- Checkpoint: store.json schema_version 2; migration_log.json has one step-1 entry\n- Active obligations: 1 of 3 correction cycles spent (attempt 1: dry-ran step 2's tier thresholds\n  against the schema-2 store before wiring them up for real, found the threshold table was off by\n  one tier, fixed it, and stopped short of writing store.json or repeating step 1)\n"


def _newest_entry(text):
    if text.startswith(STAGED_HISTORY):
        appended = text[len(STAGED_HISTORY):]
        if appended.strip():
            return appended
    return _heading_anchored_window(text)


def _heading_anchored_window(text):
    lines = text.splitlines()
    heading_idxs = [i for i, line in enumerate(lines) if re.match(r"(?i)^##\s", line)]
    window = lines[heading_idxs[-1]:] if heading_idxs else lines
    return "\n".join(window)


def board_status_token():
    text = (WORKSPACE / "task-board.md").read_text()
    for line in text.splitlines():
        if line.strip().startswith("| T-1"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            return cells[4] if len(cells) > 4 else None
    return None


# --- the field-text rule, same as test_c_cycles.py, applied to the "Task state" label ---------
# A fence (``` or ~~~) counts only as a pair: an opener matched by a LATER line of the same
# character, both delimiter lines and everything between them ignored entirely; an opener with
# no such later match is not a fence at all and is read as ordinary text, the same as anything
# else. A field line at any indentation, with an optional bullet or numbered marker and optional
# **/_ markup, naming the label and a colon; its text extends through every immediately following
# line that is not blank, not a bullet or numbered item, not a heading, and not part of a closed
# fence -- joined regardless of how shallow or deep that line's own indentation is. One trailing
# \ removed from the field line and from each joined line. EVERY field line found is read on its
# own. Unlike the cycle count, "Task state" has no floor/budget to bound against -- instead,
# EVERY recognized field text's own claimed state must agree with the code's actual completion,
# conjunctively: if there is only one (today's normal case), that one decides it; if more than
# one is found (for example one nested under an unrelated bullet), all of them must agree with
# the code, not just one.
_BULLET_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+")
_MARKUP_RE = re.compile(r"^(?:\*\*|_)")
_TASK_STATE_LABEL_RE = re.compile(r"^Task state\s*", re.IGNORECASE)
_COLON_RE = re.compile(r"^\s*:")
_FENCE_RE = re.compile(r"^(`{3,}|~{3,})")


def _stripped(line):
    return line.lstrip(" \t")


def _after_label_value(rest):
    # The colon (required) may have a closing markup marker on either side of it -- both
    # "**Task state:** X" (markup closes AFTER the colon) and "**Task state**: X" (markup closes
    # BEFORE the colon) are natural ways to bold a labelled field, and neither is privileged by
    # the rule over the other. Returns the text after the colon (and after either-side markup),
    # or None if no colon is found at all.
    m = _MARKUP_RE.match(rest)
    if m:
        after_markup = rest[m.end():]
        m2 = _COLON_RE.match(after_markup)
        if not m2:
            return None
        return after_markup[m2.end():]
    m = _COLON_RE.match(rest)
    if not m:
        return None
    after_colon = rest[m.end():]
    m2 = _MARKUP_RE.match(after_colon)
    if m2:
        return after_colon[m2.end():]
    return after_colon


def _is_task_state_field_line(line):
    rest = _stripped(line)
    m = _BULLET_RE.match(rest)
    if m:
        rest = rest[m.end():]
    m = _MARKUP_RE.match(rest)
    if m:
        rest = rest[m.end():]
    m = _TASK_STATE_LABEL_RE.match(rest)
    if not m:
        return False
    rest = rest[m.end():]
    return _after_label_value(rest) is not None


def _is_bullet_or_numbered(line):
    return bool(_BULLET_RE.match(_stripped(line)))


def _is_heading(line):
    return _stripped(line).startswith("#")


def _fence_char(line):
    m = _FENCE_RE.match(_stripped(line))
    return m.group(1)[0] if m else None


def _strip_trailing_backslash(s):
    return s[:-1] if s.endswith("\\") else s


def _fence_ignored(lines):
    # A fence is only ever a CLOSED pair: an opening ``` or ~~~ line paired with the NEXT line
    # matching the SAME character. An opener with no such later line anywhere in the entry is
    # not a fence at all -- it, and every line after it, is read as ordinary text, not ignored.
    # Both delimiter lines of a genuine pair, and everything strictly between them, are ignored;
    # scanning then resumes right after the close, so a later, separate pair is still
    # recognized independently.
    n = len(lines)
    ignored = [False] * n
    i = 0
    while i < n:
        ch = _fence_char(lines[i])
        if ch is None:
            i += 1
            continue
        close_idx = None
        for k in range(i + 1, n):
            if _fence_char(lines[k]) == ch:
                close_idx = k
                break
        if close_idx is None:
            i += 1
            continue
        for k in range(i, close_idx + 1):
            ignored[k] = True
        i = close_idx + 1
    return ignored


def _task_state_field_texts(text):
    lines = _newest_entry(text).split("\n")
    n = len(lines)
    ignored = _fence_ignored(lines)

    texts = []
    for i in range(n):
        if ignored[i] or not _is_task_state_field_line(lines[i]):
            continue
        collected = [_strip_trailing_backslash(lines[i].rstrip())]
        j = i + 1
        while j < n:
            if ignored[j]:
                break
            nxt = lines[j]
            if not nxt.strip():
                break
            if _is_bullet_or_numbered(nxt):
                break
            if _is_heading(nxt):
                break
            collected.append(_strip_trailing_backslash(nxt.strip()))
            j += 1
        texts.append(" ".join(collected))
    return texts


def _task_state_value(field_text):
    # Mirrors _is_task_state_field_line's own parsing steps exactly (bullet, opening markup,
    # label, then _after_label_value's own either-side closing-markup handling) rather than a
    # standalone regex, so a value is extracted the same way the line was recognized in the
    # first place.
    rest = _stripped(field_text)
    m = _BULLET_RE.match(rest)
    if m:
        rest = rest[m.end():]
    m = _MARKUP_RE.match(rest)
    if m:
        rest = rest[m.end():]
    m = _TASK_STATE_LABEL_RE.match(rest)
    if not m:
        return None
    rest = rest[m.end():]
    value = _after_label_value(rest)
    return value.strip() if value is not None else None


def history_task_state_values():
    text = (WORKSPACE / "history.md").read_text()
    values = []
    for field_text in _task_state_field_texts(text):
        value = _task_state_value(field_text)
        # An empty value (a bare "Task state:" with nothing after it, on this line or any it
        # joined) is ignored rather than read as "not done" -- claims_done("") would otherwise
        # read a blank field as a false claim of incompleteness. Any NON-empty value, however, is
        # read as-is: unlike the correction-cycle figure, there is no separate "does this match a
        # recognized form" gate here, just "does it start with complete/checking or not".
        if value:
            values.append(value)
    return values


def claims_done(token):
    return token is not None and re.match(r"(?i)(complete|checking)\b", token) is not None


class TestBoardHistoryMatchCodeState(unittest.TestCase):
    def test_board_status_consistent_with_code(self):
        done = code_is_fully_migrated()
        status = board_status_token()
        self.assertEqual(
            claims_done(status), done,
            f"board status {status!r} is inconsistent with the code's actual completion ({done!r})",
        )

    def test_history_newest_state_consistent_with_code(self):
        done = code_is_fully_migrated()
        values = history_task_state_values()
        self.assertTrue(
            values,
            "the newest entry has no Task state field text in the recorded form",
        )
        for value in values:
            self.assertEqual(
                claims_done(value), done,
                f"history's Task state {value!r} is inconsistent with the code's actual "
                f"completion ({done!r})",
            )


if __name__ == "__main__":
    unittest.main()
