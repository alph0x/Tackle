# Task T-A — Compile a result package

## Purpose and scope

- **Write scope**: `result.csv`, `result.json` in the fixture cwd.
- **Inputs**: the shared clause below, revision 1, with the hash of its exact bytes.
- **Goal**: compile a result package for the declared consumer.

## Contract and cases

### Shared clauses (compiled)

- **CA-contract-fixture · 1 · sha256 `322132fd8ac12c7f79d67c9c86f587e1acccbe217f1663aaa9b96118bd2dc6b4`**: The task states its observable purpose, interfaces, invariants, cases, constraints, and acceptance evidence. Exact bytes apply only where specified; valid semantic alternatives remain accepted. A coherent implementation and its tests are one vertical slice.

### Interface and invariants

- **Produces**: `result.csv` exact UTF-8 bytes and `result.json` with keys `name`, `score`.
- JSON whitespace and key order are valid alternatives; values and types remain required.

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | Bo=3, Ada=2 | result.csv rows descending, result.json has name=Bo and score=3 | contract test |
| boundary | compact or pretty JSON with either key order | same typed keys and values; JSON whitespace and order do not matter | semantic validator |
| invalid | missing result.json | rejection with diagnostic | negative fixture |

## Approach

Use a producer and a read-only validator.

## Acceptance and recovery

Run all contract cases and print `PASS` after every checked assertion.

```sh
python3 -c 'import json; from pathlib import Path; d=json.loads(Path("result.json").read_text()); assert set(d)=={"name","score"} and type(d["name"]) is str and type(d["score"]) is int and d=={"name":"Bo","score":3}; assert Path("result.csv").read_bytes()==b"name,score\nBo,3\nAda,2\n"; print("PASS task")'
```
