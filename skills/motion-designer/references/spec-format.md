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
  {"id": "rule", "type": "rect", "x": 160, "y": 648, "w": 360, "h": 2, "color": "light@70", "anchor": "left",
   "in": {"treatment": "draw", "at": 0.2}, "out": {"treatment": "fade", "at": 5.9}},
  {"id": "title", "type": "text", "text": "Nothing has roots", "font": "display", "size": 84,
   "color": "light", "x": 160, "y": 580, "align": "left",
   "in": {"treatment": "rise-mask", "at": 0.55}, "out": {"treatment": "sink", "at": 5.9}}
 ]
}
```

- `in` (spec level): timeline seconds where the graphic starts. `duration`: seconds. Layer times
  are clip-local.
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
  `reveal_out` (0–1 wipe), `draw` (0–1, rects). The ease is the one used to arrive at that key:
  `settle`, `glide`, `breathe`, `snap`, `exit`, `linear`.
- `allow_busy: true` on a layer silences the "too many moving properties" error. Say why in the
  storyboard.

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
 "tracks": {"graphics": 3, "subtitles": 4}, "timeline_offset": 0,
 "graphics": [{"id": "03-rooted-title", "spec": "specs/03-rooted-title.json", "in": 74.2,
               "render": "out/03-rooted-title_1m14s20.mov"}],
 "subtitles": "work/subtitles.json"
}
```

`fps` may be a fraction string (`"24000/1001"`). Use the timeline's frame rate.
