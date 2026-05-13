# Recipe: openrewrite

Run the external `axon4to5-openrewrite` skill once as the bulk mechanical pass.

## Canonical reference

- [../docs/paths/index.adoc](../docs/paths/index.adoc)
- [verification.md](verification.md)

## Goal

Apply the Axon 4 -> 5 OpenRewrite recipe and leave the working tree ready for
per-construct recipes. Compilation is not expected after this step.

## Inputs

- `license`: pinned `free-af5` or `axoniq-commercial`.
- `build-tool`: pinned `maven` or `gradle`.
- `commit`: always false; the migration runner owns commits.

## Preflight

1. If the build already depends on AF5 and the OpenRewrite migration commit is
   present, emit `skipped`.
2. If the project has no Axon 4 dependency, emit `rejected`.

## Procedure

1. Map license to external flag:

   | License | External flag |
   |---|---|
   | `free-af5` | `--framework axon` |
   | `axoniq-commercial` | `--framework axoniq` |

2. Invoke `axon4to5-openrewrite` with commit disabled.
3. Capture the external result:

   | External result | Recipe result |
   |---|---|
   | exit 0 and diff exists | `success` |
   | already applied/no diff | `skipped` |
   | license/build ambiguity | `needs-decision` |
   | tool failure | `failed` with external summary in notes |

4. Do not run compile/verify. The next per-target recipe owns that.

## End condition

- OpenRewrite either produced a diff, was already applied, or failed with a
  classified reason.
- No project files were added by this recipe except the external recipe's
  normal source/build edits.

## Output

```yaml
result: success | skipped | rejected | needs-decision | failed
target: <project root>
reason: <required except success>
decisions:
  framework: axon | axoniq
  compile-expected: false
caller-expects:
  commit: true | false
  next: proceed | ask-user | halt
notes: []
```
