"""Graphic spec: the single source both backends (Fusion, HTML) render from.

A spec describes one graphic on the motion-graphics track. Times are clip-local seconds.
Positions and sizes are pixels in the spec's frame (default 1920x1080), y pointing down.
Treatments (named entrances/exits) expand into keyframe tracks here, once, so Fusion and
HTML always agree on timing and easing.

Pure standard library: this module also runs inside DaVinci Resolve's Python.
"""
import copy
import json
import math
import os

# ---------------------------------------------------------------- easing
# Cubic-bezier control points (x1, y1, x2, y2), the same numbers CSS uses.
# Each maps 1:1 onto Fusion BezierSpline handles, so both backends share one curve.
EASES = {
    "linear":  (0.0, 0.0, 1.0, 1.0),
    "settle":  (0.16, 1.0, 0.3, 1.0),    # arrives with intent, long soft landing (entrances)
    "glide":   (0.45, 0.0, 0.2, 1.0),    # deliberate A -> B (repositioning, rules drawing)
    "breathe": (0.37, 0.0, 0.63, 1.0),   # symmetric, for slow drifts and holds
    "exit":    (0.55, 0.0, 0.85, 0.35),  # leaves quickly, no landing (exits)
    "snap":    (0.2, 0.9, 0.25, 1.0),    # short and firm, for small UI-like moves
}
BANNED_EASES = {"bounce", "elastic", "back", "overshoot"}


def bezier_y(ease, u):
    """Value progress (0..1) of a cubic-bezier ease at time progress u (0..1)."""
    x1, y1, x2, y2 = EASES[ease]
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0

    def bx(s):
        return 3 * x1 * s * (1 - s) ** 2 + 3 * x2 * s * s * (1 - s) + s ** 3

    def by(s):
        return 3 * y1 * s * (1 - s) ** 2 + 3 * y2 * s * s * (1 - s) + s ** 3

    lo, hi = 0.0, 1.0
    for _ in range(40):  # bisection: monotonic in x for valid eases
        mid = (lo + hi) / 2
        if bx(mid) < u:
            lo = mid
        else:
            hi = mid
    return by((lo + hi) / 2)


def sample(keys, t):
    """Value of a keyframe track at time t. keys: [[t, v, ease_into_this_key?], ...] sorted."""
    if not keys:
        return None
    if t <= keys[0][0]:
        return keys[0][1]
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            ease = b[2] if len(b) > 2 else "glide"
            span = b[0] - a[0]
            u = 1.0 if span <= 0 else (t - a[0]) / span
            p = bezier_y(ease, u)
            return a[1] + (b[1] - a[1]) * p
    return keys[-1][1]


# ---------------------------------------------------------------- treatments
# Each treatment says something. Pick it for its meaning (references/treatments.md),
# and let the ledger keep any one from becoming the channel's signature.
# Durations are scaled by kit.motion.tempo (>1 = slower), distances by kit.motion.distance.
TREATMENTS_IN = {
    "cut":        "appears on the word with no motion: plain, confident, trusts the words",
    "fade":       "quiet arrival; nothing to notice but the content",
    "rise":       "a small lift into place: gentle emphasis",
    "rise-mask":  "rises out of an invisible line: editorial, precise",
    "wipe":       "revealed left to right like a line being read",
    "track-in":   "letters gather from wide spacing: a word settling into meaning",
    "settle":     "a 3-4% scale settle: presence without movement",
    "focus":      "comes into focus from a soft blur: reflective (use sparingly, it is an AI cliche as a default)",
    "draw":       "a rule or shape draws itself on: structure, underlining",
    "collage":    "a piece laid down: slightly large and turned, settling flat as it fades in",
    "paper":      "a sheet slides in from its edge (box layers); a soft edge wipe in Fusion",
}
# The moves the standing animation rule allows: a collage, a paper effect, a light movement with an
# opacity shift, or no animation. Anything else is a lint error (older specs still build).
ALLOWED_IN = {"cut", "fade", "rise", "settle", "collage", "paper"}
ALLOWED_OUT = {"cut", "fade", "sink", "paper"}
TREATMENTS_OUT = {
    "cut":   "leaves with the cut",
    "fade":  "fades, faster than it arrived",
    "sink":  "drops slightly while fading: the thought is finished",
    "wipe":  "wipes away in reading direction",
    "focus": "softens out of focus",
    "undraw": "a rule retracts toward its anchor",
    "paper": "a sheet slides back to its edge",
}


