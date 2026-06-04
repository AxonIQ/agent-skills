---
name: axoniq-framework-contribute-docs
description: >
  Add or update Axon Framework 5 reference documentation.
  Use when the user says "add docs", "update docs", "document feature", "write documentation for",
  "update the reference guide", "add a page", "edit the docs", "adapt documentation",
  or any variation of creating or editing AsciiDoc pages in the Axon Framework docs.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Edit, Write, Task, Bash
---

# Documentation Add/Update Skill

Add or update pages in the Axon Framework 5 reference guide (`docs/reference-guide/`) or standalone guides (`docs/getting-started/`, `docs/*-guide/`).

## Arguments
- $ARGUMENTS: What to document — a feature name, a file path, a GitHub issue number, or a free-form description.

---

## Phase 1: Understand the Request

Determine the **intent** from $ARGUMENTS:

- **New page** — user wants to add documentation that doesn't exist yet.
- **Update existing page** — user wants to change or extend content in an existing `.adoc` file.
- **Rename/restructure** — user wants to rename a file or move content between sections.
- **Document current changes** — user wants to write or update documentation for the changes in the current branch or PR. In this case, start by analyzing the local changes before proceeding.

### If the intent is "document current changes"

Before doing anything else, analyze what has changed. This flow requires **Bash access** to run git commands — if Bash is unavailable, ask the user to describe what changed or paste the relevant source files.

1. **Check local git diff** to see what files and code changed on the current branch:
   ```bash
   git diff main...HEAD --stat
   git diff main...HEAD -- '*.java' '*.kt'
   ```
2. **Read the changed source files** to understand what new APIs, behaviors, or concepts were introduced.
3. **Check if there is an associated PR** for additional context (description, linked issues):
   ```bash
   gh pr view --json title,body,url 2>/dev/null
   ```
4. Use what you find as the basis for $ARGUMENTS and continue with Phase 2 onwards.

If the intent is unclear, ask:
1. Which module does this belong to? (commands / events / queries / messaging-concepts / testing / tuning / monitoring / migration / ROOT)
2. Is this a new page or an update to an existing one?
3. Is there a related GitHub issue or framework class to verify APIs against?

---

## Phase 2: Orient in the Structure

### Reference guide module layout

```
docs/reference-guide/modules/
├── ROOT/                    pages: index, conversion, spring-boot-integration, modules
├── messaging-concepts/      pages: timeouts, correlation, exception handling, processing-context
├── commands/                pages: command-handlers, command-dispatching; modeling/ subdir
├── events/                  pages: event-sourcing, publishing; event-processors/ subdir
├── queries/                 pages: query-handlers, query-dispatching
├── testing/                 pages: test fixtures and patterns
├── migration/               pages: paths/ subdir for AF4->AF5 migration guides
├── tuning/                  pages: performance optimization
├── monitoring/              pages: observability and metrics
└── release-notes/           pages: version release notes
```

Each module has:
- `modules/<name>/pages/` — content `.adoc` files
- `modules/<name>/partials/nav.adoc` — navigation entries for that module
- (optional) `modules/<name>/images/` — diagrams

### Standalone guides

```
docs/getting-started/          tutorial (9-page progressive tutorial)
docs/identifier-generation-guide/
docs/message-handler-customization-guide/
docs/meta-annotations-guide/
```

### Step-by-step orientation
1. **Find the target location**: use `find docs/reference-guide/modules -name "*.adoc" | grep <keyword>` to locate existing files.
2. **Read the nav**: read `docs/reference-guide/modules/<module>/partials/nav.adoc` to understand the navigation shape.
3. **Study a neighbour file**: read 1-2 nearby `.adoc` files to match structure and tone.
4. **Check changes-to-process.md** if relevant: read the section for this topic to see if there's existing tracking/intent.

---

## Phase 3: Verify APIs Before Writing

**CRITICAL — never document APIs from memory.** Before writing any code example:

1. Search for the class or interface in framework source:
   ```bash
   find . -name "*.java" -not -path "*/legacy/*" | xargs grep -l "ClassName" | head -10
   ```
2. Read the actual method signatures, return types, and parameter types.
3. Check for related builder or config classes.
4. Verify the class is NOT in a legacy package — if it is, do NOT document it as available in Axon 5.

**Key AF5 API patterns to be aware of:**
- `ProcessingContext` (replaces UnitOfWork / ThreadLocal) — mandatory on handling side, optional on dispatch side
- `EventSink` (replaces EventBus for publishing) — explain its relationship to EventBus
- `Converter` (replaces Serializer)
- `PooledStreamingEventProcessor` (replaces TrackingEventProcessor)
- `CommandResult` wraps async dispatch — not raw `CompletableFuture`
- `@EventSourced` annotation for entities (Spring style)
- `MessagingConfigurer` / `ModellingConfigurer` / `EventSourcingConfigurer` for plain Java config

**Not available in Axon 5.0 — do NOT document as usable:**
- Sagas (moved to legacy — document stateful event handlers as alternative)
- Deadlines (moved to legacy — document Spring `@Scheduled` / external schedulers as alternative)
- DomainEventMessage (removed — use EventMessage)
- Anything in a `legacy` package

---

## Phase 4: Write the Content

### AsciiDoc file template

