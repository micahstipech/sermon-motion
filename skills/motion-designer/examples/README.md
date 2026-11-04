# Example: "Rooted" (placeholder series)

A worked example that exercises the whole engine. The art is a generated placeholder, not a real
church's artwork; the words are a short synthetic excerpt with made-up timings.

- `Sermon Series/Rooted/`: a series folder in the standard shape (Background.jpg, Background 2.jpg,
  Colors.jpg, Caladea + Inter fonts, Example.png, Assets/ with a title card, icon and logo) and its
  finished `kit.json`
- `specs/`: four graphics (title with rule and reference, keyword, chapter turn, verse card on the
  series background)
- `storyboard.json`, `moodboard.json`, `plan.json`: gate pages and the build plan
- `words.json` → `subtitles.json` / `.srt`: chunker input and output

Run `bash tests/run.sh` from the repo root. Generated files (`build/`, `out/`, `review/`) are git-ignored.
