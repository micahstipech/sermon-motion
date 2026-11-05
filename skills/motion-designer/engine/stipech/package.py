"""Bundle everything the editing PC needs into one folder: specs, kit (fonts, brand assets),
fallback renders, subtitles, the engine and the Resolve placement script.

The PC regenerates the Fusion comps from the specs at placement time, so every file path inside
the comps points at the PC's own copy of the assets.
"""
import json
import os
import shutil

from .spec import load_json

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)


def build(plan_path, out_dir):
    plan = load_json(plan_path)
    base = os.path.dirname(os.path.abspath(plan_path))

    def p(x):
        return x if os.path.isabs(x) else os.path.join(base, x)

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(os.path.join(out_dir, "specs"))
    kit_src = os.path.dirname(p(plan["kit"]))
    shutil.copytree(kit_src, os.path.join(out_dir, "kit"))
    manifest = {
        "project": plan.get("project"),
        "fps": plan.get("fps", 24),
        "width": plan.get("width", 1920),
        "height": plan.get("height", 1080),
        "kit": "kit/" + os.path.basename(plan["kit"]),
        "mode": plan.get("mode", "generated"),
        "bin": plan.get("bin") or plan.get("project"),
        "tracks": plan.get("tracks", {"graphics": 3, "subtitles": 4}),
        "timeline_offset": plan.get("timeline_offset", 0.0),
        "graphics": [],
        "subtitles": None,
    }
    for g in plan.get("graphics", []):
        spec = load_json(p(g["spec"]))
        name = f"{g['id']}.json"
        with open(os.path.join(out_dir, "specs", name), "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=1)
        entry = {"id": g["id"], "spec": "specs/" + name, "in": float(g.get("in", spec.get("in", 0))),
                 "duration": float(spec["duration"]), "title": g.get("title", spec.get("id"))}
        if g.get("render") and os.path.exists(p(g["render"])):
            os.makedirs(os.path.join(out_dir, "renders"), exist_ok=True)
            dst = os.path.join("renders", os.path.basename(g["render"]))
            try:  # same volume: hard link (ProRes 4444 is large; no second copy on disk)
                os.link(p(g["render"]), os.path.join(out_dir, dst))
            except OSError:
                shutil.copy2(p(g["render"]), os.path.join(out_dir, dst))
            entry["fallback"] = dst.replace(os.sep, "/")
        elif manifest["mode"] == "generated":
            raise SystemExit(f"{g['id']}: no rendered clip at {g.get('render')!r}. Generated mode places renders: run render.js first, "
                             "or set \"mode\": \"fusion\" in the plan for editable Fusion graphics.")
        manifest["graphics"].append(entry)
    if plan.get("subtitles"):
        shutil.copy2(p(plan["subtitles"]), os.path.join(out_dir, "subtitles.json"))
        manifest["subtitles"] = "subtitles.json"
        srt = os.path.splitext(p(plan["subtitles"]))[0] + ".srt"
        if os.path.exists(srt):
            shutil.copy2(srt, os.path.join(out_dir, "subtitles.srt"))
    shutil.copytree(HERE, os.path.join(out_dir, "engine", "stipech"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    for fname in ("place.py", "carrier.setting", "install.py"):
        shutil.copy2(os.path.join(ENGINE, "resolve", fname), os.path.join(out_dir, fname))
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    with open(os.path.join(out_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write(README.format(project=manifest["project"], mode=manifest["mode"], n=len(manifest["graphics"]),
                              subs="yes" if manifest["subtitles"] else "no",
                              g=manifest["tracks"]["graphics"], s=manifest["tracks"]["subtitles"]))
    return manifest


README = """Sermon Motion package: {project}
Mode: {mode}   Graphics: {n}   Subtitles: {subs}   Tracks: graphics V{g}, subtitles V{s} (overflow goes higher)

On the editing PC, with the sermon timeline open in DaVinci Resolve:

1. First time only:  python install.py
   (installs the SM Carrier title + a Workspace > Scripts entry; then drag
    Effects > Titles > "SM Carrier" into this project's Media Pool; media pools are per project.
    Subtitles need it in both modes; graphics need it only in fusion mode.)
2. Install the series fonts in kit/ (right-click > Install for all users) and restart Resolve.
3. Place everything:
     python place.py .            (Resolve Studio, from a terminal)
   or Workspace > Scripts > Sermon Motion - Place, and pick this folder.
   Add --dry-run to see what would be placed, --replace to clear an earlier placement,
   --new-timeline "Name" to place on a copy of the open timeline,
   --archive-older "Text" to move other timelines with that text in their name to Older Versions.

Every graphic is an editable Fusion comp (Text+ nodes, keyframed). Subtitles are Text+ clips:
trim them on the timeline to change timing, or open them in Fusion to change text.
"""
