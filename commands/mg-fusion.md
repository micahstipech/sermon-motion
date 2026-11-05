---
description: Build every approved graphic as an editable Fusion comp instead of the default generated clips
argument-hint: [motion/ folder]
---
Use the **motion-designer** skill (`${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/SKILL.md`, steps 3–5) for: $ARGUMENTS, in **Fusion mode**.

This is the same pipeline as `/mg-build`, and both approval gates still apply, with these differences:

- Set `"mode": "fusion"` in `motion/plan.json`. Each graphic is placed as an SM Carrier title holding a Fusion comp (Text+ nodes with keyframes), so words, fonts and timing can be changed in the Fusion page without a re-render.
- Render ProRes 4444 fallbacks anyway. `place.py` uses one if a comp fails to import.
- Torn paper edges and the paper slide are generated-mode looks. In Fusion a torn panel has a straight edge and the slide becomes an edge wipe, so tell the user if the mood board relied on them.
- Install the series fonts and restart Resolve before placing: a missing Text+ font fails the whole comp and the render.

The standing rules still apply: one clip per graphic change on the graphics track, subtitles as their own track, and only the allowed animation.
