"""Spec -> DaVinci Resolve Fusion composition (.comp) and macro (.setting).

Every layer becomes an editable node chain:
    Text+ / Background / Loader -> [Blur] -> Transform -> Merge (Blend = opacity, EffectMask = reveal)
Merges stack bottom-to-top onto a transparent Background and end in MediaOut1.
Animated inputs are BezierSplines whose handles carry the spec's cubic-bezier eases,
so the curves stay smooth and editable in the Fusion spline editor.

Pure standard library (runs inside Resolve's Python too).
Values marked CALIBRATE are the ones to confirm on first contact with Resolve
(see references/resolve.md, "Calibration").
"""
import os
import struct

from .spec import EASES, font_for, resolve_color, estimate_text_width, text_block_height, fps_value

# CALIBRATE: Text+ Size is relative to frame width (1.0 = text as tall as the frame is wide).
TEXT_SIZE_PER_PX = 1.0 / 1920.0
# CALIBRATE: Text+ CharacterSpacing 1.0 = normal; +0.1 roughly = +0.1 em of tracking.
TRACKING_SCALE = 1.0
# CALIBRATE: Blur XBlurSize units per spec pixel of blur.
BLUR_SCALE = 1.0
# Text+ anchor values (HorizontalLeftCenterRight): -1 left, 0 centre, 1 right.
ANCHOR = {"left": -1, "center": 0, "right": 1}


class Lua:
    """Tiny Lua-table writer for Fusion's file format."""

    def __init__(self, raw):
        self.raw = raw

    def __repr__(self):
        return self.raw


