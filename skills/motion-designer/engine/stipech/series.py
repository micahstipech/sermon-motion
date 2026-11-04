"""The series folder: the one standard way a new sermon series arrives.

    Sermon Series/
      <Series Name>/
        Background.(jpg|png)        large square texture; more allowed: "Background 2", "Background - Paper", ...
        Colors.(jpg|png)            photo whose colours the series uses (analysed, then picked from)
        *.ttf / *.otf               the series fonts (any names; a Fonts/ subfolder is fine too)
        Example.png                 everything used together: the reference for how assets combine
        Assets/                     transparent PNGs: icons, logos, title cards, other art elements
        kit.json                    written by us: the series style kit (draft first, then approved)
        _stipech/                   written by us: inventory, colour analysis, swatches

`scan` inventories the folder and lists what is missing or unusable, worded as questions for the
user. `draft_kit` turns the inventory into a draft kit.json for the designer to finish.
"""
import json
import os
import re

from .spec import image_size

IMG = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp")
FONT_OK = (".ttf", ".otf")
FONT_WEB = (".woff", ".woff2")
WORK = "_stipech"


def _stem(name):
    return os.path.splitext(name)[0].strip().lower()


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "asset"


def _alpha_info(path):
    """(has_alpha_channel, share_of_transparent_pixels) using Pillow; (None, None) without it."""
    try:
        from PIL import Image
    except ImportError:
        return None, None
    with Image.open(path) as im:
        if im.mode not in ("RGBA", "LA", "PA") and not (im.mode == "P" and "transparency" in im.info):
            return False, 0.0
        a = im.convert("RGBA").getchannel("A")
        a.thumbnail((256, 256))
        px = list(a.getdata())
        return True, sum(1 for v in px if v < 250) / max(1, len(px))


def _font_names(path):
    """(family, style, avg_char) where avg_char is the mean glyph advance in em for running text."""
    try:
        from PIL import ImageFont
        f = ImageFont.truetype(path, 100)
        fam, style = f.getname()
        sample = "The Lord is my shepherd I shall not want grace roots"
        avg = f.getlength(sample) / (len(sample) * 100)
        return fam, style, round(avg, 3)
    except Exception:
        return None, None, None


def _asset_kind(stem):
    for kind, words in (("logo", ("logo", "lockup", "wordmark", "mark")),
                        ("title", ("title", "card", "series")),
                        ("icon", ("icon", "symbol", "glyph"))):
        if any(w in stem for w in words):
            return kind
    return "element"


