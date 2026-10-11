# Order totals

The checkout service computes the amount due for a basket. Start with the task board and T-41 brief. Product rules are in contract.md; the supplied rate examples are in evidence/host-observations.md. Run the focused check from this directory:

    python3 -B tests/test_change_gate.py

The test file is a protected check. Implement the calculator in src/change_gate.py.