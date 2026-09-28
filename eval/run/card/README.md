# RUN card checks

Deterministic checks of the RUN card, `references/guides/run-card.md`, and its depth guide,
`references/guides/run.md`; they read the shipped text and measure no executor. Run them from the
repository root:

```sh
python3 -m unittest discover -s eval/run/card -p 'test_*.py' -v
```

- `test_run.py` checks that the card and its guide hold one state machine with an integrated close bar;
  that the team, agents and current-work templates bind to RUN without competing loops; and that the card
  and the Focused plan stop an older workspace with `migrate first` before their first write, while a
  STATUS handoff on such a workspace writes nothing.

`results/p06-integrated-acceptance.json` keeps the integrated-acceptance record of the original PLAN and RUN
rewrite, byte for byte. The synthetic measurement that rewrite prepared, never started, was removed with its
harness and fixtures; git history keeps them.
