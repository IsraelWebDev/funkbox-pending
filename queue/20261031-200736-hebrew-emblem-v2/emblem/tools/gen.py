#!/usr/bin/env python3
"""Writes the emblem *.poster.json files (A faithful, B gold, C hybrid) from pixel coordinates.

Every element is a funkbox poster layer: shape (polygon, rect, path, polyline), solid, gradient, text. Nothing is
imported from the reference pictures; they are only scored against with `funkbox poster compare`.

    python gen.py OUT_DIR VARIANT DRAFT      # VARIANT a|b|c
"""
import json
import math
import sys
from pathlib import Path

W, H = 1400, 1440


def P(x, y):
    return [round(x / W, 5), round(y / H, 5)]


def poly(id_, pts, fill, stroke=None, px=0, **kw):
    lay = {"id": id_, "type": "shape", "kind": "polygon", "points": [P(*p) for p in pts], "fill": fill}
    if stroke:
        lay |= {"stroke": stroke, "stroke_px": px}
    return lay | kw


def path(id_, d, fill, stroke=None, px=0, **kw):
    lay = {"id": id_, "type": "shape", "kind": "path", "units": "px", "d": d, "fill": fill}
    if stroke:
        lay |= {"stroke": stroke, "stroke_px": px}
    return lay | kw


def arc_pts(cx, cy, r, a0, a1, n=33):
    """Points on a circle (angles in degrees from straight down, + to the right)."""
    out = []
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * i / (n - 1))
        out.append((cx + r * math.sin(a), cy + r * math.cos(a)))
    return out


# ------------------------------------------------------------------ palettes
PAL = {
    "a": dict(navy="#1b224b", white="#ffffff", yellow="#fdd94e", red="#ec334b", blue="#3e61ad",
              letter="#ffffff", band_text="#3e61ad", ribbon="#fdd94e", ribbon_text="#1b224b",
              ribbon_line="#1b224b", top_text="#1b224b"),
}
PAL["b"] = dict(navy="#2b2416", white="#d8b55e", yellow="#d3b365", red="#4b5320", blue="#3a3424",
                letter="#f6e7b4", band_text="#4b5320", ribbon="#3a2e1f", ribbon_text="#e8cc7a",
                ribbon_line="#2b2416", top_text="#2b2416")
PAL["c"] = dict(PAL["a"], ribbon="#3a2e1c", ribbon_text="#e8cc7a", ribbon_line="#1b224b")

TOP = "צבאות ה׳ לישראל"


