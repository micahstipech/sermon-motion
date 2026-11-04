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
}
TREATMENTS_OUT = {
    "cut":   "leaves with the cut",
    "fade":  "fades, faster than it arrived",
    "sink":  "drops slightly while fading: the thought is finished",
    "wipe":  "wipes away in reading direction",
    "focus": "softens out of focus",
    "undraw": "a rule retracts toward its anchor",
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
                                 "track-in": 1.1, "settle": 0.8, "focus": 0.8, "draw": 0.7}.get(lin["treatment"], 0.6) * tempo))
    dout = float(lout.get("dur", {"cut": 0.0, "fade": 0.3, "sink": 0.35, "wipe": 0.45, "focus": 0.35,
                                   "undraw": 0.4}.get(lout["treatment"], 0.3) * tempo))
    ein = lin.get("ease", e_in)
    eout = lout.get("ease", e_out)
    d = float(lin.get("distance", dist))
    one_frame = 1.0 / 60

    tin = lin["treatment"]
    if tin not in TREATMENTS_IN:
        raise ValueError(f"layer {layer.get('id')}: unknown entrance treatment {tin!r}; known: {sorted(TREATMENTS_IN)}")
    if tin == "cut":
        _add(tracks, "opacity", [[max(0.0, ti - one_frame), 0.0], [ti, 1.0, "linear"]])
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
        elif tin == "focus":
            _add(tracks, "blur", [[ti, float(lin.get("from", 10))], [ti + din, 0.0, ein]])

    tout = lout["treatment"]
    if tout not in TREATMENTS_OUT:
        raise ValueError(f"layer {layer.get('id')}: unknown exit treatment {tout!r}; known: {sorted(TREATMENTS_OUT)}")
    if to < duration or tout != "cut":
        start = to - dout
        if tout == "cut":
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


def load_spec(spec_path_or_obj, kit=None):
    spec = copy.deepcopy(spec_path_or_obj if isinstance(spec_path_or_obj, dict) else load_json(spec_path_or_obj))
    spec.setdefault("width", 1920)
    spec.setdefault("height", 1080)
    spec.setdefault("fps", 24)
    if "duration" not in spec:
        raise ValueError(f"spec {spec.get('id')}: missing duration")
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
