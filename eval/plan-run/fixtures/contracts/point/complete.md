## Purpose and scope
Compile a result package for the declared consumer.
- **Touches**: `result.csv`, `result.json` in the fixture cwd.
- **cwd**: the disposable directory containing the generated files.
- **Inputs**: `canonical-clause.md` revision 1, exact UTF-8 bytes and recorded sha256 below.

## Contract and cases
### Shared clauses (compiled)
- **Id**: `C2-contract-fixture` · **revision**: `1` · **source**: `canonical-clause.md` · **sha256**: `74133e76e6a7a0bccc222a01095e034ee90fa80fc813010057ff0e9e94b1b918`

<!-- CLAUSE-BYTES: UTF-8, exact bytes below, final newline included -->
```text
Clause C2-contract-fixture revision 1
The Point states its observable purpose, interfaces, invariants, cases, constraints, and
acceptance evidence. Exact bytes apply only where specified; valid semantic alternatives remain
accepted. A coherent implementation and its tests are one vertical slice.
```
<!-- END-CLAUSE-BYTES -->
### Interface and invariants
- **Produces**: `result.csv` exact UTF-8 bytes and `result.json` with keys `name`, `score`.
- JSON whitespace and key order are valid alternatives; values and types remain required.
### Case matrix
| Case | Input | Expected observable result | Check |
| normal | Bo=3, Ada=2 | result.csv rows descending, result.json has name=Bo and score=3 | contract test |
| boundary | compact or pretty JSON with either key order | same typed keys and values; JSON whitespace/order do not matter | semantic validator |
| invalid | missing result.json | rejection with diagnostic | negative fixture |
## Approach
Use a producer and a read-only validator.
## Acceptance and recovery
Run all contract cases and print `PASS` after every checked assertion.

```sh
python3 -c 'import json; from pathlib import Path; d=json.loads(Path("result.json").read_text()); assert set(d)=={"name","score"} and type(d["name"]) is str and type(d["score"]) is int and d=={"name":"Bo","score":3}; assert Path("result.csv").read_bytes()==b"name,score\nBo,3\nAda,2\n"; print("PASS point")'
```
