"""Coordinate search over a few tune parameters, scoring each candidate with funkbox's poster_compare.
    python opt.py VARIANT START_TUNE OUT_TUNE key.path:step ...  (e.g. letters.y:0.01)"""
import copy, json, sys, os, time
sys.path.insert(0, "/home/claude/build/tools"); sys.path.insert(0, "/home/claude/work/funkbox")
os.chdir("/home/claude/work/funkbox")
import gen
from funkbox.stills import render, compare
from PIL import Image
E = "/home/claude/build/days/2026-11-01/emblem"
REF = {"a": "A-faithful", "b": "B-idf-gold", "c": "C-hybrid"}
v, start, out = sys.argv[1], sys.argv[2], sys.argv[3]
keys = [(k.split(":")[0], float(k.split(":")[1])) for k in sys.argv[4:]]
ref = Image.open(f"/home/claude/build/days/2026-11-01/refs/{REF[v]}.png").convert("RGB")
cache = {}

def score(t):
    k = json.dumps(t, sort_keys=True)
    if k not in cache:
        doc = gen.build(v, 0, t)
        try:
            r = render.render_document(doc, base_dir=E, scale=float(os.environ.get("SCALE", 0.35)))
        except Exception as e:
            print("ERR", e); cache[k] = -1; return -1
        im = Image.fromarray(r.image)
        cache[k] = compare.compare(im, ref).scores["overall"]
    return cache[k]

def get(t, path):
    for p in path.split(".")[:-1]: t = t[p]
    return t, path.split(".")[-1]

def getp(t, path):
    cur = t
    for p in path.split("."):
        cur = cur[p] if not isinstance(cur, list) else cur[int(p)]
    return cur

def setp(t, path, val):
    parts = path.split("."); cur = t
    for p in parts[:-1]:
        cur = cur[p] if not isinstance(cur, list) else cur[int(p)]
    last = parts[-1]
    if isinstance(cur, list): cur[int(last)] = val
    else: cur[last] = val

t = json.load(open(start))
best = score(t); print("start", best, flush=True)
for rnd in range(int(os.environ.get("ROUNDS", 3))):
    improved = False
    for path, step in keys:
        st = step / (2 ** rnd)
        for d in (st, -st):
            c = copy.deepcopy(t); setp(c, path, round(getp(c, path) + d, 5))
            s = score(c)
            if s > best + 0.05:
                best, t, improved = s, c, True
                print(rnd, path, getp(t, path), best, flush=True)
                # keep going in the same direction
                while True:
                    c = copy.deepcopy(t); setp(c, path, round(getp(c, path) + d, 5)); s = score(c)
                    if s > best + 0.05:
                        best, t = s, c; print(rnd, path, getp(t, path), best, flush=True)
                    else: break
                break
    if not improved and rnd > 0: pass
json.dump(t, open(out, "w"), ensure_ascii=False, indent=1)
print("best", best)
