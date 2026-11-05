# DaVinci Resolve: tracks, placement, calibration

## Track layout

| Track | Name | Content |
|---|---|---|
| V1 | (editor's) | sermon footage |
| V2 | (editor's) | existing B-roll |
| V3 | SM Graphics | motion graphics (Fusion comps in SM Carrier titles) |
| V4 | SM Subtitles | subtitles (Text+ comps in SM Carrier titles) |
| V5+ | SM Overflow | anything that collided with an existing clip on its target track |

The rule: **if the target track is occupied at that time, go up**, to the first free track above V4,
adding tracks as needed. Never go down; never overwrite. Only tracks that `place.py` creates (plus V3
and V4) get renamed. Clip colours: Teal = graphics, Sand = subtitles, Orange = moved up.

Timing: seconds in the package are measured from the timeline start (the storyboard was made from a
timeline export). `place.py` maps them as `timeline start frame + round(seconds × timeline fps)`.
Pass `--offset S` if the video you analysed starts S seconds into the timeline.

## Two modes

- **Generated (default, `/mg-build`).** Each graphic is a transparent ProRes 4444 clip. `place.py` imports it into
  its own bin (Motion Graphics/<project>) and puts it on V3 as a video-only clip. Nothing is burned into the footage.
- **Fusion (`/mg-fusion`, `"mode": "fusion"` in the plan).** Each graphic is an SM Carrier title holding a Fusion
  comp, described below, with the ProRes clip as a fallback.

Subtitles are Text+ clips on V4 in both modes. Keep the Media Pool organized: everything a package brings in stays
in its bin, and `--archive-older "Text"` moves superseded timelines to Older Versions/Timelines (nothing is deleted).

## How a Fusion graphic gets onto the timeline

1. `SM Carrier` is a transparent title template (`engine/resolve/carrier.setting`). `install.py`
   copies it to `…/Fusion/Templates/Edit/Titles/Sermon Motion/`. **Once**, the editor drags
   Effects › Titles › SM Carrier into the Media Pool (any bin). The script finds it by name.
2. For each graphic: `MediaPool.AppendToTimeline([{mediaPoolItem: carrier, startFrame: 0,
   endFrame: frames-1, trackIndex, recordFrame}])` puts a carrier of the right length on the right
   track.
3. `TimelineItem.ImportFusionComp(<generated .comp>)` loads the graphic into it. The comp is
   regenerated on the PC from the spec, so file paths (logos, textures) point at the PC's copy.
4. If the carrier is missing or the import fails, the graphic's ProRes 4444 render is imported and
   placed instead (`mediaType: 1`, video only).

The result is fully editable: open the clip in the Fusion page and you get the node tree
(Text+ → [Blur] → Transform → Merge, per layer), with BezierSpline keyframes carrying the eases. Text,
font, colour and timing are all ordinary Fusion controls.

`.setting` files are also written for every graphic. Paste one into any Fusion comp, or install it
as a title template for manual reuse.

## Running place.py

```bash
python place.py PACKAGE_DIR --dry-run          # what would go where, nothing touched
python place.py PACKAGE_DIR                    # place
python place.py PACKAGE_DIR --replace          # remove earlier SM clips on SM tracks first
python place.py PACKAGE_DIR --new-timeline "Name"     # duplicate the open timeline, place on the copy
python place.py PACKAGE_DIR --archive-older "Reel 1"  # then move older timelines with that text to Older Versions
python place.py PACKAGE_DIR --prefer-renders   # Fusion mode: ProRes renders instead of comps
python place.py PACKAGE_DIR --no-subtitles     # graphics only
```

- **Resolve Studio**: external scripting works from a terminal. Enable Preferences › System ›
  General › External scripting using: Local. Environment (Windows):
  ```
  RESOLVE_SCRIPT_API=%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting
  RESOLVE_SCRIPT_LIB=C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll
  PYTHONPATH=%PYTHONPATH%;%RESOLVE_SCRIPT_API%\Modules
  ```
  `place.py` also tries the default module paths on its own.
- **Resolve (free)**: external scripting is not available. Use Workspace › Scripts › Utility ›
  "Sermon Motion - Place" (installed by `install.py`), which asks for the package folder.
- Python 3 (64-bit) must be installed on the PC for Resolve's scripting.
- Large subtitle runs (1,500+ chunks for a long sermon) take a few minutes. The script prints
  progress every 100.

## When Claude is connected to the PC

1. `python place.py <pkg> --dry-run` and read the plan (tracks, overflow count).
2. Make sure the right timeline is open (the script uses the current timeline), then place.
3. Read `placement-report.json`; screenshot or describe the first placed graphic against its HTML
   still (Calibration below) the first few times.
4. Never delete or move the editor's clips. `--replace` only touches tracks named "SM …".

## Calibration (first contact; then record results here and in `fusion.py`)

The Fusion file format has a few values that cannot be verified away from Resolve. Place the example
package (`examples/plan.json` → `mg.py package`) and compare each graphic with its HTML still:

| Check | Where | If wrong |
|---|---|---|
| Text size matches the still | `TEXT_SIZE_PER_PX` in `fusion.py` | scale it by still size ÷ Resolve size |
| Left-aligned text starts at its x | `HorizontalLeftCenterRight` / `HorizontalJustificationNew` codes | swap the codes; record the mapping |
| Rule length and thickness | `RectangleMask` Width/Height units (assumed relative to frame width) | convert Height to frame-height units |
| Reveal band hides text until it rises | band Height in the same units | as above |
| Tracking feel | `TRACKING_SCALE` | adjust |
| Comp loads at all | `ImportFusionComp` with a `.comp` | fall back to `comp.Paste(bmd.readfile(setting))` in `place.py` |
| Font found | Text+ Font/Style names | match exact names from Fusion's font list |

Record each confirmed value in a line here with the date and Resolve version, so later machines and
sessions inherit it.

Confirmed (2026-11-04, DaVinci Resolve Studio 21.1.2, Windows, 1080x1920 @ 24, checked against HTML stills):
- Comp loads with `ImportFusionComp` (.comp). Loaders arrive as MediaIn nodes and still render.
- Text size: `Size = px * 1.554 / width` (`TEXT_SIZE_K`); within ~1.5 % of the still. Recheck on 1920x1080.
- Left / centre / right anchors and justification codes: correct as written.
- RectangleMask Width is relative to frame width, Height to frame height (was Height / width).
- `AppendToTimeline` `endFrame` is exclusive: pass the frame count, not count - 1.
- Fonts: a missing Text+ font fails the whole comp and the render (no fallback). Install the series fonts
  and restart Resolve before placing.
- A layer id that is a Lua keyword (`not`, `end`, …) made the .comp unparseable: Resolve imported an
  empty comp that renders opaque black. Node names are now prefixed when they collide.
- Disabling a track does not stop its comps from being evaluated in a render; disable the clip instead.
