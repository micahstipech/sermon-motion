# Style intake: series folder → style kit

The user drops a series folder into `Sermon Series/` (Background, Colors, fonts, Example.png,
Assets/; see [series-folder.md](series-folder.md)) and says "make the graphics relate to the sermon".
This is how you turn that into a kit (`Sermon Series/<name>/kit.json`) quickly, without inventing a
look. Scan and draft first (`mg.py series "<name>" --draft`), then make the decisions below.

The kit is the *only* thing that changes between series. Gates, restraint, treatment meanings and
checks stay the same.

## 1. Look before you decide

Open **Example.png** at full size first, then the backgrounds and assets. Write one line each:

- **What the art is made of**: photograph, flat illustration, paper and print, paint, type-only,
  texture. Material decides the motion more than colour does: paper suggests things being set or
  laid down, paint suggests things spreading, photography suggests light changing.
- **Its value structure**: mostly light, mostly dark, or mixed. Where the eye goes first.
- **Its type**: the series title lettering (case, weight, spacing, serif or sans, any ligature or
  custom mark). The graphics should feel like they were set by whoever set the title.
- **Its one gesture**: a line, an arc, a crop, a texture, a grid. This can become a signature move.
- **The sermon's central image** (from the transcript): where it meets the art's gesture is the
  motif for this video.

## 2. Colour: find, then build a system

The series scan has already analysed the **Colors photo** (`_stipech/palette.json`, and the swatch
strip `_stipech/colors-swatch.png`). For any other image:
`python3 $SKILL/engine/mg.py palette <image>`.

The tool reports clusters (share, Lab lightness, chroma, hue), suggests roles leaning light, and
flags house looks. It is a starting point; you decide, and you record every swatch's fate in
`color_analysis.picked`.

**Where colours come from, in order** (write the source on every role, `from:`):
1. The Colors photo (the tool's sampled hexes), cross-checked against the backgrounds.
2. Brand values in `house/brand/` (logo files, brand guide).
3. The footage itself (sample a still): when graphics sit over footage, the palette must sit
   inside it.
4. Invention, last, labelled "invented: …".

**Roles** (each with one job):

| Role | Job | Share of a full-frame graphic |
|---|---|---|
| ground | full-frame cards, the world | most |
| surface | panels one step off the ground | ~15 % |
| ink | type and rules on light grounds | small |
| light | type over footage (near-white, neutral) | small |
| accent | one meaning only (the reference, the number, the turn) | ≤ 5 % |
| extra hue from the art (e.g. sage) | a second family, used rarely | ≤ 10 % |

**Rules:**
- **Value first.** Desaturate a still: the hierarchy must still read.
- **Keep it light.** Grounds come from the art's lightest large area. If the art is dark, ask
  whether full-frame graphics should be dark or use a light area of the art. Never default to
  black.
- **Type is neutral.** Near-white over footage, near-black on light grounds, with at most a whisper
  of the ground's hue (the tool's derived ink does this). No cream or bone type.
- **The accent is scarce.** If an accent is in every graphic, it marks nothing. Darken or lighten
  it until it holds 3:1 against its ground for large text, 4.5:1 for small.
- **Over footage, most graphics need no colour at all.** Near-white type, a rule and the footage
  carry it. Colour appears in full-frame moments and small marks.

## 3. Type

- **The given font** is `display` when it is a display or serif face, or `text` when it is a plain
  sans. Read its family and style names exactly as the OS shows them, because Fusion matches on these.
- **No usable or legible fonts → Roboto Condensed** from Google Fonts, for all roles or only the
  roles the series font can't carry ([series-folder.md](series-folder.md) §5b,
  `mg.py font-fallback`).
- **At most two families.** Pair only if needed: a serif display with a quiet sans for references
  and subtitles, or a sans display with the same sans at another weight. Choose the partner by
  structure (x-height, stroke contrast), not by trend. Never pair two display faces.
- **Subtitles** use the most legible face in the kit at a medium weight, usually the text sans,
  never the display face unless it is a plain sans.
- **Roles in the kit**: `display`, optionally `italic`, `text`, `subtitle`. Each has `family`,
  `style`, `weight`, `file` (relative to the kit) and `avg_char` (average glyph width in em; about
  0.5 for serifs, 0.56 for sans, 0.6+ for wide faces). `avg_char` sizes the reveal masks.
- **Scale** (px at 1080p): title 72–96, phrase 56–72, label 26–32 (letter-spaced if caps), subtitle
  42–50. Scale contrast does the work, not weight.
- **Fonts must be installable** (`.ttf`/`.otf`). They live in the series folder. The scan reads their
  exact family and style names and measures `avg_char`, so use its values.

## 4. Motion personality

Score the series on these sliders from the art and the sermon (−2 … +2), and write one sentence:

| Slider | −2 | +2 | Moves |
|---|---|---|---|
| still ↔ lively | lament, Good Friday | Easter, launch, kids | `tempo` (1.3 → 0.85), how many graphics |
| precise ↔ organic | Swiss, editorial | hand-made, painted | eases (`settle`/`snap` → `breathe`), rules vs soft shapes |
| reverent ↔ conversational | liturgy, scripture-led | topical series, Q&A | serif vs sans, centred vs left |
| traditional ↔ contemporary | hymn, heritage | modern, urban | ornament vs none, tracking, case |
| sparse ↔ rich | quiet | layered | how many layers per graphic (1–3) |

Then set in the kit:
- `motion.tempo`: multiplies durations (1.0 = defaults; calm series 1.1–1.3).
- `motion.distance`: travel in px for rises and sinks (12–28; never more than ~3 % of frame height).
- `motion.ease_in` / `ease_out`: from the ease set (`settle`, `glide`, `breathe`, `snap`; exits
  `exit`).
- `motion.notes`: the sentence, plus which treatments lead for this series.

## 5. Signature moves (3–5)

Write the rules that make this series recognisably itself, stated so anyone could apply them.
Examples:

- "A hairline rule draws first; the words rise out of it."
- "One italic word inside a roman title carries the human beat."
- "References small, caps, +14 % tracking, always under the verse, never larger."
- "Graphics live in the left third; the speaker keeps the right."

One of them should come from the art's gesture, and one per video from the sermon's central image
(SKILL.md §2).

## 6. Avoid list

3–5 things this series must not do, drawn from the art (for example: "no colour fields: the art is
mostly paper", "no centred text: the art is asymmetric").

## 7. Two directions (new series only)

The two directions differ in **language** (which treatments lead, where graphics live, type role
emphasis), not in invented colour. For example, A "set in type" (rules, rise-mask, left third) and
B "spoken" (single words, track-in, centred over the empty side). Each gets one key frame and one
motion sample on the mood board, plus a one-line rationale. Recommend one.

## kit.json

See [spec-format.md](spec-format.md) §kit and `examples/Sermon Series/Rooted/kit.json`.
