# Benchmark — iteration-1

## with_skill
- passed all-assertions: **1 / 2**
- mean assertion pass rate: 94.74%
- mean total_tokens: 33,284
- mean wall-clock: 17.4s

## without_skill
- passed all-assertions: **0 / 2**
- mean assertion pass rate: 75.88%
- mean total_tokens: 28,986
- mean wall-clock: 22.9s

## Per-eval

| Eval | Recipe | with_skill | without_skill |
|---|---|---|---|
| aggregate-heroes-dwelling | aggregate | ❌ 17/19 | ❌ 13/19 |
| aggregate-heroes-calendar | aggregate | — | — |
| event-processor-heroes-creature | event-processor | — | — |
| command-gateway-heroes-recruit | command-gateway | — | — |
| command-gateway-heroes-builddwelling-mcp | command-gateway | — | — |
| query-gateway-heroes-mcp | query-gateway | — | — |
| query-handler-heroes-getbyid | query-handler | ✅ 6/6 | ❌ 5/6 |
| event-storage-engine-heroes-entityscan | event-storage-engine | — | — |
| event-storage-engine-heroes-gameconfig | event-storage-engine | — | — |
| event-storage-engine-heroes-yaml | event-storage-engine | — | — |
| saga-bike-rental-payment | saga | — | — |
