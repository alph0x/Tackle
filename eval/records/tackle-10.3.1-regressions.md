# Tackle 10.3.1 deterministic regressions

This report summarizes the targeted regression checks behind the 10.3.1 entry of the changelog. Their inputs are temporary synthetic workspaces, files and links. A passing case establishes its encoded assertion at its actual consumer. It is not a behavioral cohort, and it does not accept or migrate any private workspace.

Eight of the new test files first failed their predicted methods against the unchanged code, then passed after the change. For those files, planted wrong implementations (mutants) were run through the same tests and failed them. The suite-index test has neither a recorded base failure nor a mutant run. The observations below were repeated on the integrated tree before the release stamp, with CPython 3.10.22 and 3.14.4 on macOS. The final full registry runs separately on the stamped candidate.

## Content link identity

Thirteen methods pass in `eval/tests/product/migration/test_content_symlinks.py`. A relative `node_modules/.bin/nanoid` link nested in retained evidence is diagnosed without changing the source. Typed inventories are compared through checkpoint, candidate and restoration copies, and changing a link's target text, type or presence changes the tree identity. Relative, external, broken, chained, circular and directory targets stay inert. Real adoption, restoration and interrupted recovery are covered, with the protected adapter contracts, control aliases and collisions. A Markdown link one directory below the workspace, which native lint reads as a regular input, is refused before dispatch; an ordinary Markdown file plus a deeper nanoid link remains a passing alternative. The completion review also tried escapes through a link named only in a resource-usage Verification cell, at `n/a`, or in a Source cell; after its correction each is refused. Logical path, type, mode and target are the persisted contract, not inode identity.

## Receipt snapshots

Nine methods pass in `eval/tests/product/migration/test_owner_confinement.py`; seven of them failed on the unchanged code. They cover an owner job whose recorded source lies outside the admitted roots, the filesystem root `/` offered as a root, a hardlinked absolute evidence file with an outside name, and a reference graph that reads a file after checking its hash. Native results and verdict streams are consumed from the checked bytes, including a substitution that keeps the same verdict. Review probes added symbolic-link, directory, FIFO, missing and invalid owner `state.json` and `manifest.json` files: none reached an outside path, and a FIFO owner manifest no longer blocks. The owner-file refusals and the second-read sites at closed errata have reviewer probes and a diff read, not a pinned test. A FIFO owner `state.json` still blocks in the existing state loader, as in 10.3.0.

## Event boundaries

Eight methods pass in `eval/tests/product/lint/rows/test_event_boundaries.py`; four failed on the unchanged code. A `#` or `##` section after an event no longer carries its `Run ID:` into that event, and a level-four heading stays inside it. Fenced headings and fields stay inert. A first change let level-one and level-two Event headings start records, which changed row 16's verdict on 23 reports compared with 10.3.0; the shipped rule sets the record id only at a level-three Event heading, and no level-one or level-two Event row differs from 10.3.0. Tilde fences and the per-call fence reset have no dedicated case.

## Citation reads

Eleven methods pass in `eval/tests/product/lint/rows/test_citation_read_confinement.py`; nine failed on the unchanged code. They run the real rows 2, 4, 12 and 14 against traversal and absolute citations, symbolic-link briefs, symbolic-link `AGENTS.md` and `reference.md`, and task ids containing `/..`, and against valid repository, workspace and sibling citations. Row 14's record loop was checked under a sandbox that denies every temporary location: it exits 0, as 10.3.0 did. Known gaps: a symbolic-link directory inside the repository is still followed; a row 4 citation without `..` to a link or FIFO inside the repository, and inputs a row names literally, are not link-checked.

## Isolated invocations

One method passes in `eval/tests/product/migration/test_catalog_isolated_invocation.py`. It decodes the installed catalog and runs both lint commands with a clean and a poisoned `PYTHONPATH`; an unisolated control shows the poison is live, and the isolated commands match the clean result. Each command without `-I` fails the method. The evaluation-rounds introduction change is the `-I` prefix alone; its seventeen recipes are unchanged. The catalog revision and target move once more in the release stamp, with their checker, guards and digests.

## Default observation

Twelve methods pass in `eval/tests/product/run/evidence-capture/test_default_observation.py`. On Python 3.10.22 the unchanged default accepted an empty suite and a printed summary that imitated a passing run; on both runtimes it ran a hostile `sitecustomize.py`, and its receipt recorded a child started without `-I`. After the change, zero tests are refused through unittest's result objects, the child starts with `-I`, a real passing suite is accepted and a failing suite, including a mixed suite with a failing module, is rejected. The cases use synthetic suites; arbitrary user suites are not covered.

## Retro candidates

