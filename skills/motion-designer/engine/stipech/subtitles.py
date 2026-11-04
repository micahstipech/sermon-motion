"""Word timestamps -> clean 2-3 word subtitle chunks (+ SRT), and per-chunk graphic specs.

Input formats for `load_words`:
  * our words.json            [{"w": "Grace", "s": 1.20, "e": 1.48}, ...]
  * faster-whisper / WhisperX {"segments": [{"words": [{"word", "start", "end"}]}]}
  * SRT / VTT                 cue text spread across the cue by character count (~0.2 s accuracy)
"""
import json
import re

WEAK_END = {
    "a", "an", "the", "to", "of", "and", "but", "or", "in", "on", "at", "for", "with", "by", "from",
    "my", "your", "his", "her", "our", "their", "its", "is", "are", "was", "were", "be", "that",
    "this", "as", "if", "so", "not", "no", "than", "into", "unto", "who", "whom", "which", "i", "we",
    "you", "he", "she", "they", "it", "will", "can", "would", "could", "should", "has", "have", "had",
}
HARD_PUNCT = re.compile(r'[.?!;:]["”’)]*$')
SOFT_PUNCT = re.compile(r'[,—–-]["”’)]*$')


def _ts(x):
    return sum(float(v) * 60 ** i for i, v in enumerate(reversed(x.strip().replace(",", ".").split(":"))))


def load_words(path):
    text = open(path, encoding="utf-8-sig").read()
    if path.lower().endswith(".json"):
        data = json.loads(text)
        if isinstance(data, list):
            return [{"w": d["w"], "s": float(d["s"]), "e": float(d["e"])} for d in data]
        words = []
        for seg in data.get("segments", []):
            for w in seg.get("words", []):
                if "start" in w and "end" in w:
                    words.append({"w": w["word"].strip(), "s": float(w["start"]), "e": float(w["end"])})
        if not words:
            raise ValueError(f"{path}: no word timestamps (transcribe with word_timestamps=True)")
        return words
    words = []
    for blk in re.split(r"\n\s*\n", text.strip()):
        lines = blk.strip().split("\n")
        i = next((i for i, l in enumerate(lines[:3]) if "-->" in l), None)
        if i is None:
            continue
        a, b = [_ts(x.split()[0]) for x in lines[i].split("-->")]
        toks = re.sub(r"<[^>]*>", "", " ".join(lines[i + 1:])).split()
        if not toks:
            continue
        n = sum(len(w) + 1 for w in toks)
        c = 0
        for w in toks:
            s = a + (b - a) * c / n
            c += len(w) + 1
            words.append({"w": w, "s": round(s, 3), "e": round(a + (b - a) * (c - 1) / n, 3)})
    if not words:
        raise ValueError(f"{path}: no cues found (expected words.json, whisper JSON, SRT or VTT)")
    return words


def _bare(w):
    return re.sub(r"[^\w']", "", w.lower())


def chunk(words, max_words=3, max_chars=24, pause=0.35, min_dur=0.4, tail=0.2, punctuation="drop-trailing", case="as-spoken"):
    """Greedy chunker. Prefers breaks at punctuation and pauses, never ends on a weak word
    when the chunk can still grow, and keeps every chunk at 2-3 words where speech allows."""
    chunks = []
    cur = []

    def flush():
        if cur:
            chunks.append(list(cur))
            cur.clear()

    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        text_len = len(" ".join(x["w"] for x in cur))
        gap = (nxt["s"] - w["e"]) if nxt else 99
        hard = bool(HARD_PUNCT.search(w["w"]))
        soft = bool(SOFT_PUNCT.search(w["w"]))
        full = len(cur) >= max_words or (nxt and text_len + 1 + len(nxt["w"]) > max_chars)
        if nxt is None or hard or gap >= pause:
            flush()
        elif full:
            # don't strand a weak word at the end if the next chunk can take it
            if _bare(cur[-1]["w"]) in WEAK_END and len(cur) > 1 and not soft:
                carry = cur.pop()
                flush()
                cur.append(carry)
            else:
                flush()
        elif soft and len(cur) >= 2:
            flush()

    # merge lonely single words into a neighbour when speech allows (no pause / sentence end between)
    merged = []
    for c in chunks:
        if (merged and len(c) == 1 and len(merged[-1]) < max_words
                and not HARD_PUNCT.search(merged[-1][-1]["w"])
                and c[0]["s"] - merged[-1][-1]["e"] < pause
                and len(" ".join(x["w"] for x in merged[-1] + c)) <= max_chars):
            merged[-1].extend(c)
        else:
            merged.append(c)

    out = []
    for i, c in enumerate(merged):
        text = " ".join(x["w"] for x in c)
        if punctuation == "drop-trailing":
            text = re.sub(r"[,.;:—–-]+([\"”’)]*)$", r"\1", text)
        elif punctuation == "none":
            text = re.sub(r"[^\w\s'?!]", "", text)
        if case == "lower":
            text = text.lower()
        elif case == "upper":
            text = text.upper()
        s = c[0]["s"]
        e = c[-1]["e"] + tail
        nxt = merged[i + 1][0]["s"] if i + 1 < len(merged) else None
        if nxt is not None:
            if e > nxt or nxt - e < 0.12:  # no overlaps, no single-frame flicker gaps
                e = nxt
        if e - s < min_dur:
            e = s + min_dur if nxt is None else min(nxt, s + min_dur)
        out.append({"i": i + 1, "text": text, "s": round(s, 3), "e": round(e, 3), "words": len(c)})
    return out


def srt(chunks):
    def tc(t):
        ms = int(round(t * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    return "\n".join(f"{c['i']}\n{tc(c['s'])} --> {tc(c['e'])}\n{c['text']}\n" for c in chunks)


def chunk_spec(c, kit, width=1920, height=1080, fps=24):
    """One subtitle as a graphic spec: clean, no animation (cut in, cut out), optional soft shadow."""
    st = (kit or {}).get("subtitles", {})
    size = float(st.get("size", 46))
    y = float(st.get("y", height * 0.86))
    layers = []
    if st.get("shadow", True):
        layers.append({
            "id": "Shadow", "type": "text", "text": c["text"], "font": st.get("font", "subtitle"),
            "size": size, "x": width / 2, "y": y + size * 0.05, "align": "center",
            "color": st.get("shadow_color", "#000000@35"), "tracking": float(st.get("tracking", 0.0)),
            "case": st.get("case_transform"),
            "anim": {"blur": [[0, float(st.get("shadow_blur", 6))]]},
        })
    layers.append({
        "id": "Subtitle", "type": "text", "text": c["text"], "font": st.get("font", "subtitle"),
        "size": size, "x": width / 2, "y": y, "align": "center",
        "color": st.get("color", "#FFFFFF"), "tracking": float(st.get("tracking", 0.0)),
        "case": st.get("case_transform"),
    })
    return {"id": f"sub-{c['i']:04}", "kind": "subtitle", "width": width, "height": height, "fps": fps,
            "duration": round(c["e"] - c["s"], 3), "in": c["s"], "layers": layers}
