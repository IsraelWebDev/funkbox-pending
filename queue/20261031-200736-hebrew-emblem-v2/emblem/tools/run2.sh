#!/bin/bash
# run2.sh VARIANT DRAFT TUNE_BASE: renders the shield poster (palette VARIANT, full size), then the star poster
# that places the shield's SVG export, then compares the star poster with the reference.
set -e
V=$1; D=$2; TUNE=$3
E=/home/claude/build/days/2026-11-01/emblem
cd /home/claude/work/funkbox
export FUNK_GL_BACKEND=egl FUNK_INPUTS=/home/claude/build/days FUNK_OUT=/home/claude/build/days
python3 - "$TUNE" "$E/tune-$V$D-shield.json" "$E/tune-$V$D-star.json" "$E/renders/emblem-$V-shield-draft$D.svg" <<'PY'
import json, sys
t = json.load(open(sys.argv[1]))
sh = dict(t, shield_only=True); json.dump(sh, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
st = dict(t, svg_shield=sys.argv[4]); json.dump(st, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
PY
python3 /home/claude/build/tools/gen.py $E $V $D $E/tune-$V$D-shield.json >/dev/null
python -m funkbox poster render $E/emblem-$V-shield-draft$D.poster.json --name emblem-$V-shield-draft$D --out $E/renders --formats png,svg 2>&1 | grep -iE "error|warn" || true
python3 /home/claude/build/tools/gen.py $E $V $D $E/tune-$V$D-star.json >/dev/null
case $V in b) REF=B-idf-gold;; c) REF=C-hybrid;; esac
python -m funkbox poster render $E/emblem-$V-draft$D.poster.json --name emblem-$V-draft$D --out $E/renders --formats png,svg 2>&1 | grep -iE "error|warn" || true
python -m funkbox poster compare $E/renders/emblem-$V-draft$D.png /home/claude/build/days/2026-11-01/refs/$REF.png --name compare-$V-draft$D --out $E/compare 2>&1 | tail -6
