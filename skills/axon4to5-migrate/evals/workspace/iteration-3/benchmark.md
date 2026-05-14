# Benchmark — iteration-3

## with_skill
- passed all-assertions: **14 / 16**
- mean assertion pass rate: 98.86%
- mean total_tokens: 37,686
- mean wall-clock: 27.1s

## without_skill
- passed all-assertions: **0 / 16**
- mean assertion pass rate: 60.13%
- mean total_tokens: 28,647
- mean wall-clock: 21.1s

## Per-eval

| Eval | Recipe | with_skill | without_skill |
|---|---|---|---|
| aggregate-heroes-dwelling | aggregate | ✅ 19/19 | ❌ 13/19 |
| aggregate-heroes-calendar | aggregate | ✅ 7/7 | ❌ 6/7 |
| event-processor-heroes-creature | event-processor | ✅ 17/17 | ❌ 8/17 |
| command-gateway-heroes-recruit | command-gateway | ✅ 8/8 | ❌ 7/8 |
| command-gateway-heroes-builddwelling-mcp | command-gateway | ✅ 6/6 | ❌ 4/6 |
| query-gateway-heroes-mcp | query-gateway | ✅ 7/7 | ❌ 2/7 |
| query-handler-heroes-getbyid | query-handler | ✅ 6/6 | ❌ 5/6 |
| event-storage-engine-heroes-entityscan | event-storage-engine | ✅ 5/5 | ❌ 4/5 |
| event-storage-engine-heroes-gameconfig | event-storage-engine | ✅ 13/13 | ❌ 4/13 |
| event-storage-engine-heroes-yaml | event-storage-engine | ✅ 5/5 | ❌ 1/5 |
| aggregate-gamerental-game | aggregate | ❌ 13/14 | ❌ 8/14 |
| event-processor-heroes-dwelling-projector | event-processor | ✅ 10/10 | ❌ 5/10 |
| query-handler-heroes-dual-role | query-handler | ✅ 10/10 | ❌ 5/10 |
| query-gateway-heroes-getdwellingbyid-controller | query-gateway | ✅ 8/8 | ❌ 7/8 |
| command-gateway-heroes-builddwelling-controller | command-gateway | ✅ 8/8 | ❌ 6/8 |
| saga-bike-rental-payment | saga | ❌ 16/18 | ❌ 8/18 |
