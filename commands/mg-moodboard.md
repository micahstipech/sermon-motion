---
description: Build the mood board approval page (gate 2) from the approved storyboard and the series kit
argument-hint: [motion/ folder] [series]
---
Use the **motion-designer** skill (`${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/SKILL.md`, step 2) for: $ARGUMENTS

Check that the storyboard is approved; if not, stop and say so. Load or create the series kit (`/mg-style` rules). Build 2–4 key graphics from the storyboard as specs, render a motion sample over a real sermon frame (`--bg`), take stills with `--over`, make a subtitle sample, write `motion/moodboard.json`, run `mg.py moodboard`, and share it. For a new series, show two directions and recommend one. **Stop and wait for approval.**
