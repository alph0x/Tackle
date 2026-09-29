# Foundations — structural decisions and evidence

> **Full-gate depth artifact.** Use this file when a Full initiative introduces architecture,
> a subsystem, a boundary, or a reusable pattern. A bounded change that follows existing
> structure can justify the choice in its task instead.

Foundations records decisions that affect more than one task. The standard is observable
responsibility, relevant constraints, and integration fit. A design is justified by the need
it serves and the evidence that checks it; generic style slogans do not substitute for either.

## Decision → responsibility → evidence

Every new abstraction or boundary gets a row before it ships. Explain the responsibility it
owns, why that boundary is useful here, and the test or inspection that would expose a wrong
shape. Record a superseding decision before changing a sealed row or replacing its rationale;
the new row names the earlier decision and the retained safety obligation.

| Choice and location | Responsibility / constraint | Evidence and source |
|---|---|---|
| {{abstraction or boundary}} | {{single observable responsibility; relevant correctness, security, performance, or dependency constraint}} | {{test, contract clause, local precedent, or external source}} |

## Applying the foundations

1. Prefer the smallest coherent shape that satisfies the contract and its consumers.
2. Keep each boundary's inputs, outputs, errors, and effects visible in the contract or task.
3. Add a row when a new abstraction appears; missing evidence is a review finding.
4. Keep local freedom for equivalent implementations and formatting where consumers do not
   observe them. A reviewer evaluates the stated responsibility and evidence, not a preferred
   pattern name.
