"""Find colours in source art (sermon art, brand files, footage stills) instead of inventing them.

Reports each cluster's share of the image, Lab lightness/chroma/hue and a suggested role,
plus contrast ratios and warnings for the palettes that read as AI-made.
Requires Pillow.
"""
import json
import math


def srgb_to_lab(rgb):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(float(x)) for x in rgb)
    X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    L = 116 * f(Y) - 16
    a = 500 * (f(X) - f(Y))
    bb = 200 * (f(Y) - f(Z))
    return L, a, bb


def luminance(rgb):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(float(x)) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def hexof(rgb):
    return "#%02X%02X%02X" % tuple(int(x) for x in rgb)


def extract(path, k=8):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im.thumbnail((360, 360))
    q = im.quantize(colors=k, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[: 3 * k]
    counts = sorted(q.getcolors(), reverse=True)
    total = sum(c for c, _ in counts)
    swatches = []
    for c, idx in counts:
        rgb = tuple(pal[3 * idx: 3 * idx + 3])
        L, a, b = srgb_to_lab(rgb)
        chroma = math.hypot(a, b)
        hue = (math.degrees(math.atan2(b, a)) + 360) % 360
        near = next((w for w in swatches if math.dist((L, a, b), w["_lab"]) < 5), None)
        if near:  # merge near-duplicates (paper grain, compression noise)
            near["share"] = round(near["share"] + c / total, 3)
            continue
        swatches.append({"hex": hexof(rgb), "rgb": rgb, "share": round(c / total, 3),
                         "L": round(L, 1), "chroma": round(chroma, 1), "hue": round(hue), "_lab": (L, a, b)})
    for w in swatches:
        w.pop("_lab")
    return swatches


def neutral_ink(ground_rgb, light=False):
    """A near-neutral ink carrying a whisper of the ground's hue (type stays neutral)."""
    L, a, b = srgb_to_lab(ground_rgb)
    k = 0.12
    target_L = 96 if light else 14
    return lab_to_hex(target_L, a * k, b * k)


def lab_to_hex(L, a, b):
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200

    def inv(t):
        return t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    X, Y, Z = inv(fx) * 0.95047, inv(fy), inv(fz) * 1.08883
    r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z
    g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
    bb = 0.0557 * X - 0.2040 * Y + 1.0570 * Z

    def gam(c):
        c = max(0.0, min(1.0, c))
        return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return hexof([round(gam(c) * 255) for c in (r, g, bb)])


def suggest_roles(sw):
    """A starting point only: the designer decides. Value first, scarce accent, neutral type."""
    by_share = sorted(sw, key=lambda s: -s["share"])
    # Keep it light: the ground is the lightest colour with a real presence (>= 10 %), if it is light;
    # otherwise the dominant colour (dark art stays dark only when the art itself is dark).
    big = [s for s in by_share if s["share"] >= 0.10]
    light = max(big, key=lambda s: s["L"], default=None)
    ground = light if light and light["L"] >= 70 else by_share[0]
    rest = [s for s in sw if s is not ground]
    ink = max(rest, key=lambda s: contrast(s["rgb"], ground["rgb"])) if rest else ground
    surface = min((s for s in rest if s is not ink), key=lambda s: abs(s["L"] - ground["L"]) + s["chroma"] * 0.3,
                  default=ground)
    derived_ink = contrast(ink["rgb"], ground["rgb"]) < 4.5
    accent_pool = [s for s in rest if s is not surface and (derived_ink or s is not ink) and s["chroma"] > 20]
    accent = max(accent_pool, key=lambda s: s["chroma"] * (1 - s["share"]), default=None)
    roles = {"ground": ground["hex"], "surface": surface["hex"], "ink": ink["hex"]}
    if derived_ink:  # the art has no usable type colour: derive a neutral one
        roles["ink"] = neutral_ink(ground["rgb"], light=ground["L"] < 50)
        roles["ink_note"] = "derived: no colour in the art reaches 4.5:1 on the ground"
    if accent:
        roles["accent"] = accent["hex"]
    return roles


def warnings(roles):
    """Flag the house looks that make a piece read as generated (references/anti-patterns.md)."""
    w = []

    def lab(h):
        return srgb_to_lab(tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)))
    g = lab(roles["ground"])
    acc = lab(roles["accent"]) if roles.get("accent") else None
    ink = lab(roles["ink"])
    if g[0] < 20 and acc and math.hypot(acc[1], acc[2]) > 45:
        w.append("near-black ground + saturated accent: the high-contrast 'AI' look. Lighten the ground or mute the accent.")
    if g[0] < 20:
        w.append("dark ground: the brief is 'keep it light'. Use only if the sermon art itself is dark, and say so.")
    if acc:
        hue = (math.degrees(math.atan2(acc[2], acc[1])) + 360) % 360
        if g[0] < 25 and 20 <= hue <= 70:
            w.append("dark ground + warm orange/amber accent: a known generated house look.")
        if g[0] > 88 and 20 <= hue <= 50 and math.hypot(g[1], g[2]) > 6:
            w.append("cream ground + terracotta accent: a known generated house look.")
        if 95 <= hue <= 135 and math.hypot(acc[1], acc[2]) > 50:
            w.append("acid lime/green accent: a known generated house look.")
    if ink[0] > 85 and math.hypot(ink[1], ink[2]) > 8:
        w.append("tinted (cream/bone) type: keep type neutral white or neutral dark.")
    return w


def report(path, k=8):
    sw = extract(path, k)
    roles = suggest_roles(sw)
    rgb = {r: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for r, h in roles.items() if h.startswith("#")}
    out = {
        "source": path,
        "swatches": sw,
        "suggested_roles": roles,
        "contrast": {"ink_on_ground": round(contrast(rgb["ink"], rgb["ground"]), 2),
                     "white_on_ground": round(contrast((255, 255, 255), rgb["ground"]), 2)},
        "warnings": warnings(roles),
    }
    return out


def swatch_png(sw, out_path, w=1200, h=180):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    x = 0
    for s in sw:
        ww = max(4, int(round(s["share"] * w)))
        d.rectangle([x, 0, x + ww, h], fill=s["hex"])
        x += ww
    im.save(out_path)


if __name__ == "__main__":
    import sys
    print(json.dumps(report(sys.argv[1]), indent=1))
