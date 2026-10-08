# ratebook 2.4

Offline reference exchange rates for shell scripts. This directory is a vendored copy.

| File | What |
|---|---|
| `rates.tsv` | One row per date and currency: date, ISO code, units of that currency per US dollar |
| `lookup.sh` | `sh lookup.sh <base> <quote> <YYYY-MM-DD>` prints `<base>/<quote> <date> <rate>`, four decimals |
| `reindex.sh` | Builds `rates.idx`, the date index of `rates.tsv` |

Rates are end-of-day reference values. ratebook is distributed under the MIT licence.
