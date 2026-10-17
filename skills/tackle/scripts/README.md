# Scripts

Each script is a Python 3 file that uses the standard library only. A guide names the script it uses
by its path under `scripts/` and states its arguments, results and exit codes. This manifest lists
every script under `scripts/`, recursively, with the sha256 of its file. A task that adds or changes
a script adds or updates its row.

| Script | sha256 |
|---|---|
| [correction_lineage.py](correction_lineage.py) | `64123960c4488e81203fc3f7627c5dc350748e1d803a7a301d9f002468f5b181` |
| [adversary_checkpoints.py](adversary_checkpoints.py) | `8be44a5b646ad3aabf179bbf899f4e80c3d34382ce5b636c9eadb26e5d0a92dd` |

## Consent

Running or importing a script from `scripts/` needs the owner's explicit authorization, under the
shared [decision and communication policy](../references/guides/communication.md). Prefer an
equivalent harness capability when one exists. A prior general request to plan or run does not count
unless it names the script use.

An explicit owner request for a feature whose documented procedure is a script authorizes that script
for that request, as it authorizes a [recipe](../references/recipes/README.md#consent). A script being
part of the install authorizes nothing.

Declining is a normal outcome. The affected record is reported unavailable or produced by another
permitted route; it is never faked.