def build(variant: str, draft: int, tune: dict) -> dict:
    c = PAL[variant]
    t = tune
    star = variant in ("b", "c") and not t.get("shield_only")
    # geometry of the shield (A is the full-size layout; B and C put a smaller shield on a star)
    s = t.get("shield_scale", 1.0 if not star else 0.716)
    ox, oy = t.get("shield_dx", 0), t.get("shield_dy", 0 if not star else 262)

    def T(x, y):                                     # shield space -> canvas px
        return (700 + (x - 700) * s + ox, 113 + (y - 113) * s + oy) if star else (x, y)

    def TP(pts):
        return [T(*p) for p in pts]

    def d_of(cmds):
        out = []
        for cmd, *pts in cmds:
            out.append(cmd + " " + " ".join(f"{T(*p)[0]:.1f},{T(*p)[1]:.1f}" for p in pts))
        return " ".join(out) + " Z"

    sp = lambda v: v * s                             # noqa: E731 - scale a length
    layers = [{"id": "bg", "type": "solid", "color": "#ffffff"}]

    if t.get("shield_only"):                         # the shield alone, on a transparent canvas
        layers = []
    if star:
        layers += star_layers(t)
        if t.get("svg_shield"):                      # the shield poster's own SVG export, scaled onto the star
            sv = t["svg_shield"]
            layers.append({"id": "shield-svg", "type": "svg", "path": sv, "x": round(T(0, 0)[0] / W, 5),
                           "y": round(T(0, 0)[1] / H, 5), "width": round(s, 5)})
            return {"version": 1, "name": f"emblem-{variant}-d{draft}",
                    "canvas": {"width": W, "height": H, "background": "#ffffff"},
                    "layers": layers, "export": {"formats": ["png", "svg"]}}

    # outer white shield with its navy rim (stroke drawn outside the shape)
    L, R, top = 220, 1179, 122
    outer = [("M", (L, top)), ("L", (R, top)), ("L", (R, 850)), ("Q", (R, 928), (1100, 968)),
             ("L", (700, 1168)), ("L", (300, 968)), ("Q", (L, 928), (L, 850))]
    layers.append(path("rim", d_of(outer), c["white"] if variant != "b" else "#d9b25e", c["navy"],
                       max(2, round(sp(10)))))
    # the four slots in the rim's crenellation
    for i, cx in enumerate((405, 601, 797, 994)):
        layers.append(poly(f"slot{i}", TP([(cx - 10, 112), (cx + 10, 112), (cx + 10, 172), (cx - 10, 172)]), c["navy"]))
    # inner shield: crenellated top band, filled with the band colour
    L2, R2, top2, nb = 253, 1146, 155, 206
    notches = [(361, 449), (557, 645), (754, 842), (950, 1038)]
    cmds = [("M", (L2, top2))]
    for a, b in notches:
        cmds += [("L", (a, top2)), ("L", (a, nb)), ("L", (b, nb)), ("L", (b, top2))]
    cmds += [("L", (R2, top2)), ("L", (R2, 840)), ("Q", (R2, 908), (1070, 946)), ("L", (700, 1131)),
             ("L", (330, 946)), ("Q", (L2, 908), (L2, 840))]
    band_fill = c["yellow"]
    if variant == "b":
        layers.append(path("shield", d_of(cmds), "#d9b25e", c["navy"], max(2, round(sp(10)))))
        layers.append({"id": "band-gold", "type": "gradient", "kind": "linear", "angle": 90,
                       "stops": [{"pos": 0, "color": "#e2c27a"}, {"pos": 1, "color": "#b48b3c"}], "clip": "shield"})
        if t.get("shield_only"):                     # an imported SVG keeps no clip: a flat gold band instead
            layers.pop()
    else:
        layers.append(path("shield", d_of(cmds), band_fill, c["navy"], max(2, round(sp(10)))))
    # field: the lower part of the shield, split on the diagonal (clipped to the shield)
    split = t.get("split", (388, 922))
    # field: the lower part of the shield (its own outline, so no clip is needed), split on the diagonal
    fl = [("M", (L2, 394)), ("L", (R2, 394)), ("L", (R2, 840)), ("Q", (R2, 908), (1070, 946)), ("L", (700, 1131)),
          ("L", (330, 946)), ("Q", (L2, 908), (L2, 840))]
    layers.append(path("field-low", d_of(fl), c["blue"]))
    layers.append(poly("field-high", TP([(L2, 394), (R2, 394), (R2, 850), (1125, 905), (L2, 388)]), c["red"]))
    if t.get("split_line"):
        layers.append({"id": "split-line", "type": "shape", "kind": "polyline",
                       "points": [P(*T(L2, 388)), P(*T(1125, 905))], "width": round(sp(t["split_line"]) / W, 5),
                       "fill": c["navy"], "cap": "butt"})
    fc = [("M", (L2, 394)), ("L", (R2, 394)), ("L", (R2, 840)), ("Q", (R2, 908), (1070, 946)), ("L", (700, 1131)),
          ("L", (330, 946)), ("Q", (L2, 908), (L2, 840))]
    layers.append(path("field-clip", d_of(fc), "#000000", opacity=0.0))
    lc = [("M", (L2, 394)), ("L", (R2, 394)), ("L", (R2, 810)), ("L", (578, 1070)), ("L", (330, 946)),
          ("Q", (L2, 908), (L2, 840))]
    layers.append(path("letters-clip", d_of(lc), "#000000", opacity=0.0))
    layers.append(poly("divider", TP([(242, 384), (1157, 384), (1157, 394), (242, 394)]), c["navy"]))

    # Hebrew title, right to left, from the copy deck
    tx, ty, tsz = t.get("top", (0.19, 0.172, 0.071))
    if star:
        tx, ty, tsz = (0.5 - (0.5 - tx) * s + ox / W, (113 + (ty * H - 113) * s + oy) / H, tsz * s)
    layers.append({"id": "title", "type": "text", "copy_id": "top", "style": "display", "size": round(tsz, 4),
                   "x": round(tx, 4), "y": round(ty, 4), "max_width": round(1 - 2 * tx, 4), "align": "center",
                   "color": c["top_text"], "wrap": False})

    # centre block letters: one text layer, slanted like the shield's isometric letters
    lt = t.get("letters", {})
    lx, ly, lsz, lw = lt.get("x", 0.19), lt.get("y", 0.27), lt.get("size", 0.36), lt.get("w", 0.62)
    if star:
        lx, ly, lsz, lw = (0.5 - (0.5 - lx) * s + ox / W, (113 + (ly * H - 113) * s + oy) / H, lsz * s, lw * s)
    lay = {"id": "letters", "type": "text", "copy_id": "centre", "style": "display", "size": round(lsz, 4),
           "x": round(lx, 4), "y": round(ly, 4), "max_width": round(lw, 4), "align": "center",
           "color": c["letter"], "wrap": False, "skew_y": lt.get("skew_y", 30),
           "effects": {"stroke": {"width": lt.get("stroke", 0.03), "color": c["navy"]}}}
    if lt.get("spacing"):
        lay["letter_spacing"] = lt["spacing"]
    if lt.get("targets"):                            # each letter at its own place: a stepped baseline path
        lay.pop("skew_y")
        px = round(lsz * H)
        per = lt.get("per", {})                       # per letter: {"צ": {"font": ..., "scale": ...}}
        cs = centres(lt["font"], "צהל", px, lt.get("spacing", 0.0), per)
        trk = lt.get("spacing", 0.0) * px / 2         # on_path centres the advance, which includes the tracking
        tg = [(x + trk, y) for x, y in (T(*p) for p in lt["targets"])]
        pts = stepped_path(cs, tg)
        lay["on_path"] = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        lay["path_units"] = "px"
        lay["align"] = "left"
    if lt.get("clip") and not t.get("patch"):
        lay["clip"] = lt["clip"]
    if lt.get("font"):
        lay["runs"] = [{"match": "צהל", "font": lt["font"]}] + [
            {"match": ch, **v} for ch, v in lt.get("per", {}).items()]
    layers.append(lay)
    if t.get("patch"):     # instead of a clip (an imported SVG drops clips): repaint the field below the band
        pb = [("M", (578, 1070)), ("L", (1146, 810)), ("L", (1146, 840)), ("Q", (1146, 908), (1070, 946)),
              ("L", (700, 1131))]
        layers.append(path("patch-low", d_of(pb), c["blue"]))
        layers.append(poly("patch-high", TP([(1028, 848), (1146, 790), (1146, 850), (1125, 905)]), c["red"]))
        if t.get("split_line"):
            layers.append({"id": "split-line-2", "type": "shape", "kind": "polyline",
                           "points": [P(*T(1000, 831)), P(*T(1125, 905))],
                           "width": round(sp(t["split_line"]) / W, 5), "fill": c["navy"], "cap": "butt"})

    # the slanted white band that carries the English line
    bd = t.get("band", [(325, 1080), (670, 908), (730, 878), (1105, 690), (1105, 810), (730, 995), (670, 1030),
                        (455, 1145)])
    layers.append(poly("band", TP(bd), "#ffffff" if variant != "b" else "#f5e4b0", c["navy"], max(2, round(sp(9)))))
    if t.get("leg"):
        layers.append(poly("leg", TP(t["leg"]), c["letter"], c["navy"], max(2, round(sp(9)))))
    et = t.get("eng", {})
    ex, ey, esz, ew = et.get("x", 0.29), et.get("y", 0.62), et.get("size", 0.04), et.get("w", 0.5)
    if star:
        ex, ey, esz, ew = (0.5 - (0.5 - ex) * s + ox / W, (113 + (ey * H - 113) * s + oy) / H, esz * s, ew * s)
    eng = {"id": "eng", "type": "text", "copy_id": "army", "style": "caption", "size": round(esz, 4),
           "x": round(ex, 4), "y": round(ey, 4), "max_width": round(ew, 4), "align": "center",
           "color": c["band_text"], "wrap": False, "skew_y": et.get("skew_y", -28)}
    ef = et.get("font", "Exo 2:600:italic")
    eng["runs"] = [{"match": "Army of Hashem for Israel", "font": ef}]
    if et.get("gap"):                                 # widen only the space after "of" (the leg stands there):
        # the space takes a font with a wide space glyph, scaled; "of" itself is set back to the line's font
        eng["runs"] += [{"match": "of ", "scale": et["gap"], "all": False, "font": et.get("gap_font", ef)},
                        {"match": "of", "scale": 1.0, "all": False, "font": ef}]
    layers.append(eng)

    # ribbon: tails, an arched band, and the motto set on the same circle
    rb = t.get("ribbon", {})
    cx, cy, r, half, wid = 700, rb.get("cy", 160), rb.get("r", 1082), rb.get("half", 31.5), rb.get("w", 0.079)
    if star:
        cx, cy, r = T(cx, cy)[0], T(cx, cy)[1], r * s
        wid *= s
    tail_l = rb.get("tail", [(40, 1050), (115, 1040), (148, 965), (220, 1020), (185, 1170)])
    tl = TP(tail_l) if star else tail_l
    tr = [(2 * (700 + ox) - x, y) for x, y in tl] if star else [(1400 - x, y) for x, y in tail_l]
    layers.append(poly("tail-l", tl, c["ribbon"], c["ribbon_line"], max(2, round(sp(9)))))
    layers.append(poly("tail-r", tr, c["ribbon"], c["ribbon_line"], max(2, round(sp(9)))))
    layers.append({"id": "ribbon", "type": "shape", "kind": "polyline",
                   "points": [P(*p) for p in arc_pts(cx, cy, r, -half, half)], "width": round(wid, 4),
                   "fill": c["ribbon"], "stroke": c["ribbon_line"], "stroke_px": max(2, round(sp(9))), "cap": "butt"})
    mt = t.get("motto", {})
    msz = mt.get("size", 0.075) * (s if star else 1)
    my = (cy + r) / H - msz * mt.get("lift", 0.62)
    layers.append({"id": "motto", "type": "text", "copy_id": "motto", "style": "caption", "size": round(msz, 4),
                   "x": round(mt.get("x", 0.12), 4) if not star else round(0.5 - (0.5 - mt.get("x", 0.12)) * s, 4),
                   "y": round(my, 4),
                   "max_width": round(1 - 2 * mt.get("x", 0.12), 4) if not star else round((1 - 2 * mt.get("x", 0.12)) * s, 4),
                   "align": "center", "color": c["ribbon_text"], "wrap": False,
                   "arc": round(r / W * mt.get("arc_k", 1.0), 4), "letter_spacing": mt.get("spacing", 0.0) or None})
    if layers[-1]["letter_spacing"] is None:
        del layers[-1]["letter_spacing"]

    return {"version": 1, "name": f"emblem-{variant}-d{draft}", "canvas": {"width": W, "height": H, "background": "transparent" if t.get("shield_only") else "#ffffff"},
            "copy": "emblem.copy.json",
            "brand": {"primary": c["red"], "secondary": c["navy"], "text": c["navy"],
                      "font_display": t.get("font_display", "Rubik:800"),
                      "font_caption": t.get("font_caption", "Exo 2:700"),
                      "font_fallback": "Rubik:800"},
            "layers": layers, "export": {"formats": ["png", "svg"]}}


