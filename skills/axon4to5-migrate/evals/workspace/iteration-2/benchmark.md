# Benchmark — iteration-2

## with_skill
- passed all-assertions: **1 / 1**
- mean assertion pass rate: 100.00%
- mean total_tokens: 37,607
- mean wall-clock: 22.1s

## without_skill
- passed all-assertions: **0 / 1**
- mean assertion pass rate: 68.42%
- mean total_tokens: 30,740
- mean wall-clock: 22.6s

## Per-eval

| Eval | Recipe | with_skill | without_skill |
|---|---|---|---|
| aggregate-heroes-dwelling | aggregate | ✅ 19/19 | ❌ 13/19 |
| aggregate-heroes-calendar | aggregate | — | — |
| event-processor-heroes-creature | event-processor | — | — |
| command-gateway-heroes-recruit | command-gateway | — | — |
| command-gateway-heroes-builddwelling-mcp | command-gateway | — | — |
| query-gateway-heroes-mcp | query-gateway | — | — |
| query-handler-heroes-getbyid | query-handler | — | — |
| event-storage-engine-heroes-entityscan | event-storage-engine | — | — |
| event-storage-engine-heroes-gameconfig | event-storage-engine | — | — |
| event-storage-engine-heroes-yaml | event-storage-engine | — | — |
| saga-bike-rental-payment | saga | — | — |
