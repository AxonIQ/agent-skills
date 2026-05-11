# Axon Framework References

**For AI Agents:** Use this index to quickly identify relevant repositories for your task. Scan the **Keywords** field to match your task requirements, then read the linked markdown file for comprehensive details about that repository.

## AxonFramework4
[Details](axonframework_AxonFramework4.md) — branch `axon-4.13.x`.
**Keywords:** axon 4, aggregate, saga, tracking event processor, migration source, spring boot 3
Canonical source tree for the Axon Framework 4 maintenance line; the migration **source** that Axon 4 → 5 skills read from.

## AxonFramework5
[Details](axonframework_AxonFramework5.md) — branch `feat/5.1-openrewrite`.
**Keywords:** axon 5, dynamic consistency boundary, event sourced entity, reactive, migration target, axon test fixture
Canonical source tree for Axon Framework 5; the migration **target** for all Axon 4 → 5 skills.

## AxoniqFramework
[Details](axonframework_AxoniqFramework.md) — branch `main`.
**Keywords:** commercial axon, dead-letter queue, snapshots, axon server connector, distributed buses, postgresql event store, spring boot 4
Commercial companion to Axon Framework 5 — provides DLQ, snapshots, AxonServer integration, distributed buses, and a PostgreSQL event store for migrations that need Axon 4 enterprise features.

## extension-workflow
[Details](axonframework_extension-workflow.md) — branch `axoniq-workflow-0.1.x`.
**Keywords:** workflow, durable execution, saga replacement, axon 5 extension, workflow dsl, process management, axoniq workflow
AxonIQ Workflow extension for Axon Framework 5 — durable-execution engine and DSL that replaces the Saga pattern removed from core Framework 5; the migration **target** for Axon 4 saga → Framework 5 workflow migrations.

## claude-plugin
[Details](axonframework_claude-plugin.md) — branch `main`.
**Keywords:** claude plugin, axon 5 skills, migration skill patterns, agent skill authoring, axoniq claude plugin
AxonIQ's Claude Code plugin — bundled Axon Framework 5 skills that serve as the authoring reference for how migration/authoring skills in this repo should be shaped.
