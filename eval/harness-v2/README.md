# Protocol v2 harness

One harness for every new cohort. It supersedes CLEAR-EVAL-1, the manual trap path and
`eval/plan-run/protocol.md` for new work; those stay as historical records. It does five things:

- stages a control arm (no skill) or a treated arm (the full install) from the sealed scenario index;
- runs each prompt as a headless session under a temporary HOME;
- records per-role usage, exactly or as `n/a`;
- writes [C01](../protocol-v2/PROTOCOL.md) episode records that `check.py` accepts;
- builds blinded judge packets.

```sh
python3 eval/harness-v2/harness.py stage   --scenario <id> --variant <vid> --arm <arm> --host codex|claude-code|fake [--install <dir>] --out <episode> [--repo <dir>]
python3 eval/harness-v2/harness.py run     --episode <dir> --adapter fake|codex|claude-code --budget-seconds <n> [--isolation local|container] [--model-map <file>] [--credential-file <file>] [--image <image>] [--network <name>] [--broker-bind <address>] [--allow-model-calls]
python3 eval/harness-v2/harness.py dispatch --episode <dir> --role <role> --tier fast|standard|frontier --prompt-file <file> [--allow-model-calls]
python3 eval/harness-v2/harness.py record  --episode <dir> --cohort <dir> --episode-id <id> --judgment <file>
python3 eval/harness-v2/harness.py packet  --cohort <dir> --episodes <dir>... --seed <n> --out <dir> --labels <dir> [--repo <dir>]
python3 eval/harness-v2/harness.py probe   --adapter <name> --probes eval/harness-v2/probes.json --install <dir> --out <dir> [run's isolation and credential options]
python3 -m unittest discover -s eval/harness-v2 -p 'test_*.py' -v
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
  using the functions in `check_index.py`. It refuses when the C06 digest differs from the index's
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
- `stage.json`: the C06 digests of the input, the install, the staged skill and the work tree.

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

No credential is mounted, copied or passed into a participant's container, HOME, environment or prompt.

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

- **`record`** appends one C01 line to `<cohort>/episodes.jsonl`.
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
    `ablation-R-1`, or a bare rule id. The method's name is also replaced.
  - Transcript lines that read skill files are dropped, and the label map counts them.
  - A packet that would contain a line of its scenario's or variant's answer sheet is refused. The
    sheets come from the git index of `--repo`.
  - Every remaining C01 leak pattern, JSON-escaped paths included, becomes `<redacted>`.
  - Packet order is shuffled by the seed.
  - The label map goes only under `--labels`, which must be outside `--out`; its sha256 is printed.
  - Blinding is mechanical. Structural or content re-identification is the reviewer's to catch: a
    participant deliberately encoding its arm with look-alike characters, markup or base64, or the
    style of a skill-guided answer.

## Subagent episodes

D-87: some episodes run as a Task-tool subagent of the coordinating session (the operator's own login)
instead of a headless CLI subprocess, because a headless session has no credential of its own. Staging is
unchanged (`harness.py stage --host claude-code ...`); `subagent.py` replaces `run` for these episodes:

```sh
python3 eval/harness-v2/subagent.py prompt  --episode <dir>
python3 eval/harness-v2/subagent.py finish  --episode <dir> --transcript <subagent jsonl> --model <id> \
    --started <utc> --finished <utc>
```

- **`prompt`** prints, to stdout: one fixed preamble naming the episode directory and saying to work only
  inside it; the staged `prompts/` text, verbatim; for a treated arm only, one fixed sentence naming the
  staged install's `SKILL.md` path (`stage.json`'s `skill_dir` under `home/`). Control and method output
  are byte-identical except for that one sentence. A multi-prompt episode (more than one entry in
  `stage.json`'s `prompts`) is refused: one transcript is one session.
- **`finish`** is handed the subagent's own session transcript (JSONL, the same shape
  `usage.claude_code_transcript` reads) after the fact, and writes:
  - `run.json` in harness.py's own `run` schema, so `harness.py record` and `judge.py --episode` consume
    it unchanged. Tokens come from `usage.claude_code_transcript`; wall seconds from `--started`/
    `--finished`; tool calls count `tool_use` blocks deduplicated by id (a streamed transcript can repeat
    one as it fills in); files written compares the work tree against `stage.json`'s `work_files`.
    `outcome` is `completed`, or `error` when the transcript's last `user`/`assistant` message is not
    from the assistant. Two fields mark this as a different execution path from a headless CLI session:
    `adapter` is `"subagent"` (not `"claude-code"`), and `executor.harness` is `"claude-code-subagent"`.
    One disclosed consequence: `judge.py`'s correction-cycle parser selects by `adapter`, has no
    `"subagent"` entry, and so reports `check_runs`, `correction_cycles` and `transcript_format` as `n/a`
    for these episodes even though `sessions/01/stdout` holds a real Claude Code transcript.
  - `audit.json` (`{outside_paths, skill_used, verdict, reason}`), this tool's own contamination check,
    independent of `run.json`. `outside_paths` names every tool-call path argument and every absolute
    path in a Bash command that does not resolve under the episode directory (a `~` or `$HOME`-led token
    always counts as outside: these subagents share the operator's real HOME). `skill_used` is set by any
    `Skill` tool call, or by a path named `SKILL.md` or carrying a `references` segment that does not
    resolve under this episode's own staged install; a method arm reading its own staged copy does not
    set it. `verdict` is `invalid`, naming the reason, for a control episode with `skill_used` or any
    episode with a non-empty `outside_paths`; otherwise `clean`. The file names paths only, never file
    content. The coordinator, not this tool, merges the verdict into the judgment before `record`.

## Probes

`probe` runs each prompt in `probes.json` in an empty work tree with the install. The set holds six
trigger prompts (English and Spanish for plan, run and status) and four non-triggers. `skill_loaded`
(`true`, `false` or `n/a`) comes from transcript evidence only.

## Unobserved until an authorized smoke episode

These need one authorized smoke episode per adapter before a paid cohort:

- the real host output formats and triggering;
- a real container run;
- the broker route on the internal network;
- in-container `dispatch`, which is not available yet.
