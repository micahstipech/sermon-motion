---
description: Take in a new sermon series folder (Sermon Series/<name>) and ask for anything missing, then analyse Colors and draft the kit
argument-hint: <Series Name or folder path>
---
Use the **motion-designer** skill's series-folder guide (`${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/references/series-folder.md`) for: $ARGUMENTS

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/engine/mg.py series "<name>"` (`--list` shows all series). It resolves the name inside `series_root`, which defaults to `<house>/Sermon Series`.
2. If it reports MISSING or CHECK lines, ask for everything in **one** message, worded from the scan, and say what you'll do in the meantime. Never invent a missing asset. Missing, web-only, unreadable or illegible fonts → Roboto Condensed from Google Fonts (`mg.py font-fallback "<name>" [--roles text,subtitle]`; the draft does it automatically when there are no usable fonts).
3. Look at Example.png, then the backgrounds, Assets and the Colors photo yourself.
4. Run with `--draft` to write `kit.json` (or keep the existing kit; use `--force` only if the user wants it redone), then finish it with `/mg-style` rules: pick colours from the Colors analysis and record `color_analysis.picked` for every swatch; assign type roles; give each background and asset a `use` (`"brand": true` for logos and title cards); set motion, signature moves and the avoid list.
5. Summarise: what was found, the colours you picked (and didn't), the font roles, each background's job, and anything still missing. The kit stays `"draft": true` until the mood board is approved.
