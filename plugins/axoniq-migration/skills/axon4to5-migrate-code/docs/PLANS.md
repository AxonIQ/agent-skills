# Plans

Parked ideas for this skill. For humans only: nothing here is implemented, and nothing here may be
referenced from `SKILL.md` or any file the skill loads at runtime.

## Sync the commercial (Axoniq Framework) migration docs

**Status:** blocked, deliberately not implemented.

`scripts/sync-migration-docs.sh` mirrors the open-source migration docs from
[AxonIQ/AxonFramework](https://github.com/AxonIQ/AxonFramework) (public, Apache-2.0). The
commercial counterpart lives in `AxonIQ/axoniq-framework`, which is **private and proprietary
(NOASSERTION)**. This repository is **public**. Syncing the second into the third would publish
proprietary content in full text, into git history where a later delete does not really undo it.

**Unblock condition:** `AxonIQ/axoniq-framework` becomes public, or the commercial content is
explicitly cleared for public distribution. Failing that, the work belongs in a separate private
plugin rather than here. Note the blocker is the *source* repo's visibility, not this one's.

There is also a practical reason beyond licensing: a public repo whose sync script needs
credentials for a private repo breaks for external contributors, and the CI `--check` job would
fail on any fork or unauthenticated runner.

### What it would involve

The commercial docs are an Antora *overlay of the same module* we already sync, so the existing
resolver works unchanged:

| Source | Content |
| --- | --- |
| `docs/reference-guide/modules/migration/pages/paths/` | `upcasters.adoc`, `multi-tenancy.adoc` |
| `docs/reference-guide/modules/migration/examples/migration/paths/multitenancy/` | 13 `.java` samples |
| `docs/reference-guide/modules/advanced-migration/pages/paths/` | `5.0-to-5.1.adoc`, `5.2.0-to-5.2.1.adoc` |
| `docs/reference-guide/modules/{message-transformation,multi-tenancy}/` | further commercial pages |

Same module path, same `include::example$migration/...[tag=...]` mechanism. The work is therefore
mostly plumbing: lift the repo URL, ref, module path and target directory out of
`scripts/sync-migration-docs.sh` into a small config so one implementation drives both syncs, then
re-run the existing validation suite against the second source.

### Symptom it would fix

`references/docs/paths/index.adoc` carries `xref:` links to `paths/upcasters.adoc` and
`paths/multi-tenancy.adoc` inside `ifdef::advanced-framework[]`. Antora resolves those correctly
when building the commercial site, but an agent reading the raw AsciiDoc does not honour the
conditional and can follow a link to a file that is not present.

### Lighter alternative

Leave the commercial content out entirely and teach the recipes to recognise `upcasters` and
`multi-tenancy` as commercial-only paths, pointing the user at the Axoniq documentation by name.
No content duplication and no licensing question, while still removing the dead end.
