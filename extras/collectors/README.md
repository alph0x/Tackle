# Collector capability profiles

These profiles describe optional, declarative capability boundaries. They do not install, activate,
or require a collector. The universal ledger remains useful when every exact field is `n/a`.

| Harness | Native scope | Exact correlation path | Exact fields | Non-authoritative / unavailable |
|---|---|---|---|---|
| [Claude Code](claude-code.md) | session; request spans when OTel is exposed | explicit Tackle run attribute or reviewed mapping | request input/output/cache tokens, model, duration, ids | local `/usage` dollars, current-context fields, billing cost |
| [Oh My Pi](oh-my-pi.md) | session, folder, model, aggregate | reviewed mapping from a controlled session export | provider-reported token totals, requests, latency, duration | subscription/API-equivalent dollars; private log internals |
| [OpenAI Responses](openai-responses.md) | API request | application metadata or response id owned by integration | exact request usage and reasoning/cache details where exposed | Codex Desktop task export; account-limit deltas |
| [Antigravity CLI](antigravity-cli.md) | headless conversation; interactive session | one-to-one `run_id` ↔ `conversation_id` only under controlled integration | input/output/thinking/cache-read tokens, duration, tool steps | cache-write, cost, request count, compactions, context |
| [OpenCode](opencode.md) | session; project; aggregate stats | explicit Tackle run attribute or reviewed one-to-one mapping; otherwise unjoined | documented session stats/export fields when their semantics are exposed | role-scoped tokens/cost/correlation are `n/a` without mapping and authoritative source |
| [Kimi Code](kimi-code.md) | persistent session; local export | explicit Tackle run attribute or reviewed one-to-one mapping; otherwise unjoined | transcript/stream/export fields when exposed | cumulative role tokens, canonical cost, request counts, and role correlation are `n/a` by default |
| [Cursor](cursor.md) | CLI chat/session; Admin API team/account | explicit Tackle run attribute or reviewed one-to-one mapping; otherwise native scope | CLI duration/session/request ids; Admin API team usage where authorized | CLI token/cost fields and exact role attribution are `n/a` unless a newer surface proves them |

## Shared mapping rules

- Preserve native `scope` and `scope_id`; role scope requires an exact `run_id`.
- Timestamp proximity, account deltas, and allocation are not correlation.
- Normalize `thinking_tokens` to `reasoning_tokens` only when the source documents it.
- Missing or undocumented fields stay `n/a`; API-equivalent prices never populate canonical `cost`.
- Collect minimum necessary metadata and never copy prompts, tool payloads, or raw responses into telemetry.
