# Changelog

All notable changes to the **axoniq-framework-contribution** plugin will be documented in
this file. This plugin is for **contributors to the Axon Framework project itself** (developing
the framework) — *not* for developers building applications with it (use `axoniq-app-development`).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> History before 1.3.1 was authored upstream while this plugin was named
> `axonframework-contributor-tools` (and earlier as the standalone `code-review` /
> `axonframework-core-coding` skills). Entry bodies are preserved; the duplicated/mis-ordered
> upstream version headers were consolidated.

## [1.4.2] - 2026-07-16

### Changed

- `axoniq-framework-contribute-code`: aligned the "What Belongs in Each Framework" split with the 5.2.0 release — the OpenTelemetry tracing extension is no longer part of open-source Axon Framework, and the commercial Axoniq Framework list now includes message transformation (`EventTransformation`, `EventTransformerChain`) and persistent streams in the Axon Server connector.

## [1.4.1] - 2026-07-08

### Changed

- `axoniq-framework-contribute-code`: split the 2144-line `SKILL.md` into a core file (framework selection, design philosophy, coding conventions, checklist, anti-patterns) plus a routing table, with the eight detailed pattern topics moved verbatim into `references/`.
- `axoniq-framework-contribute-review`: deduplicated the report format, which previously lived three times (twice inline plus `templates/review-report-template.md`) and now lives only in the template; fix-crafting detail moved to `references/fix-patterns.md`; handler-wrapper and test-quality sections now point at the `contribute-code` references instead of repeating them.
- `axoniq-framework-contribute-pr-comments`: compressed the rare >100-reply pagination sub-query to prose and removed special-case handling already covered elsewhere in the workflow.

### Fixed

- `axoniq-framework-contribute-review`: `quick-reference.md` instructed the OPPOSITE of the project's null-annotation convention in three places — it recommended `jakarta` annotations and flagged `jspecify` as BLOCKING, when `jakarta` is actually forbidden by checkstyle. Also removed dead links to `code-review-checklist.md` and a nonexistent `axon-framework-5-patterns` skill.
- `axoniq-framework-contribute-code`: fixed stale `allowed-tools` (`Task` → `Agent`), duplicate section numbering, misplaced fluent-API examples, and references to nonexistent skills.
- `axoniq-framework-contribute-docs`, `axoniq-framework-contribute-review`, `axoniq-framework-contribute-pr-comments`: replaced stale `Task`/`TodoWrite` tool grants and references with the current `Agent`/`TaskCreate`/`TaskUpdate` tools — the `Task` subagent tool no longer exists in Claude Code.

## [1.4.0] - 2026-06-04

### Changed

- Renamed all four skills to the `axoniq-framework-contribute-*` scheme (directories and skill `name`), updating slash-command examples and cross-references throughout:
  - `axonframework-contributor-coding` → **`axoniq-framework-contribute-code`**
  - `axonframework-contributor-docs-update` → **`axoniq-framework-contribute-docs`**
  - `axonframework-contributor-review` → **`axoniq-framework-contribute-review`**
  - `axonframework-contributor-pr-comments` → **`axoniq-framework-contribute-pr-comments`**
- Fixed a stale `axonframework-core-coding` path reference in the contribute-code README. No skill-content changes.

## [1.3.1] - 2026-06-02

### Changed

- Renamed from `axonframework-contributor-tools` to **`axoniq-framework-contribution`** and folded into the `axoniq` multi-runtime marketplace; now packaged for Claude, Codex, and Cursor. No skill-content changes.
- Consolidated the changelog: de-duplicated the two conflicting `1.1.0` sections and backfilled the previously-missing `1.3.0` entry.

## [1.3.0] - 2026-05-12

### Added

- **`axonframework-contributor-pr-comments` skill** — systematically process GitHub PR review comments one by one: resolves PR refs, fetches inline/review-body/issue comments, filters noise, classifies threads, and verifies each concern against the current code while running related tests.
- **`axonframework-contributor-docs-update` skill** — add or update Axon Framework 5 reference documentation (AsciiDoc conventions, module structure, API verification, navigation updates), including a current-branch flow.

