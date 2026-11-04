"""Spec -> self-contained HTML page with seek(t), for previews, mood-board stills and the
ProRes 4444 fallback render (engine/render.js). Same tracks and eases as the Fusion backend.

Every style is a pure function of t: no CSS transitions, no timers, no Math.random.
Fonts and images are embedded as base64 so a render never silently falls back.
"""
import base64
import json
import mimetypes
import os

from .spec import EASES, font_for, resolve_color, estimate_text_width, text_block_height, image_size, image_fit

FONT_MIME = {".otf": "font/otf", ".ttf": "font/ttf", ".woff": "font/woff", ".woff2": "font/woff2"}


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _image_data(path, dw, dh):
    """Embed an image; big textures (8K squares) are downscaled to what the frame shows, if Pillow is here."""
    mime = mimetypes.guess_type(path)[0] or "image/png"
    try:
        from PIL import Image
        import io
        with Image.open(path) as im:
            if im.width > dw * 1.5 and im.height > dh * 1.5:
                im = im.copy()
                im.thumbnail((int(dw * 1.25), int(dh * 1.25)), Image.LANCZOS)
                buf = io.BytesIO()
                if im.mode in ("RGBA", "LA", "P"):
                    im.save(buf, "PNG")
                    mime = "image/png"
                else:
                    im.convert("RGB").save(buf, "JPEG", quality=92)
                    mime = "image/jpeg"
                return mime, base64.b64encode(buf.getvalue()).decode("ascii")
    except ImportError:
        pass
    return mime, _b64(path)


def _rgba(c):
    r, g, b, a = c
    return f"rgba({round(r * 255)},{round(g * 255)},{round(b * 255)},{a:.3f})"


def font_faces(kit, kit_root):
    css = []
    for role, f in ((kit or {}).get("type") or {}).items():
        path = f.get("file")
        if not path:
            continue
        full = path if os.path.isabs(path) else os.path.join(kit_root or ".", path)
        if not os.path.exists(full):
            raise FileNotFoundError(f"kit font for role {role!r} not found: {full}")
        ext = os.path.splitext(full)[1].lower()
        fmt = {".otf": "opentype", ".ttf": "truetype", ".woff": "woff", ".woff2": "woff2"}[ext]
        css.append(f"@font-face{{font-family:'kit-{role}';src:url(data:{FONT_MIME[ext]};base64,{_b64(full)}) "
                   f"format('{fmt}');font-weight:{f.get('weight', 400)};font-style:normal;}}")
    return "\n".join(css)


