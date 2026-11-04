"""Variation ledger: remembers what each video used so intros, outros and treatments never settle
into a recognisable template. Branding assets (beats marked "brand": true) are exempt.

house/ledger.json:
{"projects": [{"project", "date", "series",
               "intro": {"kind", "treatment_in", "zone", "idea"},
               "outro": {...},
               "graphics": [{"kind", "treatment_in", "treatment_out", "zone"}]}]}
"""
import datetime
import json
import os

LOOKBACK = 8


def _load(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"projects": []}


def _sig(b):
    return (b.get("kind"), b.get("treatment_in"), b.get("zone"))


def _summary(board):
    beats = [b for b in board.get("beats", []) if b.get("kind") not in (None, "nothing") and not b.get("brand")]
    return {
        "project": board.get("project"),
        "date": board.get("date") or datetime.date.today().isoformat(),
        "series": board.get("series"),
        "intro": {k: (board.get("intro") or {}).get(k) for k in ("kind", "treatment_in", "zone", "idea")},
        "outro": {k: (board.get("outro") or {}).get(k) for k in ("kind", "treatment_in", "zone", "idea")},
        "graphics": [{k: b.get(k) for k in ("kind", "treatment_in", "treatment_out", "zone")} for b in beats],
    }


def check(board, ledger_path):
    led = _load(ledger_path)
    past = [p for p in led["projects"] if p.get("project") != board.get("project")][-LOOKBACK:]
    cur = _summary(board)
    errs, warns = [], []
    for end in ("intro", "outro"):
        mine = cur[end]
        if not mine.get("kind"):
            continue
        for p in past:
            other = p.get(end) or {}
            if _sig(mine) == _sig(other):
                errs.append(f"{end} repeats {p['project']} ({mine['kind']} / {mine['treatment_in']} / {mine['zone']}). Make a new one.")
            elif p is past[-1] and mine.get("treatment_in") and mine["treatment_in"] == other.get("treatment_in"):
                warns.append(f"{end} uses the same entrance as the previous video ({mine['treatment_in']}).")
    if cur["intro"].get("kind") and _sig(cur["intro"]) == _sig(cur["outro"]):
        errs.append("intro and outro are the same treatment: bookending with one move reads as a template.")
    if past:
        prev = past[-1]
        prev_sigs = [_sig(g) for g in prev.get("graphics", [])]
        repeats = [s for s in {_sig(g) for g in cur["graphics"]} if prev_sigs.count(s) >= 2]
        for s in repeats:
            warns.append(f"previous video ({prev['project']}) used {s} twice or more; this one uses it again.")
    tins = [g["treatment_in"] for g in cur["graphics"] if g.get("treatment_in")]
    for t in set(tins):
        if len(tins) >= 5 and tins.count(t) / len(tins) > 0.5:
            warns.append(f"'{t}' is {tins.count(t)}/{len(tins)} entrances in this storyboard.")
    return errs, warns


def add(board, ledger_path):
    led = _load(ledger_path)
    cur = _summary(board)
    led["projects"] = [p for p in led["projects"] if p.get("project") != cur["project"]] + [cur]
    os.makedirs(os.path.dirname(os.path.abspath(ledger_path)), exist_ok=True)
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(led, f, indent=1)
    return cur
