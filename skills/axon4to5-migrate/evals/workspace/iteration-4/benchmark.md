# Benchmark — iteration-4

## with_skill
- passed all-assertions: **2 / 2**
- mean assertion pass rate: 100.00%
- mean total_tokens: 40,902
- mean wall-clock: 36.7s

## without_skill
- passed all-assertions: **0 / 2**
- mean assertion pass rate: 0.00%

## Per-eval

| Eval | Recipe | with_skill | without_skill |
|---|---|---|---|
| aggregate-heroes-dwelling | aggregate | — | — |
| aggregate-heroes-calendar | aggregate | — | — |
| event-processor-heroes-creature | event-processor | — | — |
| command-gateway-heroes-recruit | command-gateway | — | — |
| command-gateway-heroes-builddwelling-mcp | command-gateway | — | — |
| query-gateway-heroes-mcp | query-gateway | — | — |
| query-handler-heroes-getbyid | query-handler | — | — |
| event-storage-engine-heroes-entityscan | event-storage-engine | — | — |
| event-storage-engine-heroes-gameconfig | event-storage-engine | — | — |
| event-storage-engine-heroes-yaml | event-storage-engine | — | — |
| aggregate-gamerental-game | aggregate | ✅ 14/14 | ❌ 0/14 |
| event-processor-heroes-dwelling-projector | event-processor | — | — |
| query-handler-heroes-dual-role | query-handler | — | — |
| query-gateway-heroes-getdwellingbyid-controller | query-gateway | — | — |
| command-gateway-heroes-builddwelling-controller | command-gateway | — | — |
| saga-bike-rental-payment | saga | ✅ 16/16 | ❌ 0/16 |
