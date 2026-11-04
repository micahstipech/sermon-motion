# Restraint: density, timing, legibility, self-review

The graphics draw attention lightly. A viewer should notice the words, not the animation.

## Density

| Setting | Graphics per 30 min | Use |
|---|---|---|
| light (default) | 5–9 | most sermons |
| medium | 10–15 | teaching series, many references |
| heavy | 16–25 | short clips, social cut-downs |

- Leave at least ~40 s between graphics, except a run of list items or verse cards on one reading.
- No graphic in the first 10 s of the preacher speaking unless it is the intro.
- At most one graphic on screen at a time (subtitles excepted).

## Timing

- **Lead**: start the entrance 0.2–0.3 s before the word, so the graphic is *settled* when the
  word is spoken.
- **Entrance**: 0.5–1.1 s × tempo. Never under 0.25 s for a move (a jolt).
- **Hold**: fully readable for max(1.2 s, 0.3 s × words + 0.6 s); verses longer, about the time
  it takes to read them aloud.
- **Exit**: 0.25–0.45 s, quicker than the entrance. End on a pause or the end of the thought, not
  mid-sentence.
- **Total**: most graphics are 3–7 s. Over 10 s means it is either a verse card or too long.

## Over-animation (lint enforces most of these)

- Max **two** properties change on entrance, one of which is opacity (rise = opacity + y; track-in =
  opacity + spacing).
- No bounce, elastic or overshoot eases. No loops, no constant drift, no wiggle.
- No particles, glows, lens flares, light leaks, shine sweeps, 3D spins, glitch.
- No per-letter cascades on more than one graphic per video.
- No camera moves on text. Text is set, not flown.
- Max four layers visible at once in a graphic (text + rule + label + brand).

## Legibility

- Text ≥ 28 px at 1080p (labels ≥ 22 px, marked `small`).
- Check every graphic over the **brightest** footage frame behind it. If type fails there, add the
  kit's soft shadow (not an outline or a box), move it, or use a full-frame card.
- Keep out of the subtitle band; keep 0.5 face-widths from the face.
- One line for phrases; two at most. Break lines by meaning, not width.
- Words on screen match what is said (spoken form, the preacher's wording). Scripture follows the
  translation the preacher reads from; ask if unknown.

## Self-review (before showing anything)

Watch the stills sheets and the motion sample, then write the three notes a demanding director would
give. Diagnose by layer before fixing:

1. **Looks cheap** → type, spacing, alignment, edges, colour values. Not more motion.
2. **Looks busy** → too many layers, too much travel, too many graphics close together. Remove.
3. **Unclear** → wrong words chosen, held too briefly, competing with the face or subtitles.
4. **Looks like a template** → same zone or treatment as last time, generic phrasing, a "lower third
   bar". Check the ledger, change the idea.

Fix, re-render stills, look again. Then show the user.
