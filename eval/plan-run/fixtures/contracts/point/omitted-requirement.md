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
| normal | Bo=3, Ada=2 | result.csv rows descending; result.json is required by the interface but omitted here | semantic review |
| invalid | missing result.json | rejection with diagnostic | negative fixture |
## Approach
Use a producer and a read-only validator.
## Acceptance and recovery
Run all contract cases and print `PASS` after every checked assertion.

### Semantic review rubric
Reject this Point: its `Produces` interface requires `result.json`, but its normal case omits
that required output while retaining the same requirement id and shared clause.
