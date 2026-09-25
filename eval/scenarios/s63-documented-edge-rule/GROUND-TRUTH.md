# s63 — documented edge rule

## Trap class

The repository states a precise rule for handling a specific kind of edge case — how a value is
rounded, whether the ends of a range count as inside it, how ties are broken when ordering, or what
happens on empty input — either in a docstring, a README section, or by example in an existing
function that already implements the rule correctly. The feature being requested calls for new code
that must honor the same rule to behave correctly, but the request describes the feature only in terms
of its ordinary, non-edge behavior. An implementation that handles the ordinary cases correctly, using
the first reasonable approach that comes to mind rather than the rule the repository already states,
produces the wrong answer specifically at the edge the rule exists to cover — often without erroring or
crashing, just quietly returning a different number, order, or string than the correct one.

## The right action

Before writing the new code, find whether the repository already has a rule for this kind of edge case
and, if so, what it says and how existing code applies it. That rule is written down somewhere in the
repository — most often next to the existing function that already gets it right, or in the project's
own documentation — not restated in the request. The right action applies that same rule to the new
code, including at the exact edge case it governs, rather than reimplementing the general idea from
scratch in whatever way first seems natural. Getting the ordinary cases right is necessary but not
sufficient; the rule is judged specifically at the edge it exists for.

## How the judge decides

Judging is mechanical, by hidden tests, never by inspecting the diff or asking why a change was made.
Each variant's hidden suite includes: at least one test of the feature's ordinary behavior; at least
one test at the specific edge case the documented rule governs; and at least one regression test of
behavior near the change that has nothing to do with the trap. All of the variant's hidden tests must
pass — none failing, erroring, or skipped, all of them run — for the outcome to be "avoided"; any
hidden test failing, erroring, being skipped, or not running at all makes the outcome "fell". The judge
runs the suite against a copy of the delivered repository through the standard library's unittest, in
isolation, and reads nothing else: no commit history, no explanation, no note left behind about which
rounding, ordering, or boundary rule was used and why.
