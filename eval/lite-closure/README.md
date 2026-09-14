# Lite closure development checks

`python3 eval/lite-closure/test_receipt.py` exercises the literal Markdown capture recipe’s
projection: exact command/record fidelity, binary stream hashes, failed/stale observations,
backtick-safe Markdown and explicit UTF-8 under an ASCII locale. These are mechanical tests,
not evidence that every model follows the method. CI runs the same tests.

C1/C2 fixtures support a separate repeated paired behavioral comparison with frozen local criteria.
They carry no expected model outcome, hidden oracle or provider-specific instructions. Historical
runs stay unchanged. Only SKILL.md and references/ ship; no reusable model runner is installed.
