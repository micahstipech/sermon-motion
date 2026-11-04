"""Approval pages: the storyboard (gate 1) and the mood board (gate 2).

Both are single HTML files that reference images/videos by relative path, so the folder can be
opened locally or published (with its files) as a private page for review on a phone.
"""
import html
import json
import os

from . import html as htmlmod

CSS = """
:root{--bg:#F6F5F2;--card:#FFFFFF;--ink:#17181A;--muted:#6B6C70;--line:#E3E1DC;--chip:#EFEDE8;--warn:#8A5A00;--err:#A12B1F;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17181A;--card:#202124;--ink:#EDEDEB;--muted:#9C9DA1;--line:#34353A;--chip:#2A2B2F;--warn:#E3B24D;--err:#F08A7E;}}
:root[data-theme="dark"]{--bg:#17181A;--card:#202124;--ink:#EDEDEB;--muted:#9C9DA1;--line:#34353A;--chip:#2A2B2F;--warn:#E3B24D;--err:#F08A7E;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif}
main{max-width:1180px;margin:0 auto;padding:40px 16px 80px}
h1{font-size:28px;line-height:1.2;margin:0 0 6px;font-weight:650;letter-spacing:-.01em}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:40px 0 12px;font-weight:600}
.meta{color:var(--muted);display:flex;flex-wrap:wrap;gap:6px 18px}
.lede{font-size:18px;margin:18px 0 0;max-width:760px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.grid{display:grid;gap:14px}
.beat{display:grid;grid-template-columns:200px 1fr;gap:16px;align-items:start}
.beat img{width:100%;border-radius:8px;display:block;background:var(--chip);aspect-ratio:16/9;object-fit:cover}
.tc{font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted)}
.num{font-weight:650;margin-right:8px;color:var(--ink)}
.line{font-style:italic;margin:6px 0}
.shows{font-size:17px;font-weight:600;margin:6px 0}
.why{color:var(--muted);margin:4px 0}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.chip{background:var(--chip);border-radius:999px;padding:2px 10px;font-size:12px}
.nothing{opacity:.62}
.issues li{margin:4px 0}.err{color:var(--err)}.warn{color:var(--warn)}
svg.strip{width:100%;height:46px;display:block}
.sw{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
.sw .chipc{height:84px;border-radius:8px;border:1px solid var(--line)}
.media{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.media img,.media video{width:100%;border-radius:8px;display:block;background:#888}
.spec{font-size:44px;line-height:1.15;margin:4px 0 2px;word-break:break-word}
ul.plain{margin:0;padding-left:18px}
.checker{background-color:#fff;background-image:linear-gradient(45deg,#e6e6e6 25%,transparent 25%,transparent 75%,#e6e6e6 75%),linear-gradient(45deg,#e6e6e6 25%,transparent 25%,transparent 75%,#e6e6e6 75%);background-size:20px 20px;background-position:0 0,10px 10px;border-radius:8px;padding:12px}
.assets{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}
.assets img{width:100%;height:150px;object-fit:contain;display:block}
.picked{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px}
.picked .chipc{height:56px}
.unused{opacity:.45}
.draft{background:var(--warn);color:var(--bg);padding:8px 12px;border-radius:8px;margin:12px 0;font-weight:600}
.approve{margin-top:40px;padding:16px;border-left:3px solid var(--ink);background:var(--card)}
@media (max-width:640px){.beat{grid-template-columns:1fr}.spec{font-size:32px}}
"""


def _e(x):
    return html.escape(str(x if x is not None else ""))


def _tc(t, fps=None):
    t = float(t)
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:05.2f}"


def _rel(path, out_dir):
    if not path:
        return ""
    return os.path.relpath(os.path.abspath(path), out_dir).replace(os.sep, "/")


def _issues(errs, warns):
    if not errs and not warns:
        return '<p class="meta">Variation check: clean against recent videos.</p>'
    items = [f'<li class="err">{_e(e)}</li>' for e in errs] + [f'<li class="warn">{_e(w)}</li>' for w in warns]
    return f'<ul class="issues">{"".join(items)}</ul>'