Five methods pass in `eval/tests/product/lessons/test_correction_metrics.py`, and the thirty-one protected template methods in `test_history_and_obligation_templates.py` still pass. They run the installed recipes: the legacy journal output is unchanged, a forty-one-plus-one structured example yields located candidates, conflicting and partial facts stay distinct, unsafe or missing sources give a located `n/a`, and empty blockers are skipped without hiding real State events. Five methods in `test_clock_oracle_section.py` run the real protected clock-format method on edited copies of the guide: earlier paragraphs no longer displace it, and guidance outside the `Fixture recipe` section cannot satisfy it. Known gaps: a malformed terminal resource-usage row is skipped and can leave a bare `none`; the clock check does not detect the loss of its two other homes.

## Suite index

Three methods pass in `eval/tests/tooling/maintaining/suite-integrity/test_suite_index.py`. Every registered family appears once with its category, link and descriptive prose; reordered rows and harmless prose stay valid. The category-fault fixture changes one row, so a check of only that row would also pass it.

## Observation fingerprints

The SHA-256 values below identify the complete unittest output streams of the integrated-tree repetition, before the release stamp. Each run exited 0, reported its method count and printed `OK`; standard output was empty. They are traceability aids, not substitutes for the assertions or for the final release checks.

| Test file | Methods | stderr SHA-256, Python 3.10.22 | stderr SHA-256, Python 3.14.4 |
|---|---:|---|---|
| `eval/tests/product/migration/test_content_symlinks.py` | 13 | `5605cab619bf5c2d7358e876682cd4217e4fa2e477488ef4b16c6dbd2235840c` | `26e90fcbd2231482427ea37ae35cb160d0fa5d8bbd48abd5870644f848a584fa` |
| `eval/tests/product/migration/test_owner_confinement.py` | 9 | `971c8bf22803b5cd20721388074d35a623bb1e3a64a8bf32c9279e546c8c9377` | `c63bdbeec8ae2944366a5c5feaf3a4603b6812721538ce7b7ef220da3ec16f57` |
| `eval/tests/product/lint/rows/test_event_boundaries.py` | 8 | `4d72bac7aa83a336c70d8b76758c0b97c2451276ea110d00113ac6e074f604a5` | `ffb333fd9048f57c82eff97c7e79500b3dcbd0d19e6d9012d10f08d83cb78a33` |
| `eval/tests/product/lint/rows/test_citation_read_confinement.py` | 11 | `cba6aafc5a354e3f0c1e80a3cddbbc24a7893d93915805127a228cc454da1ff8` | `fb9068d4aebc7646b0232ff2a4c3583059947e759a7d7d5ef630358806610860` |
| `eval/tests/product/migration/test_catalog_isolated_invocation.py` | 1 | `6aa7cdbfa4a8dfb056541f8dc83feff45feff4243bb5fd6128953dadf58da645` | `b51d7ab67c70f05c1f8927fde3057a6e609f3649d1f15eeb2fa3317ec0329d2c` |
| `eval/tests/product/run/evidence-capture/test_default_observation.py` | 12 | `dd003d555082d1108a366ad23325469d328ad6728ff119b847a5c95fcb6a6222` | `73e50f65ba35d638884f62180f82229f872bc910cecbea006aca213c4b80705f` |
| `eval/tests/product/lessons/test_correction_metrics.py` | 5 | `f775917937e1e8ac74a98303bb9ca8a2b8953f46fc6087742e297d58577dcfba` | `a39ab72556912418f66eccfe68306bc86dd8ae9050714691592968f2be5d8fb9` |
| `eval/tests/product/templates/test_history_and_obligation_templates.py` | 31 | `d35d52e1dec43eebc8cb3d3797752dd79a0394f01d121e3cead79f5fe4652e72` | `4aa13fd4153717640628ae11047879b09a312fdd818a9b02af97f2fb55ea3f8c` |
| `eval/tests/product/templates/test_clock_oracle_section.py` | 5 | `5827a728ba8465600baf6a5764df33ce1cec47ff3550d05357205ddc1ef52e1a` | `97aaa2e475d1c09c3e9ac6b1dd359a938122919b1e99a8c3f569ce9809818658` |
| `eval/tests/tooling/maintaining/suite-integrity/test_suite_index.py` | 3 | `d3afaeaa522c30314e6b99b4a8fc583db562c4998b12dc1a240bcd34575c081e` | `ce82550193d8abc59a165da4d329f2907deeed11d4950f8643d01b4823140170` |

## Scope and limits

These are deterministic observations of shipped scripts, lint rows, recipes and maintainer tooling on macOS. Linux awks and the hosted CI run first observe them on the release candidate. The two PLAN preparation rules have no behavioral trap; their text is checked by its exact oracle only. No held-out behavioral cohort was run, and no result here establishes an improvement in agent behavior or a completed private migration.
