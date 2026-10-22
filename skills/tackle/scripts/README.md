# Scripts

Each script is a Python 3 file that uses the standard library only. A guide names the script it uses
by its path under `scripts/` and states its arguments, results and exit codes. This manifest lists
every script under `scripts/`, recursively, with the sha256 of its file. A task that adds or changes
a script adds or updates its row.

| Script | sha256 |
|---|---|
| [correction_lineage.py](correction_lineage.py) | `64123960c4488e81203fc3f7627c5dc350748e1d803a7a301d9f002468f5b181` |
| [adversary_checkpoints.py](adversary_checkpoints.py) | `8be44a5b646ad3aabf179bbf899f4e80c3d34382ce5b636c9eadb26e5d0a92dd` |
| [plan_view.py](plan_view.py) | `b4f7d31b67212e1ad98430f1fe296110675b7e5d2d019f8df3083358dc8a4227` |
| [architecture_map.py](architecture_map.py) | `e3a82e160b486413e366c7d4eaee8561144555947b40a6ef329bfa44d03f532c` |
| [system_one_decide.py](system_one_decide.py) | `a9c535bdd2e7fff2137b36c032c22ca55fd97886beb0bc883e8ba3dd2ffd3ffb` |
| [system_one_state.py](system_one_state.py) | `2369d7ddad068ef7247b732ecc7f1fdeef921b1dbed3b6304844f43eef273c2a` |
| [codex_usage.py](codex_usage.py) | `2fca95fcb854a8157a1b12770ff590bf776fce2f1e4307de12161ad5f83255aa` |
| [migrate/schema.py](migrate/schema.py) | `6e7c3d3de8ca67089f0a5f395ebb14bb00e581fadaf4d1e9272707666a0d4809` |
| [migrate/step_3_to_4.py](migrate/step_3_to_4.py) | `effc084a74cb31c1aea0983e89bc94e0a08a3bd26137ec87ae9fc94b9c2846f5` |
| [migrate/step_4_to_5.py](migrate/step_4_to_5.py) | `ae4dcf1ee639aa556fccf4ddbc1b70229b942d84e6a365c12009023af717501b` |
| [migrate/step_pre3_to_3.py](migrate/step_pre3_to_3.py) | `b08e63d7182d5a51d30a1973ba3f098448a174e208e9739783688d7ca82ab4b3` |
| [capture.py](capture.py) | `5fd79dbbd5edd2efb308e22d9bb71e5007a80f425fde41aa5b297adc02cb755d` |
| [evidence_capture.py](evidence_capture.py) | `f542532dc57a0e1dc7b101da8371822f66959683b2852e29b816000fef6e1ce0` |
| [lint_runner.py](lint_runner.py) | `5ecdd0e37ba5e93de5e89d9a56703893a17c3b9c163cf28373dcca37fa1ac99d` |
| [lint.py](lint.py) | `2bb1b2ad46281242854b095016c9ac995b4eef81458d58f9c3cbc43569a28cfe` |
| [context_bundle.py](context_bundle.py) | `5bed1907877c5bb016d8555969eef0c564f70b11aa7bf707849b3cf4b1c0d63f` |
| [record_store.py](record_store.py) | `8983f36d60a19894cbc215b8d34a3805d82fa50d03195650af9c58d3b8e4d640` |
| [decompose_check.py](decompose_check.py) | `22a9efddfbcf7ef33dfeac625c3c2fcdd786b99bb3beda6f555b872f2c15a6f5` |
| [controlled_writing.py](controlled_writing.py) | `79e7fc56982c60db602c4216d1eb831b57b7aeefb545a26f8aed127378b8e74a` |
| [requirements_base.py](requirements_base.py) | `d6c34cf9ca5f4cbb82ecb98c56d412a97344264da5734d839b6bb153ee10f8d0` |
| [retro_confidence.py](retro_confidence.py) | `9d61b1747858e9f6d707275324d04ab08e998a6aa5a4f9435e60a4c83070fc6c` |

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

## Python version

The scripts need Python 3.10 or later and the standard library only. The repository's full test
registry runs on Python 3.10 and on the current Python; 3.10 is the oldest version it is checked on.

## Windows

On Windows, run a script with `py -3` (or `python`) in place of `python3`, for example
`py -3 -I <skill>/scripts/plan_view.py ...`. The lint rows, which `lint.py` runs with `sh`, and the
release self-lint gates are POSIX shell programs: run them in a POSIX shell such as Git Bash or WSL.