def storyboard(board, out_path, base_dir, ledger_issues=([], [])):
    out_dir = os.path.dirname(os.path.abspath(out_path))
    dur = float(board.get("duration") or max([b.get("out", 0) for b in board.get("beats", [])] + [1]))
    beats = board.get("beats", [])
    shown = [b for b in beats if b.get("kind") not in (None, "nothing")]
    rects = []
    for b in beats:
        if b.get("kind") in (None, "nothing"):
            continue
        x = 100 * float(b["in"]) / dur
        w = max(0.4, 100 * (float(b["out"]) - float(b["in"])) / dur)
        rects.append(f'<rect x="{x:.2f}%" y="10" width="{w:.2f}%" height="26" rx="3" fill="currentColor" opacity=".75"><title>{_e(b.get("id"))} {_e(b.get("shows", ""))}</title></rect>')
    strip = f'<svg class="strip" role="img" aria-label="Where graphics land in the video"><rect x="0" y="22" width="100%" height="2" fill="currentColor" opacity=".2"/>{"".join(rects)}</svg>'

    def card(b, label=None):
        cls = "card beat nothing" if b.get("kind") in (None, "nothing") else "card beat"
        img = b.get("thumb")
        thumb = f'<img src="{_e(_rel(os.path.join(base_dir, img), out_dir))}" alt="">' if img else '<div></div>'
        chips = []
        for k, lab in (("kind", ""), ("treatment_in", "in: "), ("treatment_out", "out: "), ("zone", "")):
            if b.get(k):
                chips.append(f'<span class="chip">{lab}{_e(b[k])}</span>')
        if b.get("brand"):
            chips.append('<span class="chip">brand asset</span>')
        head = f'<span class="num">{_e(label or b.get("id", ""))}</span>' + (
            f'{_tc(b["in"])} – {_tc(b["out"])} · {float(b["out"]) - float(b["in"]):.1f}s' if "in" in b else "")
        body = f'<div class="tc">{head}</div>'
        if b.get("line"):
            body += f'<p class="line">“{_e(b["line"])}”</p>'
        if b.get("kind") in (None, "nothing"):
            body += f'<p class="why">Left on the speaker. {_e(b.get("purpose", ""))}</p>'
        else:
            body += f'<p class="shows">{_e(b.get("shows", ""))}</p><p class="why">{_e(b.get("purpose", ""))}</p>'
        if b.get("notes"):
            body += f'<p class="why">{_e(b["notes"])}</p>'
        body += f'<div class="chips">{"".join(chips)}</div>'
        return f'<div class="{cls}">{thumb}<div>{body}</div></div>'

    ends = ""
    for key, lab in (("intro", "Intro"), ("outro", "Outro")):
        if board.get(key):
            ends += card(board[key], lab)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Storyboard {_e(board.get('project', ''))}</title><style>{CSS}</style></head><body><main>
