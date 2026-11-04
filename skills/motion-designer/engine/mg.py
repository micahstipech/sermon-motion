#!/usr/bin/env python3
"""Stipech Motion command line. Run `python3 mg.py <command> -h` for each command.

  doctor                         check python/node/ffmpeg/playwright/Pillow/whisper
  inspect VIDEO OUT              specs, contact sheet, video.json
  thumbs VIDEO OUT t1 t2 ...     stills from the source at given seconds (storyboard thumbnails)
  transcribe VIDEO --out W.json  word timestamps with faster-whisper (if installed)
  words SRC --out W.json         SRT/VTT/whisper JSON -> words.json
  chunk WORDS --kit K            2-3 word subtitles -> subtitles.json + .srt
  palette IMAGE                  colours found in the art, with roles and warnings
  build SPEC --kit K             spec -> .html / .comp / .setting
  lint SPEC... --kit K           restraint checks (one spec or a whole video)
  storyboard BOARD.json          storyboard approval page (+ variation check)
  moodboard MB.json --kit K      mood board approval page
  ledger check|add BOARD.json    variation ledger
  package PLAN.json OUT          folder for the editing PC (Resolve)
  series NAME|PATH [--draft]     scan a "Sermon Series/<name>" folder; analyse Colors; draft kit.json
  series --list                  list series folders and their kit status
  font-fallback SERIES [--roles] Roboto Condensed (Google Fonts) for roles the series fonts can't carry
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stipech import spec as S  # noqa: E402


def _kit(path):
    if not path:
        return None, None
    return S.load_json(path), S.kit_dir(path)


def cmd_doctor(a):
    ok = True
    for name, check in (("python3", [sys.executable, "--version"]), ("node", ["node", "--version"]),
                        ("ffmpeg", ["ffmpeg", "-version"]), ("ffprobe", ["ffprobe", "-version"])):
        try:
            out = subprocess.run(check, capture_output=True, text=True).stdout.split("\n")[0]
            print(f"ok   {name}: {out}")
        except FileNotFoundError:
            print(f"MISS {name}")
            ok = False
    r = subprocess.run(["node", "-e", "require('playwright');console.log('ok')"], capture_output=True, text=True,
                       env={**os.environ, "NODE_PATH": os.environ.get("NODE_PATH", "")})
    print(("ok   " if r.returncode == 0 else "MISS ") + "playwright (node). Install: npm i playwright && npx playwright install chromium")
    ok &= r.returncode == 0
    for mod, why in (("PIL", "Pillow: palette extraction"), ("faster_whisper", "faster-whisper: word timestamps (optional if you have an SRT)")):
        try:
            __import__(mod)
            print(f"ok   {why}")
        except ImportError:
            print(f"MISS {why}")
    enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    print(("ok   " if "prores_ks" in enc else "MISS ") + "ffmpeg prores_ks encoder (ProRes 4444 fallback renders)")
    sys.exit(0 if ok else 1)


def cmd_inspect(a):
    os.makedirs(a.out, exist_ok=True)
    p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", a.video],
                                  capture_output=True, text=True).stdout)
    vs = [s for s in p["streams"] if s["codec_type"] == "video"][0]
    W, H, fps = int(vs["width"]), int(vs["height"]), vs["r_frame_rate"]
    dur = float(p["format"]["duration"])
    hdr = vs.get("color_transfer") in ("arib-std-b67", "smpte2084")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.video, "-vf",
                    f"fps=1/{max(1, dur / 24):.2f},scale=480:-1,tile=6x4:padding=4:color=white", "-frames:v", "1",
                    os.path.join(a.out, "contact.png")], check=True)
    info = {"width": W, "height": H, "fps": fps, "duration": dur, "hdr": hdr,
            "pix_fmt": vs.get("pix_fmt"), "color_transfer": vs.get("color_transfer")}
    with open(os.path.join(a.out, "video.json"), "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps(info, indent=1))
    if hdr:
        print("WARNING: HDR source. Graphics are designed in SDR; check them over the graded timeline in Resolve.")


def cmd_thumbs(a):
    os.makedirs(a.out, exist_ok=True)
    for t in a.times:
        name = os.path.join(a.out, f"{float(t):08.2f}.jpg")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", a.video, "-frames:v", "1",
                        "-vf", f"scale={a.width}:-2", "-q:v", "3", name], check=True)
        print(name)


def cmd_transcribe(a):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper is not installed (pip install faster-whisper), or give an SRT/VTT to `words`.")
    model = WhisperModel(a.model, compute_type="int8")
    segs, _ = model.transcribe(a.video, word_timestamps=True, vad_filter=True,
                               initial_prompt=a.prompt or None)
    words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in (s.words or [])]
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(words, f, indent=0)
    print(f"{len(words)} words -> {a.out}. Proof names and scripture references against the sermon notes.")


def cmd_words(a):
    from stipech.subtitles import load_words
    words = load_words(a.src)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(words, f, indent=0)
    print(f"{len(words)} words -> {a.out}")


def cmd_chunk(a):
    from stipech.subtitles import load_words, chunk, srt
    kit, _ = _kit(a.kit)
    st = (kit or {}).get("subtitles", {})
    ch = chunk(load_words(a.words), max_words=st.get("max_words", 3), max_chars=st.get("max_chars", 24),
               punctuation=st.get("punctuation", "drop-trailing"), case=st.get("case", "as-spoken"))
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(ch, f, indent=0)
    with open(os.path.splitext(a.out)[0] + ".srt", "w", encoding="utf-8") as f:
        f.write(srt(ch))
    sizes = [c["words"] for c in ch]
    print(f"{len(ch)} subtitles -> {a.out} (+ .srt). words/chunk: "
          + ", ".join(f"{n}:{sizes.count(n)}" for n in sorted(set(sizes))))


def cmd_palette(a):
    from stipech import palette
    rep = palette.report(a.image, a.k)
    if a.swatch:
        palette.swatch_png(rep["swatches"], a.swatch)
    if a.out:
        with open(a.out, "w") as f:
            json.dump(rep, f, indent=1)
    print(f"{'hex':8} {'share':>6} {'L':>5} {'chroma':>6} {'hue':>4}")
    for w in rep["swatches"]:
        print(f"{w['hex']:8} {w['share'] * 100:5.1f}% {w['L']:5.1f} {w['chroma']:6.1f} {w['hue']:4}")
    print("suggested roles:", json.dumps(rep["suggested_roles"]))
    print("contrast:", json.dumps(rep["contrast"]))
    for w in rep["warnings"]:
        print("WARNING:", w)


def cmd_build(a):
    from stipech import fusion, html
    kit, kroot = _kit(a.kit)
    spec = S.load_spec(a.spec, kit)
    stem = os.path.splitext(os.path.basename(a.spec))[0]
    out = a.out or os.path.dirname(os.path.abspath(a.spec))
    if not (a.html or a.fusion):
        a.html = a.fusion = True
    if a.html:
        p = os.path.join(out, stem + ".html")
        html.write(spec, kit, p, kit_root=kroot, asset_root=kroot, background=a.bg)
        print(p)
    if a.fusion:
        c = os.path.join(out, stem + ".comp")
        st = os.path.join(out, stem + ".setting")
        fusion.write(spec, kit, c, st, asset_root=kroot)
        print(c)
        print(st)


def cmd_lint(a):
    from stipech import lint
    kit, _ = _kit(a.kit)
    files = [f for pat in a.specs for f in sorted(glob.glob(pat))]
    specs = [S.load_spec(f, kit) for f in files]
    E, Wn = [], []
    for s in specs:
        e, w = lint.lint_spec(s, kit)
        E += e
        Wn += w
    e, w = lint.lint_project(specs)
    E += e
    Wn += w
    for x in E:
        print("ERROR ", x)
    for x in Wn:
        print("warn  ", x)
    print(f"{len(files)} spec(s): {len(E)} error(s), {len(Wn)} warning(s)")
    sys.exit(1 if E else 0)


def _house(a):
    h = a.house or os.environ.get("STIPECH_HOUSE")
    if not h:
        cfg = os.path.expanduser("~/.stipech-motion/config.json")
        if os.path.exists(cfg):
            h = S.load_json(cfg).get("house")
    return h


def _series_root(a=None):
    r = getattr(a, "root", None) or os.environ.get("STIPECH_SERIES")
    cfg = os.path.expanduser("~/.stipech-motion/config.json")
    if not r and os.path.exists(cfg):
        r = S.load_json(cfg).get("series_root")
    if not r:
        h = _house(a) if a else None
        if h:
            r = os.path.join(h, "Sermon Series")
    return r


def cmd_series(a):
    from stipech import series
    root = _series_root(a)
    if a.list:
        if not root or not os.path.isdir(root):
            sys.exit(f"no Sermon Series folder at {root!r}; set series_root in ~/.stipech-motion/config.json (or run /mg-setup)")
        for d in sorted(os.listdir(root)):
            p = os.path.join(root, d)
            if os.path.isdir(p) and not d.startswith((".", "_")):
                kit = os.path.join(p, "kit.json")
                state = "no kit" if not os.path.exists(kit) else ("draft kit" if S.load_json(kit).get("draft") else "kit approved")
                print(f"{d:40} {state}")
        return
    if not a.name:
        sys.exit("give a series name or folder path")
    folder = a.name if os.path.isdir(a.name) else (os.path.join(root, a.name) if root else a.name)
    inv = series.scan(folder)
    print(series.summary(inv))
    an = series.analyse_colors(inv) if (inv["colors"] or inv["backgrounds"]) else {}
    if an.get("colors"):
        print(f"\nColors photo ({inv['colors']}):")
        for w in an["colors"]["swatches"]:
            print(f"  {w['hex']}  {w['share'] * 100:5.1f}%  L{w['L']:5.1f}  C{w['chroma']:5.1f}  h{w['hue']:4}")
        print("  suggested roles:", json.dumps(an["colors"]["suggested_roles"]))
        for w in an["colors"]["warnings"]:
            print("  WARNING:", w)
    kit = os.path.join(inv["folder"], "kit.json")
    if a.draft:
        if os.path.exists(kit) and not a.force:
            print(f"\nkit.json exists; not overwritten (use --force). {kit}")
        else:
            fb = [f for f in inv["fonts"] if f.get("fallback")]
            if not [f for f in inv["fonts"] if not f.get("fallback")] and not fb:
                fb = _fallback_fonts(inv["folder"])
            with open(kit, "w", encoding="utf-8") as f:
                json.dump(series.draft_kit(inv, an, fb), f, indent=1)
            print(f"\ndraft kit -> {kit}  (finish it: references/style-intake.md, then remove \"draft\")")
    sys.exit(2 if inv["missing"] else 0)


def _fallback_fonts(folder):
    from stipech import fonts
    try:
        got = fonts.install_fallback(folder)
        print(f"\nno usable series fonts: installed Roboto Condensed (Google Fonts) -> {os.path.join(folder, 'Fonts')}")
        return got
    except Exception as e:
        print(f"\nWARNING: could not download Roboto Condensed from Google Fonts ({e}). "
              "Install it from https://fonts.google.com/specimen/Roboto+Condensed and copy the .ttf files into the series folder.")
        return []


def cmd_font_fallback(a):
    """Use Roboto Condensed for some or all type roles (no fonts, unreadable fonts, or illegible ones)."""
    from stipech import fonts
    root = _series_root(a)
    folder = a.series if os.path.isdir(a.series) else os.path.join(root or "", a.series)
    got = fonts.install_fallback(folder)
    print(f"Roboto Condensed (Google Fonts) -> {os.path.join(folder, 'Fonts')}")
    for f in got:
        print(f"  {f['family']} {f['style']}  {f['file']}  avg_char {f['avg_char']}")
    kit_path = os.path.join(folder, "kit.json")
    roles = [r.strip() for r in a.roles.split(",") if r.strip()]
    if os.path.exists(kit_path):
        kit = S.load_json(kit_path)
        kit.setdefault("type", {}).update(fonts.fallback_roles(got, roles))
        avail = kit.setdefault("available_fonts", [])
        for f in got:
            if f["file"] not in [x.get("file") for x in avail]:
                avail.append(f)
        with open(kit_path, "w", encoding="utf-8") as fh:
            json.dump(kit, fh, indent=1)
        print(f"kit.json roles now Roboto Condensed: {', '.join(roles)}")
    else:
        print("no kit.json yet; `series --draft` will use these files.")


def cmd_ledger(a):
    from stipech import ledger
    h = _house(a)
    if not h:
        sys.exit("no house folder: pass --house, set STIPECH_HOUSE, or run /mg-setup")
    board = S.load_json(a.board)
    path = os.path.join(h, "ledger.json")
    if a.action == "check":
        e, w = ledger.check(board, path)
        for x in e:
            print("ERROR ", x)
        for x in w:
            print("warn  ", x)
        print(f"variation: {len(e)} error(s), {len(w)} warning(s)")
        sys.exit(1 if e else 0)
    rec = ledger.add(board, path)
    print(f"recorded {rec['project']} in {path}")


def cmd_storyboard(a):
    from stipech import review, ledger
    board = S.load_json(a.board)
    issues = ([], [])
    h = _house(a)
    if h:
        issues = ledger.check(board, os.path.join(h, "ledger.json"))
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.board)), "review", "storyboard.html")
    review.storyboard(board, out, os.path.dirname(os.path.abspath(a.board)), issues)
    print(out)


def cmd_moodboard(a):
    from stipech import review
    kit, kroot = _kit(a.kit)
    mb = S.load_json(a.mb)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.mb)), "review", "moodboard.html")
    review.moodboard(mb, kit, kroot, out, os.path.dirname(os.path.abspath(a.mb)))
    print(out)


def cmd_package(a):
    from stipech import package
    m = package.build(a.plan, a.out)
    print(f"package -> {a.out}: {len(m['graphics'])} graphics, subtitles: {bool(m['subtitles'])}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("doctor").set_defaults(fn=cmd_doctor)
    p = sp.add_parser("inspect"); p.add_argument("video"); p.add_argument("out"); p.set_defaults(fn=cmd_inspect)
    p = sp.add_parser("thumbs"); p.add_argument("video"); p.add_argument("out"); p.add_argument("times", nargs="+")
    p.add_argument("--width", type=int, default=640); p.set_defaults(fn=cmd_thumbs)
    p = sp.add_parser("transcribe"); p.add_argument("video"); p.add_argument("--out", required=True)
    p.add_argument("--model", default="small.en"); p.add_argument("--prompt", help="names/terms to bias spelling (speaker, church, book names)")
    p.set_defaults(fn=cmd_transcribe)
    p = sp.add_parser("words"); p.add_argument("src"); p.add_argument("--out", required=True); p.set_defaults(fn=cmd_words)
    p = sp.add_parser("chunk"); p.add_argument("words"); p.add_argument("--kit"); p.add_argument("--out", required=True); p.set_defaults(fn=cmd_chunk)
    p = sp.add_parser("palette"); p.add_argument("image"); p.add_argument("--k", type=int, default=8)
    p.add_argument("--out"); p.add_argument("--swatch"); p.set_defaults(fn=cmd_palette)
    p = sp.add_parser("build"); p.add_argument("spec"); p.add_argument("--kit"); p.add_argument("--out")
    p.add_argument("--html", action="store_true"); p.add_argument("--fusion", action="store_true")
    p.add_argument("--bg", help="preview background: colour or still image (default transparent)"); p.set_defaults(fn=cmd_build)
    p = sp.add_parser("lint"); p.add_argument("specs", nargs="+"); p.add_argument("--kit"); p.set_defaults(fn=cmd_lint)
    p = sp.add_parser("ledger"); p.add_argument("action", choices=["check", "add"]); p.add_argument("board")
    p.add_argument("--house"); p.set_defaults(fn=cmd_ledger)
    p = sp.add_parser("storyboard"); p.add_argument("board"); p.add_argument("--out"); p.add_argument("--house"); p.set_defaults(fn=cmd_storyboard)
    p = sp.add_parser("moodboard"); p.add_argument("mb"); p.add_argument("--kit", required=True); p.add_argument("--out"); p.set_defaults(fn=cmd_moodboard)
    p = sp.add_parser("series"); p.add_argument("name", nargs="?"); p.add_argument("--list", action="store_true")
    p.add_argument("--draft", action="store_true", help="write a draft kit.json into the series folder")
    p.add_argument("--force", action="store_true"); p.add_argument("--root"); p.add_argument("--house")
    p.set_defaults(fn=cmd_series)
    p = sp.add_parser("font-fallback", help="Roboto Condensed from Google Fonts for some/all type roles")
    p.add_argument("series"); p.add_argument("--roles", default="display,text,subtitle")
    p.add_argument("--root"); p.add_argument("--house"); p.set_defaults(fn=cmd_font_fallback)
    p = sp.add_parser("package"); p.add_argument("plan"); p.add_argument("out"); p.set_defaults(fn=cmd_package)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
