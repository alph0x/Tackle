# Roster export format

The regatta registration desk imports a CSV with exactly these columns, in this order:

| Column | Meaning |
|---|---|
| `member_id` | club id, `PRC-` plus four digits |
| `name` | full name as on the membership card |
| `joined` | ISO date of joining |
| `tier` | `junior` or `senior` |

One row per member, UTF-8, LF line endings, header row first. Fields beyond these four are not exported.
