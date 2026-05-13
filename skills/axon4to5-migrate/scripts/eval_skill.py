#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

MAX_FILES = 8
MAX_MD_LINES = 260
MAX_TOTAL_LINES = 760


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def text(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def route(src: str) -> str | None:
    if re.search(r"@Saga\b|@SagaEventHandler|@StartSaga|@EndSaga|SagaConfigurer", src):
        return "saga"
    rules = [
        ("aggregate", r"@Aggregate\b|@AggregateRoot\b", None),
        ("command-handler", r"@CommandHandler\b|org\.axonframework\.commandhandling\.CommandHandler", r"@Aggregate\b|@AggregateRoot\b"),
        ("event-processor", r"@ProcessingGroup|org\.axonframework\.eventhandling\.EventHandler|QueryUpdateEmitter|@ResetHandler|SequencingPolicy", None),
        ("command-gateway", r"org\.axonframework\.commandhandling\.gateway\.CommandGateway|ReactorCommandGateway", r"@EventHandler|@CommandHandler|@QueryHandler"),
        ("query-gateway", r"org\.axonframework\.queryhandling\.QueryGateway|ReactorQueryGateway", r"@EventHandler|@CommandHandler|@QueryHandler"),
        ("query-handler", r"org\.axonframework\.queryhandling\.QueryHandler", None),
        ("interceptors", r"implements\s+MessageDispatchInterceptor\b|implements\s+MessageHandlerInterceptor\b", r"@CommandHandler|@EventHandler|@QueryHandler"),
        ("configuration", r"ConfigurerModule|org\.axonframework\.config\.Configurer\b|registerDeadLetterQueue|registerDefaultHandlerInterceptor|registerDispatchInterceptor|registerHandlerInterceptor|CommandBus|EventBus|QueryBus", None),
        ("event-storage-engine", r"org\.axonframework\.eventsourcing\.eventstore\.EventStore|EventStorageEngine|EmbeddedEventStore|JpaEventStorageEngine|JdbcEventStorageEngine|MongoEventStorageEngine|AxonServerEventStore|\.eventStore\(", None),
        ("test-fixture", r"AggregateTestFixture|SagaTestFixture|AxonTestFixture", None),
    ]
    for name, include, exclude in rules:
        if re.search(include, src) and not (exclude and re.search(exclude, src)):
            return name
    return None


def blockers(src: str) -> set[str]:
    checks = {
        "saga": r"@Saga\b|@SagaEventHandler|@StartSaga|@EndSaga|SagaConfigurer",
        "deadline": r"@DeadlineHandler|DeadlineManager",
        "mongo": r"MongoEventStorageEngine|MongoTokenStore|MongoSequencedDeadLetterQueue|axon-mongo",
        "jdbc-store": r"JdbcEventStorageEngine",
        "snapshot": r"snapshotTriggerDefinition|SnapshotTriggerDefinition|Snapshotter",
        "kafka": r"axon-kafka|KafkaMessageSource|KafkaMessageSourceConfigurer",
        "serializer": r"XStreamSerializer|JacksonSerializer|@Bean\s+Serializer|RevisionResolver",
    }
    return {name for name, pattern in checks.items() if re.search(pattern, src)}


def build_tool(path: str) -> str | None:
    if path.endswith("pom.xml"):
        return "maven"
    if path.endswith(("build.gradle", "build.gradle.kts")):
        return "gradle"
    return None


def wiring(src: str) -> str | None:
    if "axon-spring-boot-starter" in src or "@SpringBootApplication" in src:
        return "spring-boot"
    if re.search(r"DefaultConfigurer|org\.axonframework\.config\.Configurer\b|ConfigurerModule", src):
        return "framework-config"
    return None


def license_flags(src: str) -> set[str]:
    checks = {
        "commercial": r"org\.axoniq|axon-mongo|axon-kafka|axon-amqp|axon-tracing|ReplayToken|Upcaster|Mongo.*(TokenStore|DeadLetterQueue)",
        "free": r"org\.axonframework|axon-spring-boot-starter|axon-bom",
    }
    found = {name for name, pattern in checks.items() if re.search(pattern, src)}
    return found or {"none"}


def dispatch_shapes(src: str) -> set[str]:
    checks = {
        "send": r"\.send\s*\(",
        "send-and-wait": r"\.sendAndWait\s*\(",
        "reactor": r"ReactorCommandGateway|Mono<|Flux<",
        "callback": r"CommandCallback|send\s*\([^;]*,\s*[^;]*->",
        "kotlin-extension": r"org\.axonframework\.extensions\.kotlin",
    }
    return {name for name, pattern in checks.items() if re.search(pattern, src)}


def query_shapes(src: str) -> set[str]:
    checks = {
        "query": r"\.query\s*\(",
        "subscription": r"subscriptionQuery|SubscriptionQueryResult|subscriptionQueryMany",
        "streaming": r"streamingQuery|GetAllParticipantsForStreamingQuery",
        "scatter": r"scatterGather|GetAllParticipantsForScatterGather",
        "update-emitter": r"QueryUpdateEmitter",
        "kotlin-extension": r"org\.axonframework\.extensions\.kotlin\.query",
    }
    return {name for name, pattern in checks.items() if re.search(pattern, src)}


def processor_shapes(src: str) -> set[str]:
    checks = {
        "processing-group": r"@ProcessingGroup",
        "reset": r"@ResetHandler",
        "sequencing": r"SequencingPolicy",
        "query-update-emitter": r"QueryUpdateEmitter",
        "pooled-streaming": r"usingPooledStreamingEventProcessors",
        "dlq": r"DeadLetterQueue|SequencedDeadLetterQueue|registerDeadLetterQueue|registerDeadLetterPolicy",
    }
    return {name for name, pattern in checks.items() if re.search(pattern, src)}


def aggregate_shapes(src: str) -> set[str]:
    checks = {
        "aggregate": r"@Aggregate\b|@AggregateRoot\b",
        "constructor-command": r"@CommandHandler\s+(public\s+)?[A-Z]\w+\s*\(",
        "method-command": r"@CommandHandler[\s\S]{0,120}\b(handle|decide)\s*\(",
        "event-sourcing": r"@EventSourcingHandler",
        "apply": r"AggregateLifecycle\.apply|static org\.axonframework\.modelling\.command\.AggregateLifecycle\.apply|\bapply\s*\(",
        "aggregate-member": r"@AggregateMember",
        "aggregate-id": r"@AggregateIdentifier",
    }
    return {name for name, pattern in checks.items() if re.search(pattern, src)}


def test_shapes(src: str) -> set[str]:
    checks = {
        "af4-aggregate-fixture": r"AggregateTestFixture",
        "af4-saga-fixture": r"SagaTestFixture",
        "af5-fixture": r"AxonTestFixture",
        "given-when-then": r"\.given\(|\.when\(|\.expect",
        "disable-axon-server": r"disableAxonServer",
        "register-entity": r"registerEntity|EventSourcedEntityModule",
    }
    return {name for name, pattern in checks.items() if re.search(pattern, src)}


def workspace_root() -> Path:
    return ROOT.parents[1]


def repo_file(relative: str) -> str:
    path = workspace_root() / relative
    if not path.exists():
        fail(f"missing repository/example fixture: {relative}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    files = [p for p in ROOT.rglob("*") if p.is_file()]
    if len(files) > MAX_FILES:
        fail(f"too many files: {len(files)} > {MAX_FILES}")

    forbidden_dirs = ["docs"]
    for dirname in forbidden_dirs:
        if (ROOT / dirname).exists():
            fail(f"obsolete directory still exists: {dirname}")

    markdown = [p for p in files if p.suffix in {".md", ".adoc"}]
    total = 0
    for path in markdown:
        lines = text(path).splitlines()
        total += len(lines)
        if len(lines) > MAX_MD_LINES:
            fail(f"{path.relative_to(ROOT)} too long: {len(lines)}")
        if any(line.startswith("####") for line in lines):
            fail(f"{path.relative_to(ROOT)} nests headings too deeply")

    if total > MAX_TOTAL_LINES:
        fail(f"too many markdown lines: {total} > {MAX_TOTAL_LINES}")

    skill = text(ROOT / "SKILL.md")
    playbook = text(ROOT / "references/playbook.md")
    if "references/playbook.md" not in skill:
        fail("SKILL.md must point to the playbook")
    if "```mermaid" not in playbook:
        fail("playbook must include the flow diagram")
    for token in ["PROCESS_ITEMS", "EXECUTE_RECIPE", "orchestration.svg", "orchestrator"]:
        if token in skill + playbook:
            fail(f"stale complexity token: {token}")

    for token in ["openrewrite", "aggregate", "command-handler", "event-processor", "command-gateway", "query-gateway", "query-handler", "interceptors", "configuration", "event-storage-engine", "test-fixture", "saga"]:
        if token not in playbook:
            fail(f"missing route: {token}")

    samples = {
        "aggregate": "import org.axonframework.spring.stereotype.Aggregate; @Aggregate class A {}",
        "command-handler": "import org.axonframework.commandhandling.CommandHandler; class H { @CommandHandler void h(C c){} }",
        "event-processor": "import org.axonframework.eventhandling.EventHandler; class P { @EventHandler void on(E e){} }",
        "command-gateway": "import org.axonframework.commandhandling.gateway.CommandGateway; class C { CommandGateway g; }",
        "query-gateway": "import org.axonframework.queryhandling.QueryGateway; class C { QueryGateway q; }",
        "query-handler": "import org.axonframework.queryhandling.QueryHandler; class H { @QueryHandler Object h(Q q){return null;} }",
        "interceptors": "class I implements MessageDispatchInterceptor<CommandMessage<?>> {}",
        "configuration": "import org.axonframework.config.ConfigurerModule; class C { ConfigurerModule m; }",
        "event-storage-engine": "import org.axonframework.eventsourcing.eventstore.EventStore; class R { EventStore eventStore; }",
        "test-fixture": "class T { AggregateTestFixture<A> fixture; }",
    }
    for expected, src in samples.items():
        actual = route(src)
        if actual != expected:
            fail(f"route {expected} -> {actual}")

    mixed = "import org.axonframework.commandhandling.gateway.CommandGateway; import org.axonframework.eventhandling.EventHandler; class H { @EventHandler void on(E e){} CommandGateway g; }"
    if route(mixed) != "event-processor":
        fail("handler with gateway must route to event-processor first")

    if route("import org.axonframework.commandhandling.gateway.CommandGateway; import org.axonframework.commandhandling.CommandHandler; class H { @CommandHandler void h(C c){} CommandGateway g; }") != "command-handler":
        fail("command handler with gateway must route to command-handler")

    real_route_cases = {
        ".knowledge/repositories/axon-examples/axon4/gamerental/src/main/java/io/axoniq/demo/gamerental/command/Game.java": "aggregate",
        ".knowledge/repositories/axon-examples/axon4/auction-house/services/service-auctions/src/main/java/io/axoniq/demo/auctionhouse/auction/Auction.kt": "aggregate",
        ".knowledge/repositories/axon-examples/axon4/cinema/src/main/kotlin/com/dddheroes/cinema/modules/issues/write/openissue/OpenIssue.kt": "command-handler",
        ".knowledge/repositories/axon-examples/axon4/cinema/src/main/kotlin/com/dddheroes/cinema/modules/adminnotifications/write/sendnotification/SendAdminNotification.kt": "command-handler",
        ".knowledge/repositories/axon-examples/axon4/heroes/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/read/DwellingReadModelProjector.java": "event-processor",
        ".knowledge/repositories/axon-examples/axon4/heroes/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/automation/WhenCreatureRecruitedThenAddToArmyProcessor.java": "event-processor",
        ".knowledge/repositories/axon-examples/axon4/cinema/src/main/kotlin/com/dddheroes/cinema/modules/seatsblocking/read/getscreeningseats/GetScreeningSeats.kt": "event-processor",
        ".knowledge/repositories/axon-examples/axon4/bike-rental-extended/payment/src/main/java/io/axoniq/demo/bikerental/payment/PaymentController.java": "command-gateway",
        ".knowledge/repositories/axon-examples/axon4/gamerental/src/main/java/io/axoniq/demo/gamerental/controller/GameRentalRestController.java": "command-gateway",
        ".knowledge/repositories/axon-examples/axon4/gamerental/src/main/java/io/axoniq/demo/gamerental/ResultHandlerConfig.java": "command-gateway",
        ".knowledge/repositories/axon-examples/axon4/heroes/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/read/getdwellingbyid/GetDwellingByIdRestApi.java": "query-gateway",
        ".knowledge/repositories/axon-examples/axon4/heroes/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/read/getalldwellings/GetAllDwellingsMcp.java": "query-gateway",
        ".knowledge/repositories/axon-examples/axon4/heroes/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/read/getdwellingbyid/GetDwellingByIdQueryHandler.java": "query-handler",
        ".knowledge/repositories/axon-examples/axon4/heroes/src/main/java/com/dddheroes/heroesofddd/resourcespool/write/withdraw/PaidCommandInterceptor.java": "interceptors",
        ".knowledge/repositories/axon-examples/axon4/gamerental/src/main/java/io/axoniq/demo/gamerental/ApplicationConfig.java": "configuration",
        ".knowledge/repositories/axon-examples/axon4/cinema/src/main/kotlin/com/dddheroes/cinema/AxonFrameworkConfiguration.kt": "configuration",
        ".knowledge/repositories/axon-examples/axon4/heroes/src/main/java/com/dddheroes/heroesofddd/maintenance/read/geteventstream/EventStreamsRestApi.java": "event-storage-engine",
        ".knowledge/repositories/axon-examples/axon4/gamerental/src/test/java/io/axoniq/demo/gamerental/command/GameTest.java": "test-fixture",
    }
    for rel, expected in real_route_cases.items():
        actual = route(repo_file(rel))
        if actual != expected:
            fail(f"real route {rel}: expected {expected}, got {actual}")

    real_blocker_cases = {
        ".knowledge/repositories/axon-examples/axon4/auction-house/services/service-auctions/src/main/java/io/axoniq/demo/auctionhouse/auction/Auction.kt": {"deadline", "snapshot"},
        ".knowledge/repositories/axon-examples/axon4/bike-rental-extended/rental/src/main/java/io/axoniq/demo/bikerental/rental/command/Bike.java": {"snapshot"},
        ".knowledge/repositories/axon-examples/axon4/bike-rental-extended/rental/src/main/java/io/axoniq/demo/bikerental/rental/paymentsaga/PaymentSaga.java": {"saga", "deadline"},
    }
    for rel, expected in real_blocker_cases.items():
        actual = blockers(repo_file(rel))
        missing = expected - actual
        if missing:
            fail(f"real blockers {rel}: missing {sorted(missing)}, got {sorted(actual)}")

    real_shape_cases = {
        ".knowledge/repositories/axon-examples/axon4/bike-rental-extended/rental/src/main/java/io/axoniq/demo/bikerental/rental/ui/RentalController.java": (dispatch_shapes, {"send"}, query_shapes, {"query", "subscription"}),
        ".knowledge/repositories/axon-examples/axon4/gamerental/src/main/java/io/axoniq/demo/gamerental/controller/GameRentalRestController.java": (dispatch_shapes, {"send", "reactor"}, query_shapes, {"query", "subscription"}),
        ".knowledge/repositories/axon-examples/axon4/bike-rental-extended/payment/src/main/java/io/axoniq/demo/bikerental/payment/PaymentController.java": (query_shapes, {"streaming"}, dispatch_shapes, {"send"}),
        ".knowledge/repositories/axon-examples/axon4/auction-house/services/service-participants/src/main/java/io/axoniq/demo/auctionhouse/participants/ParticipantProjection.kt": (query_shapes, {"streaming", "scatter", "update-emitter"}, processor_shapes, {"processing-group", "query-update-emitter"}),
        ".knowledge/repositories/axon-examples/axon4/cinema/src/main/kotlin/com/dddheroes/cinema/modules/seatsblocking/read/getscreeningseats/GetScreeningSeats.kt": (query_shapes, {"kotlin-extension"}, processor_shapes, {"processing-group", "reset", "sequencing"}),
        ".knowledge/repositories/axon-examples/axon4/gamerental/src/main/java/io/axoniq/demo/gamerental/ApplicationConfig.java": (processor_shapes, {"dlq"}, license_flags, {"free"}),
        ".knowledge/repositories/axon-examples/axon4/auction-house/core/pom.xml": (license_flags, {"commercial"}, build_tool, "maven"),
        ".knowledge/repositories/axon-examples/axon4/cinema/build.gradle.kts": (build_tool, "gradle", wiring, "spring-boot"),
        ".knowledge/repositories/axon-examples/axon4/heroes/src/main/java/com/dddheroes/heroesofddd/armies/write/Army.java": (aggregate_shapes, {"aggregate", "method-command", "event-sourcing", "apply", "aggregate-id"}, route, "aggregate"),
        ".knowledge/repositories/axon-examples/axon4/gamerental/src/test/java/io/axoniq/demo/gamerental/command/GameTest.java": (test_shapes, {"af4-aggregate-fixture", "given-when-then"}, route, "test-fixture"),
    }
    for rel, checks in real_shape_cases.items():
        src = repo_file(rel)
        for fn, expected in zip(checks[0::2], checks[1::2]):
            actual = fn(rel) if fn is build_tool else fn(src)
            if isinstance(expected, set):
                missing = expected - actual
                if missing:
                    fail(f"shape {fn.__name__} {rel}: missing {sorted(missing)}, got {sorted(actual)}")
            elif actual != expected:
                fail(f"shape {fn.__name__} {rel}: expected {expected}, got {actual}")

    axon4 = workspace_root() / ".knowledge/repositories/axon-examples/axon4"
    interesting = re.compile(
        r"@Aggregate\b|@AggregateRoot\b|@ProcessingGroup|@EventHandler\b|"
        r"CommandGateway|QueryGateway|ReactorCommandGateway|ReactorQueryGateway|@CommandHandler\b|@QueryHandler\b|"
        r"MessageDispatchInterceptor|MessageHandlerInterceptor|ConfigurerModule|org\.axonframework\.config\.Configurer\b|"
        r"EventStorageEngine|org\.axonframework\.eventsourcing\.eventstore\.EventStore|@Saga\b|"
        r"SagaEventHandler|DeadlineManager|@DeadlineHandler|snapshotTriggerDefinition|QueryUpdateEmitter|@ResetHandler|SequencingPolicy"
    )
    route_counts: dict[str, int] = {}
    unclassified: list[str] = []
    for path in axon4.rglob("*"):
        if path.suffix not in {".java", ".kt"}:
            continue
        if "/src/main/" not in str(path):
            continue
        src = path.read_text(encoding="utf-8", errors="ignore")
        if not interesting.search(src):
            continue
        routed = route(src)
        found_blockers = blockers(src)
        if routed:
            route_counts[routed] = route_counts.get(routed, 0) + 1
        elif found_blockers:
            route_counts["blocked-only"] = route_counts.get("blocked-only", 0) + 1
        else:
            unclassified.append(str(path.relative_to(workspace_root())))
    if unclassified:
        fail("unclassified real Axon files: " + "; ".join(unclassified[:20]))
    minimums = {
        "aggregate": 5,
        "command-handler": 5,
        "event-processor": 10,
        "command-gateway": 5,
        "query-gateway": 3,
        "query-handler": 2,
        "interceptors": 1,
        "configuration": 5,
        "saga": 1,
    }
    for name, minimum in minimums.items():
        actual = route_counts.get(name, 0)
        if actual < minimum:
            fail(f"real repo route coverage too low for {name}: {actual} < {minimum}")

    af5_expectations = {
        ".knowledge/repositories/axon-examples/axon5/heroes/src/main/java/com/dddheroes/heroesofddd/armies/write/Army.java": ["@EventSourced", "EventAppender", "@EntityCreator"],
        ".knowledge/repositories/axon-examples/axon5/gamerental/src/main/java/io/axoniq/demo/gamerental/command/Game.java": ["@EventSourcedEntity", "EventAppender", "@EntityCreator"],
        ".knowledge/repositories/axon-examples/axon5/heroes/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/automation/WhenCreatureRecruitedThenAddToArmyProcessor.java": ["@Namespace", "CommandDispatcher"],
        ".knowledge/repositories/axon-examples/axon5/heroes/src/main/java/com/dddheroes/heroesofddd/creaturerecruitment/read/DwellingReadModelProjector.java": ["@Namespace"],
        ".knowledge/repositories/axon-examples/axon5/heroes/src/main/java/com/dddheroes/heroesofddd/shared/infrastructure/EventStoreConfiguration.java": ["AggregateBasedJpaEventStorageEngine", "EventStorageEngine"],
        ".knowledge/repositories/axon-examples/axon5/bike-rental-extended/payment/src/main/java/io/axoniq/demo/bikerental/payment/PaymentController.java": ["org.axonframework.messaging.commandhandling.gateway.CommandGateway", "org.axonframework.messaging.queryhandling.gateway.QueryGateway"],
        ".knowledge/repositories/axon-examples/axon5/gamerental/src/test/java/io/axoniq/demo/gamerental/command/GameTest.java": ["AxonTestFixture", "@AxonSpringBootTest"],
        ".knowledge/repositories/axon-examples/axon5/bike-rental-extended/rental/src/test/java/io/axoniq/demo/bikerental/rental/command/BikeTest.java": ["AxonTestFixture", "registerEntity", "disableAxonServer"],
    }
    for rel, tokens in af5_expectations.items():
        src = repo_file(rel)
        for token in tokens:
            if token not in src:
                fail(f"AF5 example {rel} missing token {token}")
        if "org.axonframework.commandhandling.gateway.CommandGateway" in src:
            fail(f"AF5 example {rel} still uses AF4 CommandGateway import")

    print("axon4to5-migrate evals passed")


if __name__ == "__main__":
    main()
