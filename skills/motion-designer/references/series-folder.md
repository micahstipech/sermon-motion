# The series folder: how a new sermon series arrives

Every series comes in the same shape, so a new look can be picked up in minutes.

```
Sermon Series/
  <Series Name>/
    Background.jpg|png        large square texture, used as the background
    Background 2.jpg …        optional extra backgrounds (any name starting "Background",
                              or a Backgrounds/ subfolder)
    Colors.jpg|png            a photo whose colours the series uses
    <font files>.ttf|.otf     the series fonts (any names; a Fonts/ subfolder is fine)
    Example.png               everything used together: the reference for how it all combines
    Assets/                   transparent PNGs: icons, logos, title cards, other art elements
    kit.json                  ← written by the skill: the series style kit
    _stipech/                 ← written by the skill: inventory, colour analysis, swatches
```

Location: `series_root` in `~/.stipech-motion/config.json`. Default: `<house>/Sermon Series`, so it
syncs through the repo. If the church keeps series art in a shared drive, point `series_root` there
instead.

Names are matched case-insensitively. "Colours" works, and so does "background - paper.png".

## 1. Scan

```bash
python3 $SKILL/engine/mg.py series "<Series Name>"        # or a full path to the folder
python3 $SKILL/engine/mg.py series --list                  # every series and its kit status
```

The scan:
- Sorts files into backgrounds, Colors, Example, fonts and assets.
- Reads each font's real family and style names (what Fusion needs) and measures its average glyph
  width.
- Checks backgrounds are square and large (≥ 2160 px).
- Checks every asset is a PNG with real transparency.
- Analyses the Colors photo and each background.

Results go to `_stipech/` in the series folder. The command exits with code 2 when something is
missing.

## 2. Ask for what's missing (one message)

When the scan reports MISSING or CHECK lines, ask for all of them in **one** message, worded from
the scan output, with what you'll do in the meantime:

| Missing | Ask | Meanwhile |
|---|---|---|
| Background | "Is there a large square background texture for this series? Name it Background." | use the kit ground colour flat; no full-frame texture |
| Colors | "Is there a Colors photo for the palette?" | sample Example.png and the background, label colours "from Example.png" |
| Fonts | "Can I get the series font files (.ttf/.otf)?" | Roboto Condensed from Google Fonts (below) |
| Only .woff/.woff2, or a file that won't open | "Resolve needs working .ttf/.otf versions of these fonts." | Roboto Condensed from Google Fonts |
| Assets folder | "Are there transparent PNGs from the art (icons, logos, title card)? They go in Assets/." | type-only graphics |
| Asset without transparency | "Is there a transparent PNG of <name>?" | don't use it over footage |
| Example | "Is there an Example.png showing everything together?" | read the art yourself; say the signature moves are guesses |
| Non-square / small background | mention it; usually fine | cover-crop |

Never invent a missing asset (no redrawn logos, no generated icons). Brand and series art are the
church's files only.

## 3. Read Example.png first

Before choosing a single value, study Example.png the way you would study a designer's layout:

- **Composition**: where the title sits, how much empty space there is, left- or centre-weighted, what is
  cropped.
- **Scale relationships**: title to subtitle, icon to title, how large the texture's grain reads.
- **Type treatment**: case, tracking, weight, line breaks, rules or ornaments, how the fonts pair.
- **Which assets appear together, and which never do.**
- **Colour use**: which Colors swatches actually appear, and in what proportions.

This is where 3–5 **signature moves** come from. They are rules like "title left-aligned over a
hairline rule; icon small, bottom right" ([style-intake.md](style-intake.md) §5).

## 4. Pick the colours

The Colors photo is the source. The scan lists its swatches (share, lightness, chroma, hue) and
suggests roles, leaning light. You decide:

- Map swatches to roles (ground, surface, ink, accent, extra hue) by **value first**, then meaning.
- Record the decision for every swatch in `kit.color_analysis.picked`, including the ones you are
  not using and why ("not used: too close to ground"). The mood board shows this, so the user sees
  what was picked.
- Cross-check with the backgrounds' swatches: the ground should sit on or near the main background.
- Apply [anti-patterns.md](anti-patterns.md): light by default, neutral type, scarce accent.

## 5. Draft, then finish the kit

```bash
python3 $SKILL/engine/mg.py series "<Series Name>" --draft      # writes kit.json with "draft": true
```

The draft fills in sources, textures, assets, available fonts, suggested palette roles and default
motion and subtitle settings. Finish it ([style-intake.md](style-intake.md)):
- choose the palette from the Colors photo and record `picked`;
- assign type roles from `available_fonts`;
- give every background and asset a `use` line (and `"brand": true` for logos and the series title card);
- set the motion personality, signature moves and avoid list.

Leave `"draft": true` until the mood board is approved, then remove it.

## 5b. Fallback font: Roboto Condensed

When the series has **no usable fonts**, use **Roboto Condensed**, loaded from Google Fonts. Usable
means installable (.ttf/.otf), readable, and legible:

- No font files, only web fonts, or files that won't open → Roboto Condensed for every role.
  `series --draft` does this automatically.
- The series font is legible for titles but not at label or subtitle sizes (script, grunge, heavy
  ornament, ultra-thin) → keep it for `display`, and use Roboto Condensed for `text` and `subtitle`:
  `mg.py font-fallback "<name>" --roles text,subtitle`.
- The series font is not legible even as a title → `mg.py font-fallback "<name>"` (all roles).

Judge legibility at real size: set a 5–7 word line at 46 px (subtitle) and 26 px (label) over a
footage frame. If you have to work to read it, it fails that role.

The command downloads TrueType files (Regular, Medium, Bold, Italic) from Google Fonts, caches them
in `~/.stipech-motion/fonts/`, copies them into the series folder's `Fonts/` so the package carries
them to the PC, and updates `kit.json`. The roles it writes are Bold for display, Medium for text and
subtitles, and Italic for italic, each marked `"fallback": true`. Still ask the user for the real
fonts; the fallback keeps work moving until they arrive. With no network, tell the user to install
Roboto Condensed from fonts.google.com and drop the .ttf files into the series folder.

## 6. Using the series files in graphics

- **Backgrounds** are image layers with `"fit": "cover"`, used for full-frame cards (verse cards,
  section breaks, intro or outro moments) and never as a box behind text over footage. With several
  backgrounds, give each a job in the kit (`use`), and record which one each beat uses
  (`"background"` on storyboard beats) so the ledger can spot overuse.
- **Assets** are image layers placed by centre and width (`"w"`). Use them at the scale and in the
  combinations Example.png shows. Logos and the series title card are brand assets (`"brand": true`):
  they may repeat across videos, but their placement and entrance still vary.
- **Fonts** must be installed on the editing PC for Fusion. The package ships the series folder,
  fonts included.
