# Open questions

**Global status**: 🟢 all intake decisions settled; no blocking questions.

---

## Q-01 · ¿Include `/tackle-analyze` cross-artifact consistency check? · provisional default: no

Spec-kit has `/speckit.analyze`. Tackle 2.0 could add a lightweight `/tackle-analyze` that checks spec→plan→tasks coverage before implement.

**Determines**: scope of P-05 / whether to add a 9th point.
**Decides**: user / maintainer.
**Already investigated**: spec-kit README lists `/speckit.analyze` as optional. Tackle 1.5 already has Step 6.5 lint (self-consistency). A separate analyze phase may duplicate that.

## Q-02 · ¿Publish a minimal CLI package, or stay markdown-only? · provisional default: no

The plan assumes `tackle init` is a trigger. A Python package would be easier to install but adds dependencies and packaging work.

**Determines**: shape of P-07.
**Decides**: user / maintainer.
**Already investigated**: spec-kit requires `uv` + Python. Tackle's model-agnostic constraint favors markdown + shell.

---

Both questions default to "no" and do not block Tackle 2.0 shipping.
