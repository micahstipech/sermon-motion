---
description: Build a style kit for a sermon series from its art and font (palette, type, motion personality)
argument-hint: <Series Name> [notes]
---
Use the **motion-designer** skill's style intake (`${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/references/style-intake.md`) to create or update the kit for: $ARGUMENTS

- Start from the series folder (`Sermon Series/<name>/`, see `references/series-folder.md`). If it hasn't been scanned, run `mg.py series "<name>" --draft` first and ask for anything missing.
- Read Example.png first. Pick the palette from the Colors photo analysis (`_stipech/palette.json`), write the source of every role, record every swatch in `color_analysis.picked` (including the unused ones and why), and apply `references/anti-patterns.md`. Keep it light.
- Assign type roles from the fonts in the folder (the scan gives exact family and style names and avg_char). Use at most two families. If none are usable or legible, use Roboto Condensed from Google Fonts (`mg.py font-fallback`).
- Give each background and asset a job (`use`), and mark logos and title cards `"brand": true`.
- Score the motion sliders, set tempo, distance and eases, and write 3–5 signature moves and an avoid list.
- New series: prepare **two directions** that differ in motion and type language, each with one key-frame spec.
- Save to `Sermon Series/<name>/kit.json` (keep `"draft": true` until the mood board is approved).

Don't build any sermon graphics here. Show the kit summary (palette with sources, type, motion sentence, signature moves). If a sermon is in progress, the kit is approved at the mood board gate.
