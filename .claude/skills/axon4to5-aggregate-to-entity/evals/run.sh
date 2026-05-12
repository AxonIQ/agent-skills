#!/usr/bin/env bash
# Evals for axon4to5-aggregate-to-entity.
#
# For each (AF4 input, AF5 expected output, --configuration-mode) triple,
# assert that the AF5 file exhibits the structural changes the skill's
# procedure prescribes. Failure means the migration-path doc evolved or
# the procedure drifted — adjust SKILL.md, then re-run.
#
# Discrepancies the skill is NOT responsible for (covered in evals/README.md)
# are not asserted: command-payload record migration, opt-in `tagKey` etc.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
EXAMPLES_ROOT="${REPO_ROOT}/.knowledge/repositories/axon-examples"

PASS=0
FAIL=0

assert_contains() {
    local file="$1" needle="$2" label="$3"
    if grep -qF -- "$needle" "$file"; then
        echo "  ✅ ${label}"
        PASS=$((PASS + 1))
    else
        echo "  ❌ ${label} — expected to find: ${needle}"
        FAIL=$((FAIL + 1))
    fi
}

assert_not_contains() {
    local file="$1" needle="$2" label="$3"
    if grep -qF -- "$needle" "$file"; then
        echo "  ❌ ${label} — should not contain: ${needle}"
        FAIL=$((FAIL + 1))
    else
        echo "  ✅ ${label}"
        PASS=$((PASS + 1))
    fi
}

run_case() {
    local name="$1" af4="$2" af5="$3" mode="$4"

    echo ""
    echo "▶ Case: ${name} (--configuration-mode=${mode})"
    echo "  AF4 input:    ${af4#${REPO_ROOT}/}"
    echo "  AF5 expected: ${af5#${REPO_ROOT}/}"

    if [[ ! -f "$af4" ]]; then
        echo "  ❌ AF4 input file missing"
        FAIL=$((FAIL + 1))
        return
    fi
    if [[ ! -f "$af5" ]]; then
        echo "  ❌ AF5 expected file missing"
        FAIL=$((FAIL + 1))
        return
    fi

    # Sanity: AF4 must really be the AF4 shape this skill targets.
    assert_contains "$af4" "@Aggregate" "AF4: @Aggregate / @AggregateRoot present"
    assert_contains "$af4" "@EventSourcingHandler" "AF4: event-sourced (@EventSourcingHandler present)"

    # --- Step 1: class-level annotation swap ---
    case "$mode" in
        spring-boot)
            assert_contains "$af5" "@EventSourced" "AF5: @EventSourced annotation present"
            assert_contains "$af5" "org.axonframework.extension.spring.stereotype.EventSourced" \
                "AF5: import of Spring stereotype @EventSourced"
            ;;
        axon-configuration)
            assert_contains "$af5" "@EventSourcedEntity" "AF5: @EventSourcedEntity annotation present"
            assert_contains "$af5" "org.axonframework.eventsourcing.annotation.EventSourcedEntity" \
                "AF5: import of core @EventSourcedEntity"
            ;;
    esac
    assert_not_contains "$af5" "import org.axonframework.spring.stereotype.Aggregate" \
        "AF5: AF4 Spring @Aggregate import removed"
    assert_not_contains "$af5" "@Aggregate(" "AF5: parametrised AF4 @Aggregate removed"
    assert_not_contains "$af5" "@AggregateRoot" "AF5: AF4 @AggregateRoot removed"

    # --- Step 2: @AggregateIdentifier removed ---
    assert_not_contains "$af5" "@AggregateIdentifier" "AF5: @AggregateIdentifier removed from field"
    assert_not_contains "$af5" "org.axonframework.modelling.command.AggregateIdentifier" \
        "AF5: @AggregateIdentifier import removed"

    # --- Step 3: handler-annotation import updates ---
    assert_contains "$af5" "org.axonframework.messaging.commandhandling.annotation.CommandHandler" \
        "AF5: AF5 @CommandHandler import"
    assert_contains "$af5" "org.axonframework.eventsourcing.annotation.EventSourcingHandler" \
        "AF5: AF5 @EventSourcingHandler import"
    assert_not_contains "$af5" "import org.axonframework.commandhandling.CommandHandler;" \
        "AF5: AF4 @CommandHandler import removed"
    assert_not_contains "$af5" "import org.axonframework.eventsourcing.EventSourcingHandler;" \
        "AF5: AF4 @EventSourcingHandler import removed"

    # --- Step 4: @EntityCreator present (any of the three patterns) ---
    assert_contains "$af5" "@EntityCreator" "AF5: @EntityCreator added"

    # --- Step 5: AggregateLifecycle.apply replaced by EventAppender ---
    assert_not_contains "$af5" "AggregateLifecycle" "AF5: AggregateLifecycle gone"
    assert_not_contains "$af5" "apply(new" "AF5: static apply(...) call replaced"
    assert_contains "$af5" "EventAppender" "AF5: EventAppender introduced"
    assert_contains "$af5" ".append(" "AF5: append(...) used for event publication"

    # --- @CreationPolicy must not survive ---
    assert_not_contains "$af5" "@CreationPolicy" "AF5: @CreationPolicy removed"
    assert_not_contains "$af5" "AggregateCreationPolicy" "AF5: AggregateCreationPolicy import gone"
}

# ---- Cases ----

run_case "01 Bike (Spring Boot → spring-boot)" \
    "${EXAMPLES_ROOT}/axon4/bike-rental-extended/rental/src/main/java/io/axoniq/demo/bikerental/rental/command/Bike.java" \
    "${EXAMPLES_ROOT}/axon5/bike-rental-extended/rental/src/main/java/io/axoniq/demo/bikerental/rental/command/Bike.java" \
    "spring-boot"

run_case "02 Payment (Spring Boot → spring-boot)" \
    "${EXAMPLES_ROOT}/axon4/bike-rental-extended/payment/src/main/java/io/axoniq/demo/bikerental/payment/Payment.java" \
    "${EXAMPLES_ROOT}/axon5/bike-rental-extended/payment/src/main/java/io/axoniq/demo/bikerental/payment/Payment.java" \
    "spring-boot"

echo ""
echo "──────────────────────────────"
echo "Eval summary: ${PASS} passed, ${FAIL} failed"
echo "──────────────────────────────"

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
