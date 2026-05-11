# Reflect Skill

| name | description |
|------|-------------|
| reflect | Analyze the current session and propose improvements to skills. Run after using a skill to capture learnings. Use when user says "reflect", "improve skill", "learn from this", or at end of skill-heavy sessions. |

Analyze the current conversation and propose improvements to skills based on what worked, what didn't, and edge cases discovered.

## Trigger

Run `/reflect` or `/reflect [skill-name]` after a session where you used a skill.

## Workflow

### Step 1: Identify the Skill

If skill name not provided, ask:

```
Which skill should I analyze this session for?
- frontend-design
- code-reviewer
- [other]
```

### Step 2: Analyze the Conversation

Look for these signals in the current conversation:

**Corrections** (HIGH confidence):

- User said "no", "not like that", "I meant..."
- User explicitly corrected output
- User asked for changes immediately after generation

**Successes** (MEDIUM confidence):

- User said "perfect", "great", "yes", "exactly"
- User accepted output without modification
- User built on top of the output

**Edge Cases** (MEDIUM confidence):

- Questions the skill didn't anticipate
- Scenarios requiring workarounds
- Features user asked for that weren't covered

**Preferences** (accumulate over sessions):

- Repeated patterns in user choices
- Style preferences shown implicitly
- Tool/framework preferences

### Step 3: Propose Changes

Present findings using accessible colors (WCAG AA 4.5:1 contrast ratio):

```
┌─ Skill Reflection: [skill-name] ─────────────────────────┐
│                                                          │
│  Signals: X corrections, Y successes                     │
│                                                          │
│  Proposed changes:                                       │
│                                                          │
│  #1  🔴 [HIGH] + Add constraint: "[specific constraint]" │
│  #2  🟡 [MED]  + Add preference: "[specific preference]" │
│  #3  🔵 [LOW]  ~ Note for review: "[observation]"        │
│                                                          │
│  Commit: "[skill]: [summary of changes]"                 │
│                                                          │
└──────────────────────────────────────────────────────────┘

Apply these changes? [Y/n], a subset like "1,3", or describe tweaks
```

Every recommendation MUST be prefixed with `#N` (1-based, in display
order). The numbers are how the user refers to specific items when
selecting a subset or asking for changes ("apply #1 and #3", "drop
#2"). Keep the numbering stable for the duration of the reflection —
if the user asks for tweaks and you re-present, preserve the original
`#N` assignments rather than renumbering.

**Accessible Color Palette** (use ANSI codes in terminal output):

- HIGH: `\033[1;31m` (bold red #FF6B6B - 4.5:1 on dark)
- MED: `\033[1;33m` (bold yellow #FFE066 - 4.8:1 on dark)
- LOW: `\033[1;36m` (bold cyan #6BC5FF - 4.6:1 on dark)
- Reset: `\033[0m`

Avoid: pure red (#FF0000) on black, green on red (colorblind users)

- **Y** — Apply changes, commit, and push
- **n** — Skip this update
- Or describe any tweaks to the proposed changes

### Step 4: If Approved

1. Read the current skill file from `~/.claude/skills/[skill-name]/SKILL.md`
2. Apply the changes using the Edit tool
3. Run git commands:

```bash
cd ~/.claude/skills
git add [skill-name]/SKILL.md
git commit -m "[skill]: [change summary]"
git push origin main
```

4. Confirm: "Skill updated and pushed to GitHub"

### Step 5: If Declined

Ask: "Would you like to save these observations for later review?"

If yes, append to `~/.claude/skills/[skill-name]/OBSERVATIONS.md`

## Example Session

User runs `/reflect frontend-design` after a UI session:

```
┌─ Skill Reflection: frontend-design ──────────────────────┐
│                                                          │
│  Signals: 2 corrections, 3 successes                     │
│                                                          │
│  Proposed changes:                                       │
│                                                          │
│  #1  🔴 [HIGH] + Constraints/NEVER:                      │
│                 "No gradients unless explicitly asked"   │
│                                                          │
│  #2  🔴 [HIGH] + Color & Theme:                          │
│                 "Dark backgrounds: use #000, not #1a1a1a"│
│                                                          │
│  #3  🟡 [MED]  + Layout:                                 │
│                 "Prefer CSS Grid for card layouts"       │
│                                                          │
│  Commit: "frontend-design: no gradients, #000 dark"      │
│                                                          │
└──────────────────────────────────────────────────────────┘

Apply these changes? [Y/n], a subset like "1,3", or describe tweaks
```

## Git Integration

This skill has permission to:

- Read skill files from `~/.claude/skills/`
- Edit skill files (with user approval)
- Run `git add`, `git commit`, `git push` in the skills directory

The skills repo should be initialized at `~/.claude` with a remote origin.

## Important Notes

- Always show the exact changes before applying
- Always number recommendations `#1`, `#2`, … in display order so the
  user can select a subset ("apply #1 and #3") without quoting wording
- Keep `#N` assignments stable across re-presentations within the same
  reflection
- Accept subset replies of the form `1,3` or `#1 #3` as approval for
  exactly those numbered items; treat anything else as decline-or-tweak
- Never modify skills without explicit user approval
- Commit messages should be concise and descriptive
- Push only after successful commit

## Claude Code Hook Configuration

To automatically trigger the reflect skill at the end of sessions, add the following hook to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "~/.claude/skills/reflect/reflect.sh"
      }]
    }]
  }
}
```

This hook will run the reflect script whenever a Claude Code session stops, prompting you to analyze and improve skills based on the session.