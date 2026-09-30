# PLAN checks

Deterministic checks of the PLAN feature; they read the shipped text and measure no executor. Run them
from the repository root:

```sh
python3 -m unittest discover -s eval/tests/product/plan -p 'test_*.py' -v
```

- `test_plan.py` checks that the plan template keeps the section order its consumers read: behavior and
  acceptance strategy before the task decomposition, then readiness and the per-task and initiative-level
  acceptance sections, in that order.

The brief template and the readiness lint have their own families, `eval/templates/` and `eval/lint/`.
