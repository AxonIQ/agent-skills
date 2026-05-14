# STOP: Unsupported framework

Per SKILL.md Pre-step 1 (Parse), the `framework` argument must be one of `{axon, axoniq}`.

- Received: `framework=spring`
- Supported values: `axon`, `axoniq`
- Result: **STOP — unsupported framework**

No migration was run. No source files were modified (Calendar.java remains in its AF4 shape). The OpenRewrite pre-step was not invoked because parameter validation failed at Pre-step 1.

## Action required

Re-invoke the skill with a supported `framework` value, e.g.:

```
framework=axon configuration=spring mode=single source=...
framework=axoniq configuration=spring mode=single source=...
```
