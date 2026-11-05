"""Restraint checks: catch over-animation, unreadable holds and drift from the kit before anyone sees it.

Errors are rule breaks (fix before showing). Warnings are judgement calls (look, decide, note why).
"""
import re

from .spec import (sample, TREATMENTS_IN, ALLOWED_IN, ALLOWED_OUT, subtitle_style, text_safe_box,
                   estimate_text_width, text_block_height)

MOVING = ("dx", "dy", "scale", "blur", "tracking", "reveal", "draw")


def _visible_window(tr, duration):
    """First time fully opaque and last time fully opaque (the readable hold)."""
    op = tr.get("opacity") or [[0, 1]]
    times = [i / 100 * duration for i in range(101)]
    full = [t for t in times if sample(op, t) >= 0.98]
    if not full:
        return None
    return full[0], full[-1]


def lint_spec(spec, kit):
    errs, warns = [], []
    W, H = spec["width"], spec["height"]
    safe = float(((kit or {}).get("layout") or {}).get("safe", 0.06))
    dur = float(spec["duration"])
    roles = set(((kit or {}).get("palette") or {}).keys())
    sid = spec.get("id", "?")
    is_sub = spec.get("kind") == "subtitle"

    for L in spec["layers"]:
        tr = L["tracks"]
        lid = f"{sid}/{L['id']}"
        if L.get("box") and len(L["box"]) == 4:
            bx, by, bw, bh = (float(v) for v in L["box"])
            if bx < -1 or by < -1 or bx + bw > W + 1 or by + bh > H + 1:
                warns.append(f"{lid}: box [{bx:.0f},{by:.0f},{bw:.0f},{bh:.0f}] runs off the {W}x{H} frame.")
        tin_ = (L.get("in") or {}).get("treatment", "cut")
        tout_ = (L.get("out") or {}).get("treatment", "cut")
        if tin_ not in ALLOWED_IN:
            errs.append(f"{lid}: entrance '{tin_}' breaks the animation rule. Use {sorted(ALLOWED_IN)}.")
        if tout_ not in ALLOWED_OUT:
            errs.append(f"{lid}: exit '{tout_}' breaks the animation rule. Use {sorted(ALLOWED_OUT)}.")
        for p in ("tracking", "blur", "reveal", "draw"):
            if p in (L.get("anim") or {}):
                errs.append(f"{lid}: custom '{p}' animation breaks the animation rule (collage, paper, a light move with opacity, or none).")
        for p, keys in (L.get("anim") or {}).items():
            if p in ("dx", "dy") and any(abs(k[1]) > 60 for k in keys):
                warns.append(f"{lid}: {p} travels more than 60 px; movement onto the screen should stay light.")
        moving_in = [p for p in MOVING if p in tr and len(tr[p]) > 1 and tr[p][0][0] < dur * 0.5]
        if len(moving_in) > 2 and not L.get("allow_busy"):
            errs.append(f"{lid}: {len(moving_in)} properties move on entrance ({', '.join(moving_in)}). Max 2 incl. one move: over-animation.")
        for p, keys in tr.items():
            for a, b in zip(keys, keys[1:]):
                span = b[0] - a[0]
                if p != "opacity" and 0 < span < 0.2 and abs(b[1] - a[1]) > 1e-6:
                    warns.append(f"{lid}: {p} changes in {span:.2f}s: reads as a jolt; restraint wants >= 0.25s.")
                if span > 2.5 and p in ("dx", "dy", "scale") and abs(b[1] - a[1]) > 1e-6:
                    warns.append(f"{lid}: {p} drifts for {span:.1f}s: make sure the drift is intended (breathe), not a slow entrance.")
        if L.get("type", "text") == "text":
            text = str(L.get("text", ""))
            size = float(L.get("size", 60))
            if size < 28 * min(W, H) / 1080 and not L.get("small"):
                errs.append(f"{lid}: text size {size}px is below 28px at 1080p (mark small:true for labels >= 22px).")
            win = _visible_window(tr, dur)
            words = len(re.findall(r"\w+", text))
            need = max(1.2, 0.3 * words + 0.6) if not is_sub else 0.3
            if win and (win[1] - win[0]) < need:
                errs.append(f"{lid}: fully readable for {win[1] - win[0]:.2f}s; {words} words need ~{need:.1f}s.")
            if not is_sub and words > 14:
                warns.append(f"{lid}: {words} words on one layer. B-roll text should be a phrase, not a paragraph.")
        x, y = float(L.get("x", W / 2)), float(L.get("y", H / 2))
        if not is_sub and not L.get("box") and L.get("type", "text") != "text" and (x < W * safe - 1 or x > W * (1 - safe) + 1 or y < H * safe - 1 or y > H * (1 - safe) + 1):
            warns.append(f"{lid}: anchor ({x:.0f},{y:.0f}) is outside the {int(safe * 100)}% safe area.")
        if not is_sub and L.get("type", "text") == "text" and not L.get("allow_unsafe"):
            sl, st_, sr, sb = text_safe_box(W, H, kit)
            tw = estimate_text_width(L, kit) / 1.08
            th = text_block_height(L) * float(L.get("leading", 1.0)) / 1.25 * 1.1
            align = L.get("align", "left")
            x0 = x if align == "left" else x - tw / 2 if align == "center" else x - tw
            x1, y0, y1 = x0 + tw, y - th / 2, y + th / 2
            if x0 < sl - 1 or x1 > sr + 1 or y0 < st_ - 1 or y1 > sb + 1:
                errs.append(f"{lid}: text at x {x0:.0f}-{x1:.0f}, y {y0:.0f}-{y1:.0f} leaves the safe area "
                            f"(x {sl:.0f}-{sr:.0f}, y {st_:.0f}-{sb:.0f}). Move it, break the line or shrink it.")
        st = subtitle_style(kit, W, H) if (kit or {}).get("subtitles") else None
        if st and not is_sub and L.get("type", "text") == "text":
            band_top = float(st.get("y", H * 0.86)) - float(st.get("size", 46)) * 0.9
            bottom = y + float(L.get("size", 60)) * 0.6 * (str(L.get("text", "")).count("\n") + 1)
            if bottom > band_top:
                errs.append(f"{lid}: sits in the subtitle band (bottom ~{bottom:.0f}px > {band_top:.0f}px). Move it up; subtitles own the bottom.")
        col = str(L.get("color", "ink")).split("@")[0]
        if roles and col.startswith("#") and not is_sub:
            warns.append(f"{lid}: literal colour {col}; use a kit role so the series stays one system.")
        if L.get("in", {}).get("treatment") == "focus":
            warns.append(f"{lid}: 'focus' (blur-in) is a generated-motion cliche as a default. Keep it to one per video, with a reason.")

    # how many layers are on screen at once
    peak = 0
    for i in range(101):
        t = i / 100 * dur
        # a split-screen panel is the ground the idea sits on, not one of its layers
        n = sum(1 for L in spec["layers"] if not L.get("panel")
                and sample(L["tracks"].get("opacity") or [[0, 1]], t) > 0.05)
        peak = max(peak, n)
    if peak > 4 and not is_sub:
        errs.append(f"{sid}: {peak} layers visible at once. One idea per graphic: max 4 (text + rule + label + brand).")
    return errs, warns