def centres(font: str, text: str, px: int, spacing: float, per: dict | None = None) -> list:
    """Arc-length positions of each glyph's centre, left to right, as funkbox's on_path will place them."""
    sys.path.insert(0, "/home/claude/work/funkbox")
    from funkbox import fonts
    from funkbox.stills.typeset import _Line
    p = fonts.resolve(font, ".")
    per = per or {}
    attrs = [(fonts.resolve(per[ch]["font"], ".") if per.get(ch, {}).get("font") else p,
              float(per.get(ch, {}).get("scale", 1.0)), (0, 0, 0, 255)) for ch in text]
    line = _Line(text, attrs, px, spacing)
    return [gx + adv / 2 for _, _, gx, _, adv in line.glyphs(0, len(text), True)]


def stepped_path(cs: list, targets: list) -> list:
    """A path whose arc length puts glyph centre i at targets[i] = (x, baseline y), on a level piece; the extra
    length between two letters is spent going up and down at the gap."""
    (x0, b0) = targets[0]
    pts = [(x0 - cs[0] - 10, b0), (x0, b0)]
    for k in range(1, len(cs)):
        (xa, ba), (xb, bb) = targets[k - 1], targets[k]
        ds, dx = cs[k] - cs[k - 1], xb - xa
        rest = ds - dx
        if rest < abs(bb - ba):
            raise SystemExit(f"letters {k-1}->{k}: need more letter_spacing ({rest:.0f} < {abs(bb - ba):.0f})")
        ye = min(ba, bb) - (rest - abs(bb - ba)) / 2
        xm = xa + dx / 2
        pts += [(xm - 2, ba), (xm - 2, ye), (xm + 2, ye), (xm + 2, bb), (xb, bb)]
        # (a 4 px wide loop, so the up and down strokes are not merged into one line)
    xl, bl = targets[-1]
    pts.append((xl + 600, bl))
    return pts


