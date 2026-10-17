# Recipes

Each recipe is a Markdown file that holds one fenced code block and nothing else. This manifest lists
every recipe under `references/recipes/`, recursively, with the sha256 of its file. A task that adds
or changes a recipe adds or updates its row.

| Recipe | sha256 |
|---|---|
| [controlled-writing.md](controlled-writing.md) | `fd9329811aa210991fef5ebdbd224b41ad0108c534f0ac6014632ab3813caed9` |
| [requirements-base.md](requirements-base.md) | `4b31065e084c08123fc13c5bb1f2318f206aafe3c618eebd374896d06f74aa6b` |

## Consent

A recipe script is a program that a guide tells the agent to save as a file, import, extract or run:
the Python recipes embedded in guides and the files under `references/recipes/`. A documented one-line
check command, such as a lint row or a retro metric command, is not a recipe script.

Saving a recipe script and running it each need the owner's explicit authorization, under the shared
[decision and communication policy](../guides/communication.md). A prior general request to plan or run
does not count unless it names the recipe use. Prefer an equivalent harness capability when one exists.

An explicit owner request for a feature whose documented procedure is a recipe authorizes that recipe
for that request, such as the plan view, a migration, or a System One use that the workspace recorded
`yes` for. A general request to plan or run does not.

Declining is a normal outcome. The affected record is reported unavailable or produced by another
permitted route; it is never faked.