def _motion(kit):
    m = (kit or {}).get("motion", {})
    return float(m.get("tempo", 1.0)), float(m.get("distance", 24)), m.get("ease_in", "settle"), m.get("ease_out", "exit")


def _add(tracks, prop, keys):
    tracks.setdefault(prop, [])
    tracks[prop].extend(keys)


def expand_layer(layer, kit, duration):
    """Turn a layer's `in`/`out` treatments into explicit keyframe tracks (`anim`)."""
    tempo, dist, e_in, e_out = _motion(kit)
    tracks = {}
    lin = layer.get("in") or {"treatment": "cut", "at": 0.0}
    lout = layer.get("out") or {"treatment": "cut", "at": duration}
    ti = float(lin.get("at", 0.0))
    to = float(lout.get("at", duration))
    din = float(lin.get("dur", {"cut": 0.0, "fade": 0.5, "rise": 0.7, "rise-mask": 0.75, "wipe": 0.9,
                                 "track-in": 1.1, "settle": 0.8, "focus": 0.8, "draw": 0.7, "collage": 0.6, "paper": 0.6}.get(lin["treatment"], 0.6) * tempo))
    dout = float(lout.get("dur", {"cut": 0.0, "fade": 0.3, "sink": 0.35, "wipe": 0.45, "focus": 0.35,
                                   "undraw": 0.4, "paper": 0.5}.get(lout["treatment"], 0.3) * tempo))
    ein = lin.get("ease", e_in)
    eout = lout.get("ease", e_out)
    d = float(lin.get("distance", dist))
    one_frame = 1.0 / 60

    tin = lin["treatment"]
    if tin not in TREATMENTS_IN:
        raise ValueError(f"layer {layer.get('id')}: unknown entrance treatment {tin!r}; known: {sorted(TREATMENTS_IN)}")
    if tin == "cut":
        _add(tracks, "opacity", [[max(0.0, ti - one_frame), 0.0], [ti, 1.0, "linear"]])
    elif tin == "paper":
        _add(tracks, "opacity", [[max(0.0, ti - one_frame), 0.0], [ti, 1.0, "linear"]])
        _add(tracks, "paper", [[ti, 0.0], [ti + din, 1.0, lin.get("ease", "breathe")]])
    elif tin == "draw":
        _add(tracks, "opacity", [[max(0.0, ti - one_frame), 0.0], [ti, 1.0, "linear"]])
        _add(tracks, "draw", [[ti, 0.0], [ti + din, 1.0, lin.get("ease", "glide")]])
    else:
        _add(tracks, "opacity", [[ti, 0.0], [ti + din * (0.6 if tin != "fade" else 1.0), 1.0, "glide" if tin != "fade" else "breathe"]])
        if tin == "rise":
            _add(tracks, "dy", [[ti, d], [ti + din, 0.0, ein]])
        elif tin == "rise-mask":
            layer.setdefault("clip", "band")
            _add(tracks, "dy", [[ti, float(layer.get("size", 60)) * 1.15], [ti + din, 0.0, ein]])
            tracks["opacity"] = [[max(0.0, ti - one_frame), 0.0], [ti, 1.0, "linear"]]
        elif tin == "wipe":
            layer.setdefault("clip", "band")
            tracks["opacity"] = [[max(0.0, ti - one_frame), 0.0], [ti, 1.0, "linear"]]
            _add(tracks, "reveal", [[ti, 0.0], [ti + din, 1.0, lin.get("ease", "glide")]])
        elif tin == "track-in":
            _add(tracks, "tracking", [[ti, float(lin.get("from", 0.25))], [ti + din, float(layer.get("tracking", 0.0)), ein]])
        elif tin == "settle":
            _add(tracks, "scale", [[ti, float(lin.get("from", 1.035))], [ti + din, 1.0, ein]])
        elif tin == "collage":
            rot = float(layer.get("rotation", 0.0))
            _add(tracks, "scale", [[ti, 1.04], [ti + din, 1.0, ein]])
            _add(tracks, "rotation", [[ti, rot + 1.5], [ti + din, rot, ein]])
        elif tin == "focus":
            _add(tracks, "blur", [[ti, float(lin.get("from", 10))], [ti + din, 0.0, ein]])

    tout = lout["treatment"]
    if tout not in TREATMENTS_OUT:
        raise ValueError(f"layer {layer.get('id')}: unknown exit treatment {tout!r}; known: {sorted(TREATMENTS_OUT)}")
    if to < duration or tout != "cut":
        start = to - dout
        if tout == "cut":
            _add(tracks, "opacity", [[to - one_frame, 1.0], [to, 0.0, "linear"]])
        elif tout == "paper":
            _add(tracks, "paper_out", [[start, 0.0], [to, 1.0, lout.get("ease", "breathe")]])
            _add(tracks, "opacity", [[to - one_frame, 1.0], [to, 0.0, "linear"]])
        elif tout == "undraw":
            _add(tracks, "draw", [[start, 1.0], [to, 0.0, eout]])
            _add(tracks, "opacity", [[to - one_frame, 1.0], [to, 0.0, "linear"]])
        elif tout == "wipe":
            layer.setdefault("clip", "band")
            layer["wipe_out"] = True
            _add(tracks, "reveal_out", [[start, 0.0], [to, 1.0, eout]])
            _add(tracks, "opacity", [[to - one_frame, 1.0], [to, 0.0, "linear"]])
        else:
            _add(tracks, "opacity", [[start, 1.0], [to, 0.0, eout]])
            if tout == "sink":
                _add(tracks, "dy", [[start, 0.0], [to, d * 0.4, eout]])
            elif tout == "focus":
                _add(tracks, "blur", [[start, 0.0], [to, 8.0, eout]])

    # explicit keyframes in the spec override treatment output for that property
    for prop, keys in (layer.get("anim") or {}).items():
        tracks[prop] = [list(k) for k in keys]
    for prop in tracks:
        tracks[prop].sort(key=lambda k: k[0])
        for k in tracks[prop]:
            if len(k) > 2 and k[2] in BANNED_EASES:
                raise ValueError(f"layer {layer.get('id')}: ease {k[2]!r} is banned (over-animation)")
            if len(k) > 2 and k[2] not in EASES:
                raise ValueError(f"layer {layer.get('id')}: unknown ease {k[2]!r}; known: {sorted(EASES)}")
    layer["tracks"] = tracks
    return layer


