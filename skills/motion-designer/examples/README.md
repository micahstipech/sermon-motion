# Example: "Rooted" (placeholder series)

A worked example that exercises the whole engine. The art is a generated placeholder, not a real
church's artwork; the words are a short synthetic excerpt with made-up timings.

- `kit/`: style kit (palette from `art.jpg` with sources, Caladea + Inter, motion personality, subtitle style)
- `specs/`: three graphics (title with rule and reference, keyword, chapter turn)
- `storyboard.json`, `moodboard.json`, `plan.json`: gate pages and the build plan
- `words.json` → `subtitles.json` / `.srt`: chunker input and output

Run `bash tests/run.sh` from the repo root. Generated files (`build/`, `out/`, `review/`) are git-ignored.
