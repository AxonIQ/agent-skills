# Flow

This skill has one loop. Recipes do the edits; the runner owns state and
commits.

```mermaid
flowchart TD
  A[Invoke skill] --> B{Mode}
  B -->|phased| C[Read or create progress.md]
  B -->|single target| D[Resolve file/FQCN]
  B -->|debug| E[Compile and cluster errors]
  C --> F[Pick next routing row]
  D --> F
  E --> F
  F --> G[Pick one target]
  G --> H[Run recipe preflight]
  H --> I{Already done or wrong recipe?}
  I -->|skipped| N[Mark done; no commit]
  I -->|rejected| F
  I -->|needs work| J[Apply flat recipe checklist]
  J --> K[Verify recipe end condition]
  K --> L{result}
  L -->|success| M[Update progress.md and commit explicit paths]
  L -->|needs-decision| O[Ask once, pin answer, rerun or defer]
  L -->|blocked| P[Record blocker; commit only intentional state/TODOs]
  L -->|failed| Q[Stop; surface reason or enter debug]
  M --> F
  N --> F
  O --> F
  P --> F
  F -->|no rows left| R[Clean isolated scopes]
  R --> S[Run full build]
  S --> T[Commit final state]
```

## Rules Behind the Diagram

- Only one target is edited at a time.
- A recipe never commits and never updates migration state directly.
- `result:` is the only branch discriminator.
- Full project builds happen only during finalization.
- Isolated build scopes are always created and removed by
  `axon4to5-isolatedtest`.
