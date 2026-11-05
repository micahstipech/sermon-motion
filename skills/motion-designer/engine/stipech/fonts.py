"""Fallback type: Roboto Condensed from Google Fonts, used when a series has no usable fonts.

"Usable" means installable (.ttf/.otf), readable, and legible at the sizes the role needs. When the
series fonts fail that, the role falls back to Roboto Condensed (display, text and subtitle alike, or
only the roles the series font can't carry). The files are downloaded as TrueType (Fusion needs
installable fonts), cached in ~/.sermon-motion/fonts/, and copied into the series folder's Fonts/
so the package carries them to the editing PC.
"""
import os
import re
import shutil
import urllib.request

FALLBACK_FAMILY = "Roboto Condensed"
# (italic, weight) -> file style name
FALLBACK_STYLES = {(0, 400): "Regular", (0, 500): "Medium", (0, 700): "Bold", (1, 400): "Italic"}
CACHE = os.path.expanduser("~/.sermon-motion/fonts")
CSS_URL = "https://fonts.googleapis.com/css2?family={family}:ital,wght@{axes}"
# Google Fonts serves .ttf to clients it does not recognise as a modern browser (woff2 otherwise).
UA = "sermon-motion/1.0"


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def download_google_font(family=FALLBACK_FAMILY, styles=FALLBACK_STYLES, cache=CACHE):
    """Download TTFs for `family` (cached). Returns [(path, style_name, weight, italic)]."""
    slug = family.replace(" ", "")
    cdir = os.path.join(cache, slug)
    want = {k: os.path.join(cdir, f"{slug}-{v}.ttf") for k, v in styles.items()}
    if all(os.path.exists(p) for p in want.values()):
        return [(want[k], styles[k], k[1], bool(k[0])) for k in styles]
    os.makedirs(cdir, exist_ok=True)
    axes = ";".join(f"{i},{w}" for i, w in sorted(styles))
    css = _get(CSS_URL.format(family=family.replace(" ", "+"), axes=axes)).decode("utf-8")
    got = []
    for block in re.findall(r"@font-face\s*{(.*?)}", css, re.S):
        ital = 1 if re.search(r"font-style:\s*italic", block) else 0
        weight = int(re.search(r"font-weight:\s*(\d+)", block).group(1))
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        key = (ital, weight)
        if key not in styles:
            continue
        data = _get(url)
        if data[:4] not in (b"\x00\x01\x00\x00", b"true", b"OTTO"):
            raise RuntimeError(f"Google Fonts returned a non-TrueType file for {family} {styles[key]} ({url})")
        with open(want[key], "wb") as f:
            f.write(data)
        got.append((want[key], styles[key], weight, bool(ital)))
    if len(got) < len(styles):
        missing = [styles[k] for k in styles if not os.path.exists(want[k])]
        raise RuntimeError(f"Google Fonts did not return {family}: {', '.join(missing)}")
    return got


def install_fallback(series_folder, family=FALLBACK_FAMILY):
    """Copy the fallback TTFs into <series>/Fonts/ and return font records like the scan's."""
    from .series import _font_names
    files = download_google_font(family)
    dest = os.path.join(series_folder, "Fonts")
    os.makedirs(dest, exist_ok=True)
    out = []
    for path, style, weight, italic in files:
        target = os.path.join(dest, os.path.basename(path))
        if not os.path.exists(target):
            shutil.copy2(path, target)
        fam, sty, avg = _font_names(target)
        out.append({"file": os.path.relpath(target, series_folder).replace("\\", "/"),
                    "family": fam or family, "style": sty or style, "weight": weight,
                    "avg_char": avg, "fallback": True})
    return out


def fallback_roles(fonts, roles=("display", "text", "subtitle")):
    """Kit type roles built from fallback font records (Medium for text/subtitles, Bold for display)."""
    by = {f["style"]: f for f in fonts}

    def role(f, use):
        return {"family": f["family"], "style": f["style"], "weight": f.get("weight", 400), "file": f["file"],
                "avg_char": f.get("avg_char") or 0.45, "fallback": True, "use": use}
    table = {
        "display": role(by.get("Bold") or by.get("Medium") or fonts[0], "titles (fallback: Roboto Condensed Bold)"),
        "italic": role(by.get("Italic") or fonts[0], "the human word (fallback)"),
        "text": role(by.get("Medium") or by.get("Regular") or fonts[0], "labels, references (fallback)"),
        "subtitle": role(by.get("Medium") or by.get("Regular") or fonts[0], "subtitles (fallback)"),
    }
    return {r: table[r] for r in roles}
