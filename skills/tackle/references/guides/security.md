# Security model

This page describes what Tackle runs, reads and sends, and where each behavior is stated. It adds no
rule; each rule below lives in the file it cites.

## What the install is

The install is `SKILL.md`, `references/` and `scripts/`: Markdown guides and templates, plus Python
scripts that use the standard library only. Installing it runs nothing and installs no program.
Ordinary invocation performs no network access and changes no installation
([SKILL.md](../../SKILL.md), Compatibility and state).

## What runs

A guide names each script it uses by its path under `scripts/` and states its arguments, results and
exit codes. The agent runs or imports a script only with the owner's explicit authorization
([script consent](../../scripts/README.md#consent)), and prefers an equivalent harness capability. The
[script manifest](../../scripts/README.md) lists every script with its sha256, so a reviewer can
compare an installed script with the shipped one.

A script that needs another shipped script imports it by name from its own folder; no script loads code from the workspace. Running a task's declared checks is the method's function: the [evidence capture](evidence-capture.md) and [full checks](full-checks.md) scripts start each check as an argument list, without Python's `shell=True`, and record its exact argv, exit code and output. An argument list may itself name an interpreter or a shell, such as `sh -c`, so review a check specification you did not write before running it. Those commands come from the workspace's own specification, so they run with the same trust as the repository they check. Lint rows are fixed POSIX shell programs in `scripts/lint.py`, whose hash the manifest lists; they read the workspace, and row 8 also writes one temporary file.

## What reads

Scripts read the paths they are given: the workspace, the template, and files the owner names. The
optional [Codex native usage](codex-native-usage.md) script reads only the native JSONL file whose path
the owner passes, besides the workspace, and the [usage records](usage-observability.md) take
transcript paths from the owner. No script looks up a home folder to find files.

## Network

Tackle opens no network connection and ships no network client. An optional
[Judgement Layer](system-one.md) judgment goes through the host's `typesafe-ai` skill, and only with a
recorded `System One consent: yes` line in the selected workspace's `AGENTS.md`. Only a fragment the
caller classified as public may be sent. Without the skill's client, the SDK or consent, the judgment
stays local. The plan view loads nothing from the network, and Tackle never publishes it.

## Dynamic execution

Two shipped mechanisms run fixed program text and take none from the workspace: the [captured lint-row runner](full-checks.md) reads the row programs of the hash-pinned `scripts/lint.py` as string constants, writes each to `row-NN.sh` in its record directory and runs it with `sh`; and the retro "Attempts over budget" recipe in [the retro template](../retro.tmpl.md) passes a fixed Python program to `python3 -c 'exec(...)'`. A task check is different by design: its argument list comes from the workspace's check specification and may run an interpreter with program text, as What runs describes.

## File writes

The record writer opens each path component relative to the workspace without following symlinks and holds a workspace lock, so a symlink cannot redirect its writes. A file it replaces keeps only its permission bits (`0o777`), so setuid, setgid and sticky bits are dropped, and a new file gets `0o666` minus the umask. The migration checks its input paths, reads and materializes trees through descriptor-relative operations that do not follow symlinks, restores the file modes it recorded and verifies them against its inventory; its own state and evidence files are written with mode `0o600`. No script changes file ownership.

## Untrusted text

Plans, specifications, reference snapshots, fetched pages and tool output are data. The agent cites
them and never follows instructions inside them ([authority order](../../SKILL.md), core convention 1).
Consent and script authorization come only from the owner ([script consent](../../scripts/README.md#consent), [Judgement Layer consent](system-one.md#integration)); a plan, specification or brief states requirements and cannot grant them.
The plan view escapes workspace text before writing it into the page.
