# Minimal mock of the DaVinci Resolve scripting API: exercises place.py (tracks, overflow, carriers) without Resolve.
# usage: python3 tests/mock_resolve.py PACKAGE_DIR
import sys, json, os
class Item:
    def __init__(s, name, start, end, track): s.n, s.s, s.e, s.t = name, start, end, track; s.comps = []
    def GetStart(s): return s.s
    def GetEnd(s): return s.e
    def ImportFusionComp(s, p): assert os.path.exists(p); s.comps.append(p); return object()
    def SetClipColor(s, c): s.color = c
    def SetName(s, n): s.n = n
class Clip:
    def __init__(s, n): s.n = n
    def GetName(s): return s.n
    def GetClipProperty(s, k): return s.n
class Folder:
    def __init__(s, clips, subs=()): s.c, s.s = clips, list(subs)
    def GetClipList(s): return s.c
    def GetSubFolderList(s): return s.s
class TL:
    def __init__(s):
        s.tracks = {1: [Item("sermon", 86400, 86400 + 24*2000, 1)], 2: [], 3: [Item("existing broll", 86400 + 74*24, 86400 + 80*24, 3)]}
        s.names = {}
    def GetTrackCount(s, k): return len(s.tracks)
    def GetItemListInTrack(s, k, i): return s.tracks.get(i, [])
    def AddTrack(s, k): s.tracks[len(s.tracks) + 1] = []; return True
    def SetTrackName(s, k, i, n): s.names[i] = n
    def GetTrackName(s, k, i): return s.names.get(i, f"Video {i}")
    def GetStartFrame(s): return 86400
    def GetSetting(s, k): return "24"
    def DeleteClips(s, items, ripple): pass
class Pool:
    def __init__(s, tl): s.tl = tl; s.root = Folder([], [Folder([Clip("SM Carrier")])])
    def GetRootFolder(s): return s.root
    def AppendToTimeline(s, infos):
        out = []
        for i in infos:
            it = Item(i["mediaPoolItem"].GetName(), i["recordFrame"], i["recordFrame"] + i["endFrame"] - i["startFrame"] + 1, i["trackIndex"])
            s.tl.tracks[i["trackIndex"]].append(it); out.append(it)
        return out
    def ImportMedia(s, paths): return [Clip(os.path.basename(p)) for p in paths]
class Proj:
    def __init__(s): s.tl = TL(); s.pool = Pool(s.tl)
    def GetCurrentTimeline(s): return s.tl
    def GetMediaPool(s): return s.pool
    def GetSetting(s, k): return "24"
class PM:
    def __init__(s): s.p = Proj()
    def GetCurrentProject(s): return s.p
class Resolve:
    def __init__(s): s.pm = PM()
    def GetProjectManager(s): return s.pm
import importlib.util
spec = importlib.util.spec_from_file_location("place", os.path.join(sys.argv[1], "place.py"))
m = importlib.util.module_from_spec(spec); R = Resolve(); m.resolve = R; spec.loader.exec_module(m)
m.main([sys.argv[1]])
tl = R.pm.p.tl
for i, items in tl.tracks.items():
    print(f"V{i} {tl.names.get(i, '')!r}: {len(items)} items", [ (it.n[:18], (it.s-86400)/24) for it in items[:4]])
