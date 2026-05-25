# 10 — Rejected: class with no @QueryHandler

**Why this case is interesting:** A class that dispatches queries via `QueryGateway` but has no `@QueryHandler` method looks superficially related to query handling but falls outside the scope of this recipe. The correct recipe is query-gateway.

**Apply-condition:** `$SOURCE` has `QueryGateway` dependency but no `@QueryHandler` annotation.

---

## Example — pure query dispatcher (AF4)

```java
package com.example.payment.service;

import org.axonframework.queryhandling.QueryGateway;
import org.springframework.stereotype.Service;
import java.util.concurrent.CompletableFuture;

@Service
public class PaymentDispatchService {

    private final QueryGateway queryGateway;

    public PaymentDispatchService(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    public CompletableFuture<PaymentStatus> getStatus(String paymentId) {
        return queryGateway.query(new GetPaymentStatus(paymentId), PaymentStatus.class);
    }
}
```

## Expected result

The query-handler recipe evaluates Applicable predicate 4 (no `@QueryHandler`) → **Rejected**.

```
**Result:** ⏭️ Rejected
**Recipe:** axon4to5-query-handler
**Reason:** no-query-handler — $SOURCE dispatches queries but declares no @QueryHandler methods.
Consider the query-gateway recipe for this class.
```

Source file is NOT modified.

## Routing

| Observation | Recipe |
|---|---|
| `@QueryHandler` on methods | query-handler (this recipe) |
| `QueryGateway` field, no `@QueryHandler` | query-gateway |
| `@SagaEventHandler` | saga recipe |
