# File formats

All JSON. Paths are relative to the file that contains them unless absolute.
Working examples: `examples/` (kit, specs, storyboard, moodboard, plan).

## Graphic spec (`motion/specs/NN-name.json`)

One graphic on the motion-graphics track. Both backends (Fusion and HTML) render from it.

```json
{
 "id": "03-rooted-title", "kind": "title", "duration": 6.0, "fps": 24, "in": 74.2,
 "width": 1920, "height": 1080,
 "line": "the spoken line it covers",
 "layers": [
  {"id": "rule", "type": "rect", "x": 196, "y": 648, "w": 360, "h": 2, "color": "light@70", "anchor": "left",
   "in": {"treatment": "fade", "at": 0.2}, "out": {"treatment": "fade", "at": 5.9}},
  {"id": "title", "type": "text", "text": "Nothing has roots", "font": "display", "size": 84,
   "color": "light", "x": 196, "y": 580, "align": "left",
   "in": {"treatment": "rise", "at": 0.55}, "out": {"treatment": "sink", "at": 5.9}}
 ]
}
```

- `in` (spec level): timeline seconds where the graphic starts. `duration`: seconds. Layer times
  are clip-local.
- `width`/`height` set the format: horizontal (default) or vertical. Vertical is treated as social video by default.
  Text must stay inside the safe area for its format ([restraint.md](restraint.md)).
- Coordinates: px in the spec frame, y down. Text `x,y` is the anchor: left edge (`align: left`),
  centre, or right edge, at the text's vertical middle. Rect `x,y` is the anchor end (`anchor`) at
  its vertical middle. Image `x,y` is its centre.
- `type`: `text` | `rect` | `image`.
- Text: `text` (use `\n` for a deliberate line break), `font` (a kit type role), `size` px, `color`
  (kit role, `#hex`, or `role@alpha%`), `tracking` (em), `leading`, `case: "upper"`, `small: true`
  for labels 22–27 px.
- Rect: `w`, `h`, `radius`, `anchor` (`left` | `center` | `right`; draw grows from it).
- Image: `src` relative to the series folder (`"Background.jpg"`, `"Assets/Icon - Tree.png"`).
  Size: `"fit": "cover"` (fills the frame: backgrounds), `"fit": "contain"`, `"w"` or `"h"` px. Add
  `"zoom"` with a fit for a tighter crop. `x,y` is the image centre (default: frame centre; move it to
  pan a cover crop).
- `in`/`out`: `{"treatment", "at", "dur"?, "ease"?, "distance"?, "from"?}`
  ([treatments.md](treatments.md)).
