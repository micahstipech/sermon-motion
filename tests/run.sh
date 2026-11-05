#!/usr/bin/env bash
# End-to-end check of the engine on the example series. Run from anywhere: bash tests/run.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SK="$ROOT/skills/motion-designer"; EX="$SK/examples"; PY="${PYTHON:-python3}"; MG="$PY $SK/engine/mg.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$EX"
K="Sermon Series/Rooted/kit.json"
echo "== series folder"; $MG series "Sermon Series/Rooted"
echo "== lint";        $MG lint 'specs/*.json' --kit "$K"
echo "== build";       for s in specs/*.json; do $MG build "$s" --kit "$K" --out build >/dev/null; done; ls build
if $PY -c "import lupa" 2>/dev/null; then echo "== lua parse"; $PY "$ROOT/tests/check_lua.py" build/*.comp build/*.setting "$SK/engine/resolve/carrier.setting"; else echo "(skip lua parse: pip install lupa)"; fi
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
$PY - "$TMP" <<'PY'
import json, sys
p = json.load(open("plan.json")); p["subtitles"] = sys.argv[1] + "/subtitles.json"
for g in p["graphics"]: g.pop("render", None)
p["mode"] = "fusion"
json.dump(p, open(sys.argv[1] + "/plan.json", "w"))
p["mode"] = "generated"
for g in p["graphics"]: g["render"] = g["id"] + ".mov"; open(sys.argv[1] + "/" + g["render"], "wb").write(b"fake")
json.dump(p, open(sys.argv[1] + "/plan-gen.json", "w"))
PY
cp -r "Sermon Series" specs "$TMP/"
echo "-- fusion mode"; $MG package "$TMP/plan.json" "$TMP/pkg"; $PY "$ROOT/tests/mock_resolve.py" "$TMP/pkg"
echo "-- generated mode"; $MG package "$TMP/plan-gen.json" "$TMP/pkg-gen"; $PY "$ROOT/tests/mock_resolve.py" "$TMP/pkg-gen"
echo "== the animation rule rejects a pop"
cat > "$TMP/pop.json" <<'JSON'
{"id":"pop","kind":"title","duration":3,"layers":[{"id":"t","type":"text","text":"Pop","font":"display","size":84,"x":200,"y":300,"in":{"treatment":"track-in","at":0.2}}]}
JSON
if $MG lint "$TMP/pop.json" --kit "$K" >/dev/null 2>&1; then echo "FAILED: lint allowed a banned move"; exit 1; else echo "rejected"; fi
echo "== safe zones: text too close to the edge is rejected, in both formats"
cat > "$TMP/h.json" <<'JSON'
{"id":"h","kind":"title","duration":3,"layers":[{"id":"t","type":"text","text":"Edge","font":"text","size":60,"x":100,"y":500,"in":{"treatment":"fade","at":0.2}}]}
JSON
cat > "$TMP/v.json" <<'JSON'
{"id":"v","kind":"title","duration":3,"width":1080,"height":1920,"layers":[{"id":"t","type":"text","text":"Edge","font":"text","size":60,"x":100,"y":600,"in":{"treatment":"fade","at":0.2}}]}
JSON
cat > "$TMP/ok.json" <<'JSON'
{"id":"ok","kind":"title","duration":3,"width":1080,"height":1920,"layers":[{"id":"t","type":"text","text":"Inside","font":"text","size":60,"x":540,"y":600,"align":"center","in":{"treatment":"fade","at":0.2}}]}
JSON
for f in h v; do if $MG lint "$TMP/$f.json" --kit "$K" >/dev/null 2>&1; then echo "FAILED: $f"; exit 1; fi; done
$MG lint "$TMP/ok.json" --kit "$K" >/dev/null; echo "rejected both, allowed the safe one"
echo "ALL OK"