# ---------------------------------------------------------------- kit + spec loading
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_color(value, kit):
    """'ink' / 'accent' / '#RRGGBB' / 'ink@60' (60 % alpha) -> (r, g, b, a) floats 0..1."""
    alpha = 1.0
    if isinstance(value, str) and "@" in value:
        value, a = value.split("@", 1)
        alpha = float(a) / 100.0
    pal = (kit or {}).get("palette", {})
    if isinstance(value, str) and value in pal:
        entry = pal[value]
        value = entry["hex"] if isinstance(entry, dict) else entry
    h = str(value).lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"colour {value!r} is not a palette role or #RRGGBB")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (r, g, b, alpha)


def font_for(layer, kit):
    """Font role ('display', 'text', 'subtitle', or a literal family) -> dict(family, style, weight, file)."""
    role = layer.get("font", "display")
    types = (kit or {}).get("type", {})
    f = dict(types.get(role) or {"family": role})
    f.setdefault("style", "Regular")
    f.setdefault("weight", 400)
    if layer.get("style"):
        f["style"] = layer["style"]
    if layer.get("weight"):
        f["weight"] = layer["weight"]
    return f


def estimate_text_width(layer, kit):
    """Rough text width in px (for wipes and bands). Generous on purpose: masks only need to cover."""
    text = str(layer.get("text", ""))
    size = float(layer.get("size", 60))
    lines = text.split("\n")
    longest = max((len(l) for l in lines), default=0)
    avg = float(((kit or {}).get("type", {}).get(layer.get("font", "display")) or {}).get("avg_char", 0.56))
    tracking = float(layer.get("tracking", 0.0))
    return longest * size * (avg + tracking) * 1.08


def text_block_height(layer):
    size = float(layer.get("size", 60))
    n = str(layer.get("text", "")).count("\n") + 1
    return size * (1.25 * n)


# ---------------------------------------------------------------- boxes and split screens
# A layer with "box": [x, y, w, h] (px, top-left origin) lives only inside that rectangle:
# an image is cover-fitted to the box (not the frame) and clipped to it; a rect fills it.
# A "wipe" on a box layer reveals it from the edge named by "dir" (left | right | top | bottom)
# and its "wipe" exit retracts it back toward that same edge.
SPLIT_EDGE = {"top": "top", "bottom": "bottom", "left": "left", "right": "right"}


