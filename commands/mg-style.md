---
description: Build a style kit for a sermon series from its art and font (palette, type, motion personality)
argument-hint: <series name> <art image> [font file] [notes]
---
Use the **motion-designer** skill's style intake (`${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/references/style-intake.md`) to create or update the kit for: $ARGUMENTS

- Run `mg.py palette` on the art and look at the art yourself. Take the colours from the art, write the source of every role, and apply the warnings in `references/anti-patterns.md`. Keep it light.
- Set up the type roles from the given font (copy font files into the kit; read exact family and style names). Use at most two families.
- Score the motion sliders, set tempo, distance and eases, and write 3–5 signature moves and an avoid list.
- New series: prepare **two directions** that differ in motion and type language, each with one key-frame spec.
- Save to `<house>/series/<slug>/kit.json` with the art and fonts beside it.

Don't build any sermon graphics here. Show the kit summary (palette with sources, type, motion sentence, signature moves). If a sermon is in progress, the kit is approved at the mood board gate.
