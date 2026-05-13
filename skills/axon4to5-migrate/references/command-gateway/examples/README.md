# Command Gateway Patterns

| Case | Preserve | Rewrite direction |
|---|---|---|
| REST/controller async send | returned future type | adapt AF5 command result to the existing future/void response |
| blocking `sendAndWait` | blocking public contract | make blocking explicit around AF5 async dispatch |
| callback dispatch | success/failure branches | completion-stage callbacks |
| reactive endpoint | reactive wrapper type | wrap AF5 completion stage |
| Kotlin caller | nullability/suspend shape | preserve public Kotlin API and adapt dispatch internally |

Use `../command-gateway.md` as the source of truth.