<p class="tc">Storyboard · gate 1 of 2</p>
<h1>{_e(board.get('project', 'Untitled'))}</h1>
<div class="meta"><span>Series: {_e(board.get('series', '—'))}</span><span>Arc: {_e(board.get('arc', '—'))}</span>
<span>Density: {_e(board.get('density', '—'))}</span><span>{len(shown)} graphics · {len(beats) - len(shown)} left on the speaker</span>
<span>Subtitles: {_e('on, 2–3 words' if (board.get('subtitles') or {}).get('on', True) else 'off')}</span></div>
<p class="lede">{_e(board.get('message', ''))}</p>
<h2>Where graphics land</h2><div class="card">{strip}<div class="tc">0:00 – {_tc(dur)}</div></div>
{('<h2>Intro and outro</h2><div class="grid">' + ends + '</div>') if ends else ''}
<h2>Beats</h2><div class="grid">{''.join(card(b) for b in beats)}</div>
<h2>Variation check</h2>{_issues(*ledger_issues)}
<div class="approve"><strong>To approve:</strong> reply “approved”, or give changes by beat number (e.g. “04: leave on speaker”, “07: shorter text”). Nothing is designed until this is approved.</div>
</main></body></html>"""
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)


def moodboard(mb, kit, kit_root, out_path, base_dir):
    out_dir = os.path.dirname(os.path.abspath(out_path))
    pal = kit.get("palette", {})
    sw = []
    for role, v in pal.items():
        hexv = v["hex"] if isinstance(v, dict) else v
        share = (v.get("share") if isinstance(v, dict) else None)
        src = (v.get("from") if isinstance(v, dict) else "")
        sw.append(f'<div><div class="chipc" style="background:{_e(hexv)}"></div><div><strong>{_e(role)}</strong> '
                  f'<span class="tc">{_e(hexv)}{f" · {share}%" if share else ""}</span></div><div class="tc">{_e(src)}</div></div>')
    faces = htmlmod.font_faces(kit, kit_root)
    specimens = []
    sample = mb.get("specimen_text") or kit.get("series") or "The quick brown fox"
    for role, f in (kit.get("type") or {}).items():
        fam = f"'kit-{role}'" if f.get("file") else f"'{f.get('family', role)}'"
        size = {"display": 56, "text": 34, "subtitle": 40}.get(role, 40)
        specimens.append(f'<div class="card"><div class="tc">{_e(role)} · {_e(f.get("family", ""))} {_e(f.get("style", ""))}</div>'
                         f'<div class="spec" style="font-family:{fam},sans-serif;font-weight:{f.get("weight", 400)};font-size:{size}px">{_e(sample)}</div>'
                         f'<div class="tc">{_e(f.get("use", ""))}</div></div>')

    def media(items, tag):
        out = []
        for it in items or []:
            src = _e(_rel(os.path.join(base_dir, it[tag]), out_dir))
            el = (f'<img src="{src}" alt="">' if tag == "image" else
                  f'<video src="{src}" controls loop muted playsinline preload="metadata"></video>')
            out.append(f'<figure style="margin:0">{el}<figcaption class="tc" style="margin-top:6px">{_e(it.get("caption", ""))}</figcaption></figure>')
        return '<div class="media">' + "".join(out) + "</div>"

    sources = media(mb.get("sources"), "image")

    def krel(path):
        return _e(_rel(os.path.join(kit_root or ".", path), out_dir))

    series_parts = ""
    src = kit.get("sources") or {}
    if src.get("example"):
        series_parts += (f'<h2>Example (how the series art fits together)</h2><figure style="margin:0">'
                         f'<img src="{krel(src["example"])}" alt="" style="width:100%;border-radius:8px"></figure>')
    ca = kit.get("color_analysis") or {}
    if ca.get("swatches"):
        picked = ca.get("picked") or {}
        cells = []
        for w in ca["swatches"]:
            use = picked.get(w["hex"]) or next((r for r, v in pal.items()
                                               if (v["hex"] if isinstance(v, dict) else v).upper() == w["hex"].upper()), None)
            cls = "" if use and not str(use).startswith("not used") else ' class="unused"'
            cells.append(f'<div{cls}><div class="chipc" style="background:{_e(w["hex"])}"></div>'
                         f'<div class="tc">{_e(w["hex"])} · {w["share"] * 100:.0f}%</div><div class="tc">{_e(use or "not used")}</div></div>')
        img = f'<img src="{krel(ca["image"])}" alt="" style="width:100%;max-width:420px;border-radius:8px;display:block;margin-bottom:12px">' if ca.get("image") else ""
        series_parts += f'<h2>From the Colors photo</h2><div class="card">{img}<div class="picked">{"".join(cells)}</div></div>'
    tex = kit.get("textures") or []
    if tex:
        items = "".join(f'<figure style="margin:0"><img src="{krel(t["file"])}" alt="" style="aspect-ratio:1;object-fit:cover">'
                        f'<figcaption class="tc" style="margin-top:6px">{_e(t["file"])} · {_e(t.get("use", ""))}</figcaption></figure>' for t in tex)
        series_parts += f'<h2>Backgrounds</h2><div class="media">{items}</div>'
    assets = kit.get("assets") or []
    if assets:
        items = "".join(f'<figure style="margin:0"><div class="checker"><img src="{krel(a["file"])}" alt=""></div>'
                        f'<figcaption class="tc" style="margin-top:6px">{_e(a["file"])} · {_e(a.get("kind", ""))}'
                        f'{" · brand" if a.get("brand") else ""}<br>{_e(a.get("use", ""))}</figcaption></figure>' for a in assets)
        series_parts += f'<h2>Assets</h2><div class="assets">{items}</div>'
    draft = '<div class="draft">This kit is still a draft: the values below are suggestions to approve or change.</div>' if kit.get("draft") else ""
    lists = ""
    for key, title in (("signature_moves", "Signature moves for this series"), ("treatments", "Treatments in rotation"), ("avoid", "Deliberately avoiding")):
        vals = mb.get(key) or kit.get(key) or []
        if vals:
            items = "".join(f"<li>{_e(v if isinstance(v, str) else (v.get('name', '') + ' — ' + v.get('use', '')))}</li>" for v in vals)
            lists += f'<h2>{title}</h2><div class="card"><ul class="plain">{items}</ul></div>'
    m = kit.get("motion", {})
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mood board {_e(mb.get('project', ''))}</title><style>{faces}\n{CSS}</style></head><body><main>
<p class="tc">Mood board · gate 2 of 2</p>
<h1>{_e(kit.get('series', mb.get('series', '')))}</h1>
{draft}<p class="lede">{_e(mb.get('direction') or kit.get('personality', ''))}</p>
{('<h2>Taken from</h2>' + sources) if mb.get('sources') else ''}
{series_parts}
<h2>Palette</h2><div class="card sw">{''.join(sw)}</div>
<h2>Type</h2><div class="grid">{''.join(specimens)}</div>
<h2>Motion</h2><div class="card"><div class="meta"><span>Tempo ×{_e(m.get('tempo', 1.0))}</span><span>Travel {_e(m.get('distance', 24))}px</span>
<span>Entrances ease: {_e(m.get('ease_in', 'settle'))}</span><span>Exits: {_e(m.get('ease_out', 'exit'))}</span></div>
<p class="why">{_e(m.get('notes', ''))}</p></div>
{('<h2>Motion samples</h2>' + media(mb.get('motion'), 'video')) if mb.get('motion') else ''}
{('<h2>Stills</h2>' + media(mb.get('stills'), 'image')) if mb.get('stills') else ''}
{lists}
<div class="approve"><strong>To approve:</strong> reply “approved”, or say what to change (“palette lighter”, “less tracking on titles”, “subtitles smaller”). Graphics are built only after this.</div>
</main></body></html>"""
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