def scan(folder):
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"series folder not found: {folder}")
    inv = {"series": os.path.basename(folder), "folder": folder, "backgrounds": [], "colors": None,
           "example": None, "fonts": [], "web_fonts": [], "assets": [], "other": [],
           "missing": [], "problems": []}
    files = []
    for root, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs if d != WORK and not d.startswith(".")]
        for n in names:
            if not n.startswith(".") and n != "kit.json":
                files.append(os.path.relpath(os.path.join(root, n), folder))
    def order(rel):  # "Background" before "Background 2"; natural number order
        stem = _stem(os.path.basename(rel))
        return (os.path.dirname(rel).lower(), [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", stem)])
    for rel in sorted(files, key=order):
        name = os.path.basename(rel)
        stem, ext = _stem(name), os.path.splitext(name)[1].lower()
        top = rel.replace("\\", "/").split("/")[0].lower()
        full = os.path.join(folder, rel)
        if top == "assets" and ext in IMG:
            w, h = image_size(full) or (None, None)
            has_a, clear = _alpha_info(full)
            a = {"id": _slug(stem), "file": rel.replace("\\", "/"), "kind": _asset_kind(stem), "w": w, "h": h,
                 "alpha": has_a, "transparent_share": None if clear is None else round(clear, 2)}
            if ext != ".png":
                inv["problems"].append(f"Assets/{name} is not a PNG. Can I get it as a transparent PNG?")
            elif has_a is False or (clear is not None and clear < 0.01):
                inv["problems"].append(f"Assets/{name} has no transparency. Is there a transparent PNG version?")
            inv["assets"].append(a)
        elif ext in IMG and (stem.startswith("background") or top in ("backgrounds", "background")):
            w, h = image_size(full) or (None, None)
            b = {"id": _slug(stem), "file": rel.replace("\\", "/"), "w": w, "h": h}
            if w and h:
                if abs(w - h) / max(w, h) > 0.02:
                    inv["problems"].append(f"{name} is {w}×{h}, not square. Fine to use (cover crop), but is a square version available?")
                if min(w, h) < 2160:
                    inv["problems"].append(f"{name} is only {min(w, h)}px on its short side; a full-frame card crops into it. A 3000px+ version would hold up better.")
            inv["backgrounds"].append(b)
        elif ext in IMG and stem in ("colors", "colours", "color", "colour", "color palette", "colors palette"):
            inv["colors"] = rel.replace("\\", "/")
        elif ext in IMG and stem.startswith("example"):
            inv["example"] = rel.replace("\\", "/")
        elif ext in FONT_OK:
            fam, style, avg = _font_names(full)
            inv["fonts"].append({"file": rel.replace("\\", "/"), "family": fam, "style": style, "avg_char": avg})
        elif ext in FONT_WEB:
            inv["web_fonts"].append(rel.replace("\\", "/"))
        elif ext in (".txt", ".md", ".pdf", ".rtf", ".html") or stem.startswith(("license", "ofl", "readme")):
            pass  # licences and notes travel with the fonts; nothing to do
        else:
            inv["other"].append(rel.replace("\\", "/"))

    if not inv["backgrounds"]:
        inv["missing"].append("Background: a large square texture named 'Background' (more are welcome: 'Background 2', …).")
    if not inv["colors"]:
        inv["missing"].append("Colors: a photo named 'Colors' whose colours the series should use.")
    if not inv["fonts"]:
        if inv["web_fonts"]:
            inv["missing"].append("Fonts: only web fonts (.woff/.woff2) were found. Resolve needs installable .ttf or .otf files of the same fonts.")
        else:
            inv["missing"].append("Fonts: the series font files (.ttf or .otf).")
    has_assets_dir = any(d.lower() == "assets" and os.path.isdir(os.path.join(folder, d)) for d in os.listdir(folder))
    if not has_assets_dir:
        inv["missing"].append("Assets: a folder named 'Assets' with the transparent PNGs from the series art (icons, logos, title cards).")
    elif not inv["assets"]:
        inv["missing"].append("Assets: the 'Assets' folder is empty. Are there icons, logos or title cards from the series art?")
    if not inv["example"]:
        inv["missing"].append("Example: a PNG named 'Example' showing everything used together.")
    if inv["other"]:
        inv["problems"].append("Not recognised (ignored unless you say what they are): " + ", ".join(inv["other"][:12]))

    os.makedirs(os.path.join(folder, WORK), exist_ok=True)
    with open(os.path.join(folder, WORK, "inventory.json"), "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=1)
    return inv


def analyse_colors(inv, k=10):
    """Palette analysis of the Colors photo (and a cross-check against the backgrounds)."""
    from . import palette
    folder = inv["folder"]
    out = {}
    if inv.get("colors"):
        rep = palette.report(os.path.join(folder, inv["colors"]), k)
        palette.swatch_png(rep["swatches"], os.path.join(folder, WORK, "colors-swatch.png"))
        out["colors"] = rep
    for b in inv.get("backgrounds", []):
        rep = palette.report(os.path.join(folder, b["file"]), 6)
        out.setdefault("backgrounds", {})[b["id"]] = {"swatches": rep["swatches"], "suggested_roles": rep["suggested_roles"]}
    with open(os.path.join(folder, WORK, "palette.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    return out


DEFAULT_MOTION = {"tempo": 1.1, "distance": 18, "ease_in": "settle", "ease_out": "exit", "notes": "draft: set from the art"}
DEFAULT_SUBS = {"font": "subtitle", "size": 46, "color": "#FAF9F6", "y": 940, "shadow": True,
                "shadow_color": "#000000@35", "shadow_blur": 6, "max_words": 3, "max_chars": 24,
                "punctuation": "drop-trailing", "case": "as-spoken"}


def draft_kit(inv, analysis):
    """A starting kit from the folder. Every value marked draft is a decision for the designer."""
    colors = (analysis or {}).get("colors") or {}
    roles = dict(colors.get("suggested_roles") or {})
    src = inv.get("colors") or "?"
    share = {s["hex"]: s["share"] for s in colors.get("swatches", [])}
    pal = {}
    for role in ("ground", "surface", "ink", "accent"):
        if roles.get(role):
            h = roles[role]
            note = f"{src} {h} ({share[h] * 100:.0f}%)" if h in share else f"derived ({roles.get('ink_note', '')})"
            pal[role] = {"hex": h, "from": note}
    pal["light"] = {"hex": "#FAF9F6", "from": "type over footage: near-white, neutral"}

    fonts = inv.get("fonts", [])

    def pick(pref):
        for p in pref:
            for f in fonts:
                if (f.get("style") or "").lower() == p:
                    return f
        return fonts[0] if fonts else None
    display = pick(["regular", "book", "medium", "bold"])
    text = pick(["medium", "regular", "book"])
    types = {}
    for role, f in (("display", display), ("text", text), ("subtitle", text)):
        if f:
            types[role] = {"family": f.get("family") or "?", "style": f.get("style") or "Regular",
                           "weight": 500 if (f.get("style") or "").lower() == "medium" else 400,
                           "file": f["file"], "avg_char": f.get("avg_char") or 0.53, "use": "draft"}
    return {
        "series": inv["series"],
        "draft": True,
        "personality": "draft: one sentence from the art and Example.png",
        "sources": {"backgrounds": [b["file"] for b in inv.get("backgrounds", [])], "colors": inv.get("colors"),
                    "example": inv.get("example"), "fonts": [f["file"] for f in fonts],
                    "assets": [a["file"] for a in inv.get("assets", [])]},
        "palette": pal,
        "color_analysis": {"image": inv.get("colors"), "swatches": colors.get("swatches", []),
                           "warnings": colors.get("warnings", [])},
        "textures": [{"id": b["id"], "file": b["file"], "w": b.get("w"), "h": b.get("h"),
                      "use": "draft: full-frame cards" if i == 0 else "draft: alternate"} for i, b in enumerate(inv.get("backgrounds", []))],
        "assets": [{"id": a["id"], "file": a["file"], "kind": a["kind"], "w": a.get("w"), "h": a.get("h"),
                    "use": "draft"} for a in inv.get("assets", [])],
        "available_fonts": fonts,
        "type": types,
        "scale": {"title": 84, "phrase": 64, "label": 30, "subtitle": 46},
        "motion": dict(DEFAULT_MOTION),
        "layout": {"safe": 0.07, "zones": ["lower-left", "upper-left", "center", "right-third"]},
        "subtitles": dict(DEFAULT_SUBS),
        "signature_moves": ["draft: 3-5 rules read from Example.png"],
        "avoid": ["draft"],
    }


def summary(inv):
    lines = [f"Series: {inv['series']}  ({inv['folder']})"]
    lines.append(f"  backgrounds: {len(inv['backgrounds'])}  " + ", ".join(
        f"{b['file']} {b.get('w')}×{b.get('h')}" for b in inv["backgrounds"]))
    lines.append(f"  colors:      {inv['colors'] or '—'}")
    lines.append(f"  example:     {inv['example'] or '—'}")
    lines.append(f"  fonts:       " + (", ".join(f"{f['family']} {f['style']} ({f['file']})" for f in inv["fonts"]) or "—"))
    kinds = {}
    for a in inv["assets"]:
        kinds[a["kind"]] = kinds.get(a["kind"], 0) + 1
    lines.append(f"  assets:      {len(inv['assets'])} " + (str(kinds) if kinds else ""))
    for m in inv["missing"]:
        lines.append("MISSING  " + m)
    for p in inv["problems"]:
        lines.append("CHECK    " + p)
    if not inv["missing"] and not inv["problems"]:
        lines.append("Complete.")
    return "\n".join(lines)