def split_box(side, size, W, H):
    """Box [x, y, w, h] for a split panel. size <= 1 is a fraction of the frame, else px."""
    if side not in SPLIT_EDGE:
        raise ValueError(f"split side must be one of {sorted(SPLIT_EDGE)}, not {side!r}")
    full = H if side in ("top", "bottom") else W
    px = float(size) * full if float(size) <= 1 else float(size)
    return {"top": [0, 0, W, px], "bottom": [0, H - px, W, px],
            "left": [0, 0, px, H], "right": [W - px, 0, px, H]}[side]


def expand_split(spec):
    """Spec-level "split": {"side", "size", "src" | "color", "zoom", "in", "out"} -> a box panel layer
    inserted first (under everything else). The other half of the frame stays clear for the footage."""
    sp = spec.get("split")
    if not sp:
        return
    W, H = float(spec["width"]), float(spec["height"])
    side = sp.get("side", "top")
    box = split_box(side, sp.get("size", 0.5), W, H)
    layer = {"id": sp.get("id", "split"), "box": box, "panel": True, "dir": sp.get("dir", SPLIT_EDGE[side]),
             "torn": bool(sp.get("torn", True)),
             "in": sp.get("in") or {"treatment": "cut", "at": 0.0},
             "out": sp.get("out") or {"treatment": "cut", "at": float(spec["duration"])}}
    if sp.get("src"):
        layer.update({"type": "image", "src": sp["src"], "fit": "cover", "zoom": float(sp.get("zoom", 1.0))})
        for k in ("x", "y"):
            if k in sp:
                layer[k] = sp[k]
    else:
        layer.update({"type": "rect", "color": sp.get("color", "ground")})
    if any(L.get("id") == layer["id"] for L in spec.get("layers", [])):
        return  # already expanded
    spec.setdefault("layers", []).insert(0, layer)


def box_of(layer):
    b = layer.get("box")
    if not b:
        return None
    if len(b) != 4:
        raise ValueError(f"layer {layer.get('id')}: box must be [x, y, w, h]")
    return [float(v) for v in b]


def box_extent_keys(layer):
    """Visible extent of a box (0..1 from its 'dir' edge) over time, as [[t, e, ease]] keys.
    e = reveal * (1 - reveal_out): the wipe in grows from the edge, the wipe out retracts to it."""
    tr = layer["tracks"]
    rev = tr.get("reveal") or tr.get("paper") or [[0.0, 1.0]]
    rout = tr.get("reveal_out") or tr.get("paper_out") or [[0.0, 0.0]]
    times = sorted({k[0] for k in rev} | {k[0] for k in rout})
    keys = []
    for t in times:
        ease = next((k[2] for k in rev + rout if k[0] == t and len(k) > 2), "glide")
        keys.append([t, sample(rev, t) * (1.0 - sample(rout, t)), ease])
    return keys


def torn_polygon(seed, w, h, direction, amp=9.0, step=11):
    """CSS polygon for a box with one torn edge: the edge away from `direction`, the side it entered from."""
    import random
    rnd = random.Random(seed)
    length = h if direction in ("left", "right") else w
    edge, pos, drift = [], 0.0, 0.0
    while pos < length:
        drift = drift * 0.72 + rnd.uniform(-amp, amp) * 0.55
        edge.append((pos, drift - amp))
        pos += step + rnd.randint(-3, 5)
    edge.append((length, -amp))
    if direction == "top":      # torn along the bottom
        pts = [(0, 0), (w, 0)] + [(w - p, h + d) for p, d in edge]
    elif direction == "bottom":  # torn along the top
        pts = [(p, -d) for p, d in edge] + [(w, h), (0, h)]
    elif direction == "left":    # torn along the right
        pts = [(0, 0)] + [(w + d, p) for p, d in edge] + [(0, h)]
    else:                        # torn along the left
        pts = [(-d, p) for p, d in edge] + [(w, h), (w, 0)]
    return "polygon(" + ",".join(f"{x:.1f}px {y:.1f}px" for x, y in pts) + ")"


