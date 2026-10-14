# Recipes

Each recipe is a Markdown file that holds one fenced code block and nothing else. This manifest lists
every recipe under `references/recipes/`, recursively, with the sha256 of its file. A task that adds
or changes a recipe adds or updates its row.

| Recipe | sha256 |
|---|---|
| [correction-lineage.md](correction-lineage.md) | `72ba23b903cc2183272797f397acba65baf65d9a6c0ebdc7e3ef4576b5ee9764` |
| [adversary-checkpoints.md](adversary-checkpoints.md) | `48efb6c2809ab540e98a8228ba89ae35275febbe398c6d0215f1024f4f77e2e9` |
| [controlled-writing.md](controlled-writing.md) | `fd9329811aa210991fef5ebdbd224b41ad0108c534f0ac6014632ab3813caed9` |
| [migrate/schema.md](migrate/schema.md) | `cdca8720634be9fbda16e3e6bc28062986980f6b4af8cbce99cd4ff87930dce6` |
| [migrate/step-pre3-to-3.md](migrate/step-pre3-to-3.md) | `8443d76c5cd440f44cb7d21e1fbc53793e33d4f9863a92a0de4c3d37ae95f594` |
| [migrate/step-3-to-4.md](migrate/step-3-to-4.md) | `af58980257f402fb833df362bd73c5788040642ed5dd97260da5b2461e5b440e` |
| [migrate/step-4-to-5.md](migrate/step-4-to-5.md) | `62cc9a0ed90b5389f4c4b45d827119d1621edc99992a6da773877d5f0455b182` |
| [plan-view.md](plan-view.md) | `3908f2c4cc9e1c0e6913bd447e15934113c7b4fe88be0aeaa739ebebf58889d3` |
| [plan-view-live.md](plan-view-live.md) | `aa6456ed03a611e938952afdcf8127c694c0947bf242e366182e39fc7fbd0699` |
| [architecture-map.md](architecture-map.md) | `5dff71f09364d689082f0b32748286748871c6184e8893c3d431670a4bd562c9` |
| [requirements-base.md](requirements-base.md) | `4b31065e084c08123fc13c5bb1f2318f206aafe3c618eebd374896d06f74aa6b` |
| [system-one.md](system-one.md) | `e5086fedbad1c216e0faf7726f4775fdb941f3f99a8a64bb7e5d946513fae801` |

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