def lua(v, ind=0):
    pad = "\t" * ind
    if isinstance(v, Lua):
        return v.raw
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        if isinstance(v, float):
            if abs(v) < 1e-12:
                return "0"
            return repr(round(v, 6))
        return str(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(v, (list, tuple)):
        return "{ " + ", ".join(lua(x, ind) for x in v) + " }"
    if isinstance(v, dict):
        items = []
        for k, x in v.items():
            if isinstance(k, (int, float)):
                key = f"[{lua(k)}]"
            elif k.isidentifier():
                key = k
            else:
                key = f'["{k}"]'
            items.append(f"{pad}\t{key} = {lua(x, ind + 1)},")
        return "{\n" + "\n".join(items) + f"\n{pad}}}"
    raise TypeError(type(v))


def tool(kind, inputs, pos, extra=None):
    body = {"Inputs": inputs, "ViewInfo": Lua(f"OperatorInfo {{ Pos = {{ {pos[0]}, {pos[1]} }} }}")}
    if extra:
        body.update(extra)
    return (kind, body)


def inp_value(v):
    return Lua("Input { Value = " + lua(v) + ", }")


def inp_src(op, src="Value"):
    return Lua(f'Input {{ SourceOp = "{op}", Source = "{src}", }}')


class Comp:
    def __init__(self, spec):
        self.spec = spec
        self.fps = fps_value(spec["fps"])
        self.W = int(spec["width"])
        self.H = int(spec["height"])
        self.tools = []  # (name, kind, body)

    def frame(self, t):
        return int(round(float(t) * self.fps))

    def add(self, name, kind, body):
        self.tools.append((name, kind, body))
        return name

    def spline(self, name, keys, fn, color=(225, 255, 0)):
        """keys: [[t, v, ease]]; fn maps spec value -> Fusion value. Returns a BezierSpline tool name."""
        frames = {}
        pts = [(self.frame(k[0]), fn(k[1]), k[2] if len(k) > 2 else "glide") for k in keys]
        # Two keys on one frame (a cut: 0 -> 1 within a frame): keep both by moving the earlier
        # key back one frame, so the value before the cut is held (not the value after it).
        dedup = []
        for p in pts:
            if dedup and dedup[-1][0] >= p[0]:
                prev = dedup[-1]
                if abs(prev[1] - p[1]) > 1e-9 and (len(dedup) < 2 or dedup[-2][0] < p[0] - 1):
                    dedup[-1] = (p[0] - 1, prev[1], prev[2])
                    dedup.append(p)
                else:
                    dedup[-1] = p
            else:
                dedup.append(p)
        for i, (f, v, _) in enumerate(dedup):
            entry = [v]
            if i > 0:
                pf, pv, _ = dedup[i - 1]
                x1, y1, x2, y2 = EASES[dedup[i][2]]
                entry_lh = (pf + (f - pf) * x2, pv + (v - pv) * y2)
                entry.append(Lua(f"LH = {{ {lua(float(entry_lh[0]))}, {lua(float(entry_lh[1]))} }}"))
            if i < len(dedup) - 1:
                nf, nv, ne = dedup[i + 1]
                x1, y1, x2, y2 = EASES[ne]
                rh = (f + (nf - f) * x1, v + (nv - v) * y1)
                entry.append(Lua(f"RH = {{ {lua(float(rh[0]))}, {lua(float(rh[1]))} }}"))
            if i < len(dedup) - 1 and dedup[i + 1][2] == "linear":
                entry.append(Lua("Flags = { Linear = true }"))
            frames[f] = Lua("{ " + ", ".join(lua(x) if not isinstance(x, Lua) else x.raw for x in entry) + " }")
        body = {
            "SplineColor": Lua(f"{{ Red = {color[0]}, Green = {color[1]}, Blue = {color[2]} }}"),
            "NameSet": True,
            "KeyFrames": frames,
        }
        return self.add(name, "BezierSpline", body)

    def value_or_spline(self, name, keys, fn, static):
        if keys and len(keys) > 1 and len({round(k[1], 6) for k in keys}) > 1:
            return inp_src(self.spline(name, keys, fn))
        if keys:
            return inp_value(fn(keys[0][1]))
        return inp_value(static)

    def xy_path(self, name, kx, ky, fx, fy, static):
        """Point input animated by two splines (X and Y) through an XYPath modifier."""
        ax = kx and len({round(k[1], 6) for k in kx}) > 1
        ay = ky and len({round(k[1], 6) for k in ky}) > 1
        if not ax and not ay:
            return inp_value(list(static))
        ix = inp_src(self.spline(name + "X", kx, fx)) if ax else inp_value(static[0])
        iy = inp_src(self.spline(name + "Y", ky, fy)) if ay else inp_value(static[1])
        self.add(name, "XYPath", {"ShowKeyPoints": False, "DrawMode": "ModifyOnly",
                                  "Inputs": {"X": ix, "Y": iy}})
        return inp_src(name, "Value")

    # ------------------------------------------------------------ coordinates
    def nx(self, px):
        return px / self.W

    def ny(self, py):
        return 1.0 - py / self.H


def _png_size(path):
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
    except OSError:
        pass
    return None


def _merged_keys(tracks, names):
    times = sorted({k[0] for n in names for k in tracks.get(n, [])})
    return times


def build(spec, kit, asset_root=None):
    c = Comp(spec)
    W, H = c.W, c.H
    dur_frames = c.frame(spec["duration"])
    bg = c.add("Canvas", "Background", {
        "Inputs": {
            "GlobalOut": inp_value(dur_frames),
            "Width": inp_value(W), "Height": inp_value(H),
            "UseFrameFormatSettings": inp_value(1),
            "TopLeftAlpha": inp_value(0.0),
        },
        "ViewInfo": Lua("OperatorInfo { Pos = { 0, 0 } }"),
    })
    below = bg
    x = 110
    for layer in spec["layers"]:
        lid = "".join(ch for ch in layer["id"] if ch.isalnum()) or "Layer"
        tr = layer["tracks"]
        kind = layer.get("type", "text")
        lx, ly = float(layer.get("x", W / 2)), float(layer.get("y", H / 2))
        align = layer.get("align", "left")

        # ---------------- source node
        if kind == "text":
            f = font_for(layer, kit)
            r, g, b, a = resolve_color(layer.get("color", "ink"), kit)
            size = float(layer.get("size", 60))
            track_static = 1.0 + float(layer.get("tracking", 0.0)) * TRACKING_SCALE
            inputs = {
                "GlobalOut": inp_value(dur_frames),
                "Width": inp_value(W), "Height": inp_value(H),
                "UseFrameFormatSettings": inp_value(1),
                "Center": inp_value([c.nx(lx), c.ny(ly)]),
                "StyledText": inp_value(str(layer.get("text", ""))),
                "Font": inp_value(f["family"]),
                "Style": inp_value(f.get("style", "Regular")),
                "Size": inp_value(size * TEXT_SIZE_PER_PX),
                "LineSpacing": inp_value(float(layer.get("leading", 1.0))),
                "CharacterSpacing": c.value_or_spline(lid + "Tracking", tr.get("tracking"),
                                                      lambda v: 1.0 + v * TRACKING_SCALE, track_static),
                "HorizontalLeftCenterRight": inp_value(ANCHOR.get(align, -1)),
                "HorizontalJustificationNew": inp_value({"left": 0, "center": 1, "right": 2}.get(align, 0)),
                "VerticalTopCenterBottom": inp_value(0),
                "VerticalJustificationNew": inp_value(1),
                "Red1": inp_value(r), "Green1": inp_value(g), "Blue1": inp_value(b), "Alpha1": inp_value(a),
            }
            if layer.get("case") == "upper":
                inputs["StyledText"] = inp_value(str(layer.get("text", "")).upper())
            src = c.add(lid, "TextPlus", {"Inputs": inputs, "ViewInfo": Lua(f"OperatorInfo {{ Pos = {{ {x}, -99 }} }}")})
            pivot = [c.nx(lx), c.ny(ly)]
        elif kind == "rect":
            r, g, b, a = resolve_color(layer.get("color", "ink"), kit)
            src = c.add(lid, "Background", {
                "Inputs": {
                    "GlobalOut": inp_value(dur_frames),
                    "Width": inp_value(W), "Height": inp_value(H),
                    "UseFrameFormatSettings": inp_value(1),
                    "TopLeftRed": inp_value(r), "TopLeftGreen": inp_value(g),
                    "TopLeftBlue": inp_value(b), "TopLeftAlpha": inp_value(a),
                },
                "ViewInfo": Lua(f"OperatorInfo {{ Pos = {{ {x}, -99 }} }}"),
            })
            pivot = [c.nx(lx), c.ny(ly)]
        else:  # image
            path = layer["src"]
            if asset_root and not os.path.isabs(path):
                path = os.path.join(asset_root, path)
            path = os.path.abspath(path)
            native = _png_size(path) or (int(layer.get("native_w", 1000)), int(layer.get("native_h", 1000)))
            src = c.add(lid, "Loader", {
                "Clips": Lua("{ Clip { ID = \"Clip1\", Filename = " + lua(path) +
                             ", FormatID = \"PNGFormat\", StartFrame = -1, LengthSetManually = true, TrimIn = 0, "
                             f"TrimOut = 0, ExtendFirst = 0, ExtendLast = {dur_frames}, Loop = 1, AspectMode = 0, "
                             f"Depth = 0, TimeCode = 0, GlobalStart = 0, GlobalEnd = {dur_frames} }}, }}"),
                "Inputs": {"Loop": inp_value(1), "PostMultiplyByAlpha": inp_value(0)},
                "ViewInfo": Lua(f"OperatorInfo {{ Pos = {{ {x}, -99 }} }}"),
            })
            pivot = [0.5, 0.5]
            layer["_img_scale"] = float(layer.get("w", native[0])) / native[0]
        node = src

        # ---------------- blur
        if tr.get("blur"):
            bl = lid + "Blur"
            c.add(bl, "Blur", {"Inputs": {
                "XBlurSize": c.value_or_spline(bl + "Size", tr["blur"], lambda v: v * BLUR_SCALE, 0.0),
                "Input": inp_src(node, "Output"),
            }, "ViewInfo": Lua(f"OperatorInfo {{ Pos = {{ {x}, -66 }} }}")})
            node = bl

        # ---------------- transform (offsets, scale). Images are placed by the Merge instead,
        # because a Transform's Center is relative to its own input (the native-size still).
        merge_place = {}
        if kind == "image":
            base = (c.nx(lx), c.ny(ly))
            s0 = layer["_img_scale"]
            merge_place["Center"] = c.xy_path(lid + "Place", tr.get("dx"), tr.get("dy"),
                                              lambda v: base[0] + v / W, lambda v: base[1] - v / H, base)
            merge_place["Size"] = c.value_or_spline(lid + "PlaceSize", tr.get("scale"), lambda v: v * s0, s0)
        else:
            xf = lid + "Move"
            center = c.xy_path(xf + "Center", tr.get("dx"), tr.get("dy"),
                               lambda v: 0.5 + v / W, lambda v: 0.5 - v / H, (0.5, 0.5))
            size = c.value_or_spline(xf + "Size", tr.get("scale"), lambda v: v, 1.0)
            c.add(xf, "Transform", {"Inputs": {
                "Center": center, "Pivot": inp_value(pivot),
                "Size": size, "Input": inp_src(node, "Output"),
            }, "ViewInfo": Lua(f"OperatorInfo {{ Pos = {{ {x}, -33 }} }}")})
            node = xf

        # ---------------- mask (rect shape, reveal band, wipe)
        mask = None
        if kind == "rect":
            w, h = float(layer.get("w", 200)), float(layer.get("h", 2))
            anchor = layer.get("anchor", "left")
            draw = tr.get("draw") or [[0.0, 1.0]]

            def cx(dv, w=w, anchor=anchor):
                if anchor == "left":
                    return c.nx(lx + w * dv / 2)
                if anchor == "right":
                    return c.nx(lx - w * dv / 2)
                return c.nx(lx)
            mask = lid + "Shape"
            c.add(mask, "RectangleMask", {"Inputs": {
                "MaskWidth": inp_value(W), "MaskHeight": inp_value(H),
                "PixelAspect": inp_value([1, 1]), "ClippingMode": Lua('Input { Value = FuID { "None" }, }'),
                "SoftEdge": inp_value(0.0),
                "CornerRadius": inp_value(float(layer.get("radius", 0)) / max(w, h, 1)),
                "Center": c.xy_path(mask + "Center", draw, None, cx, None, (cx(1.0), c.ny(ly))),
                # CALIBRATE: mask Width/Height assumed relative to frame width.
                "Width": c.value_or_spline(mask + "W", draw, lambda dv: w * dv / W, w / W),
                "Height": inp_value(h / W),
            }, "ViewInfo": Lua(f"OperatorInfo {{ Pos = {{ {x + 55}, 0 }} }}")})
        elif layer.get("clip"):
            tw = estimate_text_width(layer, kit) + 40
            th = text_block_height(layer) * 1.1
            left = {"left": lx - 20, "center": lx - tw / 2, "right": lx - tw + 20}.get(align, lx - 20)
            rev = tr.get("reveal") or [[0.0, 1.0]]
            rout = tr.get("reveal_out") or [[0.0, 0.0]]
            times = sorted({k[0] for k in rev} | {k[0] for k in rout})
            from .spec import sample
            keys_c, keys_w = [], []
            for t in times:
                r = sample(rev, t)
                o = sample(rout, t)
                ease = next((k[2] for k in rev + rout if k[0] == t and len(k) > 2), "glide")
                keys_c.append([t, (left + tw * (o + r) / 2), ease])
                keys_w.append([t, tw * max(0.0, r - o), ease])
            mask = lid + "Band"
            c.add(mask, "RectangleMask", {"Inputs": {
                "MaskWidth": inp_value(W), "MaskHeight": inp_value(H),
                "PixelAspect": inp_value([1, 1]), "ClippingMode": Lua('Input { Value = FuID { "None" }, }'),
                "SoftEdge": inp_value(0.0),
                "Center": c.xy_path(mask + "Center", keys_c, None, lambda v: c.nx(v), None,
                                    (c.nx(keys_c[-1][1] if keys_c else left + tw / 2), c.ny(ly))),
                "Width": c.value_or_spline(mask + "W", keys_w, lambda v: v / W, tw / W),
                "Height": inp_value(th / W),
            }, "ViewInfo": Lua(f"OperatorInfo {{ Pos = {{ {x + 55}, 0 }} }}")})

        # ---------------- merge (opacity)
        mg = lid + "Merge"
        minputs = {
            "Background": inp_src(below, "Output"),
            "Foreground": inp_src(node, "Output"),
            "Blend": c.value_or_spline(mg + "Opacity", tr.get("opacity"), lambda v: v, 1.0),
            "PerformDepthMerge": inp_value(0),
        }
        minputs.update(merge_place)
        if mask:
            minputs["EffectMask"] = inp_src(mask, "Mask")
        c.add(mg, "Merge", {"Inputs": minputs, "ViewInfo": Lua(f"OperatorInfo {{ Pos = {{ {x}, 33 }} }}")})
        below = mg
        x += 110

    c.add("MediaOut1", "MediaOut", {"Inputs": {"Index": inp_value("0"), "Input": inp_src(below, "Output")},
                                     "ViewInfo": Lua(f"OperatorInfo {{ Pos = {{ {x}, 33 }} }}")})
    return c


def _tools_block(c, ind=1):
    pad = "\t" * ind
    out = [f"{pad}Tools = ordered() {{"]
    for name, kind, body in c.tools:
        out.append(f"{pad}\t{name} = {kind} " + lua(body, ind + 1) + ",")
    out.append(f"{pad}}},")
    return "\n".join(out)


def to_comp(c):
    """A full composition file for TimelineItem.ImportFusionComp()."""
    n = c.frame(c.spec["duration"])
    head = (
        "Composition {\n"
        "\tCurrentTime = 0,\n"
        f"\tRenderRange = {{ 0, {max(0, n - 1)} }},\n"
        f"\tGlobalRange = {{ 0, {max(0, n - 1)} }},\n"
        "\tCurrentID = 1,\n"
        "\tHiQ = true,\n"
        "\tPlaybackUpdateMode = 0,\n"
        "\tVersion = \"DaVinci Resolve Fusion\",\n"
        "\tSavedOutputs = 0,\n"
        "\tHeldTools = 0,\n"
        "\tDisabledTools = 0,\n"
        "\tLockedTools = 0,\n"
        "\tAudioOffset = 0,\n"
        "\tResumable = true,\n"
        "\tOutputClips = {\n\t},\n"
    )
    tail = (
        "\n\tPrefs = {\n\t\tComp = {\n\t\t\tFrameFormat = {\n"
        f"\t\t\t\tWidth = {c.W},\n\t\t\t\tHeight = {c.H},\n\t\t\t\tRate = {lua(float(c.fps))},\n"
        "\t\t\t},\n\t\t},\n\t},\n}\n"
    )
    return head + _tools_block(c) + tail


def to_setting(c, active="MediaOut1"):
    """A macro/clipboard file: paste into a Fusion comp, or install as an Edit > Titles template."""
    return "{\n" + _tools_block(c) + f'\n\tActiveTool = "{active}"\n}}\n'


def write(spec, kit, comp_path=None, setting_path=None, asset_root=None):
    c = build(spec, kit, asset_root)
    if comp_path:
        os.makedirs(os.path.dirname(os.path.abspath(comp_path)), exist_ok=True)
        with open(comp_path, "w", encoding="utf-8") as f:
            f.write(to_comp(c))
    if setting_path:
        os.makedirs(os.path.dirname(os.path.abspath(setting_path)), exist_ok=True)
        with open(setting_path, "w", encoding="utf-8") as f:
            f.write(to_setting(c))
    return c
