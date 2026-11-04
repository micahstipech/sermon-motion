# Stipech Motion

A Claude Code plugin that works as a motion-graphics designer for sermon video in DaVinci Resolve.

Give it a sermon (a timeline export and a transcript) and the name of the series folder in
`Sermon Series/`. It reads the
sermon, proposes where graphics belong, and turns the art into a style kit. After you approve a
**storyboard** and then a **mood board**, it builds restrained B-roll graphics as editable Fusion
comps on **V3** and clean 2–3 word Text+ subtitles on **V4** (going up a track whenever something is
already there).

It does not cut the edit and does no sound work.

## Install

On each machine (laptop and editing PC):

```bash
git clone https://github.com/micahstipech/stipech-motion ~/stipech-motion
```

Then in Claude Code:

```
/plugin marketplace add ~/stipech-motion
/plugin install stipech-motion@stipech-motion
/mg-setup ~/stipech-motion/house
```

After pulling updates: `/plugin marketplace update stipech-motion`.

`/mg-setup` checks the dependencies and points the skill at `house/`, the church's shared memory,
which this repo syncs between machines. Dependencies:
- Python 3 with Pillow.
- Node 18+ with Playwright and Chromium.
- ffmpeg with `prores_ks`.
- Optionally, faster-whisper for transcription.

On the editing PC, setup also installs the Resolve pieces.

## Commands

| Command | What it does |
|---|---|
| `/mg` | The whole pipeline, stopping at both approval gates |
| `/mg-setup` | First-run setup on this machine |
| `/mg-series` | Scan a `Sermon Series/<name>` folder, ask for anything missing, analyse Colors, draft the kit |
| `/mg-style` | Finish the series style kit (palette picked from Colors, type, backgrounds, assets, motion, signature moves) |
| `/mg-decode` | A reference video or image → signature moves and kit values |
| `/mg-storyboard` | Read the sermon → storyboard page (**gate 1**) |
| `/mg-moodboard` | Kit + key graphics → mood board page with motion samples (**gate 2**) |
| `/mg-build` | Build, lint, check over real footage, render fallbacks, package for Resolve |
| `/mg-resolve` | Place the package on the open timeline |
| `/mg-learn` | Turn feedback into house rules; record the video in the variation ledger |

## Adding a new sermon series

Make a folder `house/Sermon Series/<Series Name>/` (or wherever `series_root` points) containing:

| File | What it is |
|---|---|
| `Background.jpg` / `.png` | large square texture used as the background (extras: `Background 2`, …) |
| `Colors.jpg` / `.png` | a photo whose colours the series uses; the skill analyses it and picks |
| font files (`.ttf` / `.otf`) | the series fonts |
| `Example.png` | everything used together |
| `Assets/` | transparent PNGs: icons, logos, title cards, other art elements |

Then run `/mg-series <Series Name>`. If anything is missing, the skill asks for it.

## How it works

```
intake ─► storyboard ─► [approve] ─► style kit + mood board ─► [approve] ─► build ─► package ─► Resolve ─► learn
```

- **One spec, two outputs.** Each graphic is a small JSON spec (layers, entrance/exit treatments,
  timing). The engine writes it as a Fusion comp (Text+ → Blur → Transform → Merge, with
  BezierSpline keyframes carrying the eases) and as an HTML page. The HTML page is used for previews,
  mood-board stills and the ProRes 4444 fallback render. Timing and eases match exactly.
- **The style is an input; the thinking is fixed.** A new series is a folder in `Sermon Series/` (Background, Colors, fonts, Example.png, Assets/); the skill scans it, asks for anything missing, and writes the series `kit.json` there.
- **Never the same twice.** `house/ledger.json` remembers every video's intro, outro and treatments,
  and the storyboard check fails on repeats. Brand assets are exempt.
- **Restraint is checked by machine.** `mg.py lint` catches:
  - more than two properties moving on an entrance;
  - holds too short to read;
  - small text;
  - text in the subtitle band;
  - too many layers;
  - overused blur-ins.

## Layout

```
.claude-plugin/          plugin + marketplace manifests
commands/                the /mg-* commands
skills/motion-designer/
  SKILL.md               method, gates, non-negotiables
  references/            style intake, treatments, restraint, anti-patterns, variation,
                         subtitles, resolve, file formats, learning
  engine/mg.py           CLI: inspect, transcribe, chunk, palette, build, lint, ledger, review pages, package
  engine/stipech/        spec → Fusion / HTML, subtitles, palette, lint, ledger, review, package
  engine/render.js       HTML → ProRes 4444 (alpha) or H.264 preview
  engine/stills.js       stills and contact sheets over real footage frames
  engine/resolve/        place.py, install.py, SM Carrier title
  examples/              a worked example series ("Rooted"): kit, specs, storyboard, mood board, plan
house/                   brand assets, Sermon Series/ (one folder per series), rules.md, ledger.json
tests/run.sh             end-to-end check on the example
```

## Status

| Part | Status |
|---|---|
| Spec engine, HTML previews, ProRes 4444 render with alpha, stills, subtitles, palette, lint, ledger, review pages, packaging | Tested end to end (`bash tests/run.sh`) |
| Generated Fusion files | Parse as valid Lua |
| `place.py` track and overflow logic | Tested against a mock of the Resolve API |
| Fusion files and `place.py` in real Resolve | **Not yet tested.** The first session on the editing PC runs the calibration in `skills/motion-designer/references/resolve.md` (text size scale, justification codes, mask units, comp import) and records the results. |

## Credits

Built by merging and adapting ideas and code from Barty-Bart/motion-graphics, alchaincyf/huashu-motion,
Anil-matcha/vox-ai-motion-graphics-generator and coreyhaines31/marketingskills (all MIT). See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
