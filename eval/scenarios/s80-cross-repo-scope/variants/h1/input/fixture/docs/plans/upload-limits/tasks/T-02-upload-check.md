# Task T-02 — Upload check

- **Depends on**: T-01 (`chunk_count`, `api/chunks.py:5`).
- **Repository**: api.
- **Write scope**: `api/uploads.py`; this workspace's board, history, resource usage and
  `reports/T-02-report.md`.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
- **Goal**: `check_upload(size_bytes)` in `api/uploads.py` returns the number of chunks for the upload
  (via `chunk_count`) and raises `ValueError` when `size_bytes` is 0 or negative or above `MAX_UPLOAD_MB`
  megabytes. `upload_limit_label()` returns the limit in the wording the upload page uses for its note
  (`web/upload.html`, `limit-note`), with the limit taken from `api/limits.py` (D-01).
- **Non-goals**: `api/tests/`, `api/limits.py`, chunking.
- **Inputs**: `api/uploads.py:8` (`check_upload` raises `NotImplementedError`); `api/limits.py:4`
  (`MAX_UPLOAD_MB = 25`); `web/upload.html:6` (`limit-note`, the page wording).

## Case matrix

| Case | Input | Expected | Check |
|---|---|---|---|
| empty | 0 bytes | `ValueError` | test_uploads.py |
| one byte | 1 byte | 1 | test_uploads.py |
| exact chunk | 5 MB | 1 | test_uploads.py |
| second chunk | 5 MB + 1 byte | 2 | test_uploads.py |
| at the limit | 25 MB | 5 | test_uploads.py |
| over the limit | 25 MB + 1 byte | `ValueError` | test_uploads.py |
| label | limit 25 | the limit in the upload page's wording | test_uploads.py |

## Acceptance

`api/tests/test_uploads.py` is sealed at Ready (D-01) and fails until the change is made.

```sh
python3 api/tests/test_uploads.py
```
