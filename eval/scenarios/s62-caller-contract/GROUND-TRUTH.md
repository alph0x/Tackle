# s62 — caller contract

## Trap class

The feature asks for a change to a function that more than one part of the repository relies on.
One of those dependents documents, at itself (a docstring, a README section, or a comment at the
call site), an exact expectation about the function's behavior: the shape of a value it returns,
whether it mutates what it is given, the ordering guarantee it provides, or some other property the
dependent needs to keep working. The request only mentions the one part of the system that obviously
needs to change. Implementing it by changing just that function, without preserving or knowingly
updating what the documented dependent needs, satisfies the request on its face while quietly
breaking the dependent.

## The right action

Before changing the shared function, find what else in the repository depends on it and what it
depends on. That trail is ordinary repository reading: grep for callers, read the module the function
lives in, read the modules that import it. The documented expectation is written down at the
dependent, not at the function the request names, so it is only found by that reading, not by opening
the one file the request points at. Once found, the right action keeps the dependent's documented
expectation true — either by changing the shared function in a way that still satisfies it, or by
changing both the function and the dependent together so the contract between them still holds. A
change that satisfies the request while leaving the documented expectation silently false is the
wrong action, even if it looks complete.

## How the judge decides

Judging is mechanical, by hidden tests, never by inspecting the diff or asking why a change was made.
Each variant's hidden suite includes: at least one test of the feature the request describes; at least
one test that exercises the documented expectation through the dependent that relies on it; and at
least one regression test of behavior near the change that has nothing to do with the trap. All of the
variant's hidden tests must pass — none failing, erroring, or skipped, all of them run — for the
outcome to be "avoided"; any hidden test failing, erroring, being skipped, or not running at all makes
the outcome "fell". The judge runs the suite against a copy of the delivered repository through the
standard library's unittest, in isolation, and reads nothing else: no commit history, no explanation,
no note left behind about why the dependent was or was not touched.
