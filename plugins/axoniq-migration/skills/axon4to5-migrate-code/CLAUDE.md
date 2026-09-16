# CLAUDE.md

All-file content language: English.

Be proactive, challenge me. If you think you have a better idea than what I wanted from you, propose other things.

## `references/docs/` is generated -- never edit it

Everything under `references/docs/` is a one-way mirror of
`docs/reference-guide/modules/migration/pages` in [AxonIQ/AxonFramework](https://github.com/AxonIQ/AxonFramework),
produced by `scripts/sync-migration-docs.sh` at the repo root. Antora `include::example$...` directives are
resolved inline during the sync, so each page carries its own code samples.

To change any of that content:

1. Fix it upstream in the AxonFramework repository and get it merged to `main`.
2. Run `scripts/sync-migration-docs.sh` here to pull it in.

Do not patch the files directly -- the next sync overwrites them without warning, and
`scripts/sync-migration-docs.sh --check` fails on any hand-edit. Provenance (upstream commit) and
per-file checksums live in `references/docs/.upstream.json`.

Hand-authored knowledge belongs in `references/recipes/` and `references/DURABILITY.md` instead.
