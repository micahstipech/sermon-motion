# Subtitles

Clean, readable, and quiet. Two to three words at a time, no animation, on their own track (V4) as
Text+ clips, so the editor can trim timing and fix words in Resolve.

## Words

1. Best: word-level JSON from `mg.py transcribe` (faster-whisper with `word_timestamps`) or from
   the editor's tools. Prompt the transcriber with names, the church, and the books cited.
2. OK: an SRT/VTT from Resolve or YouTube. Word times are estimated within each cue (±0.2 s).
3. Proofread the words against sermon notes: names, scripture references, capitalisation of divine
   names and pronouns as the church's style has it (ask once; record it in `house/rules.md`).

## Chunking (`mg.py chunk`)

- 2–3 words per subtitle, max ~24 characters. One word only when it stands alone in speech (a pause
  or a full stop either side) and cannot join a neighbour.
- Break at sentence ends and at pauses ≥ 0.35 s. Break after commas when the chunk already has two
  words.
- Never end a chunk on a weak word ("the", "of", "and", "my", "is", …) if the next chunk can take it.
- Timing: start at the first word, end 0.2 s after the last word or at the next chunk's start. No
  overlaps, and no gaps under 0.12 s (no flicker). Minimum 0.4 s on screen.
- Trailing commas and full stops are dropped; ? and ! are kept.
- Kit options: `max_words`, `max_chars`, `punctuation` (`drop-trailing` | `keep` | `none`), `case`
  (`as-spoken` | `lower` | `upper`).

## Style (kit `subtitles`)

- Font: the kit's `subtitle` role, a legible sans at medium weight. Size 42–50 px at 1080p.
- Colour: near-white (`#FAF9F6`-ish), neutral. A soft shadow (black at 30–40 %, blur 5–8 px), no
  outline, no box, no word highlight, no pop.
- Position: centred, baseline about 86–88 % down the frame (`y` ≈ 930–950 at 1080p). Graphics stay
  out of this band (lint).
- Same style all video. Subtitles are not where the style shows off.

## In Resolve

Each subtitle is an "SM Carrier" title with a generated Fusion comp (Text+ with the chunk's text,
plus a shadow Text+). To fix timing, trim the clip on V4. To fix a word, open the clip in Fusion
(or the Inspector) and edit the Text+ text. An `.srt` is also exported next to `subtitles.json` as a
backup (Resolve can import it to a subtitle track).
