#!/usr/bin/env python3
"""Validate closed migration metadata, retained source and compiled current instructions.

The finite text policy below is reviewed current-target instruction content, not an NLP
oracle or independent semantic/adoption evidence. It accepts documented equivalent
prose while retaining literal command/receipt contracts. No product module is imported.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import stat
import sys
import unicodedata
from pathlib import Path

FAMILIES = ("I", "P", "S", "A", "R", "B", "M", "E", "J", "H", "N", "Q", "W", "O", "V", "Z")
FAMILY_COUNTS = {"I": 8, "P": 17, "S": 7, "A": 16, "R": 7, "B": 38, "M": 11, "E": 31, "J": 3, "H": 6, "N": 1, "Q": 2, "W": 5, "O": 12, "V": 17, "Z": 39}
TOP = {"schema", "revision", "target_methodology", "supported_buckets", "rules", "provenance"}
RULE = {"id", "kind", "detector", "applies", "requires", "effect", "postcondition", "recovery", "instructions", "provenance_ids", "exceptions"}
APPLIES = {"I": "always", "P": "active", "S": "structure", "A": "structure", "R": "active", "B": "next-wave", "M": "active", "E": "active", "J": "requested", "H": "active", "N": "multi-repo", "Q": "current-consumer", "W": "requested", "O": "requested", "V": "active", "Z": "active"}
OPTIONAL = {"J", "W", "O"}
# Canonical revision1 provenance data, independent of JSON object key order.
PROVENANCE_SHA256 = "979b9d3a1db6f13e3491c09992b9a42b80f1aeb49e6eef67489250a7c3cab00e"
RECOVERY = {'I': 'preserve-original',
 'P': 'defer',
 'S': 'preserve-original',
 'A': 'preserve-original',
 'R': 'defer',
 'B': 'defer',
 'M': 'defer',
 'E': 'reconcile-job',
 'J': 'defer',
 'H': 'preserve-original',
 'N': 'defer',
 'Q': 'defer',
 'W': 'reconcile-job',
 'O': 'defer',
 'V': 'reconcile-job',
 'Z': 'restore-checkpoint'}
EXCEPTIONS = {'I': ['Already-current installation produces no install action; owner-controlled update and removal '
       'boundaries apply.'],
 'P': ['Closed and neighboring workspaces remain unchanged; unknown closure or task boundary blocks '
       'migration.'],
 'S': ['Unknown or ambiguous structure, CRLF, unclosed fences, aliases, and collisions retain existing '
       'refusal behavior; no support below pre-3 or downgrade.'],
 'A': ['No board state, completion grade, correction history, or closed evidence is inferred or rewritten.'],
 'R': ['Conflicting existing receipt or baseline values block; no generic historical repair.'],
 'B': ['No new task, filled backlog, inferred dependency, or fabricated readiness is created.'],
 'M': ['Unknown host capability and telemetry remain unknown or n/a; no model or confirmation is invented.'],
 'E': ['Optional sidecar failure never gates closure; canonical cost data requires an authoritative '
       'observation.'],
 'J': ['No consultation, permission, answer, consent, or budget allocation is created by migration.'],
 'H': ['The existing row-13 WARN exception remains non-gating where documented; records and history are '
       'never retired or shortened.'],
 'N': ['Single-repository work creates no multi-repository artifact.'],
 'Q': ['No historical requirements delta is backfilled.'],
 'W': ['No standing request means no view rebuild.'],
 'O': ['Optional artifacts and profiles are not created without a concrete upcoming consumer and existing '
       'authorization.'],
 'V': ['A legacy source may correctly report migrate-first; documented WARN rows 8, 13, and 15 remain '
       'non-gating.'],
 'Z': ['Any failed or interrupted cutover leaves the original authoritative unless exact recorded physical '
       'states permit reconciliation.']}
CURRENT_RECIPES = {'I-owner-archetypes': 'Before any separately owner-controlled install update, identify files the owner '
                       'added under references/archetypes/ and preserve them through the owner in '
                       '.tackle/archetypes/ or ~/.tackle/archetypes/. The installed artifact is SKILL.md '
                       'plus references/ plus scripts/. Migration never performs the update or moves/deletes '
                       'owner additions itself; if preservation is unresolved, keep the install-related step '
                       'pending.',
 'I-retired-producer': 'If a retired loopback live producer is actually observed, have its owner stop it '
                       'before a separately authorized install update. Current Tackle ships no live '
                       'producer. Migration neither starts a replacement service nor stops arbitrary '
                       'processes; absence of the producer creates no action.',
 'I-installed-programs': 'Use current installed scripts and their documented direct procedures, not saved '
                         'historical recipe programs or a replacement task runner. An explicit request '
                         'authorizes only its documented script use; ordinary project commands remain '
                         'available under their own scope. Current lint uses installed lint.py and canonical '
                         'rows, citation grounding retains its two phases, and scaffold/evaluation use the '
                         'current installed guides. Migration performs no installation or network operation.',
 'I-old-helper-disposition': 'The old no-helper/two-part install instruction is superseded by the current '
                             'three-part artifact SKILL.md, references/ and scripts/. Observe installed '
                             'resources and manifest before proceeding. Do not delete tracked project '
                             'helpers or fixtures as a migration step. Only the owner-controlled update '
                             'procedure may remove its exact verified legacy tombstone tackle-check, '
                             'preserving tackle and unrelated sentinels; migration neither updates nor '
                             'deletes install content.',
 'I-private-planning': 'Preserve the project boundary that docs/plans/ and docs/seeds/ are both gitignored '
                       'and neither ships in the install artifact. Check the observed project policy without '
                       'changing the original or neighboring files; a missing required boundary needs an '
                       'owner decision in its own allowed scope, not silent staging, publication or a '
                       'project-wide edit by migration.',
 'I-obsolete-artifact-disposition': 'Do not execute historical blanket deletion of todo.md, tasks.md, '
                                    'checklist.md or execution-strategy.md. Preserve historical-only files '
                                    'and record their mapping or historical role; use only supported '
                                    'structural adapters for actual current renames. Keep one current '
                                    'task-board state and resolve dependencies from the current plan/board '
                                    'contract rather than maintaining a pasted second graph. Any proposed '
                                    'removal outside the compiled structural map needs separate owner '
                                    'authority.',
 'I-self-update-superseded': 'Historical automatic/daily self-update and old update-command instructions are '
                             'superseded. Ordinary invocation and migration perform no network access or '
                             'installation mutation. Only the owner-controlled out-of-band update workflow '
                             'verifies and replaces the three-part artifact; installing/updating never '
                             'selects or migrates a workspace. An already-current artifact requires no '
                             'install action.',
 'P-selected-checkpoint': 'Select one explicitly named active workspace at an evidenced task boundary and '
                          'keep its original authoritative. Work only on a disposable copy; the original '
                          'remains unchanged before separately validated cutover. Before candidate edits, '
                          'record the canonical path, selection rationale, source/contract revision, pinned '
                          'task procedure and current diagnostic under that procedure; hash board, briefs, '
                          'reports, AGENTS.md/model map, history, usage, raw evidence and any '
                          'sidecars/snapshots that exist. Preserve exact checks, test/replay inputs, '
                          'correction lineage and historical completed/blocked/skipped/interrupted states; '
                          'unavailable evidence stays unavailable. Create an unchanged checkpoint and '
                          'observe a neighboring sentinel. Closed or unrelated workspaces and read-only '
                          'STATUS/diagnosis requests authorize no migration. Started/Checking/Interrupted '
                          'tasks retain their procedure/counters until their deliberate boundary.',
 'P-preserve-settled': 'Preserve every settled contract, state, grade, correction count and exact original '
                       'history/usage/evidence byte, including whitespace, headers and the eight-column '
                       'legacy table when present. A legacy row without an exact run_id remains '
                       'legacy-scoped. Copy and hash these bytes before transformation; never rewrite, '
                       'backfill, re-grade or reorder them, and leave the original and neighbors unchanged.',
 'P-historical-only': 'For files without a current counterpart, including context.md or reference.md, retain '
                      'them as historical data or map them to a real current artifact under an explicit '
                      'recorded decision. Preserve the original bytes and mapping; never silently delete '
                      'them, treat them as a second current state source or require a closed workspace to '
                      'migrate.',
 'S-supported-adapters': 'Determine structure with the installed schema.schema_of, separately from the '
                         'Methodology stamp. Supported routes are pre-3 to 3 to 4 to 5, 3 to 4 to 5, 4 to 5, '
                         'already-5 and explicit Gate: Lite. Use only each exact installed '
                         'detect/transform/verify adapter through schema.adopt; transform/verify receive '
                         'schema.workspace_files projections excluding legacy directories. Preserve every '
                         'existing legacy directory and add the exact original step snapshot. In Full copies '
                         'record every actual path/P-to-T mapping across plan, board, briefs, dependencies, '
                         'reports and usage; preserve original history plus the distinct once-only '
                         'structural adoption entry. Lite keeps Gate and existing history/usage and renames '
                         'only existing log.md/log-archive.md/usage.md to '
                         'history.md/history-archive.md/resource-usage.md, with old/new collision refusal '
                         'and no invented board/report/Full template. Unknown/ambiguous structure, unclosed '
                         'fences, CRLF, aliases and collisions stop mutation; no below-pre-3 support, '
                         'downgrade or inferred Ready is introduced.',
 'S-gates': 'Add `Gate: Full` on line 3 of an active Coordinated plan, following `plan.tmpl.md`; keep its '
            'title on line 1 and keep a Lite plan’s `Gate: Lite` on line 1. Preserve a known selected Lite '
            'layout without adding Full artifacts. Missing or conflicting gate/layout evidence is a hold, '
            'never an inferred conversion.',
 'S-old-layout-map': 'Retain the historical contract.md to design-contract.md, strategy.md to '
                     'execution-strategy.md and snapshots/ to reference-docs/ mapping as source provenance. '
                     'Apply only a rename supported by the actual selected structural adapter and observed '
                     'source, recording original and destination identities and refusing collisions; do not '
                     'run an obsolete additional version step or delete the old checkpoint.',
 'S-current-links': 'After an actual supported structural move, make the selected candidate’s forward-facing '
                    'links resolve to the moved files using the recorded own path/ID map. Preserve links '
                    'into other workspaces and historical evidence verbatim and diagnose unresolved '
                    'references; do not rewrite every historical hit, another workspace or the original. '
                    'Check current consumers and retain old resolution until the new references validate.',
 'S-plan-identities': 'Check that the selected candidate plan identifies all actual task IDs with their '
                      'requirement traces and briefing paths. Use the observed structural map and current '
                      'template only for the selected supported source; never invent a task, assume '
                      'readiness, mass-normalize historical P IDs or create Full structure for Lite.',
 'A-forward-requests': 'Update forward-looking requests to the single Tackle skill entry followed by plan, '
                       'run, verify, next, status, judge, retro or an explicitly scoped feature request. '
                       'Historical slash/action/helper aliases remain preserved text, not separately '
                       'installed commands. Next selects/prepares only; STATUS, diagnostics, quoted or '
                       'negated requests do not execute or mutate. Retain current gates and independent '
                       'checker closure. No wrapper, obsolete workspace flag or copied consent is '
                       'introduced.',
 'A-current-lineage': 'A workspace that adopts nothing keeps working. Rows 18 and 19 skip legacy briefs and '
                      'decisions, and row 14 asks for the hash only after the 10.2.0 stamp. Row 2 reports a '
                      'dependency on a Skipped task and a requirement whose tracing tasks are all Skipped. '
                      'Repair the first by depending on the successor, and the second by naming the Skipped '
                      "task on an open successor's `**Lineage**:` line. Preserve closed states and spent "
                      'correction lineage; do not execute skipped work or reset a pool.',
 'A-pinned-state': 'Keep the task board as sole current state and use only the exact terminology/adapter '
                   'mapping. Preserve original legacy state/grade, completed reports, '
                   'method/result/independence, IDs, correction lineage and raw history in '
                   'checkpoint/mapping data. Never infer Ready from not-started, Complete from '
                   'implementation finished, or current proof from a historic green mark. Started or '
                   'interrupted work keeps its actual pinned procedure through its own boundary; unknown end '
                   'data is recorded as observe-incomplete, not a restarted side effect. Only remaining '
                   'forward-facing work changes in the selected copy.',
 'A-no-grade-backfill': 'Retain observed legacy grades and the evidence from which each was derived; a '
                        'declared grade never substitutes for actual independent checker command/output/exit '
                        'evidence. Historical grade-backfill instructions do not authorize rewriting closed '
                        'rows or upgrading old proof during current migration. If current readiness or '
                        'acceptance needs that evidence, resolve it through current checks/review on '
                        'selected open work; unavailable proof remains unavailable.',
 'A-skipped-status': 'Map only an observed deliberate skip to Skipped with its one-line reason. A skip is '
                     'not Complete and grants no evidence; preserve original legacy state/grade in the '
                     'migration record. The board is sole state, and unknown or unsupported state vocabulary '
                     'holds rather than being guessed.',
 'A-board-sole-state': 'The current task board is the sole state source. During a supported selected '
                       'conversion, carry actual forward-facing task state into the board before removing a '
                       'redundant current per-brief or plan Status field; preserve all original bytes in the '
                       'checkpoint and do not rewrite historical records. Conflicting state sources require '
                       'resolution, never silent selection or a second state board.',
 'R-hash': 'For every Complete task on the board, hash its brief with `sha256sum <brief>`, or `shasum -a 256 '
           '<brief>` without `sha256sum`. Retain the exact baseline and original brief bytes before any '
           'other edit to a closed brief. A conflicting existing baseline holds; never recompute it to match '
           'an edited brief.',
 'R-baseline': "Put `**Brief sha256**: <64 lowercase hex digits>` on its own line in the task's report, "
               "outside code fences. Place it right before the report's `Final status:` line, or right "
               'before its `**Remains**:` line when it has none. Then append `Brief sha256 T-NN: <the same '
               'hash>` on its own line, outside code fences, to the end of `history.md`. History only grows: '
               'never edit an older entry. That report line and the history line are the only changes '
               "adoption makes to a closed task's records. Do both before any other edit to a closed brief. "
               'Skipped and Unverifiable reports may carry both too. Preserve an existing identical receipt; '
               'a conflicting value is pending, not overwritten.',
 'R-erratum': 'After recording the baseline, a closed brief changes only by erratum. An active decision '
              'authorizes the edit; then append `**Brief erratum**: D-NN · sha256 <hash after the edit>` to '
              'its report. Retain the pre-edit baseline and decision; no generic repair or silent '
              'closed-history edit is allowed.',
 'R-remains': 'End every required Complete report with `**Remains**: none`, or `**Remains**:` followed by '
              'the actual O-NN obligation IDs left behind. Resolve unknown Remains from the actual '
              'report/owner; never infer none from a terminal board mark, an empty list or a reviewer label. '
              'Add only a specifically required missing adoption receipt, preserving existing closed bytes '
              'and blocking conflicting values.',
 'R-obligations': 'On selected open work use the task-board template’s obligations section: every obligation '
                  'outliving its task has an O-NN row with owner, trigger, state Open and discharge check. '
                  'Append a new history State snapshot naming every Open ID in Active obligations; never '
                  'edit an older snapshot. Preserve obligations through task split/merge/rename and require '
                  'actual discharge evidence.',
 'R-close-provenance': 'Future closures require the actual report and Coordinator/independent checker '
                       'evidence under the current RUN protocol before the board becomes Complete. A stub or '
                       'a named reviewer alone is not current proof. Preserve existing closed reports, '
                       'legacy sign-offs and the original state without retrospective repair or regrading; '
                       'current-work/handoff are projections, never canonical state. Missing current '
                       'required evidence holds its owning open-work closure.',
 'B-scope-effort': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted '
                   'briefs wait for their own deliberate boundary and closed work stays unchanged. Run the '
                   'current rows 1–19 on the candidate. For an applicable open brief whose Effort is not low '
                   'and has neither Tier nor Tier reason, add **Tier reason** explaining the departure from '
                   'the default. Use current **Write scope** and Acceptance check labels instead of '
                   'forward-facing Touches and Done-signal aliases; replace inherit Effort with an actual '
                   'portable level supported by the observed map. Preserve original fields and refuse '
                   'conflicting aliases rather than silently preferring one.',
 'B-forbidden': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted briefs '
                'wait for their own deliberate boundary and closed work stays unchanged. Name the forbidden '
                'action classes in each new compiled brief using the Forbidden actions field of '
                'task.tmpl.md. Copy the actual job contract, invariants, side-effect boundary, required '
                'checks and owner; do not add a new execution permission or mass-rewrite older briefs.',
 'B-detail': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted briefs wait '
             'for their own deliberate boundary and closed work stays unchanged. Give each open brief one '
             'line in Purpose and scope, `- **Detail**: full` or `- **Detail**: interface`. Use `full` for '
             'the [next wave](verify.md#milestone-readiness) and for any brief whose row is Ready to run, In '
             'progress or Checking. Use `interface` for the rest. Row 18 fails a Ready to run row that names '
             "an interface brief. Edit the brief of an In progress or Checking task only at that task's "
             'boundary, never during an attempt.',
 'B-symbols': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted briefs '
              'wait for their own deliberate boundary and closed work stays unchanged. Give a brief raised '
              'to full the symbol ledger of task.tmpl.md. Under Interface and invariants, `**Produces**` and '
              '`**Consumes**` each hold `none` or indented sub-items. Every consumed name gets one source: '
              '`from T-NN`, `from T-NN [sibling]` or `exists` with an anchored citation. A `from T-NN` task '
              'must be an ancestor through `Depends on`. A `[sibling]` source must also appear in the '
              "brief's own `Depends on` cell. A name has one producing brief; row 18 fails a name that two "
              'briefs produce. The task-boundary rule applies here too. An interface brief needs no ledger.',
 'B-decision-clauses': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted '
                       'briefs wait for their own deliberate boundary and closed work stays unchanged. Add '
                       '`**Owner**: T-NN · **Clauses**: C-xx` after `**Supersedes**` only on a decision to '
                       "be checked; either part may be omitted. The owner's brief must cite the decision id "
                       'and, at `full` detail, carry each named clause compiled. When a decision with these '
                       'lines supersedes an earlier one, the earlier heading names it, as `⤴ superseded by '
                       'D-NN`. Row 19 fails a heading that names another, and a still-active predecessor is '
                       'no finding.',
 'B-runnable-case': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted '
                    'briefs wait for their own deliberate boundary and closed work stays unchanged. For '
                    'every actual acceptance case, provide a runnable literal Check with resolved absolute '
                    'cwd, prerequisites, checked failure propagation and explicit pass condition (including '
                    'required PASS/count/content), or `review: <rubric> by <reviewer role>` for a genuine '
                    'review criterion. A missing/empty extraction, TBD, cross-reference, prose or '
                    'file-existence-only claim cannot establish Ready. Retain valid and invalid disposable '
                    'controls and the native child result, not a wrapper PASS. This preparation never runs '
                    'the upcoming writing Check before adoption.',
 'B-blocker-report': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted '
                     'briefs wait for their own deliberate boundary and closed work stays unchanged. For an '
                     'active blocker record expected and observed facts, exact evidence, affected work, '
                     'viable alternatives, recommendation, consequences and an affected-only wait. Continue '
                     'independent authorized work and preserve closed reports. Missing capabilities stop '
                     'only the dependent route, without model/provider/authority invention.',
 'B-retired-flag': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted '
                   'briefs wait for their own deliberate boundary and closed work stays unchanged. The '
                   'obsolete tackle-gate flag is not current authority and cannot disable required checks or '
                   'independent closure. Preserve existing pinned briefs until their boundary. New '
                   'current-template briefs retain public-boundary E2E-first/replay obligations and explicit '
                   'loop budgets; do not rewrite unrelated old fields merely to modernize them.',
 'B-clause-seal': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted briefs '
                  'wait for their own deliberate boundary and closed work stays unchanged. A stabilized '
                  'compiled clause or acceptance heading retains its owning active decision and exact sealed '
                  'text/hash. Adding/changing a clause ID or heading requires a superseding decision and '
                  'regenerated source/seal hashes, followed by the installed verification procedure. Never '
                  'manufacture an active predecessor, silently rehash a changed sealed clause or mark Ready '
                  'before current checks.',
 'B-aliases': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted briefs '
              'wait for their own deliberate boundary and closed work stays unchanged. Use terminology.md '
              'for future visible labels while preserving P IDs, filenames, links, schema tokens and '
              'historical bytes until an actual supported structural adapter maps them. Validate both old '
              'and new fields; conflicting aliases hold rather than silently preferring one. Resolve every '
              'own moved-file link and retain external/history references.',
 'B-wave-contract': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted '
                    'briefs wait for their own deliberate boundary and closed work stays unchanged. '
                    'Re-ground only the actual declared upcoming wave: complete requirement coverage, '
                    'concrete dependency identities/artifacts, interfaces, revisions, owners, outcomes, '
                    'runnable future checks and correction lineage. Keep deferred work Draft; '
                    'split/merge/rename resets no unresolved allowance. Apply risk precedence before '
                    'simplifying. An explicitly selected already-authorized Lite source retains its '
                    'first-line Gate: Lite and existing plan/history/usage, with no board/tasks/Full '
                    'decomposition manufactured; missing Full artifacts is not evidence of Lite. Read-only '
                    'audits do not relabel or upgrade plans and historical '
                    'completed/blocked/skipped/unverifiable work is not re-executed.',
 'B-self-contained': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted '
                     'briefs wait for their own deliberate boundary and closed work stays unchanged. Copy '
                     'every prerequisite fact needed by the executor into its brief: exact inputs/source '
                     'fragments, resolved cwd, scope, invariants, acceptance and permissions. Plan, board, '
                     'AGENTS.md or conversational memory must not be hidden execution prerequisites; links '
                     'provide depth rather than replacing required facts. Unknown needed facts hold '
                     'readiness.',
 'B-json-contract': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted '
                    'briefs wait for their own deliberate boundary and closed work stays unchanged. For '
                    'semantic JSON contracts validate parsed keys, types and values; require '
                    'bytes/whitespace only when the actual contract declares exact bytes. Do not invent '
                    'formatting, newline, order or serialization requirements to reject an otherwise valid '
                    'representation.',
 'B-grounding': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted briefs '
                'wait for their own deliberate boundary and closed work stays unchanged. Resolve every '
                'upcoming file:line citation with its literal source fragment. Grounding first checks the '
                'cited line; on drift count whole-file matches: exactly one permits a mechanical line '
                'reanchor, zero is stale and more than one is ambiguous. Preserve line-accurate citations '
                'and choose unique new fragments. A moved/unrecoverable source may use explicit '
                'git-historical revision/path instead of reanchoring against wrong content. Last-verified '
                'uses ISO UTC seconds; legacy date-only stamps remain conservative and update only at the '
                'next legitimate grounding. Lint/read-only diagnosis reports staleness; writing reanchors '
                'need selected-candidate authority, stable inputs and the current installed procedure. An '
                'unread citation keeps the brief ungrounded; never use session memory as source truth.',
 'B-intake-communication': 'Prepare only caller-declared upcoming unstarted work; '
                           'started/Checking/Interrupted briefs wait for their own deliberate boundary and '
                           'closed work stays unchanged. Use current intake to understand intent before '
                           'selecting a solution, infer from available facts and batch only material owner '
                           'questions with useful defaults. Keep output concise but include the full '
                           'security/irreversible-action/ambiguity facts needed for a safe decision. This is '
                           'prospective communication guidance, not a historical workspace rewrite or extra '
                           'permission.',
 'B-type-and-dependencies': 'Prepare only caller-declared upcoming unstarted work; '
                            'started/Checking/Interrupted briefs wait for their own deliberate boundary and '
                            'closed work stays unchanged. Absent Type retains standard; discovery/experiment '
                            'uses need their actual closed-loop fields (rounds and, for experiment, metric '
                            'and threshold). Every Depends on edge names the actual crossing artifact '
                            'consumed; remove a false edge rather than waiving it. A genuine ordering-only '
                            'edge requires an explicit owner decision, never a fabricated data dependency or '
                            'reset lineage.',
 'B-intent': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted briefs wait '
             'for their own deliberate boundary and closed work stays unchanged. Before a behavior-changing '
             'edit, retain an INTENT explaining current source behavior, the actual acceptance criterion and '
             'the authoritative source, and stop on contradiction. Source checks precede code changes; a '
             'desired PASS does not redefine the contract, protected expectation or owner authority.',
 'B-triviality': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted briefs '
                 'wait for their own deliberate boundary and closed work stays unchanged. Consider direct '
                 'work only when the actual task is genuinely trivial (one file, fewer than 10 lines, no new '
                 'behavior and no source search), after risk precedence and existing owner scope. Otherwise '
                 'retain appropriate durable planning/verification. Historical sizing guidance does not '
                 'bypass security, irreversible effects, unknown acceptance or current task gates.',
 'B-traces': 'Prepare only caller-declared upcoming unstarted work; started/Checking/Interrupted briefs wait '
             'for their own deliberate boundary and closed work stays unchanged. Retain complete requirement '
             'traces for actual upcoming task IDs in the plan and each brief’s Traces to field, using the '
             'current template placement. Every remaining requirement must have an owner/outcome/check; '
             'preserve historical IDs and no invented completion or retrospective requirements delta.',
 'M-map': 'For actual remaining roles use only host-observed capabilities, provider-neutral portable tiers '
          'and Effort low/medium/high/max, explicitly bound to exposed host controls with source. Mark '
          'supported/unsupported/unknown and retain n/a for unavailable telemetry; a portable speed tier is '
          'not request service-tier telemetry. Routing fields are optional and absent fields retain the '
          'current default. A planner is stronger than Executor only when more than one suitable tier is '
          'actually bound; otherwise record the limitation. Offer an observed alternative for an unavailable '
          'exact binding or stop its affected route; never invent a model/provider or copy a confirmation. '
          'Optional cumulative/partial usage remains informative, not gating.',
 'M-confirmation': 'Show the owner the observed role-to-model/effort table for remaining roles and retain '
                   'that initiative’s actual confirmation in AGENTS.md. Do not dispatch a subagent without '
                   'the required current confirmation; an inherited record from another workspace or a '
                   'capability label is not authorization. Migration itself dispatches no agent or model '
                   'call.',
 'M-autonomy': 'Retain the workspace’s explicitly selected autonomy level and task conditions; '
               'production-path work remains capped at L2 unless an active owner decision authorizes '
               'otherwise. Unattended L3 additionally requires actual eligible independent evidence through '
               'its dependency chain; asserted/review-only or unknown upstream proof cannot be upgraded into '
               'that authority. Record any limitation and preserve existing historical grades without '
               'backfill.',
 'E-script-identity': 'A current check record binds the installed program hash, especially captures/lint '
                      'invoked from outside the working directory. If that relevant script changes, refuse '
                      'reuse as current proof and rerun only the affected authorized checks under the '
                      'updated installed program, retaining the old record unchanged and exact old/new '
                      'identities.',
 'E-corrections': 'For new correction records use `correction cycle N of 3: <failure> → <correction>; '
                  '<validation command>: <result>`; retain older `attempt N:` bytes. Count failed '
                  'correction-validation cycles from actual trace evidence, cap the same lineage at three '
                  'and stop/escalate at the bound or two identical no-progress observations under the '
                  'current RUN protocol. Splitting/renaming/migration never resets spent allowance; no '
                  'silent repeated attempt or invented positive Attempts.',
 'E-clocks': 'Write lifecycle At clocks with seconds as `YYYY-MM-DDTHH:MM:SS[.fff](Z|±HH:MM)` under '
             'resource-usage.tmpl.md, and use the same form in the Lite ledger. Unobserved clocks remain '
             'n/a; minute-only or space-separated historical clocks stay unmeasured and are not rewritten or '
             'used to invent measured seconds.',
 'E-current-closure': 'Future task closure needs both its target criterion and '
                      'surrounding-system/integration checks on the actual merged tree plus independent '
                      'Coordinator/checker closure with accessible evidence. Driver-only PASS, a grade '
                      'label, a methodology stamp or an obsolete gate-off flag cannot grant Complete. Choose '
                      'appropriate existing checks before implementation, preserve current test-first '
                      'exceptions only under the actual owner decision, and do not rewrite historical closed '
                      'methods/grades. For Lite and Full, unavailable mandatory coverage blocks its owning '
                      'scope while optional coverage/unknown telemetry stay nongating; role Outcome is '
                      'distinct from initiative completion.',
 'E-adversary-boundary': 'Do not add an Adversary line to a task completed before the applicable adoption. '
                         'Only later tasks owe the current adversary-checkpoint observations under RUN. '
                         'Preserve the historical task’s exact methods and limits; never manufacture an '
                         'independent past review.',
 'E-lifecycle-validity': 'On the selected candidate validate new lifecycle writes against legal role Outcome '
                         'states, trace-backed positive Attempts, truthful n/a versus observed zero, and '
                         'externally observed terminal clocks with exact Run ID. Retain row16 and the '
                         'installed retro lifecycle diagnostic, commands/results and unresolved Run ID '
                         'facts. A known invalid old row is a defect that holds adoption without rewriting '
                         'closed rows or neighbors; the original stays authoritative.',
 'E-test-selection': 'For remaining code work choose contract checks before the next implementation edit. '
                     'Prefer one public-boundary E2E when it observes the contract; a feasible complex '
                     'integrated feature requires one. Retain sufficient existing regressions without a unit '
                     'quota. Before adding an isolated test, state its uncovered obligation, why E2E cannot '
                     'observe it and each identified failure mode/valid alternative with expected result. Do '
                     'not add late tests merely mirroring implemented behavior or alter protected '
                     'expectations to fit output.',
 'E-replay': 'Retain each actual acceptance command/script, resolved cwd, runtime/environment, stable '
             'fixtures, contract-derived expected and observed results, raw child '
             'stdout/stderr/exit/signal/timeout and source/input/output hashes. Keep wrapper and child '
             'status separate; wrapper PASS never masks child failure. A claim without replay inputs or '
             'propagated child outcome is pending. Replay only on authorized disposable/fresh destinations, '
             'preserving original artifacts/fixtures byte-identically; outputs stay frozen during '
             'validation. Independent later audit remains possible and failed attempts retain their exact '
             'journals.',
 'E-optional-telemetry': 'The Markdown lifecycle ledger remains the universal current record, with one '
                         'truthful row/event per actual role and no historical backfill. Append schema-v2 '
                         'records after the preserved legacy section only through the current installed '
                         'template. Native telemetry/sidecars are optional: retain exact thread/Run ID, '
                         'observation source, field coverage and n/a when unavailable; no session '
                         'snapshot/time proximity may invent a role join or terminal clock. The old '
                         'tackle-usage/1 note is superseded by optional tackle-observability-telemetry/1. '
                         'Informational eval/scaffold/answer-isolation rules create no migration evaluation '
                         'campaign or held-out read; any separately authorized evaluation retains its '
                         'current integrity and no-answer-leak boundaries.',
 'E-v2-append': 'Append `Schema: tackle-observability/2` and the v2 lifecycle table below preserved legacy '
                'bytes, never replacing that table. After the marker write only the legal start, finish or '
                'observe-incomplete events. No historical row is rewritten/backfilled and adoption does not '
                'manufacture observations for previous roles.',
 'E-provenance': 'Read legacy and v2 records with their actual scope and report measured/eligible coverage. '
                 'Missing/n/a is unknown, not zero. Join role telemetry only on an exact run_id with '
                 'explicit reviewed mapping; session/account observations, timestamps, conversation IDs or '
                 'limit deltas stay separate and never become an invented role correlation.',
 'E-cost': 'Canonical provider cost requires an authoritative observed source. Keep local/API-equivalent '
           'estimates under their own labeled basis and never promote them to canonical cost, tokens or '
           'runtime telemetry. Missing cost remains n/a and optional sidecar failures never block task '
           'closure or refund consumed consultations.',
 'J-consent': 'The optional public capability is Judgement Layer; the present TypeSafe System One/Jev '
              'backend and `System One consent:` record syntax keep their compatibility meaning. Use the '
              'host typesafe-ai route only with that selected workspace’s recorded explicit answer. With an '
              'applicable configuration signal and no answer, PLAN/RUN asks once, records exact '
              'yes/no/date/actor there and retains an unanswered question without repetition; read-only '
              'STATUS only reads/detects. Never copy consent from a parent/neighbor, fabricate an answer or '
              'consult during migration. Original four uses stay compatible; '
              'bounded-recovery/evidence-signal require a declared upcoming consumer, compiled policy/public '
              'content, selected-owner consent and retained budget_scope. No request creates no new use, '
              'artifact, consultation budget, permission or acceptance.',
 'J-release-scope': 'The historical 10.1 statement that this release changes neither workspace schema nor '
                    'file formats applies to that release only. It is not a universal no-adapter exemption: '
                    'the actual selected pre-3/3/4/Lite source follows its supported structural route. '
                    'Preserve existing recorded System One consent meaning and raw identifier syntax; '
                    'changing the public label to Judgement Layer never creates or copies consent or '
                    'modernizes historical records.',
 'H-retro': 'Use current retro.tmpl.md recipes prospectively: Attempts accepts both `correction cycle N of '
            '3: <failure> → <correction>; <validation command>: <result>` and older `attempt N:` records. '
            'Gate accuracy counts distinct sessions across archive and current history and reports undated '
            'headings. Blocked durations excludes State snapshot lines. Preserve actual old bytes and '
            'counts; do not truncate history, backfill attempts or assign missing dates to improve a metric.',
 'H-policy': 'Preserve an existing workspace maintenance policy, or supply the current AGENTS template '
             'default prospectively when missing. An over-budget old entry remains unchanged. Separate '
             'archive policy requires explicit scoped authority and its actual size/age trigger; ordinary '
             'threshold400 and newest-five-session default apply only where that policy is current. '
             'Migration itself never archives or retires records. For a recent entry/short history, retain '
             'an explicit suitable History entry budget or the documented non-gating row13 warning instead '
             'of shrinking history or making WARN mandatory.',
 'H-readers': 'Use the current installed status.md cold-resume read order for the candidate’s own read '
              'lists, preserving current canonical sources and any legitimate wider-read condition. Do not '
              'introduce a second stale read-order source. Optional Judgement Layer/Jev retains the selected '
              'workspace’s recorded answer and is never silently consulted or given copied consent.',
 'H-metadata': 'Adopt optional context/projection/size-triggered metadata only for actual justified '
               'size/risk and required current consumers. Preserve original entries/indexes and validate '
               'source-backed views, stable references, archive integrity and exports on the copy. Record '
               'compaction/retirement has its own reversible prepare/verify/switch and separate policy '
               'authority; migration neither retires records nor drops old resolution before validated '
               'replacement.',
 'H-snapshots': 'For an existing reference-docs snapshot used by a current consumer, retain its real '
                'captured date/provenance; re-snapshot from the actual source only under explicit authorized '
                'prospective work. Row15 may skip undated historical files, which are not backfilled with '
                'invented dates. A workspace without such snapshots needs no new artifact.',
 'N-repositories': 'Only actual remaining multi-repository work needs a Repositories section with explicit '
                   'repository IDs, canonical paths and observed revisions in AGENTS.md, plus '
                   '`**Repository**: <id>` on its selected open briefs. A single-repository workspace adds '
                   'neither. Resolve actual current/selected consumer fields; closed historical repository '
                   'mentions alone do not create this obligation.',
 'Q-requirements': 'Create or update a source-anchored requirements base/delta only when an actual current '
                   'consumer or new change adds, changes or retires required behavior. Preserve full '
                   'upcoming-wave coverage and stable A-NN/source anchors where applicable; do not backfill '
                   'deltas/anchors for tasks or historical spec/constitution text merely because it existed '
                   'before adoption.',
 'W-standing': 'Build an optional `--initiative` page only under an owner request, following the installed '
               'plan view guide; it reads the root and one hop of declared sibling workspaces. An existing '
               'standing request permits one rebuild with installed plan_view.py after the final '
               'invalidating input change, retaining exact outputs and reviewing stderr. Without that '
               'request build no view. Resolve stale curated board prose by updating/removing it and remove '
               'leaked internal identifiers from requested export summary prose; do not overwrite product '
               'samples. Existing auxiliary pages move to the plan-view base only when the owner asks; '
               'preserve current one-hop and page-request ownership bounds.',
 'O-profile-ids': 'A profile entry without an ID remains readable. Only the next separately confirmed retro '
                  'that actually touches it assigns an ID/confidence under the existing learning policy; '
                  'migration writes no profile, seed or confidence and needs no profile-modernization '
                  'action.',
 'O-siblings': 'Sibling workspaces are optional. With none declared, create no sibling map or artifact. A '
               'concrete upcoming consumer may use explicitly declared relationships under current '
               'read/owner bounds; historical references alone are not an opt-in.',
 'O-rounds-validator': 'A verification round may keep findings.md, capped at three rounds unless `AGENTS.md` '
                       'sets `Verify round cap: N`. An `Acceptance validator:` line in `AGENTS.md` needs a '
                       "decision recording the owner's request. Neither needs a migration step. Preserve "
                       'existing scope/counters and do not run the validator or allocate a new round just to '
                       'migrate.',
 'O-directive-scopes': 'Retain an applicable learning directive’s actual action scope, including '
                       'commit-message/pre-push/release boundaries, and enforce it when that action occurs '
                       'rather than only at session start. Migration neither performs those actions nor '
                       'rewrites the profile; absence of a matching current action creates no artifact.',
 'O-no-companion': 'Planning uses the installed intake/simplicity/architecture guides and templates. The '
                   'removed companion-skill check does not authorize installing, recommending or fetching an '
                   'external planning dependency during migration. This informational change requires no '
                   'workspace edit.',
 'O-lenses': 'For a concrete upcoming consumer, optionally use the current simplicity ladder (need, reuse, '
             'standard library, native/installed dependency, one line, minimum code), security/architecture '
             'guidance and matching archetype. Lenses '
             'correctness/security/repro/performance/simplicity/polish stay opt-in and do not replace '
             'current independent review or become majority-vote authority by migration. Preserve '
             'absent/default single-checker behavior; never create an artifact, install dependency, copy an '
             'obsolete team block or rewrite old briefs merely to adopt a lens.',
 'O-learning': 'At session start consider project .tackle/profile.md, user ~/.tackle/user-profile.md and '
               'parked docs/seeds under current learning rules. Profile writes occur only through separately '
               'batch-confirmed retro; seed changes are deliberate. Migration neither writes those files nor '
               'copies a profile/consent into another workspace.',
 'O-right-size': 'For a small remaining plan (at most four tasks and no multi-track uncertainty), offer the '
                 'actual authorized Lite alternative only after risk precedence and owner selection. Do not '
                 'automatically collapse Full, infer Lite from missing artifacts, reopen closed work or '
                 'rewrite historical plans to reduce apparent size.',
 'V-warn13': 'Expect lint row13 WARN lines for dated entries after the newest State snapshot and for undated '
             'session headings. Preserve those diagnostics without promoting them to mandatory failures, '
             'inventing dates, dropping entries or editing history to obtain silence.',
 'V-current-lint': 'Run `python3 -I scripts/lint.py <slug>` on the copy and expect 19 of 19 rows silent. Repair a '
                   'finding from another row as its own guide states, and a closed brief only by erratum. '
                   'Retain documented non-gating WARN exceptions instead of treating this expected silent '
                   'control as permission to suppress warnings. Capture native raw bytes/exit and the '
                   'distinct pre-stamp phase before the final Z stamp/post-stamp check.',
 'V-native-diagnostic': 'Capture the current installed canonical lint rows1–19 on unchanged source and '
                        'selected candidate, preserving exact program/catalog/input/workspace identities, '
                        'raw stdout/stderr and native child exit/signal/timeout. A below5 source may '
                        'correctly report migrate first; retain it as a failed source diagnostic, never call '
                        'it green. Exercise actual missing briefs, dangling dependencies, alias/path '
                        'collisions, malformed states, superseded seals, loop budgets, Effort fields, '
                        'history/archive order and lifecycle usage where applicable. Correct prospective '
                        'source-backed findings only in the authorized copy; reanchor changed-source '
                        'citations at an explicit revision and keep inherited raw/replay inputs. Required '
                        'candidate FAIL/ERROR holds adoption; documented WARN rows8/13/15 stay nongating. '
                        'Read-only schema/next-wave/readiness/precondition/admission checks must prove '
                        'actual current S/A/V/Z mappings, not echo declarations; never run the upcoming '
                        'writing Check before adoption. Compare exact history/evidence/checkpoint/neighbor '
                        'hashes and restore a separate exact checkpoint probe to prove rollback. Independent '
                        'reviewer observations retain unknowns and actual failures.',
 'V-release-scope': 'Reuse observations only when every relevant consumed input remains unchanged. Migration '
                    'is not publication authority. A later separately requested release explicitly selects '
                    'its workspaces: all active workspaces retain mandatory lint/done-signal gates, selected '
                    'work additionally needs current global acceptance even if all tasks are closed, and the '
                    'union is counted once. Unselected historical/parked work reports nongating diagnostics. '
                    'Preserve current nine self-lint gates/catalog/full-registry requirements; neither old '
                    'gate counts nor historical green imply a current release PASS.',
 'Z-standard': 'After all required baselines and ordered actions, retain '
               'source/candidate/install/catalog/context identities and actual pre-stamp checks. Append '
               'exactly once the candidate-only preparation event to its existing root history carrier, '
               'preserving the entire old byte prefix and any separate structural-adoption entry. Append the '
               'exact UTF-8 preparation suffix with one leading LF and final LF: `\\n## {date} · Compact '
               'migration candidate\\n\\n- Prepared candidate: operation {operation_id}; source sha256 '
               '{source_sha256}; target Tackle {target_methodology}; catalog revision {revision}.\\n`. The '
               'displayed \\n denotes an actual LF. Use the validated context date, manifest-bound 64-hex '
               'operation_id/source_sha256, and validated pinned catalog semver target_methodology/positive '
               'integer revision, not caller text. It records candidate preparation only, never adoption, '
               'Ready or acceptance; a quoted/fenced occurrence is not the event. Validate actual unfenced '
               'Full dates in nondecreasing order and reconcile only exact pre-append identity or expected '
               'suffix/postinventory; missing/ambiguous history is pending and Lite gains no Full carrier. '
               'Then deliberately stamp the candidate, run distinct post-stamp checks and freeze it. Adopt '
               'only the validated copy at an evidenced task boundary with independent semantic/boundary '
               'admission, rechecked original/candidate/install/catalog/evidence hashes and actual '
               'cooperating locks before durable same-filesystem rename. Preserve checkpoint/original '
               'backup, record exact mappings/checks/revisions/rollback result, and reconcile interruptions '
               'only from matching physical inventories; conflicts hold without overwrite or cleanup. '
               'Restore only an unchanged adopted workspace through its verified sibling stage. A completed '
               'repeat validates its recorded physical/admission identity and changes no bytes. Historical '
               'intermediate release stamps, old command aliases and old selective/manual cutover recipes '
               'are provenance, not additional runtime steps. Use only the current pinned target/catalog '
               'operation; no migration creates Ready, completion, model permission or a release. Failure '
               'leaves the original authoritative except for the exact interrupted physical states that the '
               'recorded reconciliation can finish. For an unsupported or blocked route the owner may '
               'explicitly select a fresh remaining-work workspace, leaving the old source untouched.',
 'Z-final-stamp': 'After all required baselines and ordered actions, retain '
                  'source/candidate/install/catalog/context identities and actual pre-stamp checks. Append '
                  'exactly once the candidate-only preparation event to its existing root history carrier, '
                  'preserving the entire old byte prefix and any separate structural-adoption entry. Append '
                  'the exact UTF-8 preparation suffix with one leading LF and final LF: `\\n## {date} · '
                  'Compact migration candidate\\n\\n- Prepared candidate: operation {operation_id}; source '
                  'sha256 {source_sha256}; target Tackle {target_methodology}; catalog revision '
                  '{revision}.\\n`. The displayed \\n denotes an actual LF. Use the validated context date, '
                  'manifest-bound 64-hex operation_id/source_sha256, and validated pinned catalog semver '
                  'target_methodology/positive integer revision, not caller text. It records candidate '
                  'preparation only, never adoption, Ready or acceptance; a quoted/fenced occurrence is not '
                  'the event. Validate actual unfenced Full dates in nondecreasing order and reconcile only '
                  'exact pre-append identity or expected suffix/postinventory; missing/ambiguous history is '
                  'pending and Lite gains no Full carrier. Then deliberately stamp the candidate, run '
                  'distinct post-stamp checks and freeze it. Adopt only the validated copy at an evidenced '
                  'task boundary with independent semantic/boundary admission, rechecked '
                  'original/candidate/install/catalog/evidence hashes and actual cooperating locks before '
                  'durable same-filesystem rename. Preserve checkpoint/original backup, record exact '
                  'mappings/checks/revisions/rollback result, and reconcile interruptions only from matching '
                  'physical inventories; conflicts hold without overwrite or cleanup. Restore only an '
                  'unchanged adopted workspace through its verified sibling stage. A completed repeat '
                  'validates its recorded physical/admission identity and changes no bytes. Last, set the '
                  '`**Methodology: Tackle 10.4.0**` line in the candidate AGENTS.md only after the baseline '
                  'covers every Complete task. Then run `python3 -I scripts/lint.py <slug>` again and expect 19 of 19 '
                  'rows silent, retaining non-gating WARN exceptions. From now on row 14 requires that line '
                  'in each Complete report. The stamped candidate remains unadopted until separate verified '
                  'cutover; the source stamp is never silently changed. This target keeps '
                  '`tackle-workspace/5` and adds no required workspace field; supported structural adapters '
                  'act only on actual older source structure, not on an old stamp alone.',
 'Z-links-replay': 'After all required baselines and ordered actions, retain '
                   'source/candidate/install/catalog/context identities and actual pre-stamp checks. Append '
                   'exactly once the candidate-only preparation event to its existing root history carrier, '
                   'preserving the entire old byte prefix and any separate structural-adoption entry. Append '
                   'the exact UTF-8 preparation suffix with one leading LF and final LF: `\\n## {date} · '
                   'Compact migration candidate\\n\\n- Prepared candidate: operation {operation_id}; source '
                   'sha256 {source_sha256}; target Tackle {target_methodology}; catalog revision '
                   '{revision}.\\n`. The displayed \\n denotes an actual LF. Use the validated context date, '
                   'manifest-bound 64-hex operation_id/source_sha256, and validated pinned catalog semver '
                   'target_methodology/positive integer revision, not caller text. It records candidate '
                   'preparation only, never adoption, Ready or acceptance; a quoted/fenced occurrence is not '
                   'the event. Validate actual unfenced Full dates in nondecreasing order and reconcile only '
                   'exact pre-append identity or expected suffix/postinventory; missing/ambiguous history is '
                   'pending and Lite gains no Full carrier. Then deliberately stamp the candidate, run '
                   'distinct post-stamp checks and freeze it. Adopt only the validated copy at an evidenced '
                   'task boundary with independent semantic/boundary admission, rechecked '
                   'original/candidate/install/catalog/evidence hashes and actual cooperating locks before '
                   'durable same-filesystem rename. Preserve checkpoint/original backup, record exact '
                   'mappings/checks/revisions/rollback result, and reconcile interruptions only from '
                   'matching physical inventories; conflicts hold without overwrite or cleanup. Restore only '
                   'an unchanged adopted workspace through its verified sibling stage. A completed repeat '
                   'validates its recorded physical/admission identity and changes no bytes. Retain every '
                   'exact old title/anchor used by an incoming link, or add that exact old anchor in the '
                   'selected candidate and test the current incoming consumers before adoption; a static '
                   'template alias cannot redirect every past title. Use installed schema adapters, not the '
                   'historical inline candidate_board program. Preserve its observed legacy state/grade map '
                   'and original reports; the mapping is provenance beside the checkpoint, never a second '
                   'current-state or readiness source.',
 'Z-rollback-sentinels': 'After all required baselines and ordered actions, retain '
                         'source/candidate/install/catalog/context identities and actual pre-stamp checks. '
                         'Append exactly once the candidate-only preparation event to its existing root '
                         'history carrier, preserving the entire old byte prefix and any separate '
                         'structural-adoption entry. Append the exact UTF-8 preparation suffix with one '
                         'leading LF and final LF: `\\n## {date} · Compact migration candidate\\n\\n- '
                         'Prepared candidate: operation {operation_id}; source sha256 {source_sha256}; '
                         'target Tackle {target_methodology}; catalog revision {revision}.\\n`. The '
                         'displayed \\n denotes an actual LF. Use the validated context date, manifest-bound '
                         '64-hex operation_id/source_sha256, and validated pinned catalog semver '
                         'target_methodology/positive integer revision, not caller text. It records '
                         'candidate preparation only, never adoption, Ready or acceptance; a quoted/fenced '
                         'occurrence is not the event. Validate actual unfenced Full dates in nondecreasing '
                         'order and reconcile only exact pre-append identity or expected '
                         'suffix/postinventory; missing/ambiguous history is pending and Lite gains no Full '
                         'carrier. Then deliberately stamp the candidate, run distinct post-stamp checks and '
                         'freeze it. Adopt only the validated copy at an evidenced task boundary with '
                         'independent semantic/boundary admission, rechecked '
                         'original/candidate/install/catalog/evidence hashes and actual cooperating locks '
                         'before durable same-filesystem rename. Preserve checkpoint/original backup, record '
                         'exact mappings/checks/revisions/rollback result, and reconcile interruptions only '
                         'from matching physical inventories; conflicts hold without overwrite or cleanup. '
                         'Restore only an unchanged adopted workspace through its verified sibling stage. A '
                         'completed repeat validates its recorded physical/admission identity and changes no '
                         'bytes. The rollback rehearsal retains the exact original log/usage/evidence bytes '
                         'and neighboring sentinel; never repair live history or discard required '
                         'replay/rollback evidence. Disposal of an owned disposable probe is separate scoped '
                         'authority, not automatic cleanup of job/original/foreign files.',
 'Z-release-and-physical': 'After all required baselines and ordered actions, retain '
                           'source/candidate/install/catalog/context identities and actual pre-stamp checks. '
                           'Append exactly once the candidate-only preparation event to its existing root '
                           'history carrier, preserving the entire old byte prefix and any separate '
                           'structural-adoption entry. Append the exact UTF-8 preparation suffix with one '
                           'leading LF and final LF: `\\n## {date} · Compact migration candidate\\n\\n- '
                           'Prepared candidate: operation {operation_id}; source sha256 {source_sha256}; '
                           'target Tackle {target_methodology}; catalog revision {revision}.\\n`. The '
                           'displayed \\n denotes an actual LF. Use the validated context date, '
                           'manifest-bound 64-hex operation_id/source_sha256, and validated pinned catalog '
                           'semver target_methodology/positive integer revision, not caller text. It records '
                           'candidate preparation only, never adoption, Ready or acceptance; a quoted/fenced '
                           'occurrence is not the event. Validate actual unfenced Full dates in '
                           'nondecreasing order and reconcile only exact pre-append identity or expected '
                           'suffix/postinventory; missing/ambiguous history is pending and Lite gains no '
                           'Full carrier. Then deliberately stamp the candidate, run distinct post-stamp '
                           'checks and freeze it. Adopt only the validated copy at an evidenced task '
                           'boundary with independent semantic/boundary admission, rechecked '
                           'original/candidate/install/catalog/evidence hashes and actual cooperating locks '
                           'before durable same-filesystem rename. Preserve checkpoint/original backup, '
                           'record exact mappings/checks/revisions/rollback result, and reconcile '
                           'interruptions only from matching physical inventories; conflicts hold without '
                           'overwrite or cleanup. Restore only an unchanged adopted workspace through its '
                           'verified sibling stage. A completed repeat validates its recorded '
                           'physical/admission identity and changes no bytes. Retain actual physical '
                           'observations and current source/neighbor/checkpoint hashes for selected active '
                           'work with completed/blocked/skipped/interrupted records, changed contract and '
                           'legacy request interpretation; a boolean is insufficient. A later release needs '
                           'a separate owner order, explicit selected paths and current global acceptance '
                           'for each selected workspace, plus mandatory checks on all active work; count '
                           'their union once and keep unselected historical/parked diagnostics nongating. No '
                           'empty board or old closure infers scope.',
 'Z-v2-rollback': 'After all required baselines and ordered actions, retain '
                  'source/candidate/install/catalog/context identities and actual pre-stamp checks. Append '
                  'exactly once the candidate-only preparation event to its existing root history carrier, '
                  'preserving the entire old byte prefix and any separate structural-adoption entry. Append '
                  'the exact UTF-8 preparation suffix with one leading LF and final LF: `\\n## {date} · '
                  'Compact migration candidate\\n\\n- Prepared candidate: operation {operation_id}; source '
                  'sha256 {source_sha256}; target Tackle {target_methodology}; catalog revision '
                  '{revision}.\\n`. The displayed \\n denotes an actual LF. Use the validated context date, '
                  'manifest-bound 64-hex operation_id/source_sha256, and validated pinned catalog semver '
                  'target_methodology/positive integer revision, not caller text. It records candidate '
                  'preparation only, never adoption, Ready or acceptance; a quoted/fenced occurrence is not '
                  'the event. Validate actual unfenced Full dates in nondecreasing order and reconcile only '
                  'exact pre-append identity or expected suffix/postinventory; missing/ambiguous history is '
                  'pending and Lite gains no Full carrier. Then deliberately stamp the candidate, run '
                  'distinct post-stamp checks and freeze it. Adopt only the validated copy at an evidenced '
                  'task boundary with independent semantic/boundary admission, rechecked '
                  'original/candidate/install/catalog/evidence hashes and actual cooperating locks before '
                  'durable same-filesystem rename. Preserve checkpoint/original backup, record exact '
                  'mappings/checks/revisions/rollback result, and reconcile interruptions only from matching '
                  'physical inventories; conflicts hold without overwrite or cleanup. Restore only an '
                  'unchanged adopted workspace through its verified sibling stage. A completed repeat '
                  'validates its recorded physical/admission identity and changes no bytes. Legacy '
                  'telemetry/sidecar schemas remain historical; current optional telemetry uses '
                  'tackle-observability-telemetry/1 while the Markdown ledger stays universal. Restore exact '
                  'checkpoint bytes through the physical operation rather than deleting rows/markers in live '
                  'history. Optional telemetry failure does not block closure and adoption never requires '
                  'historical backfill.'}
ORIGIN_RECIPE = {'["G","v8.4 → v9.0 checklist",1]': 'I-owner-archetypes',
 '["G","v8.4 → v9.0 checklist",2]': 'S-supported-adapters',
 '["G","v8.4 → v9.0 checklist",3]': 'B-scope-effort',
 '["G","v8.4 → v9.0 checklist",4]': 'A-forward-requests',
 '["G","v8.4 → v9.0 checklist",5]': 'O-profile-ids',
 '["G","v8.4 → v9.0 checklist",6]': 'M-map',
 '["G","v8.4 → v9.0 checklist",7]': 'Z-standard',
 '["G","v9.2 → v9.3 checklist",1]': 'W-standing',
 '["G","v9.2 → v9.3 checklist",2]': 'O-siblings',
 '["G","v9.3 → v10.0 checklist",1]': 'I-retired-producer',
 '["G","v9.3 → v10.0 checklist",2]': 'W-standing',
 '["G","v9.3 → v10.0 checklist",3]': 'I-installed-programs',
 '["G","v9.3 → v10.0 checklist",4]': 'E-script-identity',
 '["G","v9.3 → v10.0 checklist",5]': 'J-consent',
 '["G","v10.0 → v10.1 checklist",1]': 'S-gates',
 '["G","v10.0 → v10.1 checklist",2]': 'E-corrections',
 '["G","v10.0 → v10.1 checklist",3]': 'E-clocks',
 '["G","v10.0 → v10.1 checklist",4]': 'E-clocks',
 '["G","v10.0 → v10.1 checklist",5]': 'H-retro',
 '["G","v10.0 → v10.1 checklist",6]': 'V-warn13',
 '["G","v10.0 → v10.1 checklist",7]': 'W-standing',
 '["G","v10.0 → v10.1 checklist",8]': 'B-forbidden',
 '["G","v10.0 → v10.1 checklist",9]': 'J-release-scope',
 '["G","v10.1 → v10.2 checklist",1]': 'P-selected-checkpoint',
 '["G","v10.1 → v10.2 checklist",2]': 'R-hash',
 '["G","v10.1 → v10.2 checklist",3]': 'R-baseline',
 '["G","v10.1 → v10.2 checklist",4]': 'R-erratum',
 '["G","v10.1 → v10.2 checklist",5]': 'B-detail',
 '["G","v10.1 → v10.2 checklist",6]': 'B-symbols',
 '["G","v10.1 → v10.2 checklist",7]': 'B-decision-clauses',
 '["G","v10.1 → v10.2 checklist",8]': 'V-current-lint',
 '["G","v10.1 → v10.2 checklist",9]': 'A-current-lineage',
 '["G","v10.1 → v10.2 checklist",10]': 'O-rounds-validator',
 '["G","v10.1 → v10.2 checklist",11]': 'Z-final-stamp',
 '["H","v9.2.0 → v9.2.1 checklist",1]': 'P-selected-checkpoint',
 '["H","v9.2.0 → v9.2.1 checklist",2]': 'W-standing',
 '["H","v9.2.0 → v9.2.1 checklist",3]': 'Z-standard',
 '["H","v9.1 → v9.2 checklist",1]': 'P-selected-checkpoint',
 '["H","v9.1 → v9.2 checklist",2]': 'B-runnable-case',
 '["H","v9.1 → v9.2 checklist",3]': 'N-repositories',
 '["H","v9.1 → v9.2 checklist",4]': 'Q-requirements',
 '["H","v9.1 → v9.2 checklist",5]': 'Z-standard',
 '["H","v9.1.0 → v9.1.1 checklist",1]': 'P-selected-checkpoint',
 '["H","v9.1.0 → v9.1.1 checklist",2]': 'E-current-closure',
 '["H","v9.1.0 → v9.1.1 checklist",3]': 'M-confirmation',
 '["H","v9.1.0 → v9.1.1 checklist",4]': 'J-consent',
 '["H","v9.1.0 → v9.1.1 checklist",5]': 'W-standing',
 '["H","v9.1.0 → v9.1.1 checklist",6]': 'Z-standard',
 '["H","v9.0 → v9.1 checklist",1]': 'P-selected-checkpoint',
 '["H","v9.0 → v9.1 checklist",2]': 'V-native-diagnostic',
 '["H","v9.0 → v9.1 checklist",3]': 'R-remains',
 '["H","v9.0 → v9.1 checklist",4]': 'R-obligations',
 '["H","v9.0 → v9.1 checklist",5]': 'H-policy',
 '["H","v9.0 → v9.1 checklist",6]': 'E-adversary-boundary',
 '["H","v9.0 → v9.1 checklist",7]': 'H-readers',
 '["H","v9.0 → v9.1 checklist",8]': 'Z-standard',
 '["H","v9.0.0 → v9.0.1 checklist",1]': 'P-selected-checkpoint',
 '["H","v9.0.0 → v9.0.1 checklist",2]': 'M-map',
 '["H","v9.0.0 → v9.0.1 checklist",3]': 'M-map',
 '["H","v9.0.0 → v9.0.1 checklist",4]': 'B-blocker-report',
 '["H","v9.0.0 → v9.0.1 checklist",5]': 'Z-standard',
 '["H","v9.0.0 → v9.0.1 checklist",6]': 'E-lifecycle-validity',
 '["H","v8.4.0 → v8.4.1 checklist",1]': 'P-selected-checkpoint',
 '["H","v8.4.0 → v8.4.1 checklist",2]': 'V-native-diagnostic',
 '["H","v8.4.0 → v8.4.1 checklist",3]': 'B-retired-flag',
 '["H","v8.4.0 → v8.4.1 checklist",4]': 'B-clause-seal',
 '["H","v8.4.0 → v8.4.1 checklist",5]': 'Z-standard',
 '["H","v8.3 → v8.4 checklist",1]': 'P-selected-checkpoint',
 '["H","v8.3 → v8.4 checklist",2]': 'A-pinned-state',
 '["H","v8.3 → v8.4 checklist",3]': 'S-supported-adapters',
 '["H","v8.3 → v8.4 checklist",4]': 'V-native-diagnostic',
 '["H","v8.3 → v8.4 checklist",5]': 'Z-standard',
 '["H","v8.2 → v8.3 checklist",1]': 'P-selected-checkpoint',
 '["H","v8.2 → v8.3 checklist",2]': 'E-test-selection',
 '["H","v8.2 → v8.3 checklist",3]': 'E-replay',
 '["H","v8.2 → v8.3 checklist",4]': 'Z-standard',
 '["H","v8.2.0 → v8.2.1 checklist",1]': 'P-selected-checkpoint',
 '["H","v8.2.0 → v8.2.1 checklist",2]': 'E-optional-telemetry',
 '["H","v8.2.0 → v8.2.1 checklist",3]': 'Z-standard',
 '["H","v8.1 → v8.2 checklist",1]': 'P-selected-checkpoint',
 '["H","v8.1 → v8.2 checklist",2]': 'B-aliases',
 '["H","v8.1 → v8.2 checklist",3]': 'A-pinned-state',
 '["H","v8.1 → v8.2 checklist",4]': 'B-wave-contract',
 '["H","v8.1 → v8.2 checklist",5]': 'H-metadata',
 '["H","v8.1 → v8.2 checklist",6]': 'Z-links-replay',
 '["H","v8.0 → v8.1 checklist",1]': 'P-selected-checkpoint',
 '["H","v8.0 → v8.1 checklist",2]': 'A-forward-requests',
 '["H","v8.0 → v8.1 checklist",3]': 'B-wave-contract',
 '["H","v8.0 → v8.1 checklist",4]': 'V-release-scope',
 '["H","v8.0 → v8.1 checklist",5]': 'Z-standard',
 '["H","Historical migration shape",1]': 'S-supported-adapters',
 '["H","Historical migration shape",2]': 'P-preserve-settled',
 '["H","Historical migration shape",3]': 'A-pinned-state',
 '["H","Historical migration shape",4]': 'B-wave-contract',
 '["H","Historical migration shape",5]': 'B-wave-contract',
 '["H","Historical migration shape",6]': 'V-native-diagnostic',
 '["H","v7.3 → v8.0 checklist",1]': 'P-selected-checkpoint',
 '["H","v7.3 → v8.0 checklist",2]': 'P-preserve-settled',
 '["H","v7.3 → v8.0 checklist",3]': 'B-wave-contract',
 '["H","v7.3 → v8.0 checklist",4]': 'A-pinned-state',
 '["H","v7.3 → v8.0 checklist",5]': 'E-current-closure',
 '["H","v7.3 → v8.0 checklist",6]': 'Z-rollback-sentinels',
 '["H","v7.3 → v8.0 checklist",7]': 'Z-release-and-physical',
 '["H","v7.0 → v7.1 checklist",1]': 'I-old-helper-disposition',
 '["H","v7.0 → v7.1 checklist",2]': 'I-installed-programs',
 '["H","v7.0 → v7.1 checklist",3]': 'A-forward-requests',
 '["H","v7.0 → v7.1 checklist",4]': 'I-private-planning',
 '["H","v7.0 → v7.1 checklist",5]': 'E-optional-telemetry',
 '["H","v7.0 → v7.1 checklist",6]': 'Z-standard',
 '["H","v7.1 → v7.2 checklist",1]': 'P-preserve-settled',
 '["H","v7.1 → v7.2 checklist",2]': 'E-v2-append',
 '["H","v7.1 → v7.2 checklist",3]': 'E-provenance',
 '["H","v7.1 → v7.2 checklist",4]': 'E-provenance',
 '["H","v7.1 → v7.2 checklist",5]': 'E-cost',
 '["H","v7.1 → v7.2 checklist",6]': 'V-native-diagnostic',
 '["H","v7.1 → v7.2 checklist",7]': 'Z-v2-rollback',
 '["H","v7.2 → v7.3 checklist",1]': 'B-self-contained',
 '["H","v7.2 → v7.3 checklist",2]': 'B-runnable-case',
 '["H","v7.2 → v7.3 checklist",3]': 'E-replay',
 '["H","v7.2 → v7.3 checklist",4]': 'B-json-contract',
 '["H","v7.2 → v7.3 checklist",5]': 'Z-standard',
 '["H","v6.1 → v7.0 checklist",1]': 'A-forward-requests',
 '["H","v6.1 → v7.0 checklist",2]': 'I-obsolete-artifact-disposition',
 '["H","v6.1 → v7.0 checklist",3]': 'A-forward-requests',
 '["H","v6.1 → v7.0 checklist",4]': 'Z-standard',
 '["H","v6.1 → v7.0 checklist",5]': 'V-native-diagnostic',
 '["H","v6.0 → v6.1 checklist",1]': 'E-optional-telemetry',
 '["H","v6.0 → v6.1 checklist",2]': 'E-optional-telemetry',
 '["H","v6.0 → v6.1 checklist",3]': 'Z-standard',
 '["H","v5.6 → v6.0 checklist",1]': 'E-optional-telemetry',
 '["H","v5.6 → v6.0 checklist",2]': 'E-optional-telemetry',
 '["H","v5.6 → v6.0 checklist",3]': 'Z-standard',
 '["H","v5.5 → v5.6 checklist",1]': 'R-close-provenance',
 '["H","v5.5 → v5.6 checklist",2]': 'H-snapshots',
 '["H","v5.5 → v5.6 checklist",3]': 'O-directive-scopes',
 '["H","v5.5 → v5.6 checklist",4]': 'Z-standard',
 '["H","v5.4 → v5.5 checklist",1]': 'H-policy',
 '["H","v5.4 → v5.5 checklist",2]': 'B-grounding',
 '["H","v5.4 → v5.5 checklist",3]': 'Z-standard',
 '["H","v5.3 → v5.4 checklist",1]': 'V-release-scope',
 '["H","v5.3 → v5.4 checklist",2]': 'Z-standard',
 '["H","v5.2 → v5.3 checklist",1]': 'B-grounding',
 '["H","v5.2 → v5.3 checklist",2]': 'B-grounding',
 '["H","v5.2 → v5.3 checklist",3]': 'B-grounding',
 '["H","v5.2 → v5.3 checklist",4]': 'B-grounding',
 '["H","v5.2 → v5.3 checklist",5]': 'V-native-diagnostic',
 '["H","v5.2 → v5.3 checklist",6]': 'Z-standard',
 '["H","v5.1 → v5.2 checklist",1]': 'E-optional-telemetry',
 '["H","v5.1 → v5.2 checklist",2]': 'M-map',
 '["H","v5.1 → v5.2 checklist",3]': 'M-map',
 '["H","v5.1 → v5.2 checklist",4]': 'V-native-diagnostic',
 '["H","v5.1 → v5.2 checklist",5]': 'B-runnable-case',
 '["H","v5.1 → v5.2 checklist",6]': 'Z-standard',
 '["H","v5.0 → v5.1 checklist",1]': 'O-no-companion',
 '["H","v5.0 → v5.1 checklist",2]': 'B-intake-communication',
 '["H","v5.0 → v5.1 checklist",3]': 'O-lenses',
 '["H","v5.0 → v5.1 checklist",4]': 'O-lenses',
 '["H","v5.0 → v5.1 checklist",5]': 'B-intake-communication',
 '["H","v5.0 → v5.1 checklist",6]': 'Z-standard',
 '["H","v4.4 → v5.0 checklist",1]': 'E-current-closure',
 '["H","v4.4 → v5.0 checklist",2]': 'V-native-diagnostic',
 '["H","v4.4 → v5.0 checklist",3]': 'Z-standard',
 '["H","v4.3 → v4.4 checklist",1]': 'A-forward-requests',
 '["H","v4.3 → v4.4 checklist",2]': 'Z-standard',
 '["H","v4.2 → v4.3 checklist",1]': 'E-current-closure',
 '["H","v4.2 → v4.3 checklist",2]': 'E-current-closure',
 '["H","v4.2 → v4.3 checklist",3]': 'Z-standard',
 '["H","v4.1 → v4.2 checklist",1]': 'E-current-closure',
 '["H","v4.1 → v4.2 checklist",2]': 'Z-standard',
 '["H","v4.0 → v4.1 checklist",1]': 'I-self-update-superseded',
 '["H","v4.0 → v4.1 checklist",2]': 'O-lenses',
 '["H","v4.0 → v4.1 checklist",3]': 'Z-standard',
 '["H","v3.4 → v4.0 checklist",1]': 'B-type-and-dependencies',
 '["H","v3.4 → v4.0 checklist",2]': 'B-type-and-dependencies',
 '["H","v3.4 → v4.0 checklist",3]': 'O-lenses',
 '["H","v3.4 → v4.0 checklist",4]': 'A-no-grade-backfill',
 '["H","v3.4 → v4.0 checklist",5]': 'M-autonomy',
 '["H","v3.4 → v4.0 checklist",6]': 'V-native-diagnostic',
 '["H","v3.4 → v4.0 checklist",7]': 'O-lenses',
 '["H","v3.4 → v4.0 checklist",8]': 'Z-standard',
 '["H","v3.3 → v3.4 checklist",1]': 'A-skipped-status',
 '["H","v3.3 → v3.4 checklist",2]': 'O-learning',
 '["H","v3.3 → v3.4 checklist",3]': 'V-native-diagnostic',
 '["H","v3.3 → v3.4 checklist",4]': 'Z-standard',
 '["H","v3.2 → v3.3 checklist",1]': 'M-map',
 '["H","v3.2 → v3.3 checklist",2]': 'R-close-provenance',
 '["H","v3.2 → v3.3 checklist",3]': 'Z-standard',
 '["H","v3.0 → v3.1 checklist",1]': 'B-intent',
 '["H","v3.0 → v3.1 checklist",2]': 'E-corrections',
 '["H","v3.0 → v3.1 checklist",3]': 'E-current-closure',
 '["H","v3.0 → v3.1 checklist",4]': 'B-triviality',
 '["H","v3.0 → v3.1 checklist",5]': 'E-replay',
 '["H","v3.0 → v3.1 checklist",6]': 'Z-standard',
 '["H","Artifact renames",1]': 'S-old-layout-map',
 '["H","Artifact renames",2]': 'S-current-links',
 '["H","Artifact renames",3]': 'P-historical-only',
 '["H","Artifact renames",4]': 'Z-standard',
 '["H","Historical structural conformance",1]': 'S-plan-identities',
 '["H","Historical structural conformance",2]': 'A-board-sole-state',
 '["H","Historical structural conformance",3]': 'A-skipped-status',
 '["H","Historical structural conformance",4]': 'B-traces',
 '["H","Historical citations",1]': 'B-grounding',
 '["H","v2.1 → v3.0 checklist",1]': 'B-grounding',
 '["H","v2.1 → v3.0 checklist",2]': 'E-replay',
 '["H","v2.1 → v3.0 checklist",3]': 'B-clause-seal',
 '["H","v2.1 → v3.0 checklist",4]': 'V-native-diagnostic',
 '["H","v2.1 → v3.0 checklist",5]': 'B-grounding',
 '["H","v2.1 → v3.0 checklist",6]': 'M-autonomy',
 '["H","v2.1 → v3.0 checklist",7]': 'E-current-closure',
 '["H","v2.1 → v3.0 checklist",8]': 'M-map',
 '["H","v2.1 → v3.0 checklist",9]': 'Z-standard',
 '["H","v2.0 → v2.1.0 checklist",1]': 'A-board-sole-state',
 '["H","v2.0 → v2.1.0 checklist",2]': 'B-traces',
 '["H","v2.0 → v2.1.0 checklist",3]': 'B-grounding',
 '["H","v2.0 → v2.1.0 checklist",4]': 'B-runnable-case',
 '["H","v2.0 → v2.1.0 checklist",5]': 'O-right-size',
 '["H","v2.0 → v2.1.0 checklist",6]': 'Q-requirements',
 '["H","v2.0 → v2.1.0 checklist",7]': 'M-map',
 '["H","v2.0 → v2.1.0 checklist",8]': 'V-native-diagnostic',
 '["H","v2.0 → v2.1.0 checklist",9]': 'Z-standard'}
LITERAL_CONTRACTS = {'S-gates': ['Gate: Full', 'line 3', 'title on line 1', 'Gate: Lite'],
 'R-hash': ['sha256sum <brief>', 'shasum -a 256 <brief>'],
 'R-baseline': ['**Brief sha256**: <64 lowercase hex digits>',
                'Brief sha256 T-NN: <the same hash>',
                'Final status:',
                '**Remains**:'],
 'R-erratum': ['**Brief erratum**: D-NN · sha256 <hash after the edit>'],
 'B-detail': ['- **Detail**: full', '- **Detail**: interface'],
 'B-symbols': ['**Produces**', '**Consumes**', 'from T-NN', 'from T-NN [sibling]', 'exists', 'Depends on'],
 'B-decision-clauses': ['**Owner**: T-NN · **Clauses**: C-xx', '**Supersedes**', '⤴ superseded by D-NN'],
 'E-clocks': ['YYYY-MM-DDTHH:MM:SS[.fff](Z|±HH:MM)', 'n/a'],
 'E-corrections': ['correction cycle N of 3: <failure> → <correction>; <validation command>: <result>',
                   'attempt N:'],
 'J-consent': ['System One consent:', 'typesafe-ai', 'budget_scope'],
 'O-rounds-validator': ['Verify round cap: N', 'Acceptance validator:'],
 'Z-final-stamp': ['**Methodology: Tackle 10.4.0**']}


def fail(message):
    raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def loads(data):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                fail("duplicate JSON key: " + key)
            out[key] = value
        return out
    return json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda value: fail("nonfinite JSON"))


def exact(obj, keys, label):
    if type(obj) is not dict or set(obj) != set(keys):
        fail("invalid " + label + " keys")


def item_id(source, heading, index):
    return json.dumps([source, heading, index], ensure_ascii=False, separators=(",", ":"))


def wording(text):
    """Finite reviewed equivalence; never infer semantic truth from arbitrary prose.

    For example 'the edit requires an active decision' retains exactly the authority
    of 'an active decision authorizes the edit'. Negated, reordered or missing
    substantive clauses do not acquire coverage by placing a few keywords nearby.
    Literal command/receipt contracts are checked separately without normalization.
    """
    value = unicodedata.normalize("NFKC", text).replace("’", "'").replace("–", "-")
    value = re.sub(r"[`*]", "", value).casefold()
    value = " ".join(value.split())
    alternatives = (
        ("the edit requires an active decision", "an active decision authorizes the edit"),
        ("when sha256sum is unavailable", "without sha256sum"),
        ("only if explicitly requested by the owner", "only under an owner request"),
        ("only on an explicit owner request", "only under an owner request"),
        ("adopt only a copy that passed validation", "adopt only the validated copy"),
        ("repeating a completed operation has no further effect", "a completed repeat changes no bytes"),
    )
    for alternative, canonical in alternatives:
        value = value.replace(alternative, canonical)
    value = re.sub(r"\b(?:do not|must not|shall not)\b", "never", value)
    return " ".join(re.sub(r"[,:;.!?]+", " ", value).split())


def instruction_text(text, recipe):
    if wording(text) != wording(CURRENT_RECIPES[recipe]):
        fail("incomplete or conflicting current instruction: " + recipe)
    for literal in LITERAL_CONTRACTS.get(recipe, ()):
        if literal not in text:
            fail("current literal contract missing: " + recipe + ": " + literal)
    if recipe.startswith("Z-"):
        event = (r"\n## {date} · Compact migration candidate\n\n"
                 r"- Prepared candidate: operation {operation_id}; source sha256 {source_sha256}; "
                 r"target Tackle {target_methodology}; catalog revision {revision}.\n")
        if event not in text:
            fail("exact candidate preparation event missing")


def regular_resource(root, relative):
    current = root
    parts = Path(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        mode = current.lstat().st_mode
        if stat.S_ISLNK(mode):
            fail("aliased installed resource: " + relative)
        if index < len(parts) - 1 and not stat.S_ISDIR(mode):
            fail("non-directory resource component: " + relative)
        if index == len(parts) - 1 and (not stat.S_ISREG(mode) or current.stat().st_size == 0):
            fail("missing or non-regular installed resource: " + relative)
    return current


def retained_sources(history):
    marker = b"## Original guide context for the retained installed migration source\n"
    if history.count(marker) != 1:
        fail("retained G snapshot marker missing or ambiguous")
    prefix, tail = history.split(marker, 1)
    opening = b"````markdown\n"
    closing = b"````\n"
    if opening not in tail:
        fail("retained G snapshot fence missing")
    rest = tail.split(opening, 1)[1]
    if closing not in rest:
        fail("retained G snapshot fence unclosed")
    glines = rest.split(closing, 1)[0].splitlines(keepends=True)
    # Retained bytes include original line43's anchor before original header44.
    # G's canonical inclusive coordinates begin at44: remove only that known
    # preceding anchor from the in-memory line view, never from retained bytes.
    if glines and glines[0] == b'<a id="v84--v90-checklist"></a>\n':
        glines = glines[1:]
    if not glines or glines[0] != '## v8.4 → v9.0 checklist\n'.encode("utf-8"):
        fail("retained G original line44 header missing")
    return prefix.splitlines(keepends=True), glines


def source_lines(lines, source, start, end):
    if source not in {"G", "H"}:
        fail("unknown retained source")
    base = 1 if source == "H" else 44
    low, high = start - base, end - base + 1
    if low < 0 or high > len(lines) or high <= low:
        fail("source span outside retained snapshot")
    return lines[low:high]


def validate(root):
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        fail("repository root is not a regular directory")
    # Resolve the trusted caller-supplied repository boundary once (including OS
    # temporary-directory aliases); every resource below it is checked no-follow.
    root = root.resolve(strict=True)
    required_resources = (
        "skills/tackle/SKILL.md",
        "skills/tackle/references/guides/migrate.md",
        "skills/tackle/references/guides/migration-catalog.json",
        "skills/tackle/references/guides/run-card.md",
        "skills/tackle/references/guides/plan-card.md",
        "skills/tackle/references/guides/verify.md",
        "skills/tackle/references/guides/run.md",
        "skills/tackle/references/guides/status.md",
        "skills/tackle/references/guides/system-one.md",
        "skills/tackle/references/guides/plan-view.md",
        "skills/tackle/references/guides/requirements-base.md",
        "skills/tackle/references/guides/communication.md",
        "skills/tackle/references/guides/context-lifecycle.md",
        "skills/tackle/references/guides/record-lifecycle.md",
        "skills/tackle/references/guides/design-and-contract.md",
        "skills/tackle/references/guides/retro.md",
        "skills/tackle/references/guides/lint-spec.md",
        "skills/tackle/references/task.tmpl.md",
        "skills/tackle/references/task-board.tmpl.md",
        "skills/tackle/references/plan.tmpl.md",
        "skills/tackle/references/lite-plan.tmpl.md",
        "skills/tackle/references/AGENTS.tmpl.md",
        "skills/tackle/references/history.tmpl.md",
        "skills/tackle/references/resource-usage.tmpl.md",
        "skills/tackle/references/retro.tmpl.md",
        "skills/tackle/references/terminology.md",
        "skills/tackle/scripts/README.md",
        "skills/tackle/scripts/migrate/compact.py",
        "skills/tackle/scripts/migrate/schema.py",
        "skills/tackle/scripts/migrate/step_pre3_to_3.py",
        "skills/tackle/scripts/migrate/step_3_to_4.py",
        "skills/tackle/scripts/migrate/step_4_to_5.py",
        "skills/tackle/scripts/context_bundle.py",
        "skills/tackle/scripts/decompose_check.py",
        "skills/tackle/scripts/lint.py",
        "skills/tackle/scripts/lint_runner.py",
    )
    for relative in required_resources:
        regular_resource(root, relative)
    guide = (root / "skills/tackle/references/guides/migrate.md").read_text(encoding="utf-8")
    for value in ("compact.py", "migration-catalog.json", "Tackle 10.4.0",
                  '<a id="compact-migration"></a>', '<a id="schema-keyed-migration"></a>',
                  '<a id="forward-only"></a>', '<a id="migration-rollback"></a>'):
        if value not in guide:
            fail("active migration route/resource boundary missing: " + value)
    if guide.index('<a id="compact-migration"></a>') >= guide.index('<a id="schema-keyed-migration"></a>'):
        fail("compact route must precede structural explanation")
    cat_path = root / "skills/tackle/references/guides/migration-catalog.json"
    history_path = regular_resource(root, "maintaining/migrations.md")
    cat = loads(cat_path.read_bytes())
    exact(cat, TOP, "catalog")
    if (cat["schema"] != "tackle-migration-catalog/1" or type(cat["revision"]) is not int
            or cat["revision"] != 4 or cat["target_methodology"] != "10.4.0"):
        fail("unsupported migration catalog target")
    if cat["supported_buckets"] != ["pre-3", "3", "4", "5", "lite"]:
        fail("supported bucket coverage mismatch")
    rules = cat["rules"]
    if type(rules) is not list or [r.get("id") for r in rules if type(r) is dict] != list(FAMILIES):
        fail("family order mismatch")
    for position, rule in enumerate(rules):
        exact(rule, RULE, "rule")
        family = FAMILIES[position]
        if (rule["detector"], rule["effect"], rule["postcondition"]) != (family, family, family):
            fail("family binding mismatch: " + family)
        if rule["applies"] != APPLIES[family] or rule["recovery"] != RECOVERY[family]:
            fail("family applicability/recovery mismatch: " + family)
        if rule["kind"] != ("optional" if family in OPTIONAL else "required"):
            fail("family kind mismatch: " + family)
        if rule["requires"] != ([] if position == 0 else [FAMILIES[position - 1]]):
            fail("rule dependency mismatch: " + family)
        exceptions = rule["exceptions"]
        if (type(exceptions) is not list or any(type(value) is not str or not value.strip() for value in exceptions)
                or len(exceptions) != len(EXCEPTIONS[family])
                or any(wording(value) != wording(expected)
                       for value, expected in zip(exceptions, EXCEPTIONS[family]))):
            fail("current exception mismatch: " + family)
        if type(rule["instructions"]) is not list or not rule["instructions"]:
            fail("missing installed instruction: " + family)
        refs = []
        for instruction in rule["instructions"]:
            exact(instruction, {"text", "sources"}, "instruction")
            text, sources = instruction["text"], instruction["sources"]
            if (type(text) is not str or not text.strip() or type(sources) is not list
                    or not sources or any(type(source) is not str for source in sources)):
                fail("invalid installed instruction: " + family)
            recipes = set()
            for source in sources:
                try:
                    identity = json.loads(source)
                except (TypeError, json.JSONDecodeError):
                    fail("invalid instruction source: " + family)
                if (type(identity) is not list or len(identity) != 3 or identity[0] not in {"G", "H"}
                        or type(identity[1]) is not str or type(identity[2]) is not int
                        or identity[2] < 1 or item_id(*identity) != source or source not in ORIGIN_RECIPE):
                    fail("noncanonical or unknown instruction source: " + family)
                recipes.add(ORIGIN_RECIPE[source])
                refs.append(source)
            if len(recipes) != 1:
                fail("only equivalent complete instructions may share origins")
            instruction_text(text, next(iter(recipes)))
        if refs != rule["provenance_ids"] or len(refs) != len(set(refs)):
            fail("instruction provenance mismatch: " + family)
    prov = cat["provenance"]
    exact(prov, {"groups", "items"}, "provenance")
    groups, items = prov["groups"], prov["items"]
    if type(groups) is not list or len(groups) != 44 or type(items) is not list or len(items) != 220:
        fail("provenance counts mismatch")
    canonical = json.dumps(prov, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if digest(canonical) != PROVENANCE_SHA256:
        fail("revision1 canonical source identity/mapping changed")
    hlines, glines = retained_sources(history_path.read_bytes())
    group_by_key, derived_items = {}, {}
    for group in groups:
        exact(group, {"source", "heading", "start", "end", "sha256", "families"}, "group")
        if (group["source"] not in {"G", "H"} or type(group["heading"]) is not str
                or type(group["start"]) is not int or type(group["end"]) is not int
                or group["start"] < 1 or group["end"] < group["start"]
                or type(group["families"]) is not list or any(f not in FAMILIES for f in group["families"])
                or type(group["sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", group["sha256"])):
            fail("invalid group values")
        key = (group["source"], group["heading"])
        if key in group_by_key:
            fail("duplicate group identity: " + group["heading"])
        lines = source_lines(hlines if group["source"] == "H" else glines,
                             group["source"], group["start"], group["end"])
        if digest(b"".join(lines)) != group["sha256"]:
            fail("retained group hash mismatch: " + group["heading"])
        heading = ("## " + group["heading"]).encode("utf-8")
        if not any(line.strip() == heading for line in lines):
            fail("retained heading mismatch")
        offsets = []
        for offset, line in enumerate(lines):
            match = re.match(rb"^\s*(\d+)\.\s", line)
            if match:
                if int(match.group(1)) != len(offsets) + 1:
                    fail("nonsequential retained item numbering")
                offsets.append(offset)
        if len(offsets) != len(group["families"]):
            fail("source numbering/family coverage mismatch")
        for index, begin in enumerate(offsets, 1):
            end = offsets[index] if index < len(offsets) else len(lines)
            identity = item_id(group["source"], group["heading"], index)
            derived_items[identity] = (digest(b"".join(lines[begin:end])), group["families"][index - 1])
        group_by_key[key] = group
    family_items = {family: [] for family in FAMILIES}
    seen_ids = set()
    for item in items:
        exact(item, {"source", "heading", "index", "sha256", "family"}, "item")
        if (item["source"] not in {"G", "H"} or item["family"] not in FAMILIES
                or type(item["heading"]) is not str or type(item["index"]) is not int or item["index"] < 1):
            fail("unknown source item value")
        identity = item_id(item["source"], item["heading"], item["index"])
        if identity in seen_ids:
            fail("duplicate item identity: " + identity)
        seen_ids.add(identity)
        if derived_items.get(identity) != (item["sha256"], item["family"]):
            fail("retained item hash/family mismatch: " + identity)
        family_items[item["family"]].append(identity)
    if seen_ids != set(derived_items) or seen_ids != set(ORIGIN_RECIPE):
        fail("retained numbered source coverage mismatch")
    if {family: len(family_items[family]) for family in FAMILIES} != FAMILY_COUNTS:
        fail("family coverage mismatch")
    if any(rule["provenance_ids"] != family_items[rule["id"]] for rule in rules):
        fail("catalog source mapping mismatch")
    readme = (root / "skills/tackle/scripts/README.md").read_text(encoding="utf-8")
    compact_hash = digest((root / "skills/tackle/scripts/migrate/compact.py").read_bytes())
    archive_hash = "c103d8917aa252bae62ca2bb54c565ed155124e81522bbbfc6ffef99a34f4aad"
    compact_rows = re.findall(r"^\| \[migrate/compact\.py\]\(migrate/compact\.py\) \| `([0-9a-f]{64})` \|$", readme, re.M)
    archive_rows = re.findall(r"^\| \[workspace_archive\.py\]\(workspace_archive\.py\) \| `([0-9a-f]{64})` \|$", readme, re.M)
    if compact_rows != [compact_hash] or archive_rows != [archive_hash]:
        fail("script README digest rows do not match the installed compact/archive sources")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args(argv)
    try:
        validate(args.repo)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        print("migration catalog: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