def text_safe_box(width, height, kit=None):
    """(left, top, right, bottom) px that all text stays inside.

    The margin is at least 10 % of each dimension on horizontal frames and 17.5 % on vertical ones
    (kit `layout.text_margin` overrides it). Vertical frames are social video by default, so their
    bottom edge also clears the phone app's caption area (kit `layout.social: false` turns that off).
    """
    layout = (kit or {}).get("layout") or {}
    vertical = height > width
    m = float(layout.get("text_margin", 0.175 if vertical else 0.10))
    left, top, right, bottom = width * m, height * m, width * (1 - m), height * (1 - m)
    if vertical and layout.get("social", True):
        bottom = min(bottom, height * 0.6875)
    return left, top, right, bottom


def subtitle_style(kit, width, height):
    """The kit's subtitle style, with its `vertical` overrides on portrait frames."""
    st = dict((kit or {}).get("subtitles", {}))
    if height > width:
        st.update({"size": 52, "x": width * .5, "y": height * .66})  # above the phone app's caption area
        st.update(st.get("vertical") or {})
    return st


def box_visible_rect(box, direction, e):
    """[x, y, w, h] of the visible part of a box at extent e, growing from its 'direction' edge."""
    bx, by, bw, bh = box
    if direction == "right":
        return [bx + bw * (1 - e), by, bw * e, bh]
    if direction == "top":
        return [bx, by, bw, bh * e]
    if direction == "bottom":
        return [bx, by + bh * (1 - e), bw, bh * e]
    return [bx, by, bw * e, bh]  # left


def load_spec(spec_path_or_obj, kit=None):
    spec = copy.deepcopy(spec_path_or_obj if isinstance(spec_path_or_obj, dict) else load_json(spec_path_or_obj))
    spec.setdefault("width", 1920)
    spec.setdefault("height", 1080)
    spec.setdefault("fps", 24)
    if "duration" not in spec:
        raise ValueError(f"spec {spec.get('id')}: missing duration")
    expand_split(spec)
    for layer in spec.get("layers", []):
        b = box_of(layer)
        if b and layer.get("type") == "image":
            layer.setdefault("x", b[0] + b[2] / 2)
            layer.setdefault("y", b[1] + b[3] / 2)
    seen = set()
    for i, layer in enumerate(spec.get("layers", [])):
        layer.setdefault("id", f"L{i + 1}")
        if layer["id"] in seen:
            raise ValueError(f"spec {spec.get('id')}: duplicate layer id {layer['id']}")
        seen.add(layer["id"])
        if layer.get("type", "text") not in ("text", "rect", "image"):
            raise ValueError(f"layer {layer['id']}: type must be text, rect or image")
        expand_layer(layer, kit, float(spec["duration"]))
    return spec


def fps_value(fps):
    if isinstance(fps, str) and "/" in fps:
        a, b = fps.split("/")
        return float(a) / float(b)
    return float(fps)


def kit_dir(kit_path):
    return os.path.dirname(os.path.abspath(kit_path))


# ---------------------------------------------------------------- images (stdlib, also inside Resolve)
def image_size(path):
    """(width, height) of a PNG or JPEG without Pillow, or None."""
    import struct
    try:
        with open(path, "rb") as f:
            head = f.read(26)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                return struct.unpack(">II", head[16:24])
            if head[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    marker = f.read(2)
                    if len(marker) < 2 or marker[0] != 0xFF:
                        return None
                    if marker[1] in (0xD8, 0x01) or 0xD0 <= marker[1] <= 0xD7:
                        continue
                    seg = struct.unpack(">H", f.read(2))[0]
                    if marker[1] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                        h, w = struct.unpack(">xHH", f.read(5))
                        return (w, h)
                    f.seek(seg - 2, 1)
    except OSError:
        pass
    return None


def image_fit(layer, native, W, H):
    """Display size (w, h) in px for an image layer: fit cover/contain to the frame (or to its box),
    or `w` px wide."""
    nw, nh = native
    b = layer.get("box")
    if b:
        W, H = float(b[2]), float(b[3])
    fit = layer.get("fit")
    if fit == "cover":
        s = max(W / nw, H / nh) * float(layer.get("zoom", 1.0))
    elif fit == "contain":
        s = min(W / nw, H / nh) * float(layer.get("zoom", 1.0))
    elif layer.get("w"):
        s = float(layer["w"]) / nw
    elif layer.get("h"):
        s = float(layer["h"]) / nh
    else:
        s = 1.0
    return nw * s, nh * s, s
