# Protocol v2 harness

One harness for every new cohort. It supersedes CLEAR-EVAL-1, the manual trap path and
the retired Plan → Run synthetic measurement for new work; git history keeps their record. It does five things:

- stages a control arm (no skill) or a treated arm (the full install) from the sealed scenario index;
- runs each prompt as a headless session under a temporary HOME;
- records per-role usage, exactly or as `n/a`;
- writes [tackle-episode/1](../../protocol-v2/PROTOCOL.md) episode records that `check.py` accepts;
- builds blinded judge packets.

Two routes reach a model. The broker routes below run in a container behind a host-side broker. The
[subscription route](#subscription-route), `subscription_route.py`, is separate: it runs episodes through the
pinned Claude Code CLI on the owner's subscription token, judges them with each variant's sealed oracle and
appends the same episode records. It leaves the adapters, the broker and `harness.py` as they are.

```sh
python3 eval/behavior/harness/harness.py stage   --scenario <id> --variant <vid> --arm <arm> --host codex|claude-code|fake [--install <dir>] --out <episode> [--repo <dir>]
python3 eval/behavior/harness/harness.py run     --episode <dir> --adapter fake|codex|claude-code --budget-seconds <n> [--isolation local|container] [--model-map <file>] [--credential-file <file>] [--image <image>] [--network <name>] [--broker-bind <address>] [--allow-model-calls]
python3 eval/behavior/harness/harness.py dispatch --episode <dir> --role <role> --tier fast|standard|frontier --prompt-file <file> [--allow-model-calls]
python3 eval/behavior/harness/harness.py record  --episode <dir> --cohort <dir> --episode-id <id> --judgment <file>
python3 eval/behavior/harness/harness.py packet  --cohort <dir> --episodes <dir>... --seed <n> --out <dir> --labels <dir> [--repo <dir>]
python3 eval/behavior/harness/harness.py probe   --adapter <name> --probes eval/behavior/harness/probes.json --install <dir> --out <dir> [run's isolation and credential options]
python3 -m unittest discover -s eval/tests/tooling/behavior/harness -p 'test_*.py' -v
```

Exit codes:

- 0: success.
- 1: a refusal or a failed check.
- 2: a usage error, or a real adapter used without `--allow-model-calls` or without
  `--isolation container`. This check runs before anything else happens.

The fake adapter needs no flag. The tests never pass it, and they run no real host binary, container,
network or model: fake `codex`, `claude` and `docker` executables on PATH record every invocation.

## Staging

- `stage` reads `eval/scenarios/INDEX.json` and the variant's input from the git index of `--repo`,
  using the functions in `check_index.py`. It refuses when the tree digest differs from the index's
  `fixture_sha256`.
- `--scenario` takes the full id or its short form (`s18`).
- Staging refuses when an answer sheet reaches the input: a byte copy of the scenario's or variant's
  own sheet, or a `GROUND-TRUTH.md` at the fixture root. A world's own sheets deeper in a fixture are
  fixture content.
- It also refuses:
  - a symlink in the input;
  - an existing `--out`;
  - an `--out` inside a git work tree, or under a directory that holds `AGENTS.md`, `SKILL.md`,
    `.claude/` or `.agents/`;
  - a control arm given an install.

The episode directory holds:

- `work/`: the fixture, which becomes the participant's working directory;
- `home/`: an empty HOME. For a treated arm it gets `SKILL.md` plus `references/` in the host's skill
  directory: `.agents/skills/tackle/`, `.claude/skills/tackle/` or `.fake/skills/tackle/`;
- `prompts/`: the prompts, byte-for-byte;
- `baseline/`: a pristine copy of the fixture, used for diffs;
- `stage.json`: the tree digests of the input, the install, the staged skill and the work tree.

Prompts are the same bytes for every arm. No guide is pre-injected, and nothing tells the agent to read
the skill: triggering depends on the install's frontmatter description, as it does for a real user. A
control episode whose transcript shows a skill load is recorded `invalid` with `rule_exposure: true`.

## Sessions and isolation

- **Sessions.** Each prompt (`task.md`, or `sessions/01.md`, `sessions/02.md`, …) runs as its own
  headless session, in order, in the same work tree and HOME. Resuming across sessions is therefore
  measured, not simulated.
- **Budget.** `--budget-seconds` bounds the whole episode. A session that passes it is killed, and the
  episode's outcome is `timeout`.
- **Streams.** stdout and stderr are kept byte-exact in `sessions/NN/`. `run.json` records exit, timeout,
  signal, per-session hashes, cost, roles and the capture path.
- **Environment.** The participant receives only `PATH`, `LANG`, `TERM`, `TMPDIR` and `HOME`, all inside
  the episode, plus the adapter's broker variables.
- **Local isolation** (`local`) serves the fake adapter only.
- **Container isolation** (`container`) reuses the single-entry flags:
  - `--read-only`, `--cap-drop ALL`, `--security-opt no-new-privileges` and a tmpfs `/tmp`;
  - a non-root user;
  - mounts of the episode's `work/`, `home/` and `bin/` (read-only) only.

  The fake adapter runs with `--network none`. A real adapter joins the internal network named by
  `--network`; the operator creates that network, and the harness creates none.

## Credentials

No credential is mounted, copied or passed into a participant's container, HOME, environment or prompt on the broker routes.

- **The broker.** A real adapter starts a host-side broker (`broker.py`) that reads
  `--credential-file`, which holds either the bare key or a JSON object with a `"key"` string.
  - The participant gets only the broker's base URL and a random dummy token per episode: Claude Code
    through `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`, Codex through a `-c model_providers…`
    override and `BROKER_TOKEN`.
  - The broker checks the dummy token, swaps in the credential, and forwards to the adapter's single
    upstream. It refuses any other host.
  - It refuses a chunked request body with 411, rather than forwarding it empty.
  - Every response closes its connection, so stopping the broker never waits on an idle client.
  - Its log (`broker-log.json`) holds method, path, status, bytes and duration only.
- **Not the subscription route.** The subscription route uses no broker. Its token is handled as
  described in [its section](#subscription-route).
- **The scan.** Before any launch, `credscan.py` searches the participant's argv, environment, mounts,
  prompts and staged files. It looks for the credential's secret values, in base64, hex, URL-encoded and
  JSON-escaped forms too, and for the credential's path. A hit refuses the launch with exit 1. After the
  run, the records are scanned the same way.

## Usage and roles

Token fields are integers or `n/a`; unknown is never 0 (`usage.py`).

- **Codex:** the `turn.completed` usage of `codex exec --json`, summed per session.
- **Claude Code:** the session transcripts under the episode HOME, with rows grouped by `requestId` and
  the row with the most output tokens kept. The result event is the fallback.
- **Per-role usage:**
  - Claude Code's native subagent transcripts (`subagents/agent-*.jsonl` with `meta.json`) give one role
    each.
  - `dispatch`, exposed as `bin/tackle-dispatch` for treated arms under local isolation, starts a
    separate session bound to a tier of `--model-map`.
  - Without a map, roles record model `n/a`, and `run.json` records `model_binding: unsupported`.
  - A control episode has no `tackle-*` command on its PATH.

A model map is `{"executor": {"tier", "effort"}, "tiers": {"fast"|"standard"|"frontier": {"model", "effort"}}}`.

## Records and packets

- **`record`** appends one tackle-episode/1 line to `<cohort>/episodes.jsonl`.
  - The line takes the scenario, variant, arm, seed and position from the sealed manifest's order.
  - It takes digests, roles, cost and transcript hashes from the episode.
  - It takes the outcome, scores and judge from `--judgment`.
  - `check.py`'s own field and manifest checks run before the line lands.
  - A timeout or harness error overrides the judged outcome, and so does a control skill load.
  - A multi-session episode's `transcript_sha256` is the sha256 of the JSON list of its session hashes.
  - `check.py <cohort>` passes once every order entry has its record.
- **`packet`** writes one packet per episode: the transcript, the work-tree diff and the prompts.
  - Episode, work, HOME and container paths become neutral tokens, in raw, JSON-escaped and URL-encoded
    forms. So do host skill paths, in any case.
  - Arm names become neutral tokens too, with every separator variant: `control_group`,
    `ablation-<rule id>`, or a bare rule id. The method's name is also replaced.
  - Transcript lines that read skill files are dropped, and the label map counts them.
  - A packet that would contain a line of its scenario's or variant's answer sheet is refused. The
    sheets come from the git index of `--repo`.
  - Every remaining episode-record leak pattern, JSON-escaped paths included, becomes `<redacted>`.
  - Packet order is shuffled by the seed.
  - The label map goes only under `--labels`, which must be outside `--out`; its sha256 is printed.
  - Blinding is mechanical. Structural or content re-identification is the reviewer's to catch: a
    participant deliberately encoding its arm with look-alike characters, markup or base64, or the
    style of a skill-guided answer.

## Subagent episodes

Some episodes run as a Task-tool subagent of the coordinating session (the operator's own login)
instead of a headless CLI subprocess, because a headless session has no credential of its own. Staging is
unchanged (`harness.py stage --host claude-code ...`); `subagent.py` replaces `run` for these episodes:

```sh
python3 eval/behavior/harness/subagent.py prompt  --episode <dir>
python3 eval/behavior/harness/subagent.py finish  --episode <dir> --transcript <subagent jsonl> --model <id> \
    --started <utc> --finished <utc> --notice-status completed|failed [--notice-tool-calls <n>]
```

- **`prompt`** prints, to stdout: one fixed preamble naming `work/` as the task's repository and the
  episode directory as the boundary to work inside; the staged `prompts/` text, verbatim; for a treated
  arm only, one fixed sentence naming the staged install's `SKILL.md` path (`stage.json`'s `skill_dir`
  under `home/`) and asking the executor to read it first and follow it. Control and method output are
  byte-identical except for that one sentence. A multi-prompt episode (more than one entry in
  `stage.json`'s `prompts`) is refused: one transcript is one session.
- **`finish`** is handed the subagent's own session transcript (JSONL, the same shape
  `usage.claude_code_transcript` reads) after the fact, and writes:
  - `run.json` in harness.py's own `run` schema, so `harness.py record` and `judge.py --episode` consume
    it unchanged. Tokens come from `usage.claude_code_transcript`; wall seconds from `--started`/
    `--finished`; tool calls count `tool_use` blocks deduplicated by id (a streamed transcript can repeat
    one as it fills in); files written compares the work tree against `stage.json`'s `work_files`.
    `outcome` is `completed` under a completed notice, and `error` under a failed one. `--notice-status`
    and `--notice-tool-calls` come from the host's notice for that session. With a completed notice,
    `finish` refuses, writing nothing, unless the transcript holds exactly that many tool calls,
    deduplicated by id, its last tool call already has its result, and it ends on the assistant's
    message. So a read made before the session ended is never recorded. With a failed notice, the
    outcome is `error`. Every tool call in a Claude Code transcript carries an id; an id-less one would
    be counted once per appearance. Two fields mark this as a different execution path from a headless
    CLI session: `adapter` is `"subagent"` (not `"claude-code"`), and `executor.harness` is `"claude-code-subagent"`.
    `judge.py` selects its correction-cycle parser by `adapter` and maps `"subagent"` to its Claude
    Code parser, because `sessions/01/stdout` holds a Claude Code session transcript.
  - `audit.json` (`{outside_paths, skill_used, verdict, reason}`), this tool's own contamination check,
    independent of `run.json`. `outside_paths` names every tool-call path argument and every absolute
    path in a Bash command that does not resolve under the episode directory (a `~` or `$HOME`-led token
    always counts as outside: these subagents share the operator's real HOME). A subagent's shell and
    search tools start from the session's cwd, which every transcript line records: a relative path
    resolves against it (else against `work/`), and a Glob or Grep without a path, or a Bash command that
    neither begins with `cd` nor names an absolute path inside the episode, counts that cwd itself. `/dev/null` and system tool directories are never
    outside. A text tool's program or pattern (an `awk` program, a `sed` expression, a `grep` pattern) is
    code, not a path, so its slash-delimited regexes and `~~~` are never path candidates; the files the
    tool reads, including `-f` files, still are. A call to any tool outside the listed local tools (an MCP server such as a code graph of the
    host repository, web access, a nested agent) reaches past the episode without naming a path, and is
    listed as `tool:<name>`. `skill_used` is set by any
    `Skill` tool call, or by a path named `SKILL.md` or carrying a `references` segment that does not
    resolve under this episode's own staged install; a method arm reading its own staged copy does not
    set it. `verdict` is `invalid`, naming the reason, for a control episode with `skill_used` or any
    episode with a non-empty `outside_paths`; otherwise `clean`. The file names paths only, never file
    content. The coordinator, not this tool, merges the verdict into the judgment before `record`.

### A multi-session episode: two (or three) sessions, one merged record

A `method:routed` or `method:split` episode dispatches a planner subagent, then an executor subagent, as
two separate, top-level subagents of the coordinating session — never one subagent dispatching another —
recorded as one episode with two or three sessions:

```sh
python3 eval/behavior/harness/subagent.py prompt  --episode <dir> [--session N]
python3 eval/behavior/harness/subagent.py finish  --episode <dir> [--session N] [--role planner|executor] \
    [--tier fast|standard|frontier] --transcript <jsonl> --model <id> --started <utc> --finished <utc> \
    --notice-status completed|failed [--notice-tool-calls <n>]
python3 eval/behavior/harness/subagent.py close   --episode <dir>
python3 eval/behavior/harness/subagent.py tier    --episode <dir>
```

Every other arm's `prompt`/`finish` call is unaffected: `--session`, `--role` and `--tier` are optional,
default to session 1 with no role or tier recorded, and a `finish` call with no `--session` still writes
`run.json`/`audit.json` directly in one call, exactly as above.

- **`<episode>/brief.md`** is a new fixed path, a sibling of `work/`, `home/` and `prompts/`, never inside
  `work/`. The planner writes its plan there; the coordinator never opens it.
- **`prompt --session N`** (`N` defaults to 1, and is only meaningful on a multi-session episode):
  - `N = 1`, `method:routed`: today's preamble, the staged prompt verbatim and the arm sentence, plus one
    fixed closing block asking the planner to write a paper plan to `brief.md` (with a `**Tier**:` line
    and, optionally, an `**Escalation**: declared` line), never to implement the task itself, touch
    `work/`, or run the skill's own PLAN scaffolding.
  - `N = 1`, `method:split`: the same preamble, staged prompt and arm sentence, plus a shorter closing
    block asking for the same paper plan, but naming neither a Tier nor an Escalation line at all: this
    arm always runs both sessions at the cheapest bindable tier, whatever the brief says, so there is
    nothing to declare.
  - `N >= 2`, `method:routed`: never reads the staged prompt at all. Prints the fixed preamble plus a
    request to read `brief.md` and carry out the task it describes, with a final report of exactly
    `DONE`, or exactly `ESCALATE` if the brief declares an escalation and a capability failure is hit.
  - `N >= 2`, `method:split`: the same preamble and a request to read `brief.md` and carry out the task,
    but its final report must be exactly `DONE` — this arm's own prompt never offers `ESCALATE`, since its
    brief never declares an escalation to retry into.
  - Either arm: refused if `brief.md` does not exist yet.
- **`finish --session N --role <role> --tier <tier>`**, a multi-session arm only: writes only
  `sessions/0N/{stdout,stderr,meta.json}` plus a work-tree digest snapshot; it does not write
  `run.json`/`audit.json` itself, and prints a reminder to run `close` once every session is in. The
  replacement guard is per-session: a repeat of the same `N`, a session more than one past the highest
  already recorded, or any `--session` on an episode of neither multi-session arm, is refused; `--session
  1` or its omission keeps today's exact "the episode already ran" guard on every arm. It takes the same
  two notice options, per session.
- **`close`** (a multi-session arm only, new subcommand): reads every `sessions/0N/` on disk, in order,
  and writes the merged `run.json`/`audit.json` once.
  - `cost` sums tokens, wall seconds and tool calls across sessions; `files_written` is computed once from
    the current `work/` tree; `roles` has one entry per session (`role`, `tier`, `model`, `tokens_in`,
    `tokens_out`), matching `check.py`'s own role schema.
  - The audit runs once per session's own transcript and is invalid if any session is invalid: a nested
    Task-tool (or any non-local-tool) call in either session is `tool:<name>`, unchanged from the
    single-session rule; a session's own path audit for session 1 is exactly as any other episode's, but
    a session 2 (or 3) additionally treats `prompts/`, `sessions/`, `dispatch.txt` and `stage.json` as
    off-limits even though they resolve inside the episode, so relying on anything but the brief is caught.
  - Invalidity reasons, arm-agnostic (any multi-session arm): `"planner session modified the work tree"`
    (session 1's snapshot differs from the original staged one), `"planner produced no brief"` (`brief.md`
    missing), `"executor read past its brief"` (a session >= 2 path violation above), `"escalation
    without a declared brief"` (an `ESCALATE` report with no declared escalation in the brief),
    `"live escalation out of scope for 9.0.0"` (a live session 2 hands back `ESCALATE` with no
    `sessions/03/` on disk), `"escalation attempted past its one capped retry"` (a session past position 2
    hands back `ESCALATE` — a further escalation attempt past the one capped retry the shipped skill
    allows), and `"session 3 present without a preceding escalation"` (a third session exists on disk but
    the second session's own final report was not `ESCALATE` — nothing coupled the two before this rule,
    so a coordinator slip dispatching an unwarranted third session used to merge cleanly with no
    invalidity signal).
  - Ordinary episodes of either arm never dispatch a live third session; the one disclosed exception is a
    single, scripted smoke-cohort episode proving the three-session merge and escalation mechanism live,
    never claimed as behavioral evidence. Outside that one exception, the three-session merge is proven
    only by this tool's own synthetic test fixtures.
- **`tier`** (new subcommand, mechanical and read-only): greps `brief.md` for its `**Tier**:` and
  `**Escalation**:` lines and prints `tier=<value> escalation=<declared|absent>`, nothing else. Output is
  restricted to the closed vocabulary `fast`, `standard`, `frontier`, `n/a`: a missing or malformed line,
  or a valid value followed by trailing prose, prints `tier=n/a` rather than echoing planner-authored text
  to the coordinator. A `method:split` brief has no Tier or Escalation line by design, so this ordinarily
  prints `tier=n/a escalation=absent` for that arm.

## Probes

`probe` runs each prompt in `probes.json` in an empty work tree with the install. The set holds six
trigger prompts (English and Spanish for plan, run and status) and four non-triggers. `skill_loaded`
(`true`, `false` or `n/a`) comes from transcript evidence only.

## Subscription route

```sh
python3 eval/behavior/harness/subscription_route.py run   --config <file> --cohort <dir> --repo <dir> --install <dir> --out <dir> --stage <name>
python3 eval/behavior/harness/subscription_route.py probe --config <file> --repo <dir> --workspace <dir> --install <dir> --out <dir>
python3 eval/behavior/harness/subscription_route.py judge --config <file> --oracle <dir> --final <dir> --transcript <file>
```

Exit 0 succeeds, 1 is a refusal or a stage stopped by a fault, 2 is a usage error and 130 an interrupted run.
Every subcommand takes `--config`; there is no default path. The model-free suite is `test_subscription_route.py`
beside the other harness tests. It runs the route as a subprocess against a stub `claude` and a fake
`sandbox-exec` on a PATH built from scratch, so it passes on Linux and macOS with no skip and starts no real CLI,
sandbox or model.

- **Configuration.** An untracked JSON file with the schema `tackle-route-config/1`, never committed:
  - `cli`: the pinned CLI's `path`, its `sha256` and optionally its `version`;
  - `model`, `run_root`, `state_dir`, and `token_file`, which is a path and never a value;
  - `caps`: `total_usd`, `episode` (`usd`, `seconds`, `turns`), `stages` (a USD cap per stage name) and `probe`
    (`total_usd`, and per child `child_usd`, `child_seconds`, `child_turns`);
  - `oracle`: the interpreter's `python` path and its `seconds`, and optionally `denied_prefixes`, the trees the
    interpreter must stay out of (default: the profile's own list, below). It narrows only that pre-flight check,
    for a launcher that enforces no profile; the profile never changes;
  - `launcher`: the absolute path of the sandbox launcher (`/usr/bin/sandbox-exec`), which the route runs and never
    looks up on PATH; it must be an executable file outside `/Users`;
  - optionally `child_path` and `cli_tmp_limit`, which defaults to the CLI's 44-byte temporary-path limit.
- **Before any model call** the route refuses, with an explicit reason, for any of these: a malformed
  configuration, a launcher that is not an executable file or sits under `/Users`, an interpreter under a tree the oracle profile denies or a run root under `/Users`, a held lock, a CLI whose
  sha256 or version differs from the pin, a run root over the temporary-path limit, a leftover run root, an
  ancestor of the run root that holds `AGENTS.md`, `CLAUDE.md` or `.claude`, an input or skill tree whose digest
  differs from the sealed manifest, an arm other than `control` and `method`, a missing oracle, an unsafe fixture
  path, an existing episode directory, and a missing or malformed token file. The token file is opened only
  when an episode is about to launch.
- **Staging.** `run` takes the cohort manifest's `order`, appends to its `episodes.jsonl`, and resumes after the
  records already there. Each episode gets a fresh private root under `run_root` with `home/`, `work/` and
  `tmp/`. The variant's `input/fixture/` becomes `work/`. `control` stages no skill. `method` stages the exact
  `SKILL.md` and `references/` of `--install` into the HOME's user skill root, checked against the manifest's
  candidate digest before and after the copy. The input tree must match its sealed digest and hold only
  prompts (`task.md`, or `sessions/NN.md` run in order) and `fixture/`. A fixture cannot plant `.claude`,
  `.git`, `.codex`, `.agents`, `CLAUDE.md`, `SKILL.md` or an answer sheet, and the route never reads or copies
  an answer sheet.
- **Running.** Each session is a headless run of the pinned CLI with `--model` from the configuration, in the
  same work tree and HOME. The wall-clock, turn and dollar limits are per episode, and a later session gets what
  is left; a session whose remaining dollars round to zero at four places is not launched. The child's environment holds `PATH`, `HOME`, `TMPDIR`, `LANG`, `TERM`, a few CLI switches and the
  token variable, and nothing else. The CLI's sandbox settings allow no network, deny reads under the home and
  temporary trees except the run root, allow writes only to `work/` and `tmp/`, and deny writes to
  `work/.claude`. The tools are `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep` and `Skill`, in `dontAsk` mode.
  The file tools' permission rules allow reading the run root and editing `work/`, and refuse reads under the home
  and temporary trees; a deny rule outranks an allow rule, so no deny rule covers the run root itself, which sits
  under `/private/var/tmp`. A refused `Read`, `Glob` or `Grep` inside the run root is an instrument fault.
- **Token.** The owner's subscription token is read at launch from the file the configuration names, which must
  be a regular file owned by the user; it is tightened to owner-only and must hold one value. It goes into the
  CLI process environment only, never into argv, a prompt, a staged file or a record. Before anything is kept,
  every stream, and every name, link target and file under the run root, is scanned for the token and its
  base64, hex, URL-encoded and JSON-escaped forms, and `episode.json` and the protocol line are each scanned again before they are kept. A hit
  makes the episode `invalid` with the reason `credential`, retains no stream bytes and no final tree, deletes
  the whole run root (a directory the participant made unwritable included), and writes `incident.json` to the
  state directory. Every later run, probe and judge refuses until the owner has reviewed it and removed that
  file. A probe child's hit is handled the same way.
- **Isolation.** Each session's init event must show the configured model, no API key, exactly the seven tools,
  no MCP server, only built-in plugins, `dontAsk`, memory only inside the run root, and the skill listed in the
  method arm only. A fault is `invalid` with the reason `isolation`. A control arm that lists or uses the skill
  is `invalid` with `rule_exposure` true, a method arm without it is `invalid`, and a participant-made
  `.claude` is `invalid` and ends the episode before the next session (the CLI's own empty `.claude/.cc-writes` staging is
  tolerated at any depth). The
  CLI wrapper's refused temporary write and a refused workspace write are instrument faults, recorded `error`.
  An isolation fault or a control arm's skill use outranks a reached limit or timeout: the episode is `invalid` and
  the stage stops.
- **Judging.** The oracle is `python3 check.py --final <dir> --transcript <file>`: standard library only, one
  JSON object `{"outcome", "invalid_reason", "scores"}`, exit 0 with a verdict, 1 on an internal error and 2 on a
  usage error. The route copies the oracle, the final tree and the concatenated session streams under one
  canonical root and runs it through `sandbox-exec` with a profile that allows no network, denies reads under
  `/Users`, `/private/tmp`, `/Volumes`, `/private/var/folders` and `/private/var/tmp` except that root, and
  allows writes only to a scratch directory in it. The oracle's environment holds no token. Without
  the configured launcher, or with the interpreter under a denied tree or the run root under `/Users`, the route refuses to judge with an explicit
  reason; it never judges unsandboxed, and a launcher that cannot start the oracle is an `error`. An oracle that
  exits non-zero, hangs, prints a malformed verdict or modifies its input is an `error`. `judge` runs this step
  alone and prints the verdict.
- **Records.** One `tackle-episode/1` line per order entry, checked by `check.py`'s own field and manifest rules
  before it lands.
  - `fell` and `avoided` come from the oracle, and `correct_action` is 0 or 2. An oracle `invalid` is
    `invalid` with the reason `oracle: <reason>`, sanitized, and `correct_action` is null. The other three
    scores are always null, and the oracle's own named scores are kept in the episode's `oracle.json`.
  - Route-made `invalid` reasons are a closed set: `credential`, `isolation`, `harness configuration written`,
    `control arm exposed to the skill`, `method arm skill not listed` and `final tree not preserved`.
  - `timeout` is a reached wall clock, or the CLI's own turn or dollar limit. The protocol names `timeout` for the
    harness budget only, so reporting the CLI's limits the same way is a choice of this route.
  - `error` is a CLI failure without a result, an instrument fault, an oracle failure or an interruption.
  - `unobserved` is a planned episode that a reached cap stopped. There are no re-runs: an observed cohort is
    never amended.
  - Each episode keeps `episode.json`, `oracle.json`, the byte-exact `sessions/NN/stdout.jsonl` and
    `stderr.txt`, and a copy of `final/` under `--out/<episode_id>/`. A link, a hard-linked file, a special file
    or an unreadable entry in the work tree is recorded by path and kind and never followed or copied, and the
    episode is then `invalid` with the reason `final tree not preserved`: the oracle never runs on a partial tree,
    and the stage goes on. The route's records carry neutral tokens (`<runtime>`,
    `<home>`, `<work>`, `<tmp>`, `<cli>`, `<repo>`) instead of absolute paths. The retained streams and tree are
    evidence, not records, and keep the paths the participant saw.
  - `episode.json` also holds `metrics.archive_bytes_read`: the bytes of `history-archive.md` returned to the
    agent, that is the `Read` results for that file plus the `Bash` results whose command names it.
- **Caps and stops.** `state_dir/spend.json` records each claim, and an unsettled claim counts at its cap. The
  stage and total ceilings are checked before every launch, and a reached cap stops the stage and records
  `unobserved` for what did not run. The CLI checks `--max-budget-usd` between turns, so one turn can pass it;
  the ledger settles at the cost the result event reports. A credential hit, an isolation fault, an instrument fault or an oracle
  error stops the stage after its record and exits 1. SIGTERM or SIGINT kills the child's process group, records
  the episode as `error`, releases the lock and exits 130, leaving the run root for the owner. Both leave an
  incomplete cohort that `check.py` rejects explicitly. One run root exists at a time, under an exclusive
  lock in `state_dir`.
- **Probe.** `probe` runs the method arm and the control arm once each with fixed commands, and writes
  `result.json`: the booleans `passed`, `network_denied`, `repository_read_denied`, `workspace_read_denied`,
  `method_arm_skill_loaded`, `control_arm_skill_absent`, `token_scan_clean`, `work_tree_write_allowed`,
  `work_tree_read_allowed` and `token_visible_to_tools`; the `attempts` (counts of recorded tool calls that tried
  the network, the repository and the workspace) and `work_tree_read_attempts` (the `Read` calls on the file in the
  child's own work tree); the `model`; and `cost_usd`. A denial is true only when its attempt was recorded and
  refused, and an allowance only when its attempt was recorded and succeeded: each child writes a file in its
  work tree with `Bash` and must then `Read` it, so rules that refuse the child its own files fail the probe.
  Sentinel files are planted in `--repo` and `--workspace` and removed afterwards. The probe learns whether the tools can see the
  token only through a count, never by printing it. Every probe's cost counts against the configured probe cap.
- **Control.** `token_visible_to_tools` decides which control applies. With `prevention` the model's tools
  cannot read the token. With `detection` they can, and containment is the sandbox without network plus the
  scans that invalidate a hit. This section names the control the first live probe observed.

## Unobserved until an authorized smoke episode

These need one authorized smoke episode per adapter before a paid cohort:

- the real host output formats and triggering;
- a real container run;
- the broker route on the internal network;
- in-container `dispatch`, which is not available yet;
- the subscription route against the real CLI and `sandbox-exec`: the sandbox facts and token visibility that its
  probe records, and the oracle step under the real launcher's profile.
