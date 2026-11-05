#!/usr/bin/env python3
"""Place a Sermon Motion package on the current DaVinci Resolve timeline.

    python place.py PACKAGE_DIR [--dry-run] [--replace] [--no-subtitles] [--no-graphics]
                                [--offset SECONDS] [--prefer-renders]

Graphics -> track V3 ("SM Graphics"), subtitles -> V4 ("SM Subtitles"), as set in the manifest.
If anything already sits on the target track at that time, the clip goes up to the first free
track above the subtitle track (V5, V6, ... added as needed; named "SM Overflow").

Each graphic and subtitle is an "SM Carrier" title from the Media Pool with the generated Fusion
comp imported into it, so it is fully editable (Text+ nodes, keyframes) and trimmable.
If the carrier is missing or a comp import fails, the graphic falls back to its ProRes 4444 render.

Runs from a terminal with Resolve Studio (external scripting), or from inside Resolve via
Workspace > Scripts (install.py adds the menu entry), which works on the free version too.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CARRIER = "SM Carrier"
COLORS = {"graphics": "Teal", "subtitles": "Sand", "overflow": "Orange"}


# --------------------------------------------------------------------- connect
def get_resolve():
    g = globals()
    if g.get("resolve"):
        return g["resolve"]
    try:
        return bmd.scriptapp("Resolve")  # noqa: F821  (inside Resolve's script runner)
    except Exception:
        pass
    try:
        import DaVinciResolveScript as dvr
    except ImportError:
        for p in (os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"),
                               "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting", "Modules"),
                  "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
                  "/opt/resolve/Developer/Scripting/Modules"):
            if os.path.isdir(p) and p not in sys.path:
                sys.path.append(p)
        try:
            import DaVinciResolveScript as dvr
        except ImportError:
            sys.exit("Cannot load DaVinciResolveScript. Run from Workspace > Scripts, or set RESOLVE_SCRIPT_API/"
                     "RESOLVE_SCRIPT_LIB/PYTHONPATH (see references/resolve.md). External scripting needs Resolve Studio.")
    r = dvr.scriptapp("Resolve")
    if not r:
        sys.exit("Resolve is not running, or external scripting is disabled "
                 "(Preferences > System > General > External scripting using: Local).")
    return r


def find_clip(folder, name):
    for clip in folder.GetClipList() or []:
        if clip.GetName() == name or clip.GetClipProperty("Clip Name") == name:
            return clip
    for sub in folder.GetSubFolderList() or []:
        hit = find_clip(sub, name)
        if hit:
            return hit
    return None


# --------------------------------------------------------------------- tracks
class Tracks:
    def __init__(self, tl, dry):
        self.tl, self.dry = tl, dry
        self.busy = {}
        self.count = tl.GetTrackCount("video")
        for i in range(1, self.count + 1):
            self.busy[i] = [(it.GetStart(), it.GetEnd()) for it in (tl.GetItemListInTrack("video", i) or [])]

    def ensure(self, idx, name=None, rename_existing=False):
        """Add video tracks up to idx. Names only tracks we add (or our own V3/V4), never the editor's."""
        added = self.count < idx
        while self.count < idx:
            if not self.dry:
                self.tl.AddTrack("video")
            self.count += 1
            self.busy[self.count] = []
        if name and (added or rename_existing) and not self.dry:
            try:
                self.tl.SetTrackName("video", idx, name)
            except Exception:
                pass

    def free(self, idx, s, e):
        return all(e <= a or s >= b for a, b in self.busy.get(idx, []))

    def pick(self, preferred, s, e, floor):
        """Preferred track if free, else the first free track above `floor` (go up, never down)."""
        self.ensure(preferred)
        if self.free(preferred, s, e):
            return preferred, False
        i = floor + 1
        while True:
            self.ensure(i, "SM Overflow")
            if self.free(i, s, e):
                return i, True
            i += 1

    def take(self, idx, s, e):
        self.busy.setdefault(idx, []).append((s, e))


