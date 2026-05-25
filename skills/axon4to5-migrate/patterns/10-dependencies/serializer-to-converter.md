# Serializer → Converter

AF5 renames the serialization SPI from `Serializer` to `Converter` and moves the package from
`org.axonframework.serialization` to `org.axonframework.conversion`. The Spring Boot property prefix moves
accordingly: `axon.serializer.*` → `axon.converter.*`. The OpenRewrite recipe does the package rename only —
concrete class names (`JacksonSerializer`, `XStreamSerializer`) are NOT auto-renamed and must be rewritten by AI.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.serialization.Serializer` | `org.axonframework.conversion.Converter` |
| `org.axonframework.serialization.json.JacksonSerializer` | `org.axonframework.conversion.json.JacksonConverter` |
| `org.axonframework.serialization.xml.XStreamSerializer` | *(no AF5 equivalent — replace with Jackson)* |
| YAML key `axon.serializer.*` | `axon.converter.*` |

## Detection

**Pre-migration (AF4 original):**

```bash
# Code references
grep -rn '\bSerializer\b\|JacksonSerializer\|XStreamSerializer' \
  --include='*.java' --include='*.kt' --include='*.scala' .

# Config keys
grep -rn 'axon\.serializer' --include='*.yaml' --include='*.yml' --include='*.properties' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
# Leftover class-name references after the package move
grep -rn 'JacksonSerializer\|XStreamSerializer\|\bSerializer\b' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

## Axon Framework 4 Code

```java
import org.axonframework.serialization.Serializer;
import org.axonframework.serialization.json.JacksonSerializer;

@Bean
public Serializer serializer(ObjectMapper objectMapper) {
    return JacksonSerializer.builder()
            .objectMapper(objectMapper)
            .build();
}
```

```yaml
# application.yaml
axon:
  serializer:
    general: jackson
    events: jackson
```

## Axon Framework 5 Code

```java
import org.axonframework.conversion.Converter;
import org.axonframework.conversion.json.JacksonConverter;

@Bean
public Converter converter(ObjectMapper objectMapper) {
    return JacksonConverter.builder()
            .objectMapper(objectMapper)
            .build();
}
```

```yaml
# application.yaml
axon:
  converter:
    general: jackson
    events: jackson
```

## Notes

- **`XStreamSerializer` has no AF5 replacement** — AF5 standardises on Jackson. Migrate XStream-encoded events
  ahead of the upgrade, or keep an AF4 reader process alongside until the legacy stream is drained.
- **`SerializerType.XSTREAM` / `JAVA` enum values** in `application.yaml` are intentionally left untouched by the
  recipe — they have no `ConverterType` equivalent and would silently break event reading. Fix manually to
  `jackson` (or remove if the default suffices).
- **Bean name change is conventional, not mandatory.** Renaming the `@Bean` method `serializer` → `converter`
  matches the new SPI but the framework binds by type, not name.
- **OpenRewrite status:** Partial — `ChangePackage` in `axon4-to-axon5-conversion.yml` rewrites the package
  prefix, and `ChangeSpringPropertyKey` in `axon4-to-axon5-extension-spring.yml` rewrites the YAML key prefix; AI
  rewrites the concrete class names (`JacksonSerializer` → `JacksonConverter`, drop `XStreamSerializer`) and the
  `SerializerType` enum values inside YAML.

## Partial migration state (post-OpenRewrite)

OpenRewrite's `axon4-to-axon5-conversion.yml` runs a single `ChangePackage` rule that rewrites
`org.axonframework.serialization` → `org.axonframework.conversion` recursively. After the recipe:

- Imports such as `org.axonframework.conversion.json.JacksonSerializer` are correct in terms of package but the
  AF5 class is named `JacksonConverter` — the import will not resolve. AI renames the class references.
- The `Serializer` interface name itself is also still present in code (the recipe moves only the package, not
  the class name). Rewrite to `Converter`.
- `application.yaml` keys are renamed by `ChangeSpringPropertyKey` in `axon4-to-axon5-extension-spring.yml`
  (`axon.serializer` → `axon.converter`); nested child keys (`general`, `events`, `messages`) carry over
  unchanged.

```bash
# Find leftover class-name references after the package move
grep -rn 'JacksonSerializer\|XStreamSerializer\|\bSerializer\b' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```
