---
description: Run the whole motion-graphics pipeline for a sermon, stopping at the storyboard and mood board for approval
argument-hint: [sermon video or folder] [series name]
---
Use the **motion-designer** skill (`${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/SKILL.md`) and run its full pipeline for: $ARGUMENTS

1. Intake (one message with defaults): scan the series folder (`mg.py series "<name>"`) and ask for anything missing in that same message. Then inspect the video and get word timings.
2. Read the sermon and build the storyboard. **Stop at gate 1** until the user approves it.
3. Style (load or create the series kit), then the mood board. **Stop at gate 2** until the user approves it.
4. Build, lint, check stills over real footage, self-review, render fallbacks, package.
5. Place in Resolve if connected to the editing PC, otherwise hand over the package.
6. Learn: rules, ledger, kit, and offer to commit and push the house folder.

Read `house/rules.md` first. Never skip a gate, even if the user seems in a hurry; offer a faster storyboard instead.
