# Treatments, graphic kinds and arcs

Every move says something. Pick it for what it says, then let the ledger stop it from becoming a
habit. Vocabulary adapted from huashu-motion's techniques library (MIT), narrowed for restraint.

## Entrances (`in.treatment`)

| Treatment | Says | Default (× tempo) | Good for |
|---|---|---|---|
| `cut` | plain, confident; trusts the words | 1 frame | small labels, numbers, references, list items after the first |
| `fade` | quiet arrival; nothing to notice but the content | 0.5 s | supporting lines, second layers |
| `rise` | gentle emphasis; a small lift into place | 0.7 s, `distance` px | phrases, quotes |
| `rise-mask` | precise, editorial; rises out of an invisible line | 0.75 s | titles, verses, the sermon's question |
| `wipe` | read left to right, like a line being written | 0.9 s | chapter turns, outlines, lists |
| `track-in` | a word settling into meaning; letters gather | 1.1 s, from +0.18–0.25 em | single words, series names |
| `settle` | presence without movement; a 3–4 % scale settle | 0.8 s | full-frame cards, logos, images |
| `focus` | reflective, coming into focus | 0.8 s | **max one per video**, with a reason (generated-motion cliché as a default) |
| `draw` | structure, underlining; a rule or shape draws on | 0.7 s | rules, underlines, dividers |

## Exits (`out.treatment`)

Exits are faster than entrances (0.25–0.45 s). The thought is finished; do not perform it again.

| Treatment | Says |
|---|---|
| `cut` | leaves with the edit (default when the graphic ends on a picture cut) |
| `fade` | quiet exit (the default) |
| `sink` | drops slightly while fading: the thought is complete |
| `wipe` | wipes away in reading direction: on to the next point |
| `focus` | softens out: pairs only with a `focus` entrance |
| `undraw` | a rule retracts to its anchor |

Custom motion: put explicit `anim` keyframes on a layer (`{"dy": [[t, v, ease], ...]}`). Keep to
the same restraint budget (lint enforces it).

## Choreography inside one graphic

- **Order**: structure first (rule), then the main words, then the small label. 0.3–0.6 s between.
- **One mover**: only one element travels. Others fade or cut.
- **Exit together**, or in reverse order 0.1 s apart, never one by one slowly.

## Graphic kinds (sermon vocabulary)

| Kind | When | Typical build |
|---|---|---|
| `title` | the sermon's question or big idea, said once | display phrase + rule + small reference |
| `scripture` | the main text read aloud | verse in display (≤ 18 words per card; split longer verses across cards on the reading's phrasing) + reference in text caps |
| `reference` | a passage named but not read | reference alone, small, in a corner zone |
| `keyword` | the word the sermon keeps returning to | one word or 2–4 word phrase, `track-in` or `rise` |
| `quote` | a line people will repeat (preacher or cited author) | display italic/roman, attribution small |
| `chapter` | the turn into a new main point | number (cut) + heading (wipe or rise-mask) |
| `list` / `outline` | main points recapped | items arrive on their spoken words, `cut` after the first |
| `name` (lower third) | a guest, a testimony, a location | name in text, role small; no bar, no box unless the kit has one |
| `number` | a count or date that matters | number in display, label small; only real numbers |
| `full-frame` | a breath between sections, a verse card | kit ground + type; use 0–2 per video |
| `intro` / `outro` | the opening and closing seconds | designed per sermon ([variation.md](variation.md)) |
| `nothing` | personal story, emotion, humour, prayer, the altar call | the speaker's face carries it |

Never package prayer, invitations to respond, or moments of confession and testimony unless the
user asks.

## Zones (1920 × 1080; keep within the kit's safe area)

`lower-left`, `upper-left`, `center`, `right-third`, `left-third`, `upper-right`, `full-frame`.
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
