#!/usr/bin/env bash
# End-to-end check of the engine on the example series. Run from anywhere: bash tests/run.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SK="$ROOT/skills/motion-designer"; EX="$SK/examples"; MG="python3 $SK/engine/mg.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$EX"
K="Sermon Series/Rooted/kit.json"
echo "== series folder"; $MG series "Sermon Series/Rooted"
echo "== lint";        $MG lint 'specs/*.json' --kit "$K"
echo "== build";       for s in specs/*.json; do $MG build "$s" --kit "$K" --out build >/dev/null; done; ls build
if python3 -c "import lupa" 2>/dev/null; then echo "== lua parse"; python3 "$ROOT/tests/check_lua.py" build/*.comp build/*.setting "$SK/engine/resolve/carrier.setting"; else echo "(skip lua parse: pip install lupa)"; fi
echo "== subtitles";   $MG chunk words.json --kit "$K" --out "$TMP/subtitles.json"
echo "== palette";     $MG palette "Sermon Series/Rooted/Colors.jpg" | tail -2
echo "== ledger";      $MG ledger check storyboard.json --house "$TMP/house"
echo "== review";      $MG storyboard storyboard.json --out "$TMP/review/storyboard.html" --house "$TMP/house" >/dev/null
                       $MG moodboard moodboard.json --kit "$K" --out "$TMP/review/moodboard.html" >/dev/null; echo ok
if node -e "require('playwright')" 2>/dev/null; then
  echo "== stills + alpha render"
  node "$SK/engine/stills.js" build/03-rooted-title.html "$TMP/stills" 1.0 3.0 --over '#6E6B66' >/dev/null
  mkdir -p out; node "$SK/engine/render.js" build/07-stream.html "$TMP/07.mov" --fps 24
  ffprobe -v error -select_streams v:0 -show_entries stream=pix_fmt -of csv=p=0 "$TMP/07.mov" | grep -q yuva && echo "alpha ok"
else echo "(skip render: playwright not installed)"; fi
echo "== package + mock placement"
python3 - "$TMP" <<'PY'
import json, sys
p = json.load(open("plan.json")); p["subtitles"] = sys.argv[1] + "/subtitles.json"
for g in p["graphics"]: g.pop("render", None)
json.dump(p, open(sys.argv[1] + "/plan.json", "w"))
PY
cp -r "Sermon Series" specs "$TMP/"; $MG package "$TMP/plan.json" "$TMP/pkg"
python3 "$ROOT/tests/mock_resolve.py" "$TMP/pkg"
echo "ALL OK"
