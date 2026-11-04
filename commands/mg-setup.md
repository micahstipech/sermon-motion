---
description: First-time setup for Stipech Motion on this machine (dependencies, house folder, Resolve)
argument-hint: [path to house folder]
---
Set up the **motion-designer** skill on this machine (`${CLAUDE_PLUGIN_ROOT}/skills/motion-designer`).

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/engine/mg.py doctor`. For anything missing, give the exact install command for this OS (Python 3, Node 18+, ffmpeg with prores_ks, `npm i -g playwright` or a local install plus `npx playwright install chromium`, `pip install pillow`, optionally `pip install faster-whisper`). Ask before installing anything.
2. House folder: use $ARGUMENTS if given; otherwise propose `house/` inside the user's clone of the stipech-motion repo (so git syncs the laptop and the PC). Write `~/.stipech-motion/config.json` as `{"house": "<absolute path>"}`. Create `brand/`, `series/`, `rules.md` and `ledger.json` if they are missing (copy the repo's `house/` templates).
3. Ask for brand assets (logo files, church name lockup, brand fonts) and put them in `house/brand/`.
4. If this machine is the editing PC with DaVinci Resolve: run `python ${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/engine/resolve/install.py`, then tell the user to drag Effects › Titles › SM Carrier into the Media Pool once, and ask whether they have Resolve Studio (external scripting) or the free version (Workspace › Scripts). Record the answer in `house/rules.md` under Calibration.
5. Report what is ready and what is still missing.
