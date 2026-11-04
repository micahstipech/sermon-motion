---
description: Build every approved graphic and the subtitles, check them over real footage, render fallbacks and package for Resolve
argument-hint: [motion/ folder]
---
Use the **motion-designer** skill (`${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/SKILL.md`, steps 3–4) for: $ARGUMENTS

Check that both the storyboard and the mood board are approved; if not, stop. Write one spec per beat, run `mg.py lint` until there are 0 errors, build, and take stills over the brightest real frame behind each graphic. Look at every sheet, write three self-review notes, and fix them. Chunk and proofread the subtitles. Render ProRes 4444 fallbacks at the timeline fps, write `motion/plan.json`, and run `mg.py package`. Report what was built, any lint warnings you accepted and why, and the package path.
