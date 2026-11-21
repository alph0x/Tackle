# Scripts

Each script is a Python 3 file. The default path uses the standard library only. The optional judgment feature also needs its SDK when enabled. A guide names the script it uses
by its path under `scripts/` and states its arguments, results and exit codes. This manifest lists
every script under `scripts/`, recursively, with the sha256 of its file. A task that adds or changes
a script adds or updates its row. The manifest hashes every byte of each file. The lint runner hashes the capture script after removing trailing newline bytes. Its `lint.py` pin covers the entire file.

| Script | sha256 |
|---|---|
| [evaluation_rounds.py](evaluation_rounds.py) | `b8f68b367b91eb6cf27687a7680dac54a4d56fb6cb6e3ff93382bc66c771ef0e` |
| [correction_lineage.py](correction_lineage.py) | `38ad0d5ecc95ee721d9c15ad338c750b1dea78e96df3c8abdda9d087771eea60` |
| [adversary_checkpoints.py](adversary_checkpoints.py) | `8be44a5b646ad3aabf179bbf899f4e80c3d34382ce5b636c9eadb26e5d0a92dd` |
| [plan_view.py](plan_view.py) | `64243dbc57c289f2bd0b55f8cb3b828ade5195931ca0a94621652b3f840a0f79` |
| [architecture_map.py](architecture_map.py) | `e3a82e160b486413e366c7d4eaee8561144555947b40a6ef329bfa44d03f532c` |
| [prepared_job_example.py](prepared_job_example.py) | `a737473be8d4a927a9a17415e6f055405e25232cc90ac872bb9e0d8d9209d751` |
| [system_one_decide.py](system_one_decide.py) | `3307da7275085ac410423f24736a27e62edf28a58017a5ff22588784b4569f84` |
| [system_one_state.py](system_one_state.py) | `00f8b875a4ef11b4915b090df721e43c1c4a6ebdc9d05fa03057c88dc828d4db` |
| [codex_usage.py](codex_usage.py) | `1e585f9ee478e57737d3b9f08015a5446bcafbaf6b03e7ebcf0953c8fc53ebee` |
| [record.py](record.py) | `5e35731b4589be9109b1963ee720ffe18d7adac1e40b07a56325d5e4bc761f5e` |
| [migrate/schema.py](migrate/schema.py) | `6e7c3d3de8ca67089f0a5f395ebb14bb00e581fadaf4d1e9272707666a0d4809` |
| [migrate/step_3_to_4.py](migrate/step_3_to_4.py) | `effc084a74cb31c1aea0983e89bc94e0a08a3bd26137ec87ae9fc94b9c2846f5` |
| [migrate/step_4_to_5.py](migrate/step_4_to_5.py) | `ae4dcf1ee639aa556fccf4ddbc1b70229b942d84e6a365c12009023af717501b` |
| [migrate/step_pre3_to_3.py](migrate/step_pre3_to_3.py) | `b08e63d7182d5a51d30a1973ba3f098448a174e208e9739783688d7ca82ab4b3` |
| [migrate/compact.py](migrate/compact.py) | `0f9fa5da06b0223ed46db6644218cab4f282b3addbe599ea9c6d5787863329e5` |
| [workspace_archive.py](workspace_archive.py) | `7a2be3c7317fc21581375b4935c876fdc533e41b7020b2dad6e3849eaec6136d` |
| [capture.py](capture.py) | `2f802364c3c0dd7a994e7d1de7c8914d75752f6a0791ec1c00a4636c39d10acd` |
| [evidence_capture.py](evidence_capture.py) | `235a2d594c346dd8437b98e0d2b124a2b9530f230580ffc916ada48277ce9835` |
| [lint_runner.py](lint_runner.py) | `5a2953a733b351ce01ce1089799f3f359750030c74adb65764e464bdf67a16e4` |
| [lint.py](lint.py) | `bfccde4c1ae400b6327049edff0c9b1c5e350a6c7a5e539d7bc1aaebc82c8755` |
| [context_bundle.py](context_bundle.py) | `5bed1907877c5bb016d8555969eef0c564f70b11aa7bf707849b3cf4b1c0d63f` |
| [record_store.py](record_store.py) | `8983f36d60a19894cbc215b8d34a3805d82fa50d03195650af9c58d3b8e4d640` |
| [decompose_check.py](decompose_check.py) | `22a9efddfbcf7ef33dfeac625c3c2fcdd786b99bb3beda6f555b872f2c15a6f5` |
| [controlled_writing.py](controlled_writing.py) | `79e7fc56982c60db602c4216d1eb831b57b7aeefb545a26f8aed127378b8e74a` |
| [requirements_base.py](requirements_base.py) | `d6c34cf9ca5f4cbb82ecb98c56d412a97344264da5734d839b6bb153ee10f8d0` |
| [retro_confidence.py](retro_confidence.py) | `04e036414a4c8e52f562693b4e29582f6f9dd6238bb33139fe5a6b1054f05ddb` |

## Consent

A script is a Python 3 file under `scripts/` that a guide tells the agent to run or import. A
documented one-line check command, such as a retro metric command, is not a script.

Running or importing a script needs the owner's explicit authorization, under the shared
[decision and communication policy](../references/guides/communication.md). Prefer an equivalent
harness capability when one exists. A prior general request to plan or run does not count unless it
names the script use, except for `lint.py` below.

An explicit Tackle plan or run request authorizes [lint.py](lint.py), which runs the lint rows, for
that request and authorizes no other script. An explicit owner request for a feature whose documented
procedure is a script authorizes that script for that request, such as the plan view, a migration, or a
System One use that the workspace recorded `yes` for. Otherwise a general request to plan or run
authorizes no script. A script being part of the install authorizes nothing.

Declining is a normal outcome. The affected record is reported unavailable or produced by another
permitted route, such as an equivalent harness capability or the project's own tools; it is never faked.

The optional [record writer](record.py) writes the seven workspace forms after explicit authorization
for that tool or its documented feature. Its [API and manual forms](../references/guides/usage-observability.md#record-writing-and-manual-fallback) do not change the consent policy above.

## Python version

Except for the standalone record writer, the scripts need Python 3.10 or later. Their default path uses the standard library only. `record.py` supports Python 3.9 or later with isolated `python3 -I`; it imports no other shipped
script. The repository's full test registry runs on Python 3.10 and on the current Python; the record
writer's Python 3.9 invocation is checked separately.

The record writer requires POSIX locking and descriptor-relative no-follow filesystem operations. `record.py` and `workspace_archive.py` import `fcntl` and need a supported POSIX environment.
Its workspace path is existing, absolute and physical: no component may be a symlink (including
macOS `/tmp` aliases). When these operations are unavailable, including native Windows, use the
[manual record fallback](../references/guides/usage-observability.md#record-writing-and-manual-fallback).

## Windows

For scripts other than `record.py`:

On Windows, run a script with `py -3` (or `python`) in place of `python3`, for example
`py -3 -I <skill>/scripts/plan_view.py ...`. The lint rows, which `lint.py` runs with `sh`, and the
release self-lint gates are POSIX shell programs: run them in a POSIX shell such as Git Bash or WSL. For `record.py` and `workspace_archive.py`, use an existing supported POSIX environment when needed; the manual record fallback above also remains available.