def star_layers(t: dict) -> list:
    """The six-pointed star with a gold rim, the sword and olive leaves (B and C). The star's sides bow inward
    (quadratic curves pulled toward the centre by star_bow)."""
    cx, cy = 700, t.get("star_cy", 700)
    R, r = t.get("star_R", 690), t.get("star_r", 400)
    bow, rim = t.get("star_bow", 0.0), t.get("star_rim", 0.95)

    def star_d(k):
        pts = []
        for i in range(12):
            a = math.radians(i * 30)
            rad = (R if i % 2 == 0 else r) * k
            pts.append((cx + rad * math.sin(a), cy - rad * math.cos(a)))
        d = f"M {pts[0][0]:.1f},{pts[0][1]:.1f}"
        for i in range(1, 13):
            p0, p1 = pts[i - 1], pts[i % 12]
            mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
            qx, qy = mx + (cx - mx) * bow, my + (cy - my) * bow
            d += f" Q {qx:.1f},{qy:.1f} {p1[0]:.1f},{p1[1]:.1f}"
        return d + " Z"
    out = [path("star-rim", star_d(1.0), "#c9a253", "#2b2416", int(t.get("star_stroke", 5))),
           {"id": "star-gold", "type": "gradient", "kind": "linear", "angle": 45,
            "stops": [{"pos": 0, "color": "#e6c77a"}, {"pos": 0.5, "color": "#a8822f"}, {"pos": 1, "color": "#e6c77a"}],
            "clip": "star-rim"},
           path("star-face", star_d(rim), "#3a3020", "#2b2416", 4),
           {"id": "star-shade", "type": "gradient", "kind": "radial", "cx": 0.5, "cy": 0.45, "radius": 0.6,
            "stops": [{"pos": 0, "color": "#4a3f2a"}, {"pos": 1, "color": "#2e2618"}], "clip": "star-face"}]
    # crossguard of the sword, low behind the shield
    out.append(poly("guard", [(560, 1040), (840, 1040), (840, 1078), (560, 1078)], "#c9a253", "#2b2416", 4))
    # sword: blade up the middle, pommel at the bottom
    out.append(poly("blade", [(672, 380), (672, 80), (700, 40), (728, 80), (728, 380)], "#c9a253", "#2b2214", 4))
    out.append(poly("hilt", [(684, 1170), (716, 1170), (716, 1225), (684, 1225)], "#c9a253", "#2b2214", 4))
    out.append({"id": "pommel", "type": "shape", "kind": "ellipse", "points": [P(668, 1212), P(732, 1276)],
                "fill": "#c9a253", "stroke": "#2b2214", "stroke_px": 4})
    # olive branch on the right: a stem and leaves
    out.append({"id": "stem", "type": "shape", "kind": "polyline", "points": [P(940, 218), P(995, 380)],
                "width": 0.009, "fill": "#e6c77a", "stroke": "#2b2214", "stroke_px": 3, "cap": "butt"})
    lx, ly = t.get("leaf_dx", 0), t.get("leaf_dy", 0)
    for i, (x, y, w, h) in enumerate([(890, 325, 95, 50), (1030, 400, 55, 115), (1030, 620, 75, 105),
                                      (1025, 830, 60, 80)]):
        x, y = x + lx, y + ly
        out.append({"id": f"leaf{i}", "type": "shape", "kind": "ellipse", "points": [P(x, y), P(x + w, y + h)],
                    "fill": "#d4b060", "stroke": "#2b2214", "stroke_px": 4})
    return out


if __name__ == "__main__":
    out, variant, draft = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
    tune = json.loads(Path(sys.argv[4]).read_text()) if len(sys.argv) > 4 else {}
    doc = build(variant, draft, tune)
    stem = f"emblem-{variant}{'-shield' if tune.get('shield_only') else ''}-draft{draft}"
    doc["name"] = stem
    f = out / f"{stem}.poster.json"
    f.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f)
