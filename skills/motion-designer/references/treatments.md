# Treatments, graphic kinds and arcs

Every move says something. Pick it for what it says, then let the ledger stop it from becoming a
habit. Vocabulary adapted from huashu-motion's techniques library (MIT), narrowed for restraint.

## Entrances (`in.treatment`)

The standing rule: a collage, a paper effect, a light movement with an opacity shift, or no animation.
`mg.py lint` rejects anything else, including pop, bounce, confetti, slams, shakes and per-letter effects.

| Treatment | Says | Default (× tempo) | Good for |
|---|---|---|---|
| `cut` | plain, confident; trusts the words | 1 frame | panels that cut with the picture, labels, references, list items |
| `fade` | quiet arrival; nothing to notice but the content | 0.5 s | supporting lines, second layers, strike-through lines |
| `rise` | a light lift into place with an opacity shift | 0.7 s, `distance` px | phrases, titles, quotes |
| `settle` | presence without movement; a 3–4 % scale settle | 0.8 s | full-frame cards, logos, images |
| `collage` | a piece laid down: slightly large and turned, settling flat | 0.6 s | collage tiles, stickers, assembling the art piece by piece |
| `paper` | a sheet slides in from its edge | 0.6 s | `box` panels and `split` sheets (edge wipe in Fusion) |

## Exits (`out.treatment`)

Exits are faster than entrances (0.2–0.45 s). The thought is finished; do not perform it again.

| Treatment | Says |
|---|---|
| `cut` | leaves with the edit (the default when a graphic ends on a picture cut) |
| `fade` | quiet exit |
| `sink` | drops slightly while fading: the thought is complete |
| `paper` | a sheet slides back to its edge |

## Choreography inside one graphic

- **Order**: structure first (rule), then the main words, then the small label. 0.3–0.6 s between.
- **One mover**: only one element travels. Others fade or cut.
- **Exit together**, or in reverse order 0.1 s apart, never one by one slowly.

## Graphic kinds (sermon vocabulary)

| Kind | When | Typical build |
|---|---|---|
| `title` | the sermon's question or big idea, said once | display phrase + small reference |
| `scripture` | the main text read aloud | verse in display (≤ 18 words per card; split longer verses across cards on the reading's phrasing) + reference in text caps |
| `reference` | a passage named but not read | reference alone, small, in a corner zone |
| `keyword` | the word the sermon keeps returning to | one word or 2–4 word phrase, `rise` |
| `quote` | a line people will repeat (preacher or cited author) | display italic/roman, attribution small |
| `chapter` | the turn into a new main point | number (cut) + heading (rise) |
| `list` / `outline` | main points recapped | items arrive on their spoken words, `cut` after the first |
| `name` (lower third) | a guest, a testimony, a location | name in text, role small; no bar, no box unless the kit has one |
| `number` | a count or date that matters | number in display, label small; only real numbers |
| `full-frame` | a breath between sections, a verse card | kit ground + type; use 0–2 per video |
| `split` | the words need room but the face should stay: a verse read aloud, a list, a quote | series background panel on one side (`split`, [spec-format.md](spec-format.md)), type on it, footage on the other side; the speaker must already sit in that half |
| `intro` / `outro` | the opening and closing seconds | designed per sermon ([variation.md](variation.md)) |
| `nothing` | personal story, emotion, humour, prayer, the altar call | the speaker's face carries it |

Never package prayer, invitations to respond, or moments of confession and testimony unless the
user asks.

## Zones (1920 × 1080; keep within the kit's safe area)

`lower-left`, `upper-left`, `center`, `right-third`, `left-third`, `upper-right`, `full-frame`,
and for split screens `split-top`, `split-bottom`, `split-left`, `split-right`. Text in any zone stays inside the
safe area ([restraint.md](restraint.md)).
Choose the zone from the footage: the empty side of the frame, away from the face, out of the
subtitle band. Vary zones across the video where the footage allows.

## Arcs (story shapes)

Use these to read the sermon and space the graphics. Adapted from vox's beat library (MIT).

| Arc | Sermon shape | Where graphics tend to go |
|---|---|---|
| hook → payoff | question, tension, answer | the question; the answer |
| man-in-hole | life as it is → fall → help → rising | the low point named; the turn; the hope |
| text-led (expository) | verse by verse | each verse read; each observation as a chapter |
| points | intro → 1, 2, 3 → close | each point; an outline recap |
| before → after | old way → new way | the contrast line; the new way |
| story → meaning | long narrative → application | after the story: the meaning |
| timeline | history, journey | dates, places (real ones) |

Density follows the arc: graphics cluster at turns, not evenly across time.
