---
repo_type: axonframework
repo_name: extension-data-protection
repo_path: .knowledge/repositories/axonframework/extension-data-protection
url: https://github.com/AxonIQ/extension-data-protection.git
branch: main
keywords:
  - data protection
  - gdpr
  - field-level encryption
  - cryptographic erasure
  - right to be forgotten
  - axon 5 extension
  - axoniq commercial
---

# extension-data-protection

## Purpose

AxonIQ Data Protection extension for Axoniq Framework 5 — field-level encryption
and key management for event-sourced applications. Enables GDPR "Right to be
Forgotten" through **cryptographic erasure**: sensitive event fields are
encrypted with per-subject keys stored outside the event stream, and deleting
the key permanently invalidates the encrypted data without mutating immutable
events.

Commercial module — requires a valid `axoniq.license` with
`framework.data_protection.enabled=true`. Java 21+ and Framework 5.x required.

## Feature highlights

- **Field-level encryption** — encrypt/decrypt individual fields of a Java
  object using a key derived from another field (typically the data subject ID).
- **Cryptographic erasure for GDPR** — delete the key to permanently render the
  encrypted event payload unrecoverable without mutating immutable events.
- **Pluggable key management** — keys live outside the event stream so they can
  be deleted independently.
- **Spring Boot integration with multi-language samples** — Java, Kotlin, and
  Scala sample apps under `examples/`.
- **Multi-source license loader** — license delivered through a priority chain
  of sources, configured via `axoniq.license`.

## Key paths

- `data-protection-core/` — core encryption/decryption and key-management API.
- `examples/data-protection-spring-boot-java-sample/` — Java Spring Boot sample.
- `examples/data-protection-spring-boot-kotlin-sample/` — Kotlin Spring Boot sample.
- `examples/data-protection-spring-boot-scala-sample/` — Scala Spring Boot sample.
- `docs/reference/` — In-repo Antora reference documentation.
- `docs/_playbook/` — Recurring patterns and playbook entries.

## Highlights

- Reference docs (in-repo): `docs/reference/` (Antora module) and
  `docs/_playbook/` — start here. Prefer these over any public-site
  version; this branch's `docs/` tree is the source of truth for the
  checked-out commit.
- For Axon 4 → Framework 5 migrations that need GDPR erasure, this is the
  Framework-5 home for that capability — pair it with the
  `AxoniqFramework` commercial reference when scoping the migration.
- Pick the sample matching the target language first
  (`examples/data-protection-spring-boot-{java,kotlin,scala}-sample/`) —
  they show the minimal wiring for field encryption.
- Commercial gate: anything that depends on this module requires
  `axoniq.license`. Flag this early in migration plans — it changes the
  build and runtime story.
