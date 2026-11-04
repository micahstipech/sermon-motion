---
description: Read a sermon and build the storyboard approval page (gate 1)
argument-hint: [motion/ folder or sermon video] [density light|medium|heavy]
---
Use the **motion-designer** skill (`${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/SKILL.md`, step 1) for: $ARGUMENTS

Read `house/rules.md`, then the whole transcript. Write the one thing, the arc and the central image, choose the moments (including "nothing" beats), and design this sermon's intro and outro (`references/variation.md`). Write `motion/storyboard.json`, grab thumbnails, run `mg.py ledger check` (0 errors), build `motion/review/storyboard.html`, and share it. **Stop and wait for approval.** Apply changes by beat number.
