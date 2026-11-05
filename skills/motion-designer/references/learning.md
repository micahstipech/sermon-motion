# Getting better every video

The tenth video should be right on the first try. That happens only if every note the user gives
becomes a rule the next video starts from. Method adapted from huashu-motion's experience layers and
marketingskills' living AGENTS.md (both MIT).

## house/rules.md

Read it before every project. One line per rule, newest at the bottom of its section, each tagged:

```markdown
## Preferences (the user's own words)
- [pref 2026-11-08] "Scripture references always in small caps under the verse, never above." (Rooted wk1)

## Observed (seen in one video)
- [obs 2026-11-08] Titles in the left third collide with the pulpit on wide shots at 0:00–5:00; check the wide shot first.

## Verified (held across 2+ videos, or measured)
- [ver 2026-11-22] Subtitle y=940 clears the lower thirds the editor uses for the livestream.

## Calibration (Resolve / Fusion facts)
- [cal 2026-11-10] Text+ Size = px / 1920 confirmed on Resolve 20.1, Windows.
```

- **pref**: quote the user. It holds until they say otherwise. Never generalise one user's taste
  into a shipped rule in this skill.
- **obs**: something you saw once. Promote it to **ver** when a second video confirms it.
- **cal**: technical facts about the PC and Resolve. Also update [resolve.md](resolve.md)
  §Calibration and the constants in `fusion.py` when confirmed.
- Fix any rule a new note contradicts. Don't keep both.
- If a rule could be enforced by a tool (lint, ledger, chunker), change the tool instead and delete
  the rule.

## When to write

- During review: when the user rejects or changes something, note their words right away.
- At sign-off (`/mg-learn`): go through the session's notes, write the rules, run `ledger add`,
  update the kit if the look changed, and offer to commit and push the house folder.

## Improving the skill itself

When a rule turns out to be true for any church and any series (not just this user's taste), move it
into the reference it belongs to (restraint, treatments, anti-patterns…) in the sermon-motion repo,
and delete it from rules.md.