### Changed

- Restructured into a `plugins/<plugin>/skills/` layout and renamed the original skills to `axonframework-contributor-review` (was `code-review`) and `axonframework-contributor-coding` (was `axonframework-core-coding`).

## [1.2.0] - 2026-02-26

### Added

#### Message Handler Wrapper Patterns (CRITICAL)
- **New comprehensive section in the `axonframework-contributor-coding` skill** covering handler wrapper patterns: the `unwrap()` pattern (why `instanceof` checks fail with wrappers), wrapper-chain structure, correct type-compatibility checks, preserving wrapper chains, `@HasHandlerAttributes` for configuration, and real-world examples from `ReplayAwareMessageHandlerWrapper` and `MethodSequencingPolicyEventHandlerDefinition`.
- **New checklist item in the code-review skill** (Message Handler Wrapper Patterns): critical checks for `HandlerEnhancerDefinition` implementations, anti-patterns to flag (instanceof checks, unnecessary unwrapping), and grep-based detection.
- **New fix type** for handler-wrapper pattern violations: type-check fixes (`instanceof` → `canHandleMessageType`), wrapper-chain preservation, and wrapper class definitions.

#### Key principles documented
- Use `canHandleMessageType()` instead of `instanceof`; preserve the wrapper chain; wrappers should not implement specific handler interfaces; use `unwrap()` only when accessing wrapper functionality; read attributes via `@HasHandlerAttributes` rather than annotations directly; accept `MessageHandlingMember` in signatures, not concrete handler types.

## [1.1.0] - 2026-02-17

### Added

#### Test quality guidance
- Test object creation strategy hierarchy (prefer real objects over mocks), stub implementation patterns, resource cleanup requirements (ExecutorServices, connections, file handles), and factory methods for test messages.

#### Configuration class patterns
- Immutable configuration-class design with documentation, constructor javadoc for default values, configuration testing requirements (defaults, immutability, fluent chaining, null safety), and factory methods for component creation.

#### Enhanced code-review checks
- Configuration-class verification, test-quality assessment, constructor-javadoc validation, terminology-clarity checks, and resource-cleanup verification in the review checklist and quick-reference.

### Changed

- Enhanced the code-review skill with configuration-specific checks and expanded the quick-reference with test-quality patterns.

### Fixed

- `marketplace.json`: added the required `source` field; fixed a bash-command error in the code-review skill; updated the plugin installation URL to use HTTPS.

## [1.0.1] - 2026-02-06

### Fixed

- Fixed a bash-command error in the code-review skill caused by an unescaped backtick-exclamation pattern in markdown (removed backticks around `!` in the "Breaking Change" checklist item to prevent shell interpretation issues).

## [1.0.0] - 2026-02-06

### Added

#### Two comprehensive skills

- **code-review skill** — code-review system for Axon Framework: automated documentation-completeness checks (Antora reference guide), test-coverage verification (80% minimum), JavaDoc validation (`@since`, `@author`, `@Nullable`/`@Nonnull`), AF5 pattern-compliance checking, an interactive numbered fix workflow, structured reports with severity levels (blocking/warning/suggestion), git-based change detection, a 27-category review checklist, a quick-reference with grep patterns, and report templates.
- **axonframework-core-coding skill** — three-tier API architecture (Infrastructure/Gateway/Context-scoped), AF5 fluent builder patterns with templates, modern Java patterns, Jakarta annotations, `@Nested` test organization, interface composition, component lifecycle (`Registration`, `ProcessingLifecycle`), the `ResourceKey` pattern, thread-safety guidelines, SPI-vs-API separation with `@Internal`, validation/error-handling patterns, `ComponentBuilder`/`ModuleBuilder` patterns, the `DescribableComponent` pattern, a design checklist, anti-patterns, and real examples from `EventBus`/`EventGateway`/`EventAppender`.

### Documentation

- README, per-skill READMEs, quick-reference guides, the 27-category code-review checklist, and pattern templates.
