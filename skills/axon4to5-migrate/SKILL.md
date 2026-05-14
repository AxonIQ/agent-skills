---
name: axon4to5-migrate
description: >-
  Migrate Axon Framework 4 project to Axon Framework 5 — preserves behavior (do not introduce DCB, keep AggregateBasedEventStorageEngine etc).
argument-hint: "configuration=<native|spring> framework=<axon|axoniq>"
disable-model-invocation: true
---

# axon4to5-migrate

## Inputs (all required)

| Param           | Values             | Meaning                                          |
|-----------------|--------------------|--------------------------------------------------|
| `configuration` | `native` \| `spring` | Project wiring style: plain Java vs Spring Boot. |
| `framework`     | `axon` \| `axoniq`   | Target stack: Axon Framework 5 vs AxonIQ 5.      |

Both MUST be present in `$ARGUMENTS`. No defaults. No inference.

## Flow

```mermaid
flowchart TD
    A[Skill invoked] --> P[Parse $ARGUMENTS]
    P --> V{"configuration in {native,spring}<br/>AND framework in {axon,axoniq}?"}
    V -- no --> STOP[/"STOP: report missing/invalid params<br/>show required form"/]
    V -- yes --> ACK[Echo resolved params and END]
```

## MUST

- Parse `configuration` and `framework` from `$ARGUMENTS`.
- STOP if either is missing or has a value outside its allowed set.
- Report which param is missing/invalid and the required form:
  `configuration=<native|spring> framework=<axon|axoniq>`.

## MUST NOT

- Assume a default for either parameter.
- Proceed past parameter validation (migration logic intentionally not wired yet).