# --------------------------------------------------------------------- place
def main(argv=None, package=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("package", nargs="?", default=package)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--replace", action="store_true", help="remove earlier SM clips on SM tracks first")
    ap.add_argument("--no-subtitles", action="store_true")
    ap.add_argument("--no-graphics", action="store_true")
    ap.add_argument("--prefer-renders", action="store_true", help="fusion mode: use ProRes renders instead of Fusion comps")
    ap.add_argument("--new-timeline", default=None, help="duplicate the open timeline under this name and place on the copy")
    ap.add_argument("--archive-older", default=None, metavar="TEXT",
                    help="after placing, move other timelines with TEXT in their name to Older Versions/Timelines")
    ap.add_argument("--offset", type=float, default=None, help="seconds from timeline start to video time 0")
    a = ap.parse_args(argv)
    if not a.package:
        sys.exit("usage: place.py PACKAGE_DIR")
    pkg = os.path.abspath(a.package)
    man = json.load(open(os.path.join(pkg, "manifest.json"), encoding="utf-8"))
    sys.path.insert(0, os.path.join(pkg, "engine"))
    from stipech import spec as S, fusion, subtitles as SUB  # noqa: E402

    kit = S.load_json(os.path.join(pkg, man["kit"]))
    kit_root = os.path.dirname(os.path.join(pkg, man["kit"]))
    res = get_resolve()
    proj = res.GetProjectManager().GetCurrentProject()
    tl = proj.GetCurrentTimeline() if proj else None
    if not tl:
        sys.exit("Open the sermon timeline first.")
    pool = proj.GetMediaPool()
    mode = man.get("mode", "fusion")
    if a.new_timeline and not a.dry_run:
        copy = tl.DuplicateTimeline(a.new_timeline)
        if not copy:
            sys.exit(f"Could not duplicate the timeline as {a.new_timeline!r}.")
        proj.SetCurrentTimeline(copy)
        tl = proj.GetCurrentTimeline()
    fps = float(tl.GetSetting("timelineFrameRate") or proj.GetSetting("timelineFrameRate"))
    want = S.fps_value(man["fps"])
    if abs(fps - want) > 0.01:
        print(f"WARNING: timeline is {fps} fps, package was built for {want} fps. Timing converts by seconds; "
              f"check the first and last graphic.")
    offset = man.get("timeline_offset", 0.0) if a.offset is None else a.offset
    t0 = tl.GetStartFrame() + int(round(offset * fps))
    g_track, s_track = int(man["tracks"]["graphics"]), int(man["tracks"]["subtitles"])
    floor = max(g_track, s_track)

    carrier = find_clip(pool.GetRootFolder(), CARRIER)
    if not carrier:
        print(f"NOTE: no '{CARRIER}' in the Media Pool. Run install.py once, then drag Effects > Titles > "
              f"{CARRIER} into this project's Media Pool. Subtitles are skipped; Fusion-mode graphics use their ProRes renders.")

    if a.replace and not a.dry_run:
        doomed = []
        for i in range(1, tl.GetTrackCount("video") + 1):
            if (tl.GetTrackName("video", i) or "").startswith("SM "):
                doomed += [it for it in (tl.GetItemListInTrack("video", i) or [])]
        if doomed:
            tl.DeleteClips(doomed, False)
            print(f"removed {len(doomed)} earlier SM clips")

    T = Tracks(tl, a.dry_run)
    T.ensure(g_track, "SM Graphics", rename_existing=True)
    T.ensure(s_track, "SM Subtitles", rename_existing=True)
    comps_dir = os.path.join(pkg, "comps")
    os.makedirs(comps_dir, exist_ok=True)
    report = {"graphics": [], "subtitles": 0, "overflow": 0, "fallbacks": 0, "failed": []}

    def place_carrier(track, start, frames, comp_path, color, label):
        # Resolve 21: endFrame is exclusive (frames - 1 left every clip one frame short).
        items = pool.AppendToTimeline([{"mediaPoolItem": carrier, "startFrame": 0, "endFrame": frames,
                                        "trackIndex": track, "recordFrame": start}])
        if not items:
            return None
        it = items[0]
        comp = it.ImportFusionComp(comp_path)
        if not comp:
            tl.DeleteClips([it], False)
            return None
        try:
            it.SetClipColor(color)
            it.SetName(label)
        except Exception:
            pass
        return it

    def bin_folder():
        """Everything this package brings in lives in its own bin: Motion Graphics/<project>."""
        root = pool.GetRootFolder()
        def sub(parent, name):
            return next((f for f in parent.GetSubFolderList() or [] if f.GetName() == name), None) or pool.AddSubFolder(parent, name)
        return sub(sub(root, "Motion Graphics"), str(man.get("bin") or man.get("project") or "Package"))

    def place_render(track, start, frames, mov):
        pool.SetCurrentFolder(bin_folder())
        imported = pool.ImportMedia([mov]) or []
        pool.SetCurrentFolder(pool.GetRootFolder())
        if not imported:
            return None
        items = pool.AppendToTimeline([{"mediaPoolItem": imported[0], "startFrame": 0, "endFrame": frames,
                                        "trackIndex": track, "recordFrame": start, "mediaType": 1}])
        if not items:
            return None
        try:
            items[0].SetClipColor(COLORS["graphics"])
        except Exception:
            pass
        return items[0]

    # ---------------- graphics
    if not a.no_graphics:
        for g in man["graphics"]:
            spec = S.load_spec(os.path.join(pkg, g["spec"]), kit)
            start = t0 + int(round(g["in"] * fps))
            frames = max(1, t0 + int(round((g["in"] + g["duration"]) * fps)) - start)
            track, moved = T.pick(g_track, start, start + frames, floor)
            comp_path = os.path.join(comps_dir, g["id"] + ".comp")
            fusion.write(spec, kit, comp_path, asset_root=kit_root)
            how = "fusion"
            if a.dry_run:
                pass
            elif mode == "generated":
                how = "clip"
                if not (g.get("fallback") and place_render(track, start, frames, os.path.join(pkg, g["fallback"]))):
                    report["failed"].append(g["id"])
                    continue
            elif carrier and not a.prefer_renders and place_carrier(track, start, frames, comp_path,
                                                                   COLORS["overflow" if moved else "graphics"], g.get("title") or g["id"]):
                pass
            elif g.get("fallback") and place_render(track, start, frames, os.path.join(pkg, g["fallback"])):
                how = "render"
                report["fallbacks"] += 1
            else:
                report["failed"].append(g["id"])
                continue
            T.take(track, start, start + frames)
            report["overflow"] += moved
            report["graphics"].append(f"{g['id']} V{track} @{g['in']:.2f}s ({how})")

    # ---------------- subtitles
    if man.get("subtitles") and not a.no_subtitles and (carrier or a.dry_run):
        chunks = json.load(open(os.path.join(pkg, man["subtitles"]), encoding="utf-8"))
        sub_dir = os.path.join(comps_dir, "subtitles")
        os.makedirs(sub_dir, exist_ok=True)
        for c in chunks:
            spec = S.load_spec(SUB.chunk_spec(c, kit, man["width"], man["height"], man["fps"]), kit)
            start = t0 + int(round(c["s"] * fps))
            frames = max(1, t0 + int(round(c["e"] * fps)) - start)  # round both ends: back-to-back chunks never overlap
            track, moved = T.pick(s_track, start, start + frames, floor)
            path = os.path.join(sub_dir, f"{c['i']:04}.comp")
            fusion.write(spec, kit, path, asset_root=kit_root)
            if not a.dry_run and not place_carrier(track, start, frames, path,
                                                   COLORS["overflow" if moved else "subtitles"], c["text"]):
                report["failed"].append(f"sub {c['i']}")
                continue
            T.take(track, start, start + frames)
            report["subtitles"] += 1
            report["overflow"] += moved
            if report["subtitles"] % 100 == 0:
                print(f"  subtitles placed: {report['subtitles']}/{len(chunks)}")

    print(("DRY RUN: " if a.dry_run else "") + f"{len(report['graphics'])} graphics, {report['subtitles']} subtitles, "
          f"{report['overflow']} moved up for conflicts, {report['fallbacks']} Fusion fallbacks to ProRes renders.")
    if not a.dry_run:
        if carrier and pool.GetRootFolder():
            try:
                pool.MoveClips([carrier], bin_folder())
            except Exception:
                pass
        if a.archive_older:
            root = pool.GetRootFolder()
            def sub2(parent, name):
                return next((f for f in parent.GetSubFolderList() or [] if f.GetName() == name), None) or pool.AddSubFolder(parent, name)
            older = sub2(sub2(root, "Older Versions"), "Timelines")
            keep = tl.GetName()
            moved = []
            for i in range(1, proj.GetTimelineCount() + 1):
                t = proj.GetTimelineByIndex(i)
                if t.GetName() != keep and a.archive_older in t.GetName() and t.GetMediaPoolItem():
                    moved.append(t.GetMediaPoolItem())
            if moved:
                pool.MoveClips(moved, older)
            print(f"moved {len(moved)} older timelines to Older Versions/Timelines (nothing deleted)")
    for line in report["graphics"]:
        print("  " + line)
    if report["failed"]:
        print("FAILED: " + ", ".join(report["failed"]))
    with open(os.path.join(pkg, "placement-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    return report


if __name__ == "__main__":
    main()