```adoc
= Page Title (Title Case for H1)
:navtitle: Short Nav Label
:reftext: Cross-reference text

Brief introductory paragraph explaining what this page covers and why it matters to users.

== First major section (sentence case for H2+)

Content here.

[source,java]
----
// Plain Java example
MessagingConfigurer configurer = MessagingConfigurer.create();
configurer.commandBus(CommandBusBuilder.defaultCommandBus()); // <1>
----
<1> Explanation of the key line.

[tabs]
====
Spring Boot::
+
[source,java]
----
@Configuration
public class MyConfig {
    // Spring Boot example
}
----

Plain Java::
+
[source,java]
----
// Equivalent plain Java
----
====

[NOTE]
====
Optional note for important nuances.
====

== Second major section

=== Subsection (sentence case)
```

### Mandatory conventions

**Headings:**
- H1 (`=`): Title Case — "Understanding the Event Store"
- H2-H6 (`==`+): Sentence case — "Configuring the event store"
- Exception: proper names stay capitalized in any heading level (Axon Framework, Spring Boot, PostgreSQL, etc.)

**Acronyms** — always uppercase: API, HTTP, HTTPS, JPA, JSON, JVM, gRPC, AMQP, DSL, URI, URL, YAML

**Product names** — exact casing required:
- Axon Framework, Axon Server, Axoniq Platform
- Spring, Spring Boot, GitHub, Gradle, PostgreSQL, Kafka, Testcontainers
- Do not use Axoniq Console or Axoniq Cloud — these products are retired

**Code examples:**
- Always show **both** Spring Boot and plain Java styles (use `[tabs]` blocks with Spring first)
- Use numbered callouts `<1>` `<2>` to explain key lines
- Domain: use "Axon University Registration" as the example domain when a realistic domain is needed
- Verify every class/method against actual framework source before including

**Linking:**
- Internal cross-references: `xref:module:path/file.adoc[Link text]`
- External links: `link:https://example.com[text,role=external,window=_blank]`
- Before writing an xref, verify the target file exists: `find docs -name "target-file.adoc"`
- If target doesn't exist yet, use old filename and add `// TODO: Update to new-name.adoc when renamed`

**Admonitions** (use sparingly):

```adoc
[NOTE]
====
For minor clarifications.
====

[TIP]
====
For recommended practices.
====

[IMPORTANT]
====
For critical information users must not miss.
====
```

**User-centric tone:**
- Correct: "To configure an event processor, use `EventProcessorModule`..."
- Avoid: "The event processor internally uses a token store which maintains..."
- Focus on "how do I accomplish X", not "how does X work internally"
- Explain internal details only when they affect user decisions

**ASCII only — no em-dashes, no smart quotes, no Unicode:**
- Every `.adoc` file must contain only plain ASCII characters (code points 0–127)
- This means: no em-dash in any form — not the Unicode character `—` (U+2014) and not the three-hyphen sequence `---`
- Also forbidden: curly/smart quotes (`"` `"` `'` `'`), ellipsis (`…`), any other non-ASCII glyph
- Use straight ASCII equivalents: `"`, `'`, `...`
- Replace em-dashes with a comma, colon, semicolon, or parentheses depending on context
- Correct: "The processor starts immediately, consuming from the head of the stream."
- Avoid: "The processor starts immediately — consuming from the head of the stream."
- Use LF line endings only, never CR or CRLF

**Terminology (AF5):**
- "entity" not "aggregate" for modeling patterns (aggregates are one type of entity)
- "EventSink" for publishing side — introduce it clearly, explaining its relation to EventBus
- "ProcessingContext" not "UnitOfWork"
- "Converter" not "Serializer"
- Messaging-centric framing: Commands, Events, and Queries are equally important

---

## Phase 5: Update Navigation

After creating or renaming a file, update the nav for the module.

**Nav file location:** `docs/reference-guide/modules/<module>/partials/nav.adoc`

**Nav entry format:**

```adoc
* xref:module-name:path/file.adoc[Link Text]
** xref:module-name:path/subpage.adoc[Sub-page]
```

**Rules:**
- Add the entry in a logical position relative to neighbouring topics.
- For a new top-level page in a module, add a `*` entry.
- For a subpage, indent with `**`.
- Check the ROOT nav aggregator at `docs/reference-guide/modules/ROOT/partials/nav.adoc` — it includes per-module navs via `include::`. Only update this file if adding an entirely new module.

---

## Phase 6: Verify xrefs

After writing, check that all xrefs in the new/updated file resolve:

```bash
# Find all xrefs in the file
grep -o "xref:[^[]*" docs/reference-guide/modules/<module>/pages/<file>.adoc

# For each xref target, verify the file exists
find docs/reference-guide -name "<target-file>.adoc"
```

If a target doesn't exist yet, use the current filename and add a `// TODO` comment.

---

## Phase 7: Update changes-to-process.md

Always check `docs/changes-to-process.md` after writing or updating a page — even if you didn't notice the file being tracked earlier.

1. Search for the filename you just touched:
   ```bash
   grep -n "<filename>.adoc" docs/changes-to-process.md
   ```
2. If it appears and the work is now complete, update the status:
   ```
   **Status:** COMPLETED
   **Changes applied:**
   - <bullet list of what was done>
   ```
3. If it appears and the work is only partially done, update with current progress and what remains.
4. If the file is not listed, no action needed.

Skipping this step leaves stale tracking data. It takes ten seconds and is always worth doing.

---

## Phase 8: Summary

Report back:
1. Files created or modified (with relative paths).
2. Nav entries added or updated.
3. Any xref TODOs left for future file renames.
4. `changes-to-process.md` update status.
5. Any APIs that need further verification before the page is published.