def build(spec, kit, kit_root=None, asset_root=None, background=None):
    """background: None = transparent (alpha render); a colour; or a path to a still to preview over."""
    W, H = int(spec["width"]), int(spec["height"])
    layers = []
    html_layers = []
    for layer in spec["layers"]:
        kind = layer.get("type", "text")
        lx, ly = float(layer.get("x", W / 2)), float(layer.get("y", H / 2))
        item = {"id": layer["id"], "type": kind, "x": lx, "y": ly, "tracks": layer["tracks"],
                "align": layer.get("align", "left"), "anchor": layer.get("anchor", "left"),
                "tracking": float(layer.get("tracking", 0.0))}
        if kind == "text":
            f = font_for(layer, kit)
            fam = f"'kit-{layer.get('font', 'display')}'" if f.get("file") else f"'{f['family']}'"
            text = str(layer.get("text", ""))
            if layer.get("case") == "upper":
                text = text.upper()
            size = float(layer.get("size", 60))
            style = (f"font-family:{fam},sans-serif;font-size:{size}px;font-weight:{f.get('weight', 400)};"
                     f"line-height:{1.2 * float(layer.get('leading', 1.0))};color:{_rgba(resolve_color(layer.get('color', 'ink'), kit))};"
                     f"text-align:{item['align']};")
            if layer.get("italic") or "italic" in str(f.get("style", "")).lower():
                style += "font-style:italic;"
            esc = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>"))
            if layer.get("clip"):
                item["band"] = {"w": estimate_text_width(layer, kit) + 40, "h": text_block_height(layer) * 1.1}
            html_layers.append(f'<div class="L" id="{layer["id"]}"><div class="T" style="{style}">{esc}</div></div>')
        elif kind == "rect":
            item["w"], item["h"] = float(layer.get("w", 200)), float(layer.get("h", 2))
            col = _rgba(resolve_color(layer.get("color", "ink"), kit))
            rad = float(layer.get("radius", 0))
            html_layers.append(f'<div class="L R" id="{layer["id"]}" style="background:{col};border-radius:{rad}px"></div>')
        else:
            path = layer["src"]
            if asset_root and not os.path.isabs(path):
                path = os.path.join(asset_root, path)
            native = image_size(path) or (int(layer.get("native_w", 1000)), int(layer.get("native_h", 1000)))
            dw, dh, _ = image_fit(layer, native, W, H)
            mime, data = _image_data(path, dw, dh)
            item["w"], item["h"] = dw, dh
            html_layers.append(f'<div class="L" id="{layer["id"]}"><img src="data:{mime};base64,{data}" '
                               f'style="width:{dw:.1f}px;height:{dh:.1f}px;display:block"></div>')
        layers.append(item)

    bg_css = "transparent"
    alpha = background is None
    if background and os.path.exists(str(background)):
        mime = mimetypes.guess_type(background)[0] or "image/jpeg"
        bg_css = f"url(data:{mime};base64,{_b64(background)}) center/cover"
    elif background:
        bg_css = background

    data = {"W": W, "H": H, "T": float(spec["duration"]), "layers": layers, "eases": EASES}
    return f"""<!doctype html>
<html class="{'alpha' if alpha else ''}"><head><meta charset="utf-8"><title>{spec.get('id', 'graphic')}</title>
<style>
{font_faces(kit, kit_root)}
html,body{{margin:0;padding:0;background:transparent;}}
#stage{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:{bg_css};}}
.L{{position:absolute;left:0;top:0;transform-origin:0 0;will-change:auto;}}
.T{{white-space:pre;font-kerning:normal;text-rendering:geometricPrecision;}}
</style></head><body>
<div id="stage">
{chr(10).join(html_layers)}
</div>
<script>
const D={json.dumps(data)};
window.DURATION=D.T;
function bez(e,u){{const[x1,y1,x2,y2]=D.eases[e]||D.eases.glide;if(u<=0)return 0;if(u>=1)return 1;
 const bx=s=>3*x1*s*(1-s)**2+3*x2*s*s*(1-s)+s**3,by=s=>3*y1*s*(1-s)**2+3*y2*s*s*(1-s)+s**3;
 let lo=0,hi=1;for(let i=0;i<40;i++){{const m=(lo+hi)/2;if(bx(m)<u)lo=m;else hi=m;}}return by((lo+hi)/2);}}
function smp(k,t,def){{if(!k||!k.length)return def;if(t<=k[0][0])return k[0][1];
 for(let i=1;i<k.length;i++){{const a=k[i-1],b=k[i];if(t<=b[0]){{const sp=b[0]-a[0];const u=sp<=0?1:(t-a[0])/sp;
 return a[1]+(b[1]-a[1])*bez(b[2]||'glide',u);}}}}return k[k.length-1][1];}}
const els={{}};for(const l of D.layers)els[l.id]=document.getElementById(l.id);
function measure(){{for(const l of D.layers){{const e=els[l.id];l.mw=e.offsetWidth;l.mh=e.offsetHeight;}}}}
window.seek=function(t){{
 for(const l of D.layers){{const e=els[l.id],T=l.tracks;
  const op=smp(T.opacity,t,1),dx=smp(T.dx,t,0),dy=smp(T.dy,t,0),sc=smp(T.scale,t,1),bl=smp(T.blur,t,0);
  let x=l.x,y=l.y,w=l.mw,h=l.mh,ox=0,oy=0;
  if(l.type==='text'){{ox=l.align==='left'?0:l.align==='center'?w/2:w;oy=h/2;
    e.firstChild.style.letterSpacing=smp(T.tracking,t,l.tracking)+'em';}}
  else if(l.type==='rect'){{const dv=smp(T.draw,t,1);w=l.w*dv;h=l.h;e.style.width=w+'px';e.style.height=h+'px';
    ox=l.anchor==='left'?0:l.anchor==='right'?w:w/2;oy=h/2;}}
  else{{ox=w/2;oy=h/2;}}
  e.style.opacity=op;e.style.filter=bl>0.05?`blur(${{bl}}px)`:'none';
  e.style.transformOrigin=`${{ox}}px ${{oy}}px`;
  e.style.transform=`translate(${{x-ox+dx}}px,${{y-oy+dy}}px) scale(${{sc}})`;
  if(l.band){{const r=smp(T.reveal,t,1),o=smp(T.reveal_out,t,0);
    const bw=l.band.w,bh=l.band.h,left=(l.align==='left'?-20:l.align==='center'?w/2-bw/2:w-bw+20);
    const top=oy-bh/2-dy, L=left+bw*o, R=left+bw*r;
    e.style.clipPath=`polygon(${{L}}px ${{top}}px, ${{R}}px ${{top}}px, ${{R}}px ${{top+bh}}px, ${{L}}px ${{top+bh}}px)`;}}
 }}
}};
document.fonts.ready.then(()=>{{measure();seek(0);
 if(!location.search.includes('render')){{const t0=performance.now();(function loop(){{seek(((performance.now()-t0)/1000)%D.T);requestAnimationFrame(loop);}})();}}
}});
measure();seek(0);
</script></body></html>
"""


def write(spec, kit, out_path, kit_root=None, asset_root=None, background=None):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(build(spec, kit, kit_root, asset_root, background))
