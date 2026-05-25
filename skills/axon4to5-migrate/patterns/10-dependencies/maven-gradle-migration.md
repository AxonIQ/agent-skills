# Dependency Migration — Maven / Gradle

Update project dependencies from Axon Framework 4 to Axon Framework 5. The Maven group ID and artifact IDs
changed; the YAML configuration namespace changed from `axon.serializer` to `axon.converter`.

## Import Mappings

| AF4 artifact | AF5 artifact |
|---|---|
| `org.axonframework:axon-spring-boot-starter` | `io.axoniq.framework:axoniq-spring-boot-starter` |
| `org.axonframework:axon-test` (scope=test) | `org.axonframework.extensions.spring:axon-spring-boot-starter-test` |
| `io.axoniq.console:console-framework-client-spring-boot-starter` | Remove — incompatible with AF5 |

## Detection

```bash
grep -rn 'org.axonframework' --include='pom.xml' --include='build.gradle' --include='build.gradle.kts' .
grep -rn 'axon.serializer' --include='*.yaml' --include='*.properties' .
```

## Axon Framework 4 — pom.xml

```xml
<properties>
    <axon.version>4.13.1</axon.version>
</properties>

<dependencies>
    <dependency>
        <groupId>org.axonframework</groupId>
        <artifactId>axon-spring-boot-starter</artifactId>
        <version>${axon.version}</version>
    </dependency>
    <dependency>
        <groupId>org.axonframework</groupId>
        <artifactId>axon-test</artifactId>
        <version>${axon.version}</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

## Axon Framework 5 — pom.xml

```xml
<properties>
    <axon.version>5.0.0</axon.version>
</properties>

<dependencies>
    <dependency>
        <groupId>io.axoniq.framework</groupId>
        <artifactId>axoniq-spring-boot-starter</artifactId>
        <version>${axon.version}</version>
    </dependency>
    <dependency>
        <groupId>org.axonframework.extensions.spring</groupId>
        <artifactId>axon-spring-boot-starter-test</artifactId>
        <version>${axon.version}</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

## YAML configuration namespace

```yaml
# AF4
axon:
  serializer:
    general: jackson
    events: jackson

# AF5
axon:
  converter:
    general: jackson
    events: jackson
```

- `axon.serializer.*` → `axon.converter.*` — rename the top-level key.
- All child keys (`general`, `events`, `messages`) remain the same — only the parent changes.

## Notes

- Remove `io.axoniq.console:console-framework-client-spring-boot-starter` — no AF5-compatible version exists yet.
- For Maven multi-module projects, update the BOM/parent version in the root `pom.xml` only; child modules inherit.
- For Gradle, replace `implementation("org.axonframework:axon-spring-boot-starter:…")` with
  `implementation("io.axoniq.framework:axoniq-spring-boot-starter:…")`.
- The `axon-test` artifact is replaced by `axon-spring-boot-starter-test` from the Spring extensions group.
- **OpenRewrite status:** Partial — OR renames BOM (`Axon4ToAxon5Bom`), bumps versions, swaps starter to commercial (`axon4-to-axoniq5-spring.yml`), and renames the `axon.serializer` Spring property prefix; AI removes `console-framework-client-spring-boot-starter`.
