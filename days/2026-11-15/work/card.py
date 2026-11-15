"""Add today's extra assets to assets.json: the 8 s 1080x1920 loop (funkbox loop render) and a code card of
the loop_check entry in its JSON sidecar (real file, verbatim lines, drawn by promo/assets.py's code_card)."""
import json, sys
from pathlib import Path
day = Path(sys.argv[1]); root = Path(sys.argv[2])
sys.path.insert(0, str(root / "promo"))
from assets import code_card
a = day / "assets"
man = json.loads((day / "assets.json").read_text())
man["assets"] = [x for x in man["assets"] if x["id"] not in ("canvas-loop", "card-loop-check")]
man["assets"].append({"id": "canvas-loop", "kind": "video", "path": "assets/canvas-loop.mp4",
    "note": "funkbox loop render --preset frozen-kaleido --seed 1115 --width 1080 --height 1920 --seconds 8; sidecar assets/canvas-loop.json records loop_check status ok",
    "seconds": 8})
path, span, box = code_card(a / "canvas-loop.json", '"loop_check"', 8, a / "card-loop-check.png", "canvas-loop.json")
man["assets"].append({"id": "card-loop-check", "kind": "image", "path": "assets/card-loop-check.png",
    "note": f"the loop_check entry in today's loop's JSON sidecar (assets/canvas-loop.json lines {span}, verbatim). Its text fills text_rect (top part); anchor captions at the bottom",
    "size": [1080, 1920], "source": f"assets/canvas-loop.json:{span}", "text_rect": box})
(day / "assets.json").write_text(json.dumps(man, indent=2) + "\n")
print(span, box)
