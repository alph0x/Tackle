# Plan — upload limits

## 1. Objective

Uploads above the size limit are refused by the upload API.

## 2. Non-goals

- No change to how an upload is split into chunks.

## 3. Requirements

- R1 · `chunk_count` splits an upload into chunks (T-01).
- R2 · `check_upload(size_bytes)` refuses an empty or oversize upload (T-02).

## 5. Tasks

| Task | What | Repository | Depends on |
|---|---|---|---|
| T-01 | Chunk count | api | — |
| T-02 | Upload check | api | T-01 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: the API refuses every upload above the limit.
