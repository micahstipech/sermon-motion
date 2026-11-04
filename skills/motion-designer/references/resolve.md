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

## How a graphic gets onto the timeline

1. `SM Carrier` is a transparent title template (`engine/resolve/carrier.setting`). `install.py`
   copies it to `…/Fusion/Templates/Edit/Titles/Stipech Motion/`. **Once**, the editor drags
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
python place.py PACKAGE_DIR --prefer-renders   # ProRes renders instead of comps
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
  "Stipech Motion - Place" (installed by `install.py`), which asks for the package folder.
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

Confirmed: (none yet)
