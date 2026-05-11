# .knowledge

Useful resources for skills development.
The content should be used for context engineering while building new skills.

## Submodules are read-only

All submodules under `.knowledge/repositories/` are tracked as **fetch-only**, enforced by two independent layers:

1. **Disabled push URL** — `remote.origin.pushurl` is set to `DISABLED`, so `git push` resolves to a non-existent remote and fails.
2. **Pre-push hook** — `.git/modules/<submodule>/hooks/pre-push` rejects every push attempt with a clear message. Belt-and-suspenders in case the URL is ever restored by mistake.

Fetch, pull, checkout, local commits, and local branches still work normally — only pushing upstream is blocked.

### Why

These submodules pin external reference repos (Axon Framework sources, example apps, extensions). We read them and occasionally experiment locally, but we never want to publish changes to their upstreams from this workspace.

### Applying / re-applying the lock

Hooks live under `.git/modules/...` and are **not** tracked by git, so after a fresh clone they need to be reinstalled. Run from the superproject root:

```bash
bash .knowledge/scripts/lock-submodules.sh
```

The script is idempotent — it sets the disabled push URL and installs the pre-push hook on every submodule in `.gitmodules`. Re-run it after `git submodule add`, after cloning, or any time you're unsure.

Verify the push URLs:

```bash
git submodule foreach 'git remote -v'
# expect: origin <url> (fetch) / origin DISABLED (push) for each
```

### Discarding local changes in a submodule

Reset a single submodule to its remote branch:

```bash
cd .knowledge/repositories/<path-to-submodule>
git fetch origin
git reset --hard origin/<branch>
git clean -fd
```

Or snap **all** submodules back to the commits this superproject pins (drops local submodule commits and untracked working-tree edits via checkout):

```bash
git submodule update --force --recursive
```

### Re-enabling push for a specific submodule

If you genuinely need to push from a submodule, restore the push URL **and** remove the hook:

```bash
cd .knowledge/repositories/<path-to-submodule>
git remote set-url --push origin "$(git remote get-url origin)"
rm "$(git rev-parse --git-path hooks/pre-push)"
```

Re-lock afterwards with `bash .knowledge/scripts/lock-submodules.sh` from the superproject root.
