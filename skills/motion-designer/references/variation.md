# Variation: never the same video twice

Repetition is how motion graphics start to look automated. The ledger (`house/ledger.json`) records,
for every video, its intro, outro and each graphic's kind, entrance, exit and zone.
`mg.py ledger check` compares a storyboard with the last 8 videos.

- **Errors** (fix before showing the storyboard): an intro or outro identical to any of the last 8
  videos (same kind + entrance + zone); intro and outro identical to each other.
- **Warnings** (decide, and say why in the storyboard notes): the same entrance as last week's
  intro/outro; a kind/entrance/zone combination used twice or more last week and used again; one
  entrance making up more than half of a video's text entrances.
- **Exempt**: beats marked `"brand": true` (logo files, the church lockup, a fixed announcement
  slate the church uses on purpose).

Record a video only after the user approves the result: `mg.py ledger add motion/storyboard.json`.

## Designing a new intro

The intro is the first 3–8 s of graphics. It comes from **this sermon**, never from a template. Pick
one source, and make it a different source from last week's:

- the **first sentence** the preacher says (set as type as it is spoken);
- the **series title** set fresh: different zone, treatment and type role from last time;
- the **main text's reference**, small, as the preacher opens the Bible;
- the **sermon's central image** as the signature move (a rule drawing down for "roots");
- **nothing**: let the first minute breathe and bring the series name in at the first turn.

Then vary at least two axes against the previous video: zone, entrance, type role
(display / italic / text caps), element (rule, word, reference), timing (at 0 s vs at the first
pause).

## Designing a new outro

Come down to one idea, held. Sources:
- the **closing line** or the verse the preacher ends on;
- the **sermon's question**, now answered (reuse its words, not its animation);
- the **series name** with next week's title, only if the user provides it;
- the **brand lockup** (the brand asset), placed fresh;
- **nothing**: the last frame is the speaker.

No bumpers, no "subscribe" cards unless the user asks, no logo sting unless it is the church's own
asset.

## Within one video

- Rotate entrances by meaning: the same *kind* may share a treatment (all chapter turns wipe). That
  is a system, not repetition. Across kinds, vary.
- Vary zones as the footage allows.
- The sermon's motif appears 2–3 times, not on every graphic.
