# Blocker resolution

Orchestrator-owned playbook for the **Resolve blocker** node in `SKILL.md` § Queue flow. Runs once per item after a recipe sub-flow returns **Result: 🚧 Blocker**.

For now, this node is a **single step**: present the recipe's **Options** list to the caller via the `AskUserQuestion` tool and act on their choice.

## Flow

1. Read the recipe's result block (already parsed by the orchestrator).
2. Invoke `AskUserQuestion` with:
   - **question:** something like *"Blocker on `<$SOURCE>` — how should we proceed?"* (one short sentence; include the source FQN/path so the caller does not have to scroll up).
   - **header:** short chip label, e.g. *"Blocker"*.
   - **options:** one per entry in the recipe's **Options** list. The option `label` is the option `id` rendered as bolded text (`skip`, `revert`, `solve-manually`, plus any recipe-specific extensions). The option `description` is the short description from the recipe.
   - **multiSelect:** `false` — exactly one continuation path per item.
3. Apply the caller's choice:
   - **skip** → mark the item `Blocker` in the queue with note "skipped by caller"; queue moves on.
   - **revert** → undo any edits this recipe applied to `$SOURCE` (use `git checkout -- <files>` or `git restore <files>` scoped to the item's `# Scope`); mark item `Blocker` with note "reverted"; queue moves on.
   - **solve-manually** → pause the item; surface a short instruction to the caller naming what they need to fix; on confirmation re-enter the recipe sub-flow on the same item.
   - **recipe-specific option** → re-enter the recipe sub-flow on the same item, passing the chosen option id as an additional hint so the recipe knows which path to take.

## Constraints

- One resolution attempt per item. If the re-entered sub-flow returns **Blocker** again, mark the item blocked immediately — no second `AskUserQuestion`.
- Do NOT edit source files directly from this node. `revert` uses git; everything else goes back through the recipe sub-flow.
- Do NOT invent options the recipe did not list. If the recipe omitted a baseline option by mistake, fail loudly rather than silently substituting.

## Auto mode (`auto=true`)

Skip `AskUserQuestion`. Pick the option the recipe marked `(Recommended)`; if no option is marked, fall back to `skip`. Recipes mark a non-`skip` option `(Recommended)` only when it is safe to auto-apply (see `DEFAULT.md § Blocker Options baselines`). Emit:

> ⚙️ auto: Blocker on `<$SOURCE>` → `<chosen id>`

- **skip / revert** → handled here exactly as the interactive path (mark `Blocker`, queue moves on; `revert` git-restores first). Record as `auto-<id>`.
- **recipe-specific option** (e.g. saga `stateful-rewrite`) → re-enter the recipe sub-flow on the same item, passing the chosen option id as a hint — same as interactive resolution. Budget = 1: if the re-entered run blocks again, mark blocked immediately. Record as `auto-<id>`.
