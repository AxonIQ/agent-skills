# Axon Framework Contributor Coding Skill

Guide for developing Axon Framework and Axoniq Framework core infrastructure components: API design patterns, component lifecycle, and framework-specific conventions.

This skill is for **contributing to the Axon/Axoniq frameworks themselves**, not for using them in applications. It covers both:

- **Axon Framework** (`org.axonframework`) — Apache 2.0 open source, foundational building blocks
- **Axoniq Framework** (`io.axoniq.framework`) — Commercial (free for development), adds DLQ, PostgreSQL, distributed messaging, Spring Boot auto-configuration

Both frameworks share identical coding conventions. Axoniq Framework builds on top of Axon Framework.

## Structure

```
axoniq-framework-contribute-code/
├── SKILL.md                              # Core: philosophy, conventions, checklist, anti-patterns, routing table
├── README.md                             # This file
└── references/
    ├── layered-api-design.md             # Level 1/2/3 APIs, interface composition, DescribableComponent
    ├── fluent-builders.md                # AF5 fluent builder style, defaults vs forced choices, builder tests
    ├── configuration-classes.md          # Immutable configuration, ComponentBuilder, ModuleBuilder
    ├── lifecycle-and-context.md          # Registration, ProcessingLifecycle, ResourceKey
    ├── thread-safety.md                  # Immutability, concurrent collections, lock-free patterns
    ├── spi-api-validation.md             # @Internal SPIs, validation, exception design
    ├── testing.md                        # Test object creation, resource cleanup
    └── handler-wrappers.md               # unwrap()/canHandleMessageType(), wrapper chain preservation
```

SKILL.md holds the always-relevant core; the reference files are loaded on demand via its routing table.

## Usage

```bash
/axoniq-framework-contribute-code
```

Use when designing new infrastructure components, layered APIs, builders and configuration, extension points (SPI vs API), or reviewing core framework code.

## Related Skills

- `axoniq-framework-contribute-review` — review changes against AF5 contributor standards
- `axoniq-framework-contribute-docs` — add or update the reference documentation

## Maintenance

This skill is derived from analyzing the Axon Framework 5.x codebase (event publishing stack, command handling, event store architecture, configuration system, context/resource management). When new patterns emerge in the framework, document them in the matching reference file and, if a new topic, add a routing-table row in SKILL.md.
