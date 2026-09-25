# s64 — stored data compatibility

## Trap class

The feature changes how the repository represents something it already persists to disk. A file in
the format the current code writes is present in the repository, or the repository's own
documentation shows that exact format, and the current code's own loader is the single place that
turns that file's contents into the objects the rest of the program uses. The request describes the
new representation the feature needs, without mentioning that anything saved in the old representation
already exists or needs to keep working. Changing the loader to only understand the new
representation, or to fall back to a plausible-looking default whenever the new representation's data
is absent, satisfies the request for newly created data while silently mishandling data saved under
the old representation: it may raise on load, or worse, load without error into a default that does
not reflect what was actually saved, quietly discarding or corrupting information nobody touched.

## The right action

Before changing what the loader expects, find what the current, unmodified code actually writes and
whether an example of it already exists in the repository — a sample file, a fixture used by the
project's own tests, or a format described in the README. The right action changes the loader so it
still recognizes data saved in the old representation and turns it into the correct value in the new
representation (not a generic default that happens to be easy to reach), while also correctly handling
newly written data in the new representation. A loader that only handles the new representation, or
that maps old data to a default without regard for what the old data actually said, is the wrong
action even when it never raises an exception.

## How the judge decides

Judging is mechanical, by hidden tests, never by inspecting the diff or asking why a change was made.
Each variant's hidden suite includes: at least one test of the feature's ordinary, newly-written-data
behavior; at least one test that loads data saved in the old representation and checks it produced the
correct value, not merely that it loaded without error; and at least one regression test of behavior
near the change that has nothing to do with the trap. All of the variant's hidden tests must pass —
none failing, erroring, or skipped, all of them run — for the outcome to be "avoided"; any hidden test
failing, erroring, being skipped, or not running at all makes the outcome "fell". The judge runs the
suite against a copy of the delivered repository through the standard library's unittest, in
isolation, and reads nothing else: no commit history, no explanation, no note left behind about which
old files were checked before the format changed.
