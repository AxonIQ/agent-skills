# Event Processor Patterns

| Case | Preserve | Rewrite direction |
|---|---|---|
| plain projector | namespace and handler payload | `@Namespace`, AF5 handler imports |
| handler dispatches commands | side-effect timing | method-parameter dispatcher, async send shape |
| sequencing configured externally | ordering key | `@SequencingPolicy` or AF5 processor config |
| processor config bean/YAML | processor name, token/DLQ settings | `EventProcessorDefinition` or `MessagingConfigurer#eventProcessing(...)` |

Use `../event-processor.md` and `../configuration-reads.md` as the source of
truth.