def lint_project(specs):
    """Across all graphics in one video: treatment variety, cliche budget, one clip at a time on the track."""
    errs, warns = [], []
    placed = sorted((float(s["in"]), float(s["in"]) + float(s["duration"]), s.get("id")) for s in specs if s.get("kind") != "subtitle" and "in" in s)
    for (a0, a1, an), (b0, b1, bn) in zip(placed, placed[1:]):
        if b0 < a1 - 1e-3:
            errs.append(f"{an} and {bn} overlap by {a1 - b0:.2f}s. Each graphic is its own clip on the graphics track.")
    tin = [L.get("in", {}).get("treatment", "cut") for s in specs if s.get("kind") != "subtitle" for L in s["layers"]
           if L.get("type", "text") == "text"]
    if tin:
        for t in set(tin):
            share = tin.count(t) / len(tin)
            if len(tin) >= 5 and share > 0.5:
                warns.append(f"entrance '{t}' is {share:.0%} of text entrances; vary it so no move becomes the video's tic.")
        if tin.count("focus") > 1:
            errs.append(f"'focus' entrance used {tin.count('focus')} times; budget is 1 per video.")
    texts = [str(L.get("text", "")).strip().lower() for s in specs if s.get("kind") != "subtitle" for L in s["layers"]
             if L.get("type", "text") == "text" and L.get("text")]
    dup = {t for t in texts if texts.count(t) > 1 and len(t) > 3}
    for d in dup:
        warns.append(f"the same text appears in more than one graphic: {d!r}")
    return errs, warns
