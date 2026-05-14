# Benchmark — iteration-3

## with_skill
- passed all-assertions: **2 / 2**
- mean assertion pass rate: 100.00%
- mean total_tokens: 39,801
- mean wall-clock: 26.6s

## without_skill
- passed all-assertions: **0 / 2**
- mean assertion pass rate: 59.21%
- mean total_tokens: 29,468
- mean wall-clock: 21.8s

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
| aggregate-gamerental-game | aggregate | — | — |
| event-processor-heroes-dwelling-projector | event-processor | ✅ 10/10 | ❌ 5/10 |
| query-handler-heroes-dual-role | query-handler | — | — |
| query-gateway-heroes-getdwellingbyid-controller | query-gateway | — | — |
| command-gateway-heroes-builddwelling-controller | command-gateway | — | — |
| saga-bike-rental-payment | saga | — | — |
