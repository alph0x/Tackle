# Plan — label wrap

## 1. Objective

The label stock holds 20 characters per line. Long titles run off the label today; `bin/labels.sh`
should wrap them so the print shop can print the rendered file as delivered.

## 2. Non-goals

- No change to the call number line, to titles of 20 characters or fewer, or to the blank line that ends
  each label.
- No hyphenation and no third title line.

## 3. Requirements

- R1 · `bin/labels.sh <shelf.csv> <out-file>` writes one label per row: call number line, title line,
  blank line (T-01).
- R2 · A title longer than 20 characters breaks at its last space at or before column 20; the rest goes on
  a second title line (T-02).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Label lines | — |
| T-02 | Title wrap | T-01 |

## 6. Acceptance

- 6.1 · Each task: its acceptance check passes; from T-02 on, each check with a check record (D-02)
  linked from its report.
- 6.2 · Initiative: `sh bin/labels.sh tests/data/shelf-a.csv build/shelf-a.txt` writes these ten lines:

  ```
  QA76.73 S5
  Shell Basics

  PR6045 O72
  The Waves and Other
  Short Pieces

  HD9696 B3
  Grids

  ```
