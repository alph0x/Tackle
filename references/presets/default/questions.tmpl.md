# Open questions

Single source of truth for the plan's questions. Don't delete; mark resolved with ✅ and
the decision. External ones (to other teams) also go as a packet in `external-questions/`
when sent.

**Global status**: {{🟢/🟡/🔴 summary of what is unblocked and what is not}}.

---

## Q-01 · {{title}} · {{🔴 open / 🟡 open non-blocking / 🟢 resolved / ⚠️ provisional — awaiting user confirmation}}
<!-- "provisional" = the user explicitly delegated or was unavailable, so a choice was made to
     proceed; it is user-owned and overturnable, NOT a silent assumption. Record what you chose,
     what you'd recommend they confirm, and the risk if wrong. -->

{{Concrete question. What needs deciding and why it blocks (or not).}}

**Determines**: {{what downstream choice/point this answer unblocks or shapes — e.g. "rollback
semantics", "blocks P-06". A question whose answer changes nothing isn't worth tracking.}}
**Decides**: {{who: the relevant team / owner}}.
**Already investigated**: {{what you checked before asking — e.g. "grep of pipelineScripts
found no enablement"; the partial answer you already have. Don't ask others what the codebase
can tell you.}}
<!-- On resolve: mark 🟢 and record the outcome as D-xx in `decisions.md`; link the D-id here. -->
<!-- A point gated on this question is "Deferred" in execution-strategy.md, not 🔴 in an active wave. -->