- `anim` (optional, overrides a property's treatment keys): `{"dy": [[t, value, ease], ...]}`.
  Properties: `opacity`, `dx`, `dy` (px), `scale`, `blur` (px), `tracking` (em), `reveal` /
  `reveal_out` (0–1 wipe), `draw` (0–1, rects), `rotation` (degrees). Lint rejects custom `tracking`,
  `blur`, `reveal` and `draw` keys under the animation rule. The ease is the one used to arrive at that key:
  `settle`, `glide`, `breathe`, `snap`, `exit`, `linear`.
- `allow_busy: true` on a layer silences the "too many moving properties" error. Say why in the
  storyboard.
- `rotation` (degrees) on any layer: a fixed tilt, for collage pieces and stickers.
- `torn: true` on a box layer gives it a torn paper edge, on the side away from `dir`, with a soft shadow
  (generated mode; a straight edge in Fusion). Keep a torn panel at least 18 px past any black it covers.
- `box: [x, y, w, h]` (px, top-left origin) on an `image` or `rect` layer keeps it inside that
  rectangle. An image is cover-fitted to the box, not the frame, and clipped to it (default centre:
  the box centre). A rect fills the box. A `paper` entrance slides the sheet in from the edge named by
  `dir` (`left` | `right` | `top` | `bottom`), and a `paper` exit slides it back.

### Split screen (`split`)

Half graphic, half footage. One spec-level line adds a panel under every other layer:

```json
"split": {"side": "top", "size": 0.5, "src": "Background.png",
          "in": {"treatment": "paper", "at": 0.0, "dur": 0.8}, "out": {"treatment": "paper", "at": 6.0}}
```

- `side`: `top` | `bottom` | `left` | `right`, the half the graphic takes. `size`: a fraction of
  the frame (≤ 1) or px (`720` matches a 720 px black band left by the edit).
- `src`: a series background (cover-fitted to the panel; `zoom`, `x`, `y` to adjust the crop), or
  `color`: a kit role for a flat panel (`ground`, `surface`).
- `in`/`out`: usually `paper` from the frame edge or `cut` with the edit. Panels may also `fade` or
  `settle`. `"torn": false` gives a straight edge.
- Set the type on the panel with ordinary layers (ink/accent on paper; lint treats the panel as the
  ground and does not count it as one of the four layers).
- **The footage half must be framed for it.** The graphic track cannot move the sermon clip. Use a
  split where the speaker already sits in the other half (a wide shot, or a shot the editor framed
  low, which leaves a black band), or ask the editor to reposition V1 for that stretch. Note which in
  the storyboard (`"split": "top 50%: needs V1 tilted down 760 px"`). In Resolve, Claude may set the
  V1 clip's Tilt on a duplicated timeline only when the user asks.

## Kit (`Sermon Series/<Series Name>/kit.json`)

```json
{
 "series": "Rooted", "personality": "one sentence",
 "palette": {"ground": {"hex": "#ECE9E2", "share": 70, "from": "Colors.jpg #ECE9E2 (28%)"}, "ink": {...},
             "light": {...}, "accent": {...}},
 "type": {"display": {"family": "Caladea", "style": "Regular", "weight": 400,
                      "file": "fonts/Caladea-Regular.ttf", "avg_char": 0.5, "use": "titles"},
          "text": {...}, "subtitle": {...}},
 "scale": {"title": 84, "phrase": 64, "label": 30, "subtitle": 46},
 "motion": {"tempo": 1.15, "distance": 18, "ease_in": "settle", "ease_out": "exit", "notes": "..."},
 "layout": {"safe": 0.07, "zones": ["lower-left", "right-third"]},
 "subtitles": {"font": "subtitle", "size": 46, "color": "#FAF9F6", "y": 940, "shadow": true,
               "shadow_color": "#000000@35", "shadow_blur": 6, "max_words": 3, "max_chars": 24,
               "punctuation": "drop-trailing", "case": "as-spoken"},
 "textures": [{"id": "background", "file": "Background.jpg", "w": 2400, "h": 2400, "use": "full-frame cards"}],
 "assets": [{"id": "title-card", "file": "Assets/Title Card.png", "kind": "title", "brand": true, "use": "..."}],
 "color_analysis": {"image": "Colors.jpg", "swatches": [...], "picked": {"#ECE9E2": "ground", "#DEDBD2": "not used: too close to ground"}},
 "sources": {"backgrounds": [...], "colors": "Colors.jpg", "example": "Example.png", "fonts": [...], "assets": [...]},
 "available_fonts": [{"file": "...", "family": "...", "style": "...", "avg_char": 0.41}],
 "draft": true,
 "signature_moves": ["..."], "avoid": ["..."]
}
```

File paths in the kit are relative to the series folder. `"draft": true` until the mood board is
approved; the mood board shows a draft banner while it is set.

## Storyboard (`motion/storyboard.json`)

```json
{
 "project": "2026-11-08 Rooted · Week 1", "series": "Rooted", "date": "2026-11-08",
 "duration": 1980, "message": "the one thing", "arc": "man-in-hole: …", "density": "light",
 "subtitles": {"on": true},
 "intro": {"id": "intro", "in": 2.0, "out": 7.5, "kind": "title", "shows": "exact text",
           "treatment_in": "track-in", "zone": "upper-left", "idea": "where it came from",
           "purpose": "why", "thumb": "review/thumbs/0002.00.jpg"},
 "outro": {"...": "same fields"},
 "beats": [
  {"id": "03", "in": 74.2, "out": 80.2, "kind": "title", "line": "spoken line",
   "shows": "exact text on screen", "purpose": "why it earns a graphic",
   "treatment_in": "rise-mask", "treatment_out": "sink", "zone": "lower-left",
   "notes": "optional", "thumb": "review/thumbs/0074.20.jpg", "brand": false,
   "background": "background (full-frame beats: which series background)"},
  {"id": "01", "in": 41.0, "out": 46.0, "kind": "nothing", "line": "...", "purpose": "why it stays on the speaker"}
 ]
}
```

## Mood board (`motion/moodboard.json`)

```json
{
 "project": "...", "series": "...", "direction": "the personality sentence",
 "specimen_text": "a phrase from this sermon",
 "sources": [{"image": "inputs/extra-reference.jpg", "caption": "optional: anything beyond the series folder"}],
 "motion": [{"video": "review/motion/03.mp4", "caption": "what to look at"}],
 "stills": [{"image": "review/stills/07_1.80.png", "caption": "..."}],
 "treatments": [{"name": "rise-mask", "use": "titles and verses"}],
 "signature_moves": ["optional; defaults to the kit's"], "avoid": ["optional"]
}
```

For a new series with two directions, make two mood board files (A and B), or one with both
directions' media captioned "A · …" / "B · …".

## Build plan (`motion/plan.json`)

```json
{
 "project": "...", "fps": 24, "width": 1920, "height": 1080, "kit": "/path/to/Sermon Series/Rooted/kit.json",
 "mode": "generated", "bin": "2026-11-08 Week 1", "tracks": {"graphics": 3, "subtitles": 4}, "timeline_offset": 0,
 "graphics": [{"id": "03-rooted-title", "spec": "specs/03-rooted-title.json", "in": 74.2,
               "render": "out/03-rooted-title_1m14s20.mov"}],
 "subtitles": "work/subtitles.json"
}
```

`mode`: `generated` (default; every graphic needs its `render`) or `fusion`. `bin`: the name of this package's bin
under Motion Graphics (defaults to the project). `fps` may be a fraction string (`"24000/1001"`). Use the timeline's frame rate.
